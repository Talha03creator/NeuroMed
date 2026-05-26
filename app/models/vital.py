"""
Vital Signs Model
Agentic Clinical Intelligence Platform

Records vital sign measurements during clinical encounters.
The Context Agent uses vitals trends to detect deterioration patterns
and flag cardiac/respiratory risk when correlated with current reports.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Float, DateTime, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Vital(Base, UUIDMixin, TimestampMixin):
    """Single vital signs measurement record."""

    __tablename__ = "vitals"
    __table_args__ = (
        Index("ix_vitals_patient", "patient_id"),
        Index("ix_vitals_recorded", "recorded_at"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True,
    )

    # ── Vital Measurements ────────────────────────────────────────
    heart_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="bpm")
    blood_pressure_systolic: Mapped[Optional[int]] = mapped_column(nullable=True, comment="mmHg")
    blood_pressure_diastolic: Mapped[Optional[int]] = mapped_column(nullable=True, comment="mmHg")
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="Fahrenheit")
    respiratory_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="breaths/min")
    oxygen_saturation: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="SpO2 %")
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pain_level: Mapped[Optional[int]] = mapped_column(nullable=True, comment="0-10 scale")

    # ── Measurement Context ───────────────────────────────────────
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    recorded_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, comment="sitting | standing | supine",
    )

    # ── Source Tracking ───────────────────────────────────────────
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="vitals_mock")
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="vitals")
    encounter = relationship("Encounter", back_populates="vitals")

    def __repr__(self) -> str:
        return f"<Vital patient={self.patient_id} hr={self.heart_rate} bp={self.blood_pressure_systolic}/{self.blood_pressure_diastolic}>"
