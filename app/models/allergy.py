"""
Allergy Model — Patient Allergies
Agentic Clinical Intelligence Platform

Records patient allergies with reaction type and severity.
Critical for the Context Agent to flag drug interaction risks.
"""

from datetime import date
from typing import Optional

from sqlalchemy import (
    String, Date, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Allergy(Base, UUIDMixin, TimestampMixin):
    """Patient allergy record."""

    __tablename__ = "allergies"
    __table_args__ = (
        Index("ix_allergy_patient", "patient_id"),
        Index("ix_allergy_allergen", "allergen"),
    )

    # ── Foreign Key ───────────────────────────────────────────────
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )

    # ── Allergy Details ───────────────────────────────────────────
    allergen: Mapped[str] = mapped_column(String(300), nullable=False)
    allergen_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="drug | food | environmental | biological | other",
    )
    reaction: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
        comment="mild | moderate | severe | life_threatening",
    )
    onset_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active",
        comment="active | inactive | resolved | entered_in_error",
    )
    verified: Mapped[Optional[bool]] = mapped_column(nullable=True, default=False)
    verified_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # ── Source Tracking ───────────────────────────────────────────
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="ehr_mock")
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="allergies")

    def __repr__(self) -> str:
        return f"<Allergy allergen={self.allergen} severity={self.severity}>"
