"""
Fivetran Sync Engine — ETL/ELT Pipeline
Agentic Clinical Intelligence Platform

Implements the actual data synchronization logic:
1. Pulls data from MockHealthcareSources
2. Transforms into ORM model instances
3. Upserts into PostgreSQL clinical warehouse tables
4. Logs sync metadata to sync_logs table
5. Updates FivetranMCPClient sync history

Supports both full-refresh and incremental sync modes.
"""

import time
import uuid
import logging
from datetime import datetime, date, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.medication import Medication
from app.models.vital import Vital
from app.models.lab_result import LabResult
from app.models.diagnosis import Diagnosis
from app.models.allergy import Allergy
from app.models.clinical_note import ClinicalNote
from app.models.sync_log import SyncLog
from app.mcp.fivetran.mock_sources import MockHealthcareSources
from app.mcp.fivetran.client import fivetran_client

logger = logging.getLogger(__name__)


def _parse_date(val: Optional[str]) -> Optional[date]:
    """Safely parse an ISO date string."""
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except (ValueError, TypeError):
        return None


def _parse_datetime(val: Optional[str]) -> Optional[datetime]:
    """Safely parse an ISO datetime string."""
    if not val:
        return None
    try:
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


class FivetranSyncEngine:
    """
    Executes mock Fivetran sync pipelines that pull from external
    healthcare sources and load into the PostgreSQL clinical warehouse.
    """

    def __init__(self):
        self._sources = MockHealthcareSources(num_patients=15)
        self._patient_id_map: Dict[str, str] = {}  # source_id → db_id
        self._encounter_id_map: Dict[str, str] = {}  # source_id → db_id

    async def _create_sync_log(
        self, db: AsyncSession, connector_name: str, source_type: str
    ) -> SyncLog:
        """Create a pending sync log entry."""
        log = SyncLog(
            connector_name=connector_name,
            connector_id=f"conn_{source_type}_mock",
            source_type=source_type,
            sync_status="in_progress",
            sync_mode="full_refresh",
            triggered_by="sync_engine",
            started_at=datetime.now(timezone.utc),
        )
        db.add(log)
        await db.flush()
        return log

    async def _complete_sync_log(
        self,
        db: AsyncSession,
        log: SyncLog,
        rows: int,
        duration: float,
        status: str = "completed",
        error: Optional[str] = None,
    ) -> None:
        """Finalize a sync log entry."""
        log.sync_status = status
        log.rows_synced = rows
        log.duration_seconds = round(duration, 3)
        log.completed_at = datetime.now(timezone.utc)
        log.error_message = error
        await db.flush()

    # ── Sync Patients ─────────────────────────────────────────────
    async def sync_patients(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync patient records from EHR source."""
        connector = "ehr_connector"
        log = await self._create_sync_log(db, connector, "ehr")
        start = time.monotonic()

        try:
            await fivetran_client.trigger_sync(connector)
            source_patients = self._sources.get_patients()
            rows_synced = 0

            for sp in source_patients:
                # Check if patient already exists by source_id
                result = await db.execute(
                    select(Patient).where(Patient.source_id == sp["source_id"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    for key in ["first_name", "last_name", "phone", "email", "address",
                                "insurance_provider", "insurance_id"]:
                        if sp.get(key):
                            setattr(existing, key, sp[key])
                    self._patient_id_map[sp["source_id"]] = existing.id
                else:
                    # Create new
                    patient = Patient(
                        mrn=sp["mrn"],
                        first_name=sp["first_name"],
                        last_name=sp["last_name"],
                        date_of_birth=_parse_date(sp["date_of_birth"]),
                        gender=sp["gender"],
                        blood_type=sp.get("blood_type"),
                        phone=sp.get("phone"),
                        email=sp.get("email"),
                        address=sp.get("address"),
                        emergency_contact=sp.get("emergency_contact"),
                        insurance_provider=sp.get("insurance_provider"),
                        insurance_id=sp.get("insurance_id"),
                        active=sp.get("active", True),
                        source_system=sp["source_system"],
                        source_id=sp["source_id"],
                    )
                    db.add(patient)
                    await db.flush()
                    self._patient_id_map[sp["source_id"]] = patient.id

                rows_synced += 1

            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, rows_synced, duration)
            fivetran_client.mark_sync_completed(connector, rows_synced, duration)
            logger.info("[Fivetran Sync] Patients synced: %d rows in %.2fs", rows_synced, duration)
            return {"connector": connector, "rows": rows_synced, "duration": duration, "status": "completed"}

        except Exception as e:
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, 0, duration, "failed", str(e))
            fivetran_client.mark_sync_failed(connector, str(e))
            logger.error("[Fivetran Sync] Patient sync failed: %s", e)
            return {"connector": connector, "rows": 0, "duration": duration, "status": "failed", "error": str(e)}

    # ── Sync Encounters ───────────────────────────────────────────
    async def sync_encounters(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync encounter records from EHR source."""
        connector = "ehr_connector"
        log = await self._create_sync_log(db, connector, "ehr")
        start = time.monotonic()

        try:
            patient_source_ids = list(self._patient_id_map.keys())
            source_encounters = self._sources.get_encounters(patient_source_ids)
            rows_synced = 0

            for se in source_encounters:
                patient_db_id = self._patient_id_map.get(se["patient_source_id"])
                if not patient_db_id:
                    continue

                result = await db.execute(
                    select(Encounter).where(Encounter.source_id == se["source_id"])
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    enc = Encounter(
                        patient_id=patient_db_id,
                        encounter_type=se["encounter_type"],
                        encounter_date=_parse_datetime(se["encounter_date"]),
                        provider_name=se.get("provider_name"),
                        department=se.get("department"),
                        chief_complaint=se.get("chief_complaint"),
                        disposition=se.get("disposition"),
                        notes=se.get("notes"),
                        source_system=se["source_system"],
                        source_id=se["source_id"],
                    )
                    db.add(enc)
                    await db.flush()
                    self._encounter_id_map[se["source_id"]] = enc.id
                else:
                    self._encounter_id_map[se["source_id"]] = existing.id

                rows_synced += 1

            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, rows_synced, duration)
            logger.info("[Fivetran Sync] Encounters synced: %d rows in %.2fs", rows_synced, duration)
            return {"connector": connector, "rows": rows_synced, "duration": duration, "status": "completed"}

        except Exception as e:
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, 0, duration, "failed", str(e))
            logger.error("[Fivetran Sync] Encounter sync failed: %s", e)
            return {"connector": connector, "rows": 0, "status": "failed", "error": str(e)}

    # ── Sync Medications ──────────────────────────────────────────
    async def sync_medications(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync medication records."""
        connector = "medication_connector"
        log = await self._create_sync_log(db, connector, "medication")
        start = time.monotonic()

        try:
            patient_source_ids = list(self._patient_id_map.keys())
            source_meds = self._sources.get_medications(patient_source_ids)
            rows_synced = 0

            for sm in source_meds:
                patient_db_id = self._patient_id_map.get(sm["patient_source_id"])
                if not patient_db_id:
                    continue

                result = await db.execute(
                    select(Medication).where(Medication.source_id == sm["source_id"])
                )
                if result.scalar_one_or_none():
                    rows_synced += 1
                    continue

                med = Medication(
                    patient_id=patient_db_id,
                    medication_name=sm["medication_name"],
                    generic_name=sm.get("generic_name"),
                    dosage=sm.get("dosage"),
                    frequency=sm.get("frequency"),
                    route=sm.get("route"),
                    start_date=_parse_date(sm.get("start_date")),
                    end_date=_parse_date(sm.get("end_date")),
                    status=sm.get("status", "active"),
                    prescribed_by=sm.get("prescribed_by"),
                    reason=sm.get("reason"),
                    source_system=sm["source_system"],
                    source_id=sm["source_id"],
                )
                db.add(med)
                rows_synced += 1

            await db.flush()
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, rows_synced, duration)
            fivetran_client.mark_sync_completed(connector, rows_synced, duration)
            logger.info("[Fivetran Sync] Medications synced: %d rows in %.2fs", rows_synced, duration)
            return {"connector": connector, "rows": rows_synced, "duration": duration, "status": "completed"}

        except Exception as e:
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, 0, duration, "failed", str(e))
            fivetran_client.mark_sync_failed(connector, str(e))
            logger.error("[Fivetran Sync] Medication sync failed: %s", e)
            return {"connector": connector, "rows": 0, "status": "failed", "error": str(e)}

    # ── Sync Vitals ───────────────────────────────────────────────
    async def sync_vitals(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync vital signs records."""
        connector = "vitals_connector"
        log = await self._create_sync_log(db, connector, "vitals")
        start = time.monotonic()

        try:
            patient_source_ids = list(self._patient_id_map.keys())
            source_vitals = self._sources.get_vitals(patient_source_ids)
            rows_synced = 0

            for sv in source_vitals:
                patient_db_id = self._patient_id_map.get(sv["patient_source_id"])
                if not patient_db_id:
                    continue

                result = await db.execute(
                    select(Vital).where(Vital.source_id == sv["source_id"])
                )
                if result.scalar_one_or_none():
                    rows_synced += 1
                    continue

                vital = Vital(
                    patient_id=patient_db_id,
                    heart_rate=sv.get("heart_rate"),
                    blood_pressure_systolic=sv.get("blood_pressure_systolic"),
                    blood_pressure_diastolic=sv.get("blood_pressure_diastolic"),
                    temperature=sv.get("temperature"),
                    respiratory_rate=sv.get("respiratory_rate"),
                    oxygen_saturation=sv.get("oxygen_saturation"),
                    weight_kg=sv.get("weight_kg"),
                    height_cm=sv.get("height_cm"),
                    pain_level=sv.get("pain_level"),
                    recorded_at=_parse_datetime(sv["recorded_at"]),
                    recorded_by=sv.get("recorded_by"),
                    position=sv.get("position"),
                    source_system=sv["source_system"],
                    source_id=sv["source_id"],
                )
                db.add(vital)
                rows_synced += 1

            await db.flush()
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, rows_synced, duration)
            fivetran_client.mark_sync_completed(connector, rows_synced, duration)
            logger.info("[Fivetran Sync] Vitals synced: %d rows in %.2fs", rows_synced, duration)
            return {"connector": connector, "rows": rows_synced, "duration": duration, "status": "completed"}

        except Exception as e:
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, 0, duration, "failed", str(e))
            fivetran_client.mark_sync_failed(connector, str(e))
            logger.error("[Fivetran Sync] Vitals sync failed: %s", e)
            return {"connector": connector, "rows": 0, "status": "failed", "error": str(e)}

    # ── Sync Lab Results ──────────────────────────────────────────
    async def sync_lab_results(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync lab results."""
        connector = "lab_connector"
        log = await self._create_sync_log(db, connector, "lab")
        start = time.monotonic()

        try:
            patient_source_ids = list(self._patient_id_map.keys())
            source_labs = self._sources.get_lab_results(patient_source_ids)
            rows_synced = 0

            for sl in source_labs:
                patient_db_id = self._patient_id_map.get(sl["patient_source_id"])
                if not patient_db_id:
                    continue

                result = await db.execute(
                    select(LabResult).where(LabResult.source_id == sl["source_id"])
                )
                if result.scalar_one_or_none():
                    rows_synced += 1
                    continue

                lab = LabResult(
                    patient_id=patient_db_id,
                    test_name=sl["test_name"],
                    test_code=sl.get("test_code"),
                    panel_name=sl.get("panel_name"),
                    result_value=sl["result_value"],
                    unit=sl.get("unit"),
                    reference_range=sl.get("reference_range"),
                    flag=sl.get("flag"),
                    collected_at=_parse_datetime(sl.get("collected_at")),
                    resulted_at=_parse_datetime(sl.get("resulted_at")),
                    ordered_by=sl.get("ordered_by"),
                    performing_lab=sl.get("performing_lab"),
                    source_system=sl["source_system"],
                    source_id=sl["source_id"],
                )
                db.add(lab)
                rows_synced += 1

            await db.flush()
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, rows_synced, duration)
            fivetran_client.mark_sync_completed(connector, rows_synced, duration)
            logger.info("[Fivetran Sync] Lab results synced: %d rows in %.2fs", rows_synced, duration)
            return {"connector": connector, "rows": rows_synced, "duration": duration, "status": "completed"}

        except Exception as e:
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, 0, duration, "failed", str(e))
            fivetran_client.mark_sync_failed(connector, str(e))
            logger.error("[Fivetran Sync] Lab sync failed: %s", e)
            return {"connector": connector, "rows": 0, "status": "failed", "error": str(e)}

    # ── Sync Diagnoses ────────────────────────────────────────────
    async def sync_diagnoses(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync diagnosis records."""
        connector = "diagnosis_connector"
        log = await self._create_sync_log(db, connector, "diagnosis")
        start = time.monotonic()

        try:
            patient_source_ids = list(self._patient_id_map.keys())
            source_dx = self._sources.get_diagnoses(patient_source_ids)
            rows_synced = 0

            for sd in source_dx:
                patient_db_id = self._patient_id_map.get(sd["patient_source_id"])
                if not patient_db_id:
                    continue

                result = await db.execute(
                    select(Diagnosis).where(Diagnosis.source_id == sd["source_id"])
                )
                if result.scalar_one_or_none():
                    rows_synced += 1
                    continue

                dx = Diagnosis(
                    patient_id=patient_db_id,
                    icd_code=sd.get("icd_code"),
                    description=sd["description"],
                    severity=sd.get("severity"),
                    diagnosis_type=sd.get("diagnosis_type", "primary"),
                    status=sd.get("status", "active"),
                    diagnosed_date=_parse_date(sd.get("diagnosed_date")),
                    resolved_date=_parse_date(sd.get("resolved_date")),
                    diagnosed_by=sd.get("diagnosed_by"),
                    source_system=sd["source_system"],
                    source_id=sd["source_id"],
                )
                db.add(dx)
                rows_synced += 1

            await db.flush()
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, rows_synced, duration)
            fivetran_client.mark_sync_completed(connector, rows_synced, duration)
            logger.info("[Fivetran Sync] Diagnoses synced: %d rows in %.2fs", rows_synced, duration)
            return {"connector": connector, "rows": rows_synced, "duration": duration, "status": "completed"}

        except Exception as e:
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, 0, duration, "failed", str(e))
            fivetran_client.mark_sync_failed(connector, str(e))
            logger.error("[Fivetran Sync] Diagnosis sync failed: %s", e)
            return {"connector": connector, "rows": 0, "status": "failed", "error": str(e)}

    # ── Sync Allergies ────────────────────────────────────────────
    async def sync_allergies(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync allergy records."""
        connector = "ehr_connector"
        log = await self._create_sync_log(db, connector, "ehr")
        start = time.monotonic()

        try:
            patient_source_ids = list(self._patient_id_map.keys())
            source_allergies = self._sources.get_allergies(patient_source_ids)
            rows_synced = 0

            for sa in source_allergies:
                patient_db_id = self._patient_id_map.get(sa["patient_source_id"])
                if not patient_db_id:
                    continue

                result = await db.execute(
                    select(Allergy).where(Allergy.source_id == sa["source_id"])
                )
                if result.scalar_one_or_none():
                    rows_synced += 1
                    continue

                allergy = Allergy(
                    patient_id=patient_db_id,
                    allergen=sa["allergen"],
                    allergen_type=sa.get("allergen_type"),
                    reaction=sa.get("reaction"),
                    severity=sa.get("severity"),
                    onset_date=_parse_date(sa.get("onset_date")),
                    status=sa.get("status", "active"),
                    verified=sa.get("verified", False),
                    source_system=sa["source_system"],
                    source_id=sa["source_id"],
                )
                db.add(allergy)
                rows_synced += 1

            await db.flush()
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, rows_synced, duration)
            logger.info("[Fivetran Sync] Allergies synced: %d rows in %.2fs", rows_synced, duration)
            return {"connector": connector, "rows": rows_synced, "duration": duration, "status": "completed"}

        except Exception as e:
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, 0, duration, "failed", str(e))
            logger.error("[Fivetran Sync] Allergy sync failed: %s", e)
            return {"connector": connector, "rows": 0, "status": "failed", "error": str(e)}

    # ── Sync Clinical Notes ───────────────────────────────────────
    async def sync_clinical_notes(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync clinical notes."""
        connector = "ehr_connector"
        log = await self._create_sync_log(db, connector, "ehr")
        start = time.monotonic()

        try:
            patient_source_ids = list(self._patient_id_map.keys())
            source_notes = self._sources.get_clinical_notes(patient_source_ids)
            rows_synced = 0

            for sn in source_notes:
                patient_db_id = self._patient_id_map.get(sn["patient_source_id"])
                if not patient_db_id:
                    continue

                result = await db.execute(
                    select(ClinicalNote).where(ClinicalNote.source_id == sn["source_id"])
                )
                if result.scalar_one_or_none():
                    rows_synced += 1
                    continue

                note = ClinicalNote(
                    patient_id=patient_db_id,
                    note_type=sn["note_type"],
                    title=sn.get("title"),
                    content=sn["content"],
                    author=sn.get("author"),
                    author_role=sn.get("author_role"),
                    department=sn.get("department"),
                    authored_at=_parse_datetime(sn["authored_at"]),
                    is_addendum=sn.get("is_addendum", False),
                    source_system=sn["source_system"],
                    source_id=sn["source_id"],
                )
                db.add(note)
                rows_synced += 1

            await db.flush()
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, rows_synced, duration)
            logger.info("[Fivetran Sync] Clinical notes synced: %d rows in %.2fs", rows_synced, duration)
            return {"connector": connector, "rows": rows_synced, "duration": duration, "status": "completed"}

        except Exception as e:
            duration = time.monotonic() - start
            await self._complete_sync_log(db, log, 0, duration, "failed", str(e))
            logger.error("[Fivetran Sync] Clinical notes sync failed: %s", e)
            return {"connector": connector, "rows": 0, "status": "failed", "error": str(e)}

    # ── Full Sync (all sources) ───────────────────────────────────
    async def run_full_sync(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Execute a complete sync across all healthcare sources.
        Order matters: patients first, then dependent tables.
        """
        logger.info("=" * 60)
        logger.info("[Fivetran Sync Engine] Starting FULL SYNC across all sources")
        logger.info("=" * 60)

        full_start = time.monotonic()
        results = {}

        # Sync in dependency order
        results["patients"] = await self.sync_patients(db)
        results["encounters"] = await self.sync_encounters(db)
        results["medications"] = await self.sync_medications(db)
        results["vitals"] = await self.sync_vitals(db)
        results["lab_results"] = await self.sync_lab_results(db)
        results["diagnoses"] = await self.sync_diagnoses(db)
        results["allergies"] = await self.sync_allergies(db)
        results["clinical_notes"] = await self.sync_clinical_notes(db)

        total_duration = time.monotonic() - full_start
        total_rows = sum(r.get("rows", 0) for r in results.values())
        failed = [k for k, v in results.items() if v.get("status") == "failed"]

        summary = {
            "status": "completed" if not failed else "partial",
            "total_rows_synced": total_rows,
            "total_duration_seconds": round(total_duration, 2),
            "tables_synced": len(results) - len(failed),
            "tables_failed": len(failed),
            "failed_tables": failed,
            "details": results,
        }

        logger.info(
            "[Fivetran Sync Engine] FULL SYNC complete: %d rows | %.2fs | %d/%d tables OK",
            total_rows, total_duration, len(results) - len(failed), len(results),
        )
        return summary


# ── Singleton ─────────────────────────────────────────────────────
sync_engine = FivetranSyncEngine()
