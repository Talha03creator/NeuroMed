"""
Medication Model — Prescription History
Agentic Clinical Intelligence Platform

Tracks all medications prescribed to a patient, including active/discontinued
status. Critical for the Context Agent to detect drug interactions and
correlate medication changes with clinical findings.
"""

from datetime import date
from typing import Optional

from sqlalchemy import (
    String, Date, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Medication(Base, UUIDMixin, TimestampMixin):
    """Medication prescription record for a patient."""

    __tablename__ = "medications"
    __table_args__ = (
        Index("ix_medications_patient", "patient_id"),
        Index("ix_medications_status", "status"),
        Index("ix_medications_name", "medication_name"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True,
    )

    # ── Medication Details ────────────────────────────────────────
    medication_name: Mapped[str] = mapped_column(String(300), nullable=False)
    generic_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    dosage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="e.g., twice daily, every 8 hours, PRN",
    )
    route: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="oral | IV | IM | topical | sublingual | inhaled",
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active",
        comment="active | discontinued | completed | on_hold",
    )
    prescribed_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Source Tracking ───────────────────────────────────────────
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="medication_mock")
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="medications")
    encounter = relationship("Encounter", back_populates=False)

    def __repr__(self) -> str:
        return f"<Medication name={self.medication_name} status={self.status}>"
