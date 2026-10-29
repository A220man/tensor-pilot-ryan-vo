from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.models import Concept, Subject, Domain, Prerequisite  # noqa: F401
from app.api.routes import health, concepts, prerequisites, subjects, domains, validation


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="tensor-pilot-ryan-vo",
        version="1.0.0",
        description="AI/ML developer tool for explorable prerequisite taxonomies",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(concepts.router, prefix="/api/v1/concepts", tags=["concepts"])
    app.include_router(prerequisites.router, prefix="/api/v1/prerequisites", tags=["prerequisites"])
    app.include_router(subjects.router, prefix="/api/v1/subjects", tags=["subjects"])
    app.include_router(domains.router, prefix="/api/v1/domains", tags=["domains"])
    app.include_router(validation.router, prefix="/api/v1/validation", tags=["validation"])

    return app


app = create_app()
