from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health, concepts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database, etc.
    yield
    # Shutdown: cleanup


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

    return app


app = create_app()