# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

project-skeleton

## Roadmap

### project-skeleton — Project skeleton with FastAPI backend and React+TypeScript frontend

Status: done

Acceptance:
- Backend FastAPI app with /health endpoint
- Frontend Vite+React+TypeScript app with build script
- Dockerfiles for backend and frontend
- docker-compose.yml with Keycloak and persistent volumes
- README with install/run/test steps
- portfolio.json at root
- Backend and frontend tests pass

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/api/routes/health.py`, `backend/app/api/routes/concepts.py`, `backend/tests/test_health.py`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/Dockerfile`, `backend/Dockerfile`, `docker-compose.yml`, `README.md`, `portfolio.json`, `CHANGELOG.md`, `LICENSE`, `.env.example`, `.gitignore`

Tests: `backend/tests/test_health.py`, `frontend/src/App.test.tsx`

### taxonomy-data-model — Taxonomy data model with JSONL storage and prerequisite graph

Status: planned

Acceptance:
- SQLite models for Concept, Prerequisite, Subject, Domain
- JSONL import/export for taxonomy data
- Prerequisite graph traversal algorithms (topological sort, reachable nodes)
- API endpoints for concepts, prerequisites, subjects, domains

### custom-domain-support — Custom domain support for taxonomy visualization (Issue #24)

Status: planned

Acceptance:
- Configurable subjects, domains, age/difficulty ranges
- Load custom taxonomy datasets following same schema
- Domain-agnostic visualization components

### learning-progress-tracker — Browser-based child learning progress tracker (Issue #16)

Status: planned

Acceptance:
- Per-child concept states: not_started, learning, known, evidence_assessed
- Multiple child profiles with local persistence
- Progress visualization: dim/hide/show-only-known modes
- Search and filters for subject, age, known concepts

### graph-linkage-validation — Graph linkage validation and quality reporting (Issue #18)

Status: planned

Acceptance:
- Detect incoherent prerequisite linkages
- Quality metrics for prerequisite graph
- Validation report API endpoint

### performance-optimization — Zoom/drag performance optimization (Issue #19)

Status: planned

Acceptance:
- Optimized graph rendering for 1500+ nodes
- Viewport culling and level-of-detail
- Smooth interaction at high zoom/drag speeds

### auth-oidc-keycloak — OIDC authentication with Keycloak and SAML broker

Status: planned

Acceptance:
- Authorization code flow with PKCE
- HttpOnly SameSite cookies with CSRF protection
- Role-based authorization (viewer/operator/admin)
- Keycloak realm import with SAML identity broker

### llm-advisory-explanations — Optional LLM explanations for learning pathways

Status: planned

Acceptance:
- OpenAI-compatible, Anthropic, Gemini, Ollama adapters
- Advisory-only explanations grounded in actual records
- Configurable provider/model/endpoint, no hardcoded keys

