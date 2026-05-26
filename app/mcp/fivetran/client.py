"""
Fivetran MCP Client — Mock Connector Management
Agentic Clinical Intelligence Platform

Simulates the Fivetran MCP API for managing connectors, triggering syncs,
and querying sync status. Mirrors real Fivetran MCP tool signatures:
- list_connectors
- get_connector_details
- trigger_sync
- get_sync_status

This is the MCP interface that the Context Agent calls.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# ── Connector Registry ────────────────────────────────────────────

CONNECTOR_REGISTRY = {
    "ehr_connector": {
        "connector_id": "conn_ehr_001",
        "connector_name": "ehr_connector",
        "source_type": "ehr",
        "destination_schema": "clinical_warehouse",
        "destination_tables": ["patients", "encounters", "clinical_notes", "allergies"],
        "sync_frequency": "every_6_hours",
        "status": "connected",
        "setup_status": "complete",
        "paused": False,
    },
    "lab_connector": {
        "connector_id": "conn_lab_002",
        "connector_name": "lab_connector",
        "source_type": "lab",
        "destination_schema": "clinical_warehouse",
        "destination_tables": ["lab_results"],
        "sync_frequency": "every_1_hour",
        "status": "connected",
        "setup_status": "complete",
        "paused": False,
    },
    "medication_connector": {
        "connector_id": "conn_med_003",
        "connector_name": "medication_connector",
        "source_type": "medication",
        "destination_schema": "clinical_warehouse",
        "destination_tables": ["medications"],
        "sync_frequency": "every_6_hours",
        "status": "connected",
        "setup_status": "complete",
        "paused": False,
    },
    "vitals_connector": {
        "connector_id": "conn_vit_004",
        "connector_name": "vitals_connector",
        "source_type": "vitals",
        "destination_schema": "clinical_warehouse",
        "destination_tables": ["vitals"],
        "sync_frequency": "every_15_minutes",
        "status": "connected",
        "setup_status": "complete",
        "paused": False,
    },
    "diagnosis_connector": {
        "connector_id": "conn_dx_005",
        "connector_name": "diagnosis_connector",
        "source_type": "diagnosis",
        "destination_schema": "clinical_warehouse",
        "destination_tables": ["diagnoses"],
        "sync_frequency": "every_6_hours",
        "status": "connected",
        "setup_status": "complete",
        "paused": False,
    },
}


class FivetranMCPClient:
    """
    Mock Fivetran MCP client that exposes tool-callable methods
    matching real Fivetran MCP tool signatures.

    Used by the Context Agent to:
    1. Check connector health
    2. Trigger data syncs before retrieving patient context
    3. Verify data freshness
    """

    def __init__(self):
        self._connectors = dict(CONNECTOR_REGISTRY)
        self._sync_history: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False
        logger.info("FivetranMCPClient initialized with %d connectors", len(self._connectors))

    # ── MCP Tool: list_connectors ─────────────────────────────────
    async def list_connectors(self) -> Dict[str, Any]:
        """
        MCP Tool: fivetran_list_connectors
        Lists all configured Fivetran connectors and their status.
        """
        logger.info("[Fivetran MCP] list_connectors called")
        connectors = []
        for name, config in self._connectors.items():
            connectors.append({
                "connector_id": config["connector_id"],
                "connector_name": name,
                "source_type": config["source_type"],
                "status": config["status"],
                "paused": config["paused"],
                "sync_frequency": config["sync_frequency"],
                "destination_tables": config["destination_tables"],
            })
        return {
            "status": "success",
            "data": {
                "connectors": connectors,
                "total": len(connectors),
            },
        }

    # ── MCP Tool: get_connector_details ───────────────────────────
    async def get_connector_details(self, connector_id: str) -> Dict[str, Any]:
        """
        MCP Tool: fivetran_get_connector_details
        Returns detailed configuration for a specific connector.
        """
        logger.info("[Fivetran MCP] get_connector_details: %s", connector_id)
        for name, config in self._connectors.items():
            if config["connector_id"] == connector_id:
                last_sync = None
                if name in self._sync_history and self._sync_history[name]:
                    last_sync = self._sync_history[name][-1]
                return {
                    "status": "success",
                    "data": {
                        **config,
                        "last_sync": last_sync,
                        "schema_config": {
                            "schema": config["destination_schema"],
                            "tables": config["destination_tables"],
                        },
                    },
                }
        return {"status": "error", "error": f"Connector {connector_id} not found"}

    # ── MCP Tool: trigger_sync ────────────────────────────────────
    async def trigger_sync(self, connector_name: str) -> Dict[str, Any]:
        """
        MCP Tool: fivetran_trigger_sync
        Triggers an immediate sync for a connector.
        Returns a sync_id for tracking.
        """
        logger.info("[Fivetran MCP] trigger_sync: %s", connector_name)
        if connector_name not in self._connectors:
            return {"status": "error", "error": f"Connector '{connector_name}' not found"}

        config = self._connectors[connector_name]
        if config["paused"]:
            return {"status": "error", "error": f"Connector '{connector_name}' is paused"}

        sync_id = f"sync_{uuid.uuid4().hex[:12]}"
        sync_record = {
            "sync_id": sync_id,
            "connector_name": connector_name,
            "connector_id": config["connector_id"],
            "source_type": config["source_type"],
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "triggered_by": "context_agent",
        }

        if connector_name not in self._sync_history:
            self._sync_history[connector_name] = []
        self._sync_history[connector_name].append(sync_record)

        return {
            "status": "success",
            "data": {
                "sync_id": sync_id,
                "connector_name": connector_name,
                "message": f"Sync triggered for {connector_name}",
            },
        }

    # ── MCP Tool: get_sync_status ─────────────────────────────────
    async def get_sync_status(self, connector_name: str) -> Dict[str, Any]:
        """
        MCP Tool: fivetran_get_sync_status
        Returns sync status and history for a connector.
        """
        logger.info("[Fivetran MCP] get_sync_status: %s", connector_name)
        if connector_name not in self._connectors:
            return {"status": "error", "error": f"Connector '{connector_name}' not found"}

        history = self._sync_history.get(connector_name, [])
        last_sync = history[-1] if history else None

        return {
            "status": "success",
            "data": {
                "connector_name": connector_name,
                "last_sync": last_sync,
                "sync_history_count": len(history),
                "connector_status": self._connectors[connector_name]["status"],
            },
        }

    # ── MCP Tool: get_data_freshness ──────────────────────────────
    async def get_data_freshness(self) -> Dict[str, Any]:
        """
        MCP Tool: fivetran_get_data_freshness
        Returns data freshness status across all connectors.
        """
        logger.info("[Fivetran MCP] get_data_freshness called")
        freshness = {}
        for name, config in self._connectors.items():
            history = self._sync_history.get(name, [])
            completed = [s for s in history if s.get("status") == "completed"]
            last_completed = completed[-1] if completed else None
            freshness[name] = {
                "connector_id": config["connector_id"],
                "source_type": config["source_type"],
                "last_successful_sync": last_completed.get("completed_at") if last_completed else None,
                "rows_last_synced": last_completed.get("rows_synced", 0) if last_completed else 0,
                "is_fresh": last_completed is not None,
                "destination_tables": config["destination_tables"],
            }
        return {"status": "success", "data": freshness}

    def mark_sync_completed(
        self, connector_name: str, rows_synced: int, duration: float
    ) -> None:
        """Called by SyncEngine after a successful sync to update history."""
        if connector_name in self._sync_history and self._sync_history[connector_name]:
            last = self._sync_history[connector_name][-1]
            last["status"] = "completed"
            last["completed_at"] = datetime.now(timezone.utc).isoformat()
            last["rows_synced"] = rows_synced
            last["duration_seconds"] = round(duration, 2)

    def mark_sync_failed(self, connector_name: str, error: str) -> None:
        """Called by SyncEngine when a sync fails."""
        if connector_name in self._sync_history and self._sync_history[connector_name]:
            last = self._sync_history[connector_name][-1]
            last["status"] = "failed"
            last["error"] = error
            last["completed_at"] = datetime.now(timezone.utc).isoformat()


# ── Singleton ─────────────────────────────────────────────────────
fivetran_client = FivetranMCPClient()
