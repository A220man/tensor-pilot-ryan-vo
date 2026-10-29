from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Concept, Subject, Domain, Prerequisite
from app.models.concept import DifficultyLevel

router = APIRouter()


@router.get("/")
async def list_concepts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    difficulty: Optional[DifficultyLevel] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Concept)
    if subject_id:
        query = query.where(Concept.subject_id == subject_id)
    if domain_id:
        query = query.where(Concept.domain_id == domain_id)
    if difficulty:
        query = query.where(Concept.difficulty == difficulty)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    concepts = result.scalars().all()

    return {
        "concepts": [c.to_dict() for c in concepts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{concept_id}")
async def get_concept(concept_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    return concept.to_dict()


@router.post("/")
async def create_concept(
    name: str,
    subject_id: str,
    description: Optional[str] = None,
    domain_id: Optional[str] = None,
    difficulty: Optional[DifficultyLevel] = None,
    estimated_hours: Optional[float] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    # Verify subject exists
    subj_result = await db.execute(select(Subject).where(Subject.id == subject_id))
    if not subj_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subject not found")

    if domain_id:
        domain_result = await db.execute(select(Domain).where(Domain.id == domain_id))
        if not domain_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Domain not found")

    concept = Concept(
        id=str(uuid4()),
        name=name,
        description=description,
        subject_id=subject_id,
        domain_id=domain_id,
        difficulty=difficulty,
        estimated_hours=estimated_hours,
        age_min=age_min,
        age_max=age_max,
    )
    db.add(concept)
    await db.commit()
    await db.refresh(concept)
    return concept.to_dict()
