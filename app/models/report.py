"""
Medical Report Model — Upgraded for Agentic Platform
Agentic Clinical Intelligence Platform

Stores uploaded medical reports and their AI analysis results.
Now linked to patient records and agent traces for full
agentic reasoning observability.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime,
    JSON, Boolean, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class MedicalReport(Base, UUIDMixin, TimestampMixin):
    """Stores uploaded medical reports and their AI analysis results."""

    __tablename__ = "medical_reports"
    __table_args__ = (
        Index("ix_reports_status", "status"),
        Index("ix_reports_patient", "patient_id"),
        Index("ix_reports_created", "created_at"),
    )

    # ── Patient Link (optional — matched during analysis) ─────────
    patient_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True,
        comment="Linked patient record (matched by Context Agent)",
    )

    # ── File Metadata ─────────────────────────────────────────────
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Analysis Status ───────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="pending | processing | completed | failed",
    )

    # ── Extracted Entities ────────────────────────────────────────
    patient_age: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    patient_gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    symptoms: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    medications: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    procedures: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    lab_values: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    body_parts: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    clinical_impression: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Agentic Structured Outputs ────────────────────────────────
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_biomarkers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    critical_risks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Autonomous Trace Memory ───────────────────────────────────
    reasoning_timeline: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    ehr_context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    incident_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    generated_actions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    copilot_memory_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Critic Agent Results ──────────────────────────────────────
    final_confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Post-critic validated confidence score",
    )
    critic_iterations: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="Number of critic self-healing iterations",
    )
    hallucination_flags: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=None,
        comment="Potential hallucination flags from Critic Agent",
    )

    # ── Full Structured JSON ──────────────────────────────────────
    full_analysis_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Performance Tracking ──────────────────────────────────────
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Agentic Workflow Metadata ─────────────────────────────────
    reasoning_chain: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None,
        comment="Complete reasoning chain: plan → steps → validations",
    )
    agent_workflow_status: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default="pending",
        comment="pending | observing | planning | reasoning | validating | critiquing | complete | failed",
    )

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="reports")
    agent_traces = relationship("AgentTrace", back_populates="report", lazy="selectin",
                                order_by="AgentTrace.created_at")
    chat_sessions = relationship("ChatSession", lazy="selectin")

    def __repr__(self) -> str:
        return f"<MedicalReport id={self.id} filename={self.filename} status={self.status}>"
