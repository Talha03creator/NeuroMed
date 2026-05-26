"""
Clinical Note Model
Agentic Clinical Intelligence Platform

Records clinical notes attached to encounters — progress notes,
discharge summaries, consult notes, etc.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, DateTime, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class ClinicalNote(Base, UUIDMixin, TimestampMixin):
    """Clinical note record."""

    __tablename__ = "clinical_notes"
    __table_args__ = (
        Index("ix_cn_patient", "patient_id"),
        Index("ix_cn_type", "note_type"),
        Index("ix_cn_date", "authored_at"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True,
    )

    # ── Note Details ──────────────────────────────────────────────
    note_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="progress",
        comment="progress | discharge_summary | consult | procedure | nursing | referral",
    )
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    author_role: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="physician | nurse | specialist",
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    authored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    is_addendum: Mapped[bool] = mapped_column(nullable=False, default=False)
    parent_note_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("clinical_notes.id", ondelete="SET NULL"), nullable=True,
    )

    # ── Source Tracking ───────────────────────────────────────────
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="ehr_mock")
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="clinical_notes")
    encounter = relationship("Encounter", back_populates="clinical_notes")

    def __repr__(self) -> str:
        return f"<ClinicalNote type={self.note_type} author={self.author}>"
