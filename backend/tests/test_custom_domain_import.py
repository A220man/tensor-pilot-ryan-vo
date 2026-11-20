"""Tests for custom domain support - JSONL import/export with age/difficulty ranges."""
import jsonlines
import os
import pytest
from uuid import uuid4

from sqlalchemy import select

from app.core.database import _test_db_context
from app.models import Subject, Domain, Concept, Prerequisite
from app.models.concept import DifficultyLevel
from app.services.taxonomy import TaxonomyService


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
async def test_subject(db_session):
    """Create a test subject."""
    subject = Subject(id=str(uuid4()), name="Mathematics", color="#FF0000", age_min=5, age_max=18)
    db_session.add(subject)
    await db_session.commit()
    await db_session.refresh(subject)
    return subject


@pytest.fixture
async def test_domain(db_session, test_subject):
    """Create a test domain."""
    domain = Domain(id=str(uuid4()), name="Algebra", color="#00FF00", subject_id=test_subject.id, age_min=10, age_max=14)
    db_session.add(domain)
    await db_session.commit()
    await db_session.refresh(domain)
    return domain


@pytest.fixture
async def test_concept(db_session, test_subject, test_domain):
    """Create a test concept."""
    concept = Concept(
        id=str(uuid4()), name="Linear Equations",
        description="Solving linear equations",
        subject_id=test_subject.id, domain_id=test_domain.id,
        difficulty=DifficultyLevel.beginner, estimated_hours=2.0,
        age_min=12, age_max=15
    )
    db_session.add(concept)
    await db_session.commit()
    await db_session.refresh(concept)
    return concept


@pytest.mark.asyncio
async def test_jsonl_export_preserves_age_difficulty(db_session, test_subject, test_domain, test_concept):
    """Test JSONL export preserves age_min, age_max, and difficulty fields."""
    from sqlalchemy import select
    service = TaxonomyService(db_session)
    
    filepath = "/tmp/test_jsonl_export_1"
    
    # Export to JSONL - the fixtures have already created test data
    counts = await service.export_to_jsonl(filepath)
    
    # Verify export counts - should include the test data
    assert counts["subjects"] >= 1
    assert counts["domains"] >= 1
    assert counts["concepts"] >= 1
    assert counts["prerequisites"] == 0
    
    # Verify files were created
    assert os.path.exists(f"{filepath}_subjects.jsonl")
    assert os.path.exists(f"{filepath}_domains.jsonl")
    assert os.path.exists(f"{filepath}_concepts.jsonl")
    assert os.path.exists(f"{filepath}_prerequisites.jsonl")
    
    # Verify JSONL content has the expected fields
    with open(f"{filepath}_subjects.jsonl", 'r') as f:
        reader = jsonlines.open(f"{filepath}_subjects.jsonl", mode="r")
        for obj in reader:
            assert "age_min" in obj, "Subject missing age_min"
            assert "age_max" in obj, "Subject missing age_max"
    
    with open(f"{filepath}_domains.jsonl", 'r') as f:
        reader = jsonlines.open(f"{filepath}_domains.jsonl", mode="r")
        for obj in reader:
            assert "age_min" in obj, "Domain missing age_min"
            assert "age_max" in obj, "Domain missing age_max"
    
    with open(f"{filepath}_concepts.jsonl", 'r') as f:
        reader = jsonlines.open(f"{filepath}_concepts.jsonl", mode="r")
        for obj in reader:
            assert "difficulty" in obj, "Concept missing difficulty"
            assert "age_min" in obj, "Concept missing age_min"
            assert "age_max" in obj, "Concept missing age_max"


@pytest.mark.asyncio
async def test_jsonl_import_preserves_age_difficulty(db_session):
    """Test JSONL import preserves age and difficulty ranges from custom datasets."""
    from sqlalchemy import select
    service = TaxonomyService(db_session)
    
    filepath = "/tmp/test_jsonl_import_1"
    
    # Create test data in this test
    subject = Subject(id=str(uuid4()), name="Mathematics", color="#FF0000", age_min=5, age_max=18)
    db_session.add(subject)
    await db_session.commit()
    
    domain = Domain(id=str(uuid4()), name="Algebra", color="#00FF00", subject_id=subject.id, age_min=10, age_max=14)
    db_session.add(domain)
    await db_session.commit()
    
    concept = Concept(
        id=str(uuid4()), name="Linear Equations",
        description="Solving linear equations",
        subject_id=subject.id, domain_id=domain.id,
        difficulty=DifficultyLevel.beginner, estimated_hours=2.0,
        age_min=12, age_max=15
    )
    db_session.add(concept)
    await db_session.commit()
    
    # First export data
    counts = await service.export_to_jsonl(filepath)
    assert counts["subjects"] == 1
    assert counts["domains"] == 1
    assert counts["concepts"] == 1
    
    # Now import into a fresh session
    async with _test_db_context() as new_sm:
        async with new_sm() as new_db:
            new_service = TaxonomyService(new_db)
            import_counts = await new_service.import_from_jsonl(filepath)
            
            # Verify import counts
            assert import_counts["subjects"] == 1
            assert import_counts["domains"] == 1
            assert import_counts["concepts"] == 1
            assert import_counts["prerequisites"] == 0
            
            # Verify imported data has correct age/difficulty ranges
            result = await new_db.execute(select(Subject))
            subjects = result.scalars().all()
            assert len(subjects) == 1
            assert subjects[0].age_min == 5
            assert subjects[0].age_max == 18
            
            result = await new_db.execute(select(Domain))
            domains = result.scalars().all()
            assert len(domains) == 1
            assert domains[0].age_min == 10
            assert domains[0].age_max == 14
            
            result = await new_db.execute(select(Concept))
            concepts = result.scalars().all()
            assert len(concepts) == 1
            assert concepts[0].difficulty == DifficultyLevel.beginner
            assert concepts[0].age_min == 12
            assert concepts[0].age_max == 15
