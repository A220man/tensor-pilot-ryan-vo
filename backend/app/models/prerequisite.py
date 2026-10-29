from sqlalchemy import Column, String, ForeignKey, Float, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class PrerequisiteType(str, enum.Enum):
    hard = "hard"
    soft = "soft"
    recommended = "recommended"


class Prerequisite(Base):
    __tablename__ = "prerequisites"
    __table_args__ = (
        UniqueConstraint("concept_id", "prerequisite_id", name="uq_concept_prerequisite"),
        Index("ix_prerequisite_concept", "concept_id"),
        Index("ix_prerequisite_prereq", "prerequisite_id"),
    )

    id = Column(String(64), primary_key=True)
    concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SQLEnum(PrerequisiteType), default=PrerequisiteType.hard, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)

    concept = relationship("Concept", foreign_keys=[concept_id], back_populates="prerequisites")
    prerequisite = relationship("Concept", foreign_keys=[prerequisite_id], back_populates="dependents")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "concept_id": self.concept_id,
            "prerequisite_id": self.prerequisite_id,
            "type": self.type.value,
            "weight": self.weight,
        }