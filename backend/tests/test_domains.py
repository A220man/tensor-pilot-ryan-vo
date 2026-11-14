import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from app.main import app
from app.core.database import get_db, _test_db_context
from app.models import Subject, Domain
@pytest.fixture
async def session_maker():
    """Create a test database session maker using in-memory SQLite."""
    async with _test_db_context() as sm:
        yield sm
@pytest.fixture
async def db_session(session_maker):
    """Create a test database session."""
    async with session_maker() as session:
        yield session
@pytest.fixture
async def test_subject(db_session: AsyncSession):
    subject = Subject(id=str(uuid4()), name="Mathematics", color="#FF0000", age_min=5, age_max=18)
    db_session.add(subject)
    await db_session.commit()
    await db_session.refresh(subject)
    return subject
@pytest.fixture
async def test_domain(db_session: AsyncSession, test_subject: Subject):
    domain = Domain(id=str(uuid4()), name="Algebra", color="#00FF00", subject_id=test_subject.id, age_min=10, age_max=14)
    db_session.add(domain)
    await db_session.commit()
    await db_session.refresh(domain)
    return domain
@pytest.fixture(autouse=True)
async def override_get_db(session_maker):
    async def _get_test_db():
        async with session_maker() as session:
            yield session
    app.dependency_overrides[get_db] = _get_test                                   # Bug: truncated? We'll rewrite more carefully.
