"""
Agent Trace Model — AI Reasoning Observability
Agentic Clinical Intelligence Platform

Records every reasoning step from the 4-agent system:
- Orchestrator planning steps
- Context Agent retrieval traces
- Critic Agent validation iterations
- DevSecOps Agent incident traces

Used by the Arize Phoenix MCP for confidence scoring,
hallucination detection, and self-healing loop monitoring.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, Float, Integer, DateTime, JSON, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class AgentTrace(Base, UUIDMixin):
    """Single reasoning step trace from an agent."""

    __tablename__ = "agent_traces"
    __table_args__ = (
        Index("ix_trace_report", "report_id"),
        Index("ix_trace_agent", "agent_name"),
        Index("ix_trace_status", "status"),
        Index("ix_trace_created", "created_at"),
        Index("ix_trace_confidence", "confidence"),
        Index("ix_trace_iteration", "iteration"),
    )

    # ── Foreign Key ───────────────────────────────────────────────
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=False,
    )

    # ── Agent Identity ────────────────────────────────────────────
    agent_name: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="orchestrator | context_agent | critic_agent | devsecops_agent",
    )
    step_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="observe | plan | retrieve_context | reason | validate | critique | improve | respond",
    )
    step_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Execution order within this agent's workflow",
    )

    # ── Input/Output ──────────────────────────────────────────────
    input_data: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Prompt or input sent to this step (PII-redacted)",
    )
    output_data: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Response or output from this step",
    )
    tool_calls: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None,
        comment="List of tool calls made during this step",
    )

    # ── Quality Metrics ───────────────────────────────────────────
    confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Confidence score for this step (0.0 - 1.0)",
    )
    hallucination_risk: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Estimated hallucination risk (0.0 - 1.0)",
    )

    # ── Performance Metrics ───────────────────────────────────────
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_input: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Self-Healing Loop ─────────────────────────────────────────
    iteration: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="Iteration count — >1 means self-healing retry occurred",
    )
    parent_trace_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("agent_traces.id", ondelete="SET NULL"), nullable=True,
        comment="Links to previous iteration trace for self-healing chains",
    )
    refinement_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Why the Critic Agent triggered a retry",
    )

    # ── Status ────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="completed",
        comment="pending | running | completed | failed | retrying",
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Metadata ──────────────────────────────────────────────────
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=None)

    # ── Timestamp ─────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(__import__('datetime').timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────
    report = relationship("MedicalReport", back_populates="agent_traces")

    def __repr__(self) -> str:
        return (
            f"<AgentTrace agent={self.agent_name} step={self.step_name} "
            f"confidence={self.confidence} iteration={self.iteration}>"
        )
