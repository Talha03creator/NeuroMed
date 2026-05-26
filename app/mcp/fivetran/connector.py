"""
Fivetran Connector Definitions
Agentic Clinical Intelligence Platform

Defines the schema and configuration for each mock Fivetran connector.
Maps source systems to destination tables and transformation rules.
"""

from typing import Dict, Any, List


CONNECTOR_CONFIGS: Dict[str, Dict[str, Any]] = {
    "ehr_connector": {
        "display_name": "Healthcare EHR System",
        "description": "Electronic Health Records — patients, encounters, notes, allergies",
        "source_type": "ehr",
        "source_schema": "ehr_production",
        "destination_schema": "clinical_warehouse",
        "tables": {
            "patients": {
                "source_table": "ehr_patients",
                "destination_table": "patients",
                "primary_key": "source_id",
                "sync_mode": "upsert",
                "columns_mapped": [
                    "mrn", "first_name", "last_name", "date_of_birth",
                    "gender", "blood_type", "phone", "email", "address",
                    "emergency_contact", "insurance_provider", "insurance_id",
                ],
            },
            "encounters": {
                "source_table": "ehr_encounters",
                "destination_table": "encounters",
                "primary_key": "source_id",
                "sync_mode": "append",
                "columns_mapped": [
                    "patient_id", "encounter_type", "encounter_date",
                    "provider_name", "department", "chief_complaint",
                    "disposition", "notes",
                ],
            },
            "clinical_notes": {
                "source_table": "ehr_notes",
                "destination_table": "clinical_notes",
                "primary_key": "source_id",
                "sync_mode": "append",
                "columns_mapped": [
                    "patient_id", "note_type", "title", "content",
                    "author", "author_role", "department", "authored_at",
                ],
            },
            "allergies": {
                "source_table": "ehr_allergies",
                "destination_table": "allergies",
                "primary_key": "source_id",
                "sync_mode": "upsert",
                "columns_mapped": [
                    "patient_id", "allergen", "allergen_type", "reaction",
                    "severity", "onset_date", "status",
                ],
            },
        },
    },
    "lab_connector": {
        "display_name": "Laboratory Information System",
        "description": "Lab results — CBC, BMP, lipid panels, cardiac markers, etc.",
        "source_type": "lab",
        "source_schema": "lab_production",
        "destination_schema": "clinical_warehouse",
        "tables": {
            "lab_results": {
                "source_table": "lab_results",
                "destination_table": "lab_results",
                "primary_key": "source_id",
                "sync_mode": "append",
                "columns_mapped": [
                    "patient_id", "test_name", "test_code", "panel_name",
                    "result_value", "unit", "reference_range", "flag",
                    "collected_at", "resulted_at", "ordered_by", "performing_lab",
                ],
            },
        },
    },
    "medication_connector": {
        "display_name": "Pharmacy Management System",
        "description": "Medication prescriptions — active, discontinued, dosages",
        "source_type": "medication",
        "source_schema": "pharmacy_production",
        "destination_schema": "clinical_warehouse",
        "tables": {
            "medications": {
                "source_table": "rx_medications",
                "destination_table": "medications",
                "primary_key": "source_id",
                "sync_mode": "upsert",
                "columns_mapped": [
                    "patient_id", "medication_name", "generic_name", "dosage",
                    "frequency", "route", "start_date", "end_date",
                    "status", "prescribed_by", "reason",
                ],
            },
        },
    },
    "vitals_connector": {
        "display_name": "Vitals Monitoring System",
        "description": "Patient vital signs — HR, BP, SpO2, temperature, etc.",
        "source_type": "vitals",
        "source_schema": "vitals_production",
        "destination_schema": "clinical_warehouse",
        "tables": {
            "vitals": {
                "source_table": "vitals_readings",
                "destination_table": "vitals",
                "primary_key": "source_id",
                "sync_mode": "append",
                "columns_mapped": [
                    "patient_id", "heart_rate", "blood_pressure_systolic",
                    "blood_pressure_diastolic", "temperature", "respiratory_rate",
                    "oxygen_saturation", "weight_kg", "height_cm",
                    "pain_level", "recorded_at", "recorded_by", "position",
                ],
            },
        },
    },
    "diagnosis_connector": {
        "display_name": "Clinical Diagnosis System",
        "description": "ICD-10 coded diagnoses — active, chronic, resolved",
        "source_type": "diagnosis",
        "source_schema": "clinical_production",
        "destination_schema": "clinical_warehouse",
        "tables": {
            "diagnoses": {
                "source_table": "clinical_diagnoses",
                "destination_table": "diagnoses",
                "primary_key": "source_id",
                "sync_mode": "upsert",
                "columns_mapped": [
                    "patient_id", "icd_code", "description", "severity",
                    "diagnosis_type", "status", "diagnosed_date",
                    "resolved_date", "diagnosed_by",
                ],
            },
        },
    },
}


def get_connector_config(connector_name: str) -> Dict[str, Any]:
    """Get configuration for a specific connector."""
    return CONNECTOR_CONFIGS.get(connector_name, {})


def get_all_destination_tables() -> List[str]:
    """Get list of all destination tables across all connectors."""
    tables = set()
    for config in CONNECTOR_CONFIGS.values():
        for table_config in config.get("tables", {}).values():
            tables.add(table_config["destination_table"])
    return sorted(tables)
