from uuid import uuid4
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Domain, Subject, Concept

router = APIRouter()


@router.get("/")
async def list_domains(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject_id: Optional[str] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    query = select(Domain)
    if subject_id:
        query = query.where(Domain.subject_id == subject_id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    domains = result.scalars().all()

    return {
        "domains": [d.to_dict() for d in domains],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{domain_id}")
async def get_domain(
    domain_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain.to_dict()


@router.post("/")
async def create_domain(
    name: str,
    subject_id: str,
    description: Optional[str] = None,
    color: Optional[str] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    # Verify subject exists
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subject not found")

    # Check if domain with same name exists in subject
    existing = await db.execute(
        select(Domain).where(Domain.name == name, Domain.subject_id == subject_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Domain with this name already exists in this subject")

    domain = Domain(
        id=str(uuid4()),
        name=name,
        description=description,
        color=color,
        subject_id=subject_id,
    )
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return domain.to_dict()


@router.put("/{domain_id}")
async def update_domain(
    domain_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[str] = None,
    subject_id: Optional[str] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    if name is not None:
        existing = await db.execute(
            select(Domain).where(Domain.name == name, Domain.subject_id == domain.subject_id, Domain.id != domain_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Domain with this name already exists in this subject")
        domain.name = name
    if description is not None:
        domain.description = description
    if color is not None:
        domain.color = color
    if subject_id is not None:
        # Verify new subject exists
        result = await db.execute(select(Subject).where(Subject.id == subject_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Subject not found")
        domain.subject_id = subject_id

    await db.commit()
    await db.refresh(domain)
    return domain.to_dict()


@router.delete("/{domain_id}")
async def delete_domain(
    domain_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    await db.delete(domain)
    await db.commit()
    return {"message": "Domain deleted"}


@router.get("/{domain_id}/concepts")
async def get_domain_concepts(
    domain_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Get all concepts in a domain."""
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    query = select(Concept).where(Concept.domain_id == domain_id)
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
