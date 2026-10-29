from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Concept, Prerequisite
from app.models.prerequisite import PrerequisiteType
from app.services.taxonomy import get_taxonomy_service, TaxonomyService

router = APIRouter()


@router.get("/")
async def list_prerequisites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    concept_id: Optional[str] = None,
    prerequisite_id: Optional[str] = None,
    type: Optional[PrerequisiteType] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Prerequisite)
    if concept_id:
        query = query.where(Prerequisite.concept_id == concept_id)
    if prerequisite_id:
        query = query.where(Prerequisite.prerequisite_id == prerequisite_id)
    if type:
        query = query.where(Prerequisite.type == type)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    prerequisites = result.scalars().all()

    return {
        "prerequisites": [p.to_dict() for p in prerequisites],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{prerequisite_id}")
async def get_prerequisite(
    prerequisite_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Prerequisite).where(Prerequisite.id == prerequisite_id))
    prereq = result.scalar_one_or_none()
    if not prereq:
        raise HTTPException(status_code=404, detail="Prerequisite not found")
    return prereq.to_dict()


@router.post("/")
async def create_prerequisite(
    concept_id: str,
    prerequisite_id: str,
    type: PrerequisiteType = PrerequisiteType.hard,
    weight: float = 1.0,
    db: AsyncSession = Depends(get_db),
):
    # Verify both concepts exist
    for cid, label in [(concept_id, "concept"), (prerequisite_id, "prerequisite")]:
        result = await db.execute(select(Concept).where(Concept.id == cid))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"{label.capitalize()} not found")

    if concept_id == prerequisite_id:
        raise HTTPException(status_code=400, detail="A concept cannot be a prerequisite of itself")

    # Check if already exists
    existing = await db.execute(
        select(Prerequisite).where(
            Prerequisite.concept_id == concept_id,
            Prerequisite.prerequisite_id == prerequisite_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Prerequisite relationship already exists")

    prereq = Prerequisite(
        id=str(uuid4()),
        concept_id=concept_id,
        prerequisite_id=prerequisite_id,
        type=type,
        weight=weight,
    )
    db.add(prereq)
    await db.commit()
    await db.refresh(prereq)
    return prereq.to_dict()


@router.delete("/{prerequisite_id}")
async def delete_prerequisite(
    prerequisite_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Prerequisite).where(Prerequisite.id == prerequisite_id))
    prereq = result.scalar_one_or_none()
    if not prereq:
        raise HTTPException(status_code=404, detail="Prerequisite not found")

    await db.delete(prereq)
    await db.commit()
    return {"message": "Prerequisite deleted"}


@router.get("/concept/{concept_id}/prerequisites", response_model=None)
async def get_concept_prerequisites(
    concept_id: str,
    recursive: bool = Query(False),
    service=Depends(get_taxonomy_service),
):
    """Get all prerequisites for a concept (direct or recursive)."""
    # Verify concept exists
    result = await service.db.execute(select(Concept).where(Concept.id == concept_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Concept not found")

    prereq_ids = await service.get_prerequisites(concept_id, recursive=recursive)
    
    # Fetch full concept details
    if prereq_ids:
        result = await service.db.execute(select(Concept).where(Concept.id.in_(prereq_ids)))
        concepts = result.scalars().all()
        return [c.to_dict() for c in concepts]
    return []


@router.get("/concept/{concept_id}/dependents")
async def get_concept_dependents(
    concept_id: str,
    recursive: bool = Query(False),
    service=Depends(get_taxonomy_service),
):
    """Get all dependents for a concept (direct or recursive)."""
    result = await service.db.execute(select(Concept).where(Concept.id == concept_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Concept not found")

    dependent_ids = await service.get_dependents(concept_id, recursive=recursive)
    
    if dependent_ids:
        result = await service.db.execute(select(Concept).where(Concept.id.in_(dependent_ids)))
        concepts = result.scalars().all()
        return [c.to_dict() for c in concepts]
    return []


@router.get("/concept/{concept_id}/reachable")
async def get_reachable_concepts(
    concept_id: str,
    direction: str = Query("downstream", pattern="^(upstream|downstream)$"),
    service=Depends(get_taxonomy_service),
):
    """Get all concepts reachable from a concept in the given direction."""
    result = await service.db.execute(select(Concept).where(Concept.id == concept_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Concept not found")

    reachable_ids = await service.reachable_nodes(concept_id, direction=direction)
    
    if reachable_ids:
        result = await service.db.execute(select(Concept).where(Concept.id.in_(reachable_ids)))
        concepts = result.scalars().all()
        return [c.to_dict() for c in concepts]
    return []


@router.get("/topological-sort")
async def get_topological_sort(
    service=Depends(get_taxonomy_service),
):
    """Get concepts in topological order (prerequisites before dependents)."""
    try:
        sorted_ids = await service.topological_sort()
        if sorted_ids:
            result = await service.db.execute(select(Concept).where(Concept.id.in_(sorted_ids)))
            concepts = result.scalars().all()
            # Reorder to match topological sort
            concept_map = {c.id: c for c in concepts}
            return [concept_map[cid].to_dict() for cid in sorted_ids if cid in concept_map]
        return []
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
