# Changelog

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

### Fixed
- TaxonomyService syntax error: removed corrupted XML artifacts from end of `backend/app/services/taxonomy.py`
- TaxonomyService dependency injection: fixed `get_taxonomy_service` to properly depend on `get_db` via `Depends`
- Added required imports (`fastapi.Depends`, `app.core.database.get_db`) to taxonomy service

### Verified
- All backend tests pass (6 tests: health endpoint, concept CRUD, filtering)
- All frontend tests pass (3 tests: App component)
- Frontend builds successfully (Vite + TypeScript)
- Taxonomy service algorithms: topological sort (Kahn's), reachable nodes (BFS upstream/downstream), cycle detection (DFS with normalization), graph validation (isolated/leaf/root nodes)
- JSONL import/export round-trip with data integrity

### Updated
- `STATUS.md`: checkpoint summary with completed fixes
- `feature-plan.json`: current feature remains `taxonomy-data-model` (completed)
- `PLAN.md`: feature status confirmed done

## 1.2.1 — work-in-progress checkpoint

### Fixed
- TaxonomyService `import_from_jsonl`: prevent mutation of input objects when converting difficulty/type strings to enums
- TaxonomyService `validate_graph`: normalize cycles to canonical form for accurate deduplication (avoids counting rotated cycles as distinct)

### Updated
- `feature-plan.json`: current feature remains `taxonomy-data-model`
- `PLAN.md`: updated current round status
- `STATUS.md`: checkpoint summary with completed fixes

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

### Fixed
- FastAPI route type annotations in `backend/app/api/routes/prerequisites.py` (4 endpoints: get_concept_prerequisites, get_concept_dependents, get_reachable_concepts, get_topological_sort)

### Completed
- Taxonomy data model feature (`taxonomy-data-model`): SQLite models (Concept, Prerequisite, Subject, Domain), JSONL import/export, prerequisite graph algorithms (topological sort, reachable nodes), API endpoints for all entities

### Updated
- `feature-plan.json`: marked `taxonomy-data-model` as done with implementation paths and tests
- `PLAN.md`: updated current round and feature statuses
- `STATUS.md`: checkpoint summary with completed work and next priorities

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-10-22

### Added
- Project skeleton with FastAPI backend and React+TypeScript frontend
- Health check endpoint at `/api/v1/health`
- Dockerfiles for backend and frontend
- docker-compose.yml with Keycloak and persistent volumes
- Backend pytest test for health endpoint
- Frontend vitest tests for App component
- README with architecture diagram, install/run/test steps
- portfolio.json with project metadata
- .env.example with configuration template
</arg_key>
<arg_key=i</arg_key>
<arg_value>Update CHANGELOG.md with taxonomy service fixes