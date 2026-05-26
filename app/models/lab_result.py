"""
Lab Result Model
Agentic Clinical Intelligence Platform

Records laboratory test results with values, units, reference ranges,
and abnormal flags. The Context Agent uses lab trends to detect
deteriorating conditions and validate current report findings.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, DateTime, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class LabResult(Base, UUIDMixin, TimestampMixin):
    """Single laboratory test result record."""

    __tablename__ = "lab_results"
    __table_args__ = (
        Index("ix_lab_patient", "patient_id"),
        Index("ix_lab_test", "test_name"),
        Index("ix_lab_collected", "collected_at"),
        Index("ix_lab_flag", "flag"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True,
    )

    # ── Test Details ──────────────────────────────────────────────
    test_name: Mapped[str] = mapped_column(String(300), nullable=False)
    test_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="LOINC code or internal code",
    )
    panel_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="e.g., Complete Blood Count, Basic Metabolic Panel",
    )

    # ── Result ────────────────────────────────────────────────────
    result_value: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    flag: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="normal | low | high | critical_low | critical_high",
    )

    # ── Timestamps ────────────────────────────────────────────────
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resulted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Ordering Info ─────────────────────────────────────────────
    ordered_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    performing_lab: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Source Tracking ───────────────────────────────────────────
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="lab_mock")
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="lab_results")
    encounter = relationship("Encounter", back_populates="lab_results")

    def __repr__(self) -> str:
        return f"<LabResult test={self.test_name} value={self.result_value} flag={self.flag}>"
