from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, deque
import json
import jsonlines
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Concept, Prerequisite, Subject, Domain
from app.models.concept import DifficultyLevel
from app.models.prerequisite import PrerequisiteType


class TaxonomyService:
    """Service for taxonomy data operations: JSONL import/export, graph algorithms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # JSONL Import/Export
    async def export_to_jsonl(self, filepath: str) -> Dict[str, int]:
        """Export all taxonomy data to JSONL files."""
        counts = {"subjects": 0, "domains": 0, "concepts": 0, "prerequisites": 0}

        # Export subjects
        with jsonlines.open(f"{filepath}_subjects.jsonl", mode="w") as writer:
            result = await self.db.execute(select(Subject))
            for subject in result.scalars().all():
                writer.write(subject.to_dict())
                counts["subjects"] += 1

        # Export domains
        with jsonlines.open(f"{filepath}_domains.jsonl", mode="w") as writer:
            result = await self.db.execute(select(Domain))
            for domain in result.scalars().all():
                writer.write(domain.to_dict())
                counts["domains"] += 1

        # Export concepts
        with jsonlines.open(f"{filepath}_concepts.jsonl", mode="w") as writer:
            result = await self.db.execute(select(Concept))
            for concept in result.scalars().all():
                writer.write(concept.to_dict())
                counts["concepts"] += 1

        # Export prerequisites
        with jsonlines.open(f"{filepath}_prerequisites.jsonl", mode="w") as writer:
            result = await self.db.execute(select(Prerequisite))
            for prereq in result.scalars().all():
                writer.write(prereq.to_dict())
                counts["prerequisites"] += 1

        return counts

    async def import_from_jsonl(self, filepath: str) -> Dict[str, int]:
        """Import taxonomy data from JSONL files."""
        counts = {"subjects": 0, "domains": 0, "concepts": 0, "prerequisites": 0}

        # Import subjects first (no dependencies)
        try:
            with jsonlines.open(f"{filepath}_subjects.jsonl", mode="r") as reader:
                for obj in reader:
                    subject = Subject(**obj)
                    self.db.add(subject)
                    counts["subjects"] += 1
            await self.db.commit()
        except FileNotFoundError:
            pass

        # Import domains (depends on subjects)
        try:
            with jsonlines.open(f"{filepath}_domains.jsonl", mode="r") as reader:
                for obj in reader:
                    domain = Domain(**obj)
                    self.db.add(domain)
                    counts["domains"] += 1
            await self.db.commit()
        except FileNotFoundError:
            pass

        # Import concepts (depends on subjects and domains)
        try:
            with jsonlines.open(f"{filepath}_concepts.jsonl", mode="r") as reader:
                for obj in reader:
                    # Convert difficulty string to enum
                    if obj.get("difficulty"):
                        obj["difficulty"] = DifficultyLevel(obj["difficulty"])
                    concept = Concept(**obj)
                    self.db.add(concept)
                    counts["concepts"] += 1
            await self.db.commit()
        except FileNotFoundError:
            pass

        # Import prerequisites last (depends on concepts)
        try:
            with jsonlines.open(f"{filepath}_prerequisites.jsonl", mode="r") as reader:
                for obj in reader:
                    if obj.get("type"):
                        obj["type"] = PrerequisiteType(obj["type"])
                    prereq = Prerequisite(**obj)
                    self.db.add(prereq)
                    counts["prerequisites"] += 1
            await self.db.commit()
        except FileNotFoundError:
            pass

        return counts

    # Graph Algorithms
    async def _build_graph(self) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Set[str]]:
        """Build forward and reverse adjacency lists from prerequisites."""
        result = await self.db.execute(select(Prerequisite))
        prerequisites = result.scalars().all()

        forward = defaultdict(set)  # concept_id -> set of prerequisite_ids
        reverse = defaultdict(set)  # prerequisite_id -> set of concept_ids
        all_nodes = set()

        for p in prerequisites:
            forward[p.concept_id].add(p.prerequisite_id)
            reverse[p.prerequisite_id].add(p.concept_id)
            all_nodes.add(p.concept_id)
            all_nodes.add(p.prerequisite_id)

        return forward, reverse, all_nodes

    async def topological_sort(self) -> List[str]:
        """Return concepts in topological order (prerequisites before dependents).
        
        Uses Kahn's algorithm. Raises ValueError if cycles detected.
        """
        forward, reverse, all_nodes = await self._build_graph()

        # Calculate in-degrees
        in_degree = defaultdict(int)
        for node in all_nodes:
            in_degree[node] = len(forward[node])

        # Queue nodes with no prerequisites
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for dependent in reverse[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(all_nodes):
            # Cycle detected
            raise ValueError("Cycle detected in prerequisite graph")

        return result

    async def reachable_nodes(self, start_node: str, direction: str = "downstream") -> Set[str]:
        """Find all nodes reachable from start_node.
        
        Args:
            start_node: Concept ID to start from
            direction: "downstream" (concepts that depend on start_node) or 
                      "upstream" (prerequisites of start_node)
        """
        forward, reverse, all_nodes = await self._build_graph()

        if start_node not in all_nodes:
            return set()

        if direction == "downstream":
            # Find all concepts that depend on start_node (transitive closure)
            visited = set()
            queue = deque([start_node])
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                for dependent in reverse[node]:
                    if dependent not in visited:
                        queue.append(dependent)
            visited.discard(start_node)
            return visited
        elif direction == "upstream":
            # Find all prerequisites of start_node (transitive closure)
            visited = set()
            queue = deque([start_node])
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                for prereq in forward[node]:
                    if prereq not in visited:
                        queue.append(prereq)
            visited.discard(start_node)
            return visited
        else:
            raise ValueError("direction must be 'upstream' or 'downstream'")

    async def get_prerequisites(self, concept_id: str, recursive: bool = False) -> List[str]:
        """Get direct or all prerequisites for a concept."""
        if recursive:
            return list(await self.reachable_nodes(concept_id, "upstream"))
        else:
            forward, _, _ = await self._build_graph()
            return list(forward.get(concept_id, set()))

    async def get_dependents(self, concept_id: str, recursive: bool = False) -> List[str]:
        """Get direct or all dependents for a concept."""
        if recursive:
            return list(await self.reachable_nodes(concept_id, "downstream"))
        else:
            _, reverse, _ = await self._build_graph()
            return list(reverse.get(concept_id, set()))

    async def validate_graph(self) -> Dict:
        """Validate prerequisite graph and return quality metrics."""
        forward, reverse, all_nodes = await self._build_graph()

        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in forward.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)

            rec_stack.discard(node)

        for node in all_nodes:
            if node not in visited:
                dfs(node, [])

        # Find isolated nodes (no prerequisites, no dependents)
        isolated = [node for node in all_nodes 
                   if len(forward.get(node, set())) == 0 and len(reverse.get(node, set())) == 0]

        # Find nodes with only incoming edges (no prerequisites but have dependents)
        only_incoming = [node for node in all_nodes 
                        if len(forward.get(node, set())) == 0 and len(reverse.get(node, set())) > 0]

        # Find nodes with only outgoing edges (have prerequisites but no dependents)
        only_outgoing = [node for node in all_nodes 
                        if len(forward.get(node, set())) > 0 and len(reverse.get(node, set())) == 0]

        return {
            "total_concepts": len(all_nodes),
            "total_prerequisites": sum(len(v) for v in forward.values()),
            "cycles": cycles,
            "isolated_nodes": isolated,
            "only_incoming": only_incoming,
            "only_outgoing": only_outgoing,
            "is_valid": len(cycles) == 0,
        }


def get_taxonomy_service(db: AsyncSession):
    """Dependency injection for TaxonomyService."""
    return TaxonomyService(db)
