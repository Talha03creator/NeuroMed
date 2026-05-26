"""
Patient Model — Master Patient Index
Agentic Clinical Intelligence Platform

Central patient record that all clinical data references.
Synced via Fivetran from mock EHR sources into the clinical warehouse.
"""

from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import (
    String, Text, Date, Boolean, JSON, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Patient(Base, UUIDMixin, TimestampMixin):
    """Master patient record — central to the clinical data warehouse."""

    __tablename__ = "patients"
    __table_args__ = (
        Index("ix_patients_mrn", "mrn", unique=True),
        Index("ix_patients_name", "last_name", "first_name"),
        Index("ix_patients_dob", "date_of_birth"),
    )

    # ── Identifiers ───────────────────────────────────────────────
    mrn: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False,
        comment="Medical Record Number — unique patient identifier",
    )

    # ── Demographics ──────────────────────────────────────────────
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    blood_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # ── Contact ───────────────────────────────────────────────────
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Emergency Contact ─────────────────────────────────────────
    emergency_contact: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None,
        comment="JSON: {name, relationship, phone}",
    )

    # ── Insurance ─────────────────────────────────────────────────
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    insurance_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Status ────────────────────────────────────────────────────
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Source Tracking ───────────────────────────────────────────
    source_system: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="ehr_mock",
        comment="Fivetran source identifier",
    )
    source_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Original ID in the source system",
    )

    # ── Relationships ─────────────────────────────────────────────
    encounters = relationship("Encounter", back_populates="patient", lazy="selectin")
    medications = relationship("Medication", back_populates="patient", lazy="selectin")
    vitals = relationship("Vital", back_populates="patient", lazy="selectin")
    lab_results = relationship("LabResult", back_populates="patient", lazy="selectin")
    diagnoses = relationship("Diagnosis", back_populates="patient", lazy="selectin")
    procedures = relationship("Procedure", back_populates="patient", lazy="selectin")
    allergies = relationship("Allergy", back_populates="patient", lazy="selectin")
    clinical_notes = relationship("ClinicalNote", back_populates="patient", lazy="selectin")
    reports = relationship("MedicalReport", back_populates="patient", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Patient mrn={self.mrn} name={self.last_name}, {self.first_name}>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
