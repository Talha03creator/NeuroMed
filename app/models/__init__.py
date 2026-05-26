"""
Models Package — Agentic Clinical Intelligence Platform

Exports all SQLAlchemy ORM models for the clinical data warehouse.
Import order matters: Base must be imported before any model that inherits it.
"""

from app.models.base import Base, UUIDMixin, TimestampMixin

# ── Clinical Warehouse Models ─────────────────────────────────────
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.medication import Medication
from app.models.vital import Vital
from app.models.lab_result import LabResult
from app.models.diagnosis import Diagnosis
from app.models.procedure import Procedure
from app.models.allergy import Allergy
from app.models.clinical_note import ClinicalNote

# ── Platform Models ───────────────────────────────────────────────
from app.models.report import MedicalReport
from app.models.agent_trace import AgentTrace
from app.models.chat_session import ChatSession, ChatMessage
from app.models.sync_log import SyncLog
from app.models.audit_log import AuditLog

__all__ = [
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    # Clinical
    "Patient",
    "Encounter",
    "Medication",
    "Vital",
    "LabResult",
    "Diagnosis",
    "Procedure",
    "Allergy",
    "ClinicalNote",
    # Platform
    "MedicalReport",
    "AgentTrace",
    "ChatSession",
    "ChatMessage",
    "SyncLog",
    "AuditLog",
]
