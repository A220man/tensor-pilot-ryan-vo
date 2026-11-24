from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.database import get_db
from app.models import Concept, Subject, Domain, ChildProgress
from app.models.child_progress import ChildProgressState


router = APIRouter(prefix="/child-progress", tags=["child-progress"])


@router.get("/")
async def list_child_progress(
    child_id: Optional[str] = Query(None, description="Filter by child ID"),
    concept_id: Optional[str] = Query(None, description="Filter by concept ID"),
    state: Optional[ChildProgressState] = Query(None, description="Filter by state"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    db: AsyncSession = Depends(get_db),
):
    """List child progress entries with optional filters."""
    query = select(ChildProgress)

    if child_id:
        query = query.where(ChildProgress.child_id == child_id)
    if concept_id:
        query = query.where(ChildProgress.concept_id == concept_id)
    if state:
        query = query.where(ChildProgress.state == state)
    if subject_id:
        # Join with concept to filter by subject
        query = query.join(ChildProgress.concept).where(Concept.subject_id == subject_id)

    result = await db.execute(query.order_by(ChildProgress.updated_at.desc()))
    progress = result.scalars().all()

    return [p.to_dict() for p in progress]


@router.get("/{progress_id}")
async def get_child_progress(progress_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific child progress entry."""
    result = await db.execute(
        select(ChildProgress).where(ChildProgress.id == progress_id)
    )
    progress = result.scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="Child progress not found")
    return progress.to_dict()


@router.post("/")
async def create_child_progress(
    child_id: str,
    concept_id: str,
    state: ChildProgressState = ChildProgressState.not_started,
    db: AsyncSession = Depends(get_db),
):
    """Create or reset a child progress entry for a concept."""
    # Verify concept exists
    concept_result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = concept_result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=400, detail="Concept not found")

    # Check if progress already exists for this child/concept pair
    existing_result = await db.execute(
        select(ChildProgress).where(
            ChildProgress.child_id == child_id,
            ChildProgress.concept_id == concept_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.state = state
        if state in (ChildProgressState.learning,):
            existing.started_at = datetime.now(timezone.utc) if existing.started_at else datetime.now(timezone.utc)
        else:
            existing.started_at = None
        existing.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return existing.to_dict()
    else:
        # Create new
        progress = ChildProgress(
            id=str(uuid4()),
            child_id=child_id,
            concept_id=concept_id,
            state=state,
            started_at=datetime.now(timezone.utc) if state == ChildProgressState.learning else None,
            updated_at=datetime.now(timezone.utc),
        )
        db.add(progress)
        await db.commit()
        await db.refresh(progress)
        return progress.to_dict()


@router.post("/{progress_id}/update")
async def update_child_progress(
    progress_id: str,
    state: ChildProgressState,
    db: AsyncSession = Depends(get_db),
):
    """Update the state of a child progress entry."""
    result = await db.execute(
        select(ChildProgress).where(ChildProgress.id == progress_id)
    )
    progress = result.scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="Child progress not found")

    progress.state = state
    if state == ChildProgressState.learning:
        if not progress.started_at:
            progress.started_at = datetime.now(timezone.utc)
    elif state in (ChildProgressState.known, ChildProgressState.evidence_assessed):
        progress.completed_at = datetime.now(timezone.utc)

    progress.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(progress)
    return progress.to_dict()


@router.get("/stats/{child_id}")
async def get_child_progress_stats(
    child_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get progress statistics for a child."""
    # Count by state
    result = await db.execute(
        select(ChildProgress.state, func.count(ChildProgress.id))
        .where(ChildProgress.child_id == child_id)
        .group_by(ChildProgress.state)
    )
    stats = {row.state.value: row.count for row in result.all()}

    # Total concepts progressed
    total_result = await db.execute(
        select(func.count(func.distinct(ChildProgress.concept_id)))
        .where(ChildProgress.child_id == child_id)
    )
    total_concepts = total_result.scalar() or 0

    # Progress by subject
    subject_result = await db.execute(
        select(Subject.name, func.count(ChildProgress.id))
        .join(Concept, ChildProgress.concept_id == Concept.id)
        .join(Subject, Concept.subject_id == Subject.id)
        .where(ChildProgress.child_id == child_id)
        .group_by(Subject.name)
    )
    by_subject = {name: count for name, count in subject_result.all()}

    return {
        "child_id": child_id,
        "total_concepts": total_concepts,
        "by_state": stats,
        "by_subject": by_subject,
    }
