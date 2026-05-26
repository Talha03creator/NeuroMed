"""
Sync Log Model — Fivetran Synchronization Metadata
Agentic Clinical Intelligence Platform

Records every Fivetran sync run with connector details, row counts,
duration, and error information. Enables the sync status panel
and data freshness monitoring on the frontend.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Integer, Float, Text, DateTime, JSON, Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class SyncLog(Base, UUIDMixin):
    """Fivetran sync execution log entry."""

    __tablename__ = "sync_logs"
    __table_args__ = (
        Index("ix_sync_connector", "connector_name"),
        Index("ix_sync_status", "sync_status"),
        Index("ix_sync_started", "started_at"),
    )

    # ── Connector Info ────────────────────────────────────────────
    connector_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="e.g., ehr_connector, lab_connector, vitals_connector",
    )
    connector_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Mock Fivetran connector ID",
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="ehr | lab | medication | vitals | diagnosis",
    )
    destination_table: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Target PostgreSQL table name",
    )
    sync_mode: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default="incremental",
        comment="full_refresh | incremental | append",
    )

    # ── Sync Status ───────────────────────────────────────────────
    sync_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending",
        comment="pending | in_progress | completed | failed | partial",
    )

    # ── Metrics ───────────────────────────────────────────────────
    rows_synced: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    rows_updated: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    rows_deleted: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bytes_transferred: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Error Tracking ────────────────────────────────────────────
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

    # ── Metadata ──────────────────────────────────────────────────
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None,
        comment="Additional sync metadata: schema changes, warnings, etc.",
    )
    triggered_by: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="scheduled",
        comment="scheduled | manual | context_agent | api",
    )

    # ── Timestamps ────────────────────────────────────────────────
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    def __repr__(self) -> str:
        return f"<SyncLog connector={self.connector_name} status={self.sync_status} rows={self.rows_synced}>"
