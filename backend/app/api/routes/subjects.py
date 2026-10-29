from uuid import uuid4
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Subject, Domain

router = APIRouter()


@router.get("/")
async def list_subjects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    query = select(Subject)
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    subjects = result.scalars().all()

    return {
        "subjects": [s.to_dict() for s in subjects],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{subject_id}")
async def get_subject(
    subject_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject.to_dict()


@router.post("/")
async def create_subject(
    name: str,
    description: Optional[str] = None,
    color: Optional[str] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    # Check if subject with same name exists
    existing = await db.execute(select(Subject).where(Subject.name == name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subject with this name already exists")

    subject = Subject(
        id=str(uuid4()),
        name=name,
        description=description,
        color=color,
        age_min=age_min,
        age_max=age_max,
    )
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject.to_dict()


@router.put("/{subject_id}")
async def update_subject(
    subject_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[str] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    if name is not None:
        # Check if new name conflicts
        existing = await db.execute(select(Subject).where(Subject.name == name, Subject.id != subject_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Subject with this name already exists")
        subject.name = name
    if description is not None:
        subject.description = description
    if color is not None:
        subject.color = color
    if age_min is not None:
        subject.age_min = age_min
    if age_max is not None:
        subject.age_max = age_max

    await db.commit()
    await db.refresh(subject)
    return subject.to_dict()


@router.delete("/{subject_id}")
async def delete_subject(
    subject_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    await db.delete(subject)
    await db.commit()
    return {"message": "Subject deleted"}


@router.get("/{subject_id}/domains")
async def get_subject_domains(
    subject_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Get all domains for a subject."""
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    result = await db.execute(select(Domain).where(Domain.subject_id == subject_id))
    domains = result.scalars().all()
    return [d.to_dict() for d in domains]
