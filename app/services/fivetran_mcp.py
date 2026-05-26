"""
Fivetran MCP Service
Simulates Fivetran data pipeline for EHR Context Retrieval.
Implemented as an asynchronous Python function to be wrapped as a Vertex AI Tool.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

MOCK_EHR_DB = {
    "P001": {
        "diagnoses": ["Hypertension", "Tachycardia"],
        "medications_active": ["Lisinopril 10mg"],
        "medications_stopped": ["Metoprolol 50mg"],
        "recent_labs": {"BP": "150/95", "HR": "110"},
        "last_encounter": "2026-05-15"
    },
    "NMG-8842": {
        "diagnoses": ["Microvascular Ischemia", "Early Parkinsonian Traits"],
        "medications_active": ["Aspirin 81mg"],
        "medications_stopped": [],
        "recent_labs": {"LDL": "160", "Fasting Glucose": "110"},
        "last_encounter": "2025-10-12",
        "family_history": "Cardiovascular disease (Father)"
    }
}

async def retrieve_ehr_context(patient_id: str) -> Dict[str, Any]:
    """
    MCP Tool: Retrieve historical EHR context for a given patient.
    """
    logger.info(f"[Fivetran MCP] Retrieving EHR context for patient {patient_id}")
    
    if patient_id in MOCK_EHR_DB:
        logger.info(f"[Fivetran MCP] Found historical context for {patient_id}")
        return MOCK_EHR_DB[patient_id]
        
    logger.warning(f"[Fivetran MCP] No historical context found for {patient_id}")
    return {"status": "no_history", "message": "No prior EHR data found."}
