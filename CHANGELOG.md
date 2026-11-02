# Changelog

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