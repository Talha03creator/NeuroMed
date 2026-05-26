"""
Diagnosis Model — Clinical Diagnoses
Agentic Clinical Intelligence Platform

Records ICD-10 coded diagnoses with severity, status (active/resolved),
and date tracking. Used by the Context Agent to build a patient's
diagnostic history for trend analysis and contradiction detection.
"""

from datetime import date
from typing import Optional

from sqlalchemy import (
    String, Date, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Diagnosis(Base, UUIDMixin, TimestampMixin):
    """Clinical diagnosis record with ICD-10 coding."""

    __tablename__ = "diagnoses"
    __table_args__ = (
        Index("ix_dx_patient", "patient_id"),
        Index("ix_dx_icd", "icd_code"),
        Index("ix_dx_status", "status"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True,
    )

    # ── Diagnosis Details ─────────────────────────────────────────
    icd_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="ICD-10 code",
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
        comment="mild | moderate | severe | critical",
    )
    diagnosis_type: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default="primary",
        comment="primary | secondary | admitting | discharge",
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active",
        comment="active | resolved | chronic | recurrent",
    )
    diagnosed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resolved_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # ── Clinical Context ──────────────────────────────────────────
    diagnosed_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # ── Source Tracking ───────────────────────────────────────────
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="diagnosis_mock")
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="diagnoses")
    encounter = relationship("Encounter", back_populates="diagnoses")

    def __repr__(self) -> str:
        return f"<Diagnosis icd={self.icd_code} desc={self.description[:50]} status={self.status}>"
