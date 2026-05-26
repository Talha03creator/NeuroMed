"""
Audit Log Model — HIPAA-Inspired Compliance Trail
Agentic Clinical Intelligence Platform

Records every significant action for compliance auditing:
data access, modifications, exports, and security events.
Immutable — no UPDATE or DELETE operations permitted.
"""

from datetime import datetime

from sqlalchemy import (
    String, Text, DateTime, JSON, Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class AuditLog(Base, UUIDMixin):
    """Immutable audit trail entry for HIPAA-inspired compliance."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_event", "event_type"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_created", "created_at"),
        Index("ix_audit_action", "action"),
    )

    # ── Event Classification ──────────────────────────────────────
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="data_access | data_modification | data_export | security | system | agent_action",
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="create | read | update | delete | export | login | analyze | chat | sync",
    )

    # ── Target Entity ─────────────────────────────────────────────
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="report | patient | chat_session | sync | agent_trace",
    )
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # ── Details ───────────────────────────────────────────────────
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None,
        comment="Structured details: fields changed, query params, etc.",
    )

    # ── Request Context ───────────────────────────────────────────
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # ── Actor ─────────────────────────────────────────────────────
    actor_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="system",
        comment="user | system | agent | api_client",
    )
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Severity ──────────────────────────────────────────────────
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info",
        comment="info | warning | critical",
    )

    # ── Timestamp (immutable) ─────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(__import__('datetime').timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AuditLog event={self.event_type} action={self.action} entity={self.entity_type}:{self.entity_id}>"
