from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.config import settings

# Global engine and session maker (can be overridden for tests)
_engine = None
_async_session_maker = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
        )
    return _engine


def get_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


# For backward compatibility
async_session_maker = get_session_maker()

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_maker()() as session:
        yield session


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None


@asynccontextmanager
async def _test_db_context(test_database_url: str = "sqlite+aiosqlite:///:memory:"):
    """Context manager for test database with isolated engine."""
    global _engine, _async_session_maker
    
    # Save original
    orig_engine = _engine
    orig_session_maker = _async_session_maker
    
    # Create test engine
    test_engine = create_async_engine(test_database_url, echo=False, future=True)
    test_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    _engine = test_engine
    _async_session_maker = test_session_maker
    
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    try:
        yield test_session_maker
    finally:
        await test_engine.dispose()
        _engine = orig_engine
        _async_session_maker = orig_session_maker
