"""
Procedure Model — Medical Procedures
Agentic Clinical Intelligence Platform

Records surgical and diagnostic procedures with CPT codes,
body site, outcome, and performing provider information.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, DateTime, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Procedure(Base, UUIDMixin, TimestampMixin):
    """Medical procedure record with CPT coding."""

    __tablename__ = "procedures"
    __table_args__ = (
        Index("ix_proc_patient", "patient_id"),
        Index("ix_proc_cpt", "cpt_code"),
        Index("ix_proc_date", "performed_at"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True,
    )

    # ── Procedure Details ─────────────────────────────────────────
    cpt_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="CPT code")
    procedure_name: Mapped[str] = mapped_column(String(500), nullable=False)
    procedure_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="surgical | diagnostic | therapeutic | preventive",
    )
    body_site: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    laterality: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="left | right | bilateral",
    )
    outcome: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="successful | complications | aborted | pending_results",
    )
    complications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Timing ────────────────────────────────────────────────────
    performed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(nullable=True)

    # ── Provider ──────────────────────────────────────────────────
    performed_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    assistant: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Source Tracking ───────────────────────────────────────────
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="ehr_mock")
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="procedures")
    encounter = relationship("Encounter", back_populates="procedures")

    def __repr__(self) -> str:
        return f"<Procedure name={self.procedure_name[:40]} outcome={self.outcome}>"
