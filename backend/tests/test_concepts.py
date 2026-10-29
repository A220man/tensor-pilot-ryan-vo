import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.main import app
from app.core.database import get_db, _test_db_context
from app.models import Concept, Subject, Domain, Prerequisite
from app.models.concept import DifficultyLevel


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
    domain = Domain(id=str(uuid4()), name="Algebra", color="#00FF00", subject_id=test_subject.id)
    db_session.add(domain)
    await db_session.commit()
    await db_session.refresh(domain)
    return domain


@pytest.fixture
async def test_concept(db_session: AsyncSession, test_subject: Subject, test_domain: Domain):
    concept = Concept(
        id=str(uuid4()),
        name="Linear Equations",
        description="Solving linear equations",
        subject_id=test_subject.id,
        domain_id=test_domain.id,
        difficulty=DifficultyLevel.beginner,
        estimated_hours=2.0,
        age_min=12,
        age_max=15,
    )
    db_session.add(concept)
    await db_session.commit()
    await db_session.refresh(concept)
    return concept


# Override the get_db dependency for tests
@pytest.fixture(autouse=True)
async def override_get_db(session_maker):
    async def _get_test_db():
        async with session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_concepts_empty(db_session: AsyncSession):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/concepts/")
        assert response.status_code == 200
        data = response.json()
        assert data["concepts"] == []
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_concept(db_session: AsyncSession, test_subject: Subject):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/concepts/",
            params={
                "name": "Test Concept",
                "subject_id": test_subject.id,
                "description": "A test concept",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Concept"
        assert data["subject_id"] == test_subject.id
        assert "id" in data


@pytest.mark.asyncio
async def test_get_concept(db_session: AsyncSession, test_concept: Concept):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/concepts/{test_concept.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_concept.id
        assert data["name"] == test_concept.name


@pytest.mark.asyncio
async def test_get_concept_not_found(db_session: AsyncSession):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/concepts/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_concepts_with_filter(db_session: AsyncSession, test_concept: Concept, test_subject: Subject):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/concepts/?subject_id={test_subject.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["concepts"]) == 1
        assert data["concepts"][0]["id"] == test_concept.id
