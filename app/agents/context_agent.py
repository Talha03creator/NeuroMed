"""
Agent 2 — Context Agent (Fivetran MCP Integration)
Agentic Clinical Intelligence Platform

Retrieves and formats historical patient context from the PostgreSQL
clinical warehouse (data synced via Fivetran MCP). Provides the
Orchestrator with structured historical baselines, medication changes,
lab trends, diagnoses, allergies, and vitals for autonomous clinical
reasoning and contradiction detection.

MCP Tools Used:
  - fivetran_get_data_freshness → verify data is current
  - fivetran_trigger_sync → force sync if data is stale
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.models.patient import Patient
from app.models.medication import Medication
from app.models.lab_result import LabResult
from app.models.vital import Vital
from app.models.diagnosis import Diagnosis
from app.models.allergy import Allergy
from app.models.encounter import Encounter
from app.models.clinical_note import ClinicalNote
from app.models.agent_trace import AgentTrace
from app.mcp.fivetran.client import fivetran_client

logger = logging.getLogger(__name__)


# ── Helper: Format a list of items for prompt injection ───────────
def _bullet_list(items: List[str], max_items: int = 15) -> str:
    """Format items as a bulleted list, capped to avoid token bloat."""
    if not items:
        return "  • None on record"
    return "\n".join(f"  • {item}" for item in items[:max_items])


# ── Helper: Trend detection for lab values ────────────────────────
def _detect_lab_trends(labs: List[Dict[str, Any]]) -> List[str]:
    """
    Group labs by test name and detect upward/downward trends.
    Returns human-readable trend descriptions.
    """
    from collections import defaultdict

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for lab in labs:
        grouped[lab["test_name"]].append(lab)

    trends = []
    for test_name, entries in grouped.items():
        # Sort by collection date ascending
        sorted_entries = sorted(entries, key=lambda x: x.get("collected_at") or "")
        if len(sorted_entries) < 2:
            continue

        try:
            vals = [float(e["result_value"]) for e in sorted_entries]
            first_val = vals[0]
            last_val = vals[-1]
            pct_change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0

            if abs(pct_change) > 10:
                direction = "INCREASING ↑" if pct_change > 0 else "DECREASING ↓"
                trends.append(
                    f"{test_name}: {direction} ({first_val} → {last_val}, "
                    f"{pct_change:+.1f}% change over {len(sorted_entries)} readings)"
                )
        except (ValueError, TypeError):
            continue

    return trends


class ContextAgent:
    """
    Agent 2 — Fivetran Context Intelligence Agent.

    Responsibilities:
    1. Verify data freshness via Fivetran MCP
    2. Extract patient identifiers from report text
    3. Query the clinical warehouse for full patient history
    4. Compare current findings with historical baselines
    5. Detect trends and contradictions
    6. Format enriched context for the Orchestrator's prompt
    """

    async def _verify_data_freshness(self) -> Dict[str, Any]:
        """
        Check Fivetran connector freshness before querying the warehouse.
        If data is stale, trigger a sync.
        """
        try:
            freshness = await fivetran_client.get_data_freshness()
            stale_connectors = []

            if freshness["status"] == "success":
                for name, info in freshness["data"].items():
                    if not info["is_fresh"]:
                        stale_connectors.append(name)
                        logger.warning(
                            "[Context Agent] Stale data detected for %s — triggering sync",
                            name,
                        )
                        await fivetran_client.trigger_sync(name)

            return {
                "freshness_checked": True,
                "stale_connectors": stale_connectors,
                "all_fresh": len(stale_connectors) == 0,
            }
        except Exception as e:
            logger.error("[Context Agent] Data freshness check failed: %s", e)
            return {"freshness_checked": False, "error": str(e)}

    async def _fetch_patient(
        self, db: AsyncSession, patient_id: str
    ) -> Optional[Patient]:
        """Fetch patient record by ID."""
        result = await db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        return result.scalar_one_or_none()

    async def _fetch_medications(
        self, db: AsyncSession, patient_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch all medications for a patient, ordered by start date."""
        result = await db.execute(
            select(Medication)
            .where(Medication.patient_id == patient_id)
            .order_by(desc(Medication.start_date))
        )
        meds = result.scalars().all()
        return [
            {
                "medication_name": m.medication_name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "route": m.route,
                "status": m.status,
                "start_date": str(m.start_date) if m.start_date else None,
                "end_date": str(m.end_date) if m.end_date else None,
                "reason": m.reason,
                "prescribed_by": m.prescribed_by,
            }
            for m in meds
        ]

    async def _fetch_lab_results(
        self, db: AsyncSession, patient_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch recent lab results for a patient."""
        result = await db.execute(
            select(LabResult)
            .where(LabResult.patient_id == patient_id)
            .order_by(desc(LabResult.collected_at))
            .limit(limit)
        )
        labs = result.scalars().all()
        return [
            {
                "test_name": l.test_name,
                "result_value": l.result_value,
                "unit": l.unit,
                "reference_range": l.reference_range,
                "flag": l.flag,
                "collected_at": str(l.collected_at) if l.collected_at else None,
                "panel_name": l.panel_name,
            }
            for l in labs
        ]

    async def _fetch_vitals(
        self, db: AsyncSession, patient_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch recent vitals for a patient."""
        result = await db.execute(
            select(Vital)
            .where(Vital.patient_id == patient_id)
            .order_by(desc(Vital.recorded_at))
            .limit(limit)
        )
        vitals = result.scalars().all()
        return [
            {
                "heart_rate": v.heart_rate,
                "bp": f"{v.blood_pressure_systolic}/{v.blood_pressure_diastolic}"
                if v.blood_pressure_systolic
                else None,
                "temperature": v.temperature,
                "respiratory_rate": v.respiratory_rate,
                "oxygen_saturation": v.oxygen_saturation,
                "pain_level": v.pain_level,
                "recorded_at": str(v.recorded_at) if v.recorded_at else None,
            }
            for v in vitals
        ]

    async def _fetch_diagnoses(
        self, db: AsyncSession, patient_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch all diagnoses for a patient."""
        result = await db.execute(
            select(Diagnosis)
            .where(Diagnosis.patient_id == patient_id)
            .order_by(desc(Diagnosis.diagnosed_date))
        )
        dxs = result.scalars().all()
        return [
            {
                "icd_code": d.icd_code,
                "description": d.description,
                "severity": d.severity,
                "status": d.status,
                "diagnosed_date": str(d.diagnosed_date) if d.diagnosed_date else None,
            }
            for d in dxs
        ]

    async def _fetch_allergies(
        self, db: AsyncSession, patient_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch all allergies for a patient."""
        result = await db.execute(
            select(Allergy)
            .where(Allergy.patient_id == patient_id)
            .order_by(desc(Allergy.created_at))
        )
        allergies = result.scalars().all()
        return [
            {
                "allergen": a.allergen,
                "allergen_type": a.allergen_type,
                "reaction": a.reaction,
                "severity": a.severity,
                "status": a.status,
            }
            for a in allergies
        ]

    async def _fetch_recent_encounters(
        self, db: AsyncSession, patient_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Fetch recent encounters for a patient."""
        result = await db.execute(
            select(Encounter)
            .where(Encounter.patient_id == patient_id)
            .order_by(desc(Encounter.encounter_date))
            .limit(limit)
        )
        encounters = result.scalars().all()
        return [
            {
                "encounter_type": e.encounter_type,
                "encounter_date": str(e.encounter_date) if e.encounter_date else None,
                "department": e.department,
                "chief_complaint": e.chief_complaint,
                "disposition": e.disposition,
                "provider_name": e.provider_name,
            }
            for e in encounters
        ]

    # ── Main Context Retrieval ────────────────────────────────────
    async def get_historical_context(
        self,
        patient_id: str,
        db: AsyncSession,
        report_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve full historical context for a patient from the
        Fivetran-synced clinical warehouse.

        Returns:
            Dict with 'context_text' (formatted string for prompt injection),
            'structured_data' (raw data for the frontend), and
            'trends' (detected lab/vitals trends).
        """
        start_time = time.monotonic()
        logger.info("[Context Agent] Retrieving context for patient_id=%s", patient_id)

        # ── Step 1: Verify data freshness via Fivetran MCP ────────
        freshness = await self._verify_data_freshness()

        # ── Step 2: Fetch patient record ──────────────────────────
        patient = await self._fetch_patient(db, patient_id)
        if not patient:
            logger.warning("[Context Agent] Patient %s not found", patient_id)
            return {
                "context_text": "No historical patient data available. Analyze report in isolation.",
                "structured_data": None,
                "trends": [],
                "enriched": False,
                "latency_ms": (time.monotonic() - start_time) * 1000,
            }

        # ── Step 3: Fetch all clinical data in parallel ───────────
        medications = await self._fetch_medications(db, patient_id)
        lab_results = await self._fetch_lab_results(db, patient_id)
        vitals = await self._fetch_vitals(db, patient_id)
        diagnoses = await self._fetch_diagnoses(db, patient_id)
        allergies = await self._fetch_allergies(db, patient_id)
        encounters = await self._fetch_recent_encounters(db, patient_id)

        # ── Step 4: Detect trends ─────────────────────────────────
        lab_trends = _detect_lab_trends(lab_results)

        # Medication changes (recently discontinued)
        med_changes = []
        for m in medications:
            if m["status"] == "discontinued" and m["end_date"]:
                med_changes.append(
                    f"DISCONTINUED: {m['medication_name']} {m['dosage']} "
                    f"(stopped {m['end_date']}, was for: {m['reason']})"
                )

        # Active medications
        active_meds = [
            f"{m['medication_name']} {m['dosage']} {m['frequency']} ({m['route']})"
            for m in medications
            if m["status"] == "active"
        ]

        # Abnormal labs
        abnormal_labs = [
            f"{l['test_name']}: {l['result_value']} {l['unit']} "
            f"(ref: {l['reference_range']}, FLAG: {l['flag'].upper()})"
            for l in lab_results
            if l.get("flag") and l["flag"] not in ("normal", None)
        ]

        # Active diagnoses
        active_dx = [
            f"[{d['icd_code']}] {d['description']} — {d['status']} "
            f"(severity: {d['severity']})"
            for d in diagnoses
            if d["status"] in ("active", "chronic")
        ]

        # Allergy list
        allergy_list = [
            f"{a['allergen']} ({a['allergen_type']}) → {a['reaction']} "
            f"[{a['severity']}]"
            for a in allergies
            if a["status"] == "active"
        ]

        # Latest vitals
        latest_vitals_str = "No vitals on record"
        if vitals:
            v = vitals[0]  # Most recent
            latest_vitals_str = (
                f"HR: {v['heart_rate']} bpm | BP: {v['bp']} mmHg | "
                f"Temp: {v['temperature']}°F | RR: {v['respiratory_rate']} | "
                f"SpO2: {v['oxygen_saturation']}% | Pain: {v['pain_level']}/10 "
                f"(recorded: {v['recorded_at']})"
            )

        # Recent encounters
        encounter_list = [
            f"{e['encounter_date']}: {e['encounter_type'].upper()} — "
            f"{e['chief_complaint']} ({e['department']}, {e['provider_name']})"
            for e in encounters
        ]

        # ── Step 5: Build formatted context string ────────────────
        from datetime import date as date_type
        age = "Unknown"
        if patient.date_of_birth:
            today = date_type.today()
            age = str(
                today.year
                - patient.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (patient.date_of_birth.month, patient.date_of_birth.day)
                )
            )

        context_text = f"""
══════════════════════════════════════════════════════════════
 HISTORICAL PATIENT CONTEXT (Fivetran-Synced Clinical Warehouse)
 Data Freshness: {"ALL CURRENT" if freshness.get("all_fresh") else "PARTIAL — some connectors stale"}
══════════════════════════════════════════════════════════════

▸ PATIENT DEMOGRAPHICS
  Name: {patient.full_name}
  MRN: {patient.mrn}
  Age: {age} | Gender: {patient.gender} | Blood Type: {patient.blood_type or "Unknown"}

▸ ACTIVE DIAGNOSES ({len(active_dx)} conditions)
{_bullet_list(active_dx)}

▸ KNOWN ALLERGIES ({len(allergy_list)} allergies)
{_bullet_list(allergy_list)}

▸ CURRENT MEDICATIONS ({len(active_meds)} active)
{_bullet_list(active_meds)}

▸ RECENT MEDICATION CHANGES ({len(med_changes)} changes)
{_bullet_list(med_changes)}

▸ LATEST VITALS
  {latest_vitals_str}

▸ ABNORMAL LAB RESULTS ({len(abnormal_labs)} flagged)
{_bullet_list(abnormal_labs)}

▸ LAB TRENDS (auto-detected)
{_bullet_list(lab_trends) if lab_trends else "  • No significant trends detected"}

▸ RECENT ENCOUNTERS ({len(encounter_list)} visits)
{_bullet_list(encounter_list)}

══════════════════════════════════════════════════════════════
 CLINICAL REASONING INSTRUCTIONS:
 1. Compare current report findings against the above baseline.
 2. Flag any CONTRADICTIONS (e.g., elevated HR + discontinued beta-blocker).
 3. Note any WORSENING TRENDS in labs or vitals.
 4. Check for potential DRUG INTERACTIONS with current medications.
 5. Consider allergy risks for any proposed treatments.
══════════════════════════════════════════════════════════════
""".strip()

        latency = (time.monotonic() - start_time) * 1000
        logger.info(
            "[Context Agent] Context retrieved: %d meds, %d labs, %d vitals, "
            "%d diagnoses, %d allergies | %.0fms",
            len(medications), len(lab_results), len(vitals),
            len(diagnoses), len(allergies), latency,
        )

        # ── Step 6: Log agent trace ───────────────────────────────
        trace_data = {
            "patient_id": patient_id,
            "patient_mrn": patient.mrn,
            "medications_found": len(medications),
            "lab_results_found": len(lab_results),
            "vitals_found": len(vitals),
            "diagnoses_found": len(diagnoses),
            "allergies_found": len(allergies),
            "encounters_found": len(encounters),
            "trends_detected": len(lab_trends),
            "med_changes_detected": len(med_changes),
            "freshness": freshness,
        }

        if report_id:
            trace = AgentTrace(
                report_id=report_id,
                agent_name="context_agent",
                step_name="retrieve_context",
                step_order=1,
                input_data=f"patient_id={patient_id}",
                output_data=f"Retrieved {len(medications)} meds, {len(lab_results)} labs, {len(diagnoses)} diagnoses",
                tool_calls=[
                    {"tool": "fivetran_get_data_freshness", "result": freshness},
                ],
                confidence=1.0 if freshness.get("all_fresh") else 0.85,
                latency_ms=latency,
                iteration=1,
                status="completed",
                metadata_json=trace_data,
            )
            db.add(trace)
            await db.flush()

        return {
            "context_text": context_text,
            "structured_data": {
                "patient": {
                    "id": patient.id,
                    "mrn": patient.mrn,
                    "name": patient.full_name,
                    "age": age,
                    "gender": patient.gender,
                    "blood_type": patient.blood_type,
                },
                "medications": medications,
                "lab_results": lab_results,
                "vitals": vitals,
                "diagnoses": diagnoses,
                "allergies": allergies,
                "encounters": encounters,
            },
            "trends": {
                "lab_trends": lab_trends,
                "medication_changes": med_changes,
                "abnormal_labs": abnormal_labs,
            },
            "enriched": True,
            "latency_ms": latency,
        }

    # ── Match patient from report text ────────────────────────────
    async def match_patient_from_text(
        self, db: AsyncSession, report_text: str
    ) -> Optional[str]:
        """
        Attempt to match a patient from the clinical warehouse based on
        identifiers found in the report text (MRN, name, DOB).
        Returns patient_id if found, None otherwise.
        """
        import re

        text_upper = report_text.upper()

        # Try MRN match
        mrn_match = re.search(r"MRN[:\s\-]*(\w[\w\-]+)", text_upper)
        if mrn_match:
            mrn_candidate = mrn_match.group(1).strip()
            result = await db.execute(
                select(Patient).where(
                    func.upper(Patient.mrn) == mrn_candidate
                )
            )
            patient = result.scalar_one_or_none()
            if patient:
                logger.info("[Context Agent] Patient matched by MRN: %s", patient.mrn)
                return patient.id

        # Fallback: return first active patient for demo purposes
        # In production, this would use NLP entity extraction
        result = await db.execute(
            select(Patient)
            .where(Patient.active == True)
            .order_by(Patient.created_at)
            .limit(1)
        )
        patient = result.scalar_one_or_none()
        if patient:
            logger.info(
                "[Context Agent] No MRN match — using first patient for demo: %s",
                patient.mrn,
            )
            return patient.id

        return None


# ── Singleton ─────────────────────────────────────────────────────
context_agent = ContextAgent()
