from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Text, ForeignKeyConstraint
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone

from app.core.database import Base


class ChildProgressState(str, enum.Enum):
    not_started = "not_started"
    learning = "learning"
    known = "known"
    evidence_assessed = "evidence_assessed"


class ChildProgress(Base):
    """Per-child concept progress tracking.

    Tracks the learning state of a concept for each child profile.
    States: not_started, learning, known, evidence_assessed
    """

    __tablename__ = "child_progress"

    id = Column(String(64), primary_key=True)
    child_id = Column(String(64), nullable=False, index=True)
    concept_id = Column(String(64), ForeignKey("concepts.id"), nullable=False, index=True)
    state = Column(SQLEnum(ChildProgressState), nullable=False, default=ChildProgressState.not_started)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    concept = relationship("Concept", back_populates="child_progress")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "child_id": self.child_id,
            "concept_id": self.concept_id,
            "state": self.state.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
