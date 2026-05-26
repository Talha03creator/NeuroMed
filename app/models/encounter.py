"""
Encounter Model — Clinical Visits
Agentic Clinical Intelligence Platform

Represents a single clinical encounter/visit. Acts as the grouping entity
for vitals, labs, diagnoses, procedures, and notes recorded during that visit.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, DateTime, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Encounter(Base, UUIDMixin, TimestampMixin):
    """A single clinical encounter (visit, admission, telehealth, etc.)."""

    __tablename__ = "encounters"
    __table_args__ = (
        Index("ix_encounters_patient", "patient_id"),
        Index("ix_encounters_date", "encounter_date"),
        Index("ix_encounters_type", "encounter_type"),
    )

    # ── Foreign Key ───────────────────────────────────────────────
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )

    # ── Encounter Details ─────────────────────────────────────────
    encounter_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="outpatient",
        comment="outpatient | inpatient | emergency | telehealth | lab_visit",
    )
    encounter_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    provider_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    disposition: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="discharged | admitted | transferred | deceased",
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Source Tracking ───────────────────────────────────────────
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="ehr_mock")
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="encounters")
    vitals = relationship("Vital", back_populates="encounter", lazy="selectin")
    lab_results = relationship("LabResult", back_populates="encounter", lazy="selectin")
    diagnoses = relationship("Diagnosis", back_populates="encounter", lazy="selectin")
    procedures = relationship("Procedure", back_populates="encounter", lazy="selectin")
    clinical_notes = relationship("ClinicalNote", back_populates="encounter", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Encounter id={self.id} type={self.encounter_type} date={self.encounter_date}>"
