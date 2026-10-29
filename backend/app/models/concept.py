from sqlalchemy import Column, String, Text, ForeignKey, Integer, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class DifficultyLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)

    concepts = relationship("Concept", back_populates="subject")
    domains = relationship("Domain", back_populates="subject")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "age_min": self.age_min,
            "age_max": self.age_max,
        }


class Domain(Base):
    __tablename__ = "domains"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)

    subject = relationship("Subject", back_populates="domains")
    concepts = relationship("Concept", back_populates="domain")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "subject_id": self.subject_id,
        }


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False, index=True)
    description = Column(Text, nullable=True)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)
    domain_id = Column(String(64), ForeignKey("domains.id"), nullable=True)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=True)
    estimated_hours = Column(Float, nullable=True)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)

    subject = relationship("Subject", back_populates="concepts")
    domain = relationship("Domain", back_populates="concepts")
    prerequisites = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.concept_id",
        back_populates="concept",
        cascade="all, delete-orphan",
    )
    dependents = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.prerequisite_id",
        back_populates="prerequisite",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "subject_id": self.subject_id,
            "domain_id": self.domain_id,
            "difficulty": self.difficulty.value if self.difficulty else None,
            "estimated_hours": self.estimated_hours,
            "age_min": self.age_min,
            "age_max": self.age_max,
        }