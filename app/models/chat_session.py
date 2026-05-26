"""
Chat Session & Message Models
Agentic Clinical Intelligence Platform

Supports the Interactive Clinical Assistant Chat with WebSocket-based
conversations. Each session links to a report and optionally a patient,
carrying a context snapshot for memory-aware reasoning.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, DateTime, JSON, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class ChatSession(Base, UUIDMixin, TimestampMixin):
    """A conversation session linked to a report and/or patient."""

    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("ix_chat_report", "report_id"),
        Index("ix_chat_patient", "patient_id"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────
    report_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("medical_reports.id", ondelete="SET NULL"), nullable=True,
    )
    patient_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True,
    )

    # ── Session Context ───────────────────────────────────────────
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    context_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None,
        comment="Frozen context for memory-aware conversations: report summary, patient history, etc.",
    )
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    message_count: Mapped[int] = mapped_column(nullable=False, default=0)

    # ── Relationships ─────────────────────────────────────────────
    messages = relationship("ChatMessage", back_populates="session", lazy="selectin",
                            order_by="ChatMessage.created_at")

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} messages={self.message_count}>"


class ChatMessage(Base, UUIDMixin):
    """A single message within a chat session."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_msg_session", "session_id"),
        Index("ix_msg_role", "role"),
        Index("ix_msg_created", "created_at"),
    )

    # ── Foreign Key ───────────────────────────────────────────────
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False,
    )

    # ── Message Content ───────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="user | assistant | system",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Metadata ──────────────────────────────────────────────────
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None,
        comment="Token usage, latency, agent traces used, confidence, etc.",
    )
    tokens_used: Mapped[Optional[int]] = mapped_column(nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(nullable=True)

    # ── Timestamp ─────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(__import__('datetime').timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage role={self.role} len={len(self.content)}>"
