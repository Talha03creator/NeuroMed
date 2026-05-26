"""
Mock Healthcare Sources — Simulated External Systems
Agentic Clinical Intelligence Platform

Simulates the external healthcare systems that Fivetran would connect to:
- EHR System (patients, encounters, clinical notes)
- Lab System (lab results)
- Medication System (prescriptions)
- Vitals Database (vital signs)
- Diagnosis Records (ICD-10 diagnoses)

Each source generates realistic mock clinical data with proper medical
terminology, realistic value ranges, and temporal consistency.
"""

import uuid
import random
from datetime import date, datetime, timedelta, timezone
from typing import List, Dict, Any


# ── Realistic Medical Reference Data ─────────────────────────────

FIRST_NAMES = [
    "James", "Maria", "Robert", "Sarah", "Michael", "Emily", "David",
    "Jessica", "William", "Jennifer", "Richard", "Linda", "Joseph",
    "Elizabeth", "Thomas", "Patricia", "Charles", "Barbara", "Ahmed", "Fatima",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas",
    "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris",
]

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

DEPARTMENTS = [
    "Emergency", "Internal Medicine", "Cardiology", "Pulmonology",
    "Neurology", "Orthopedics", "Gastroenterology", "Endocrinology",
    "Oncology", "General Practice", "Nephrology", "Dermatology",
]

CHIEF_COMPLAINTS = [
    "Chest pain radiating to left arm",
    "Persistent cough for 3 weeks with blood-tinged sputum",
    "Severe headache with visual disturbances",
    "Right knee pain after fall, unable to bear weight",
    "Abdominal pain with nausea and vomiting",
    "Elevated blood sugar levels despite medication",
    "Shortness of breath on exertion",
    "Recurring dizziness and lightheadedness",
    "Lower back pain radiating to left leg",
    "Skin rash spreading across trunk and extremities",
    "Fatigue and unexplained weight loss over 3 months",
    "Palpitations with episodes of syncope",
    "Difficulty swallowing and persistent heartburn",
    "Joint stiffness and swelling in both hands",
    "Frequent urination and excessive thirst",
]

MEDICATIONS_LIST = [
    ("Metformin", "500mg", "twice daily", "oral", "Type 2 Diabetes"),
    ("Lisinopril", "10mg", "once daily", "oral", "Hypertension"),
    ("Atorvastatin", "20mg", "once daily at bedtime", "oral", "Hyperlipidemia"),
    ("Metoprolol", "50mg", "twice daily", "oral", "Hypertension/Tachycardia"),
    ("Omeprazole", "20mg", "once daily before breakfast", "oral", "GERD"),
    ("Amlodipine", "5mg", "once daily", "oral", "Hypertension"),
    ("Levothyroxine", "75mcg", "once daily on empty stomach", "oral", "Hypothyroidism"),
    ("Aspirin", "81mg", "once daily", "oral", "Cardiac prophylaxis"),
    ("Warfarin", "5mg", "once daily", "oral", "Anticoagulation"),
    ("Gabapentin", "300mg", "three times daily", "oral", "Neuropathic pain"),
    ("Albuterol", "2 puffs", "every 4-6 hours PRN", "inhaled", "Asthma/COPD"),
    ("Prednisone", "10mg", "once daily tapering", "oral", "Inflammation"),
    ("Insulin Glargine", "20 units", "once daily at bedtime", "subcutaneous", "Diabetes"),
    ("Clopidogrel", "75mg", "once daily", "oral", "Post-stent antiplatelet"),
    ("Furosemide", "40mg", "once daily", "oral", "Heart failure/Edema"),
]

LAB_TESTS = [
    ("Complete Blood Count", "CBC", [
        ("WBC", "7.5", "x10^3/uL", "4.5-11.0", "normal"),
        ("RBC", "4.8", "x10^6/uL", "4.2-5.9", "normal"),
        ("Hemoglobin", "14.2", "g/dL", "12.0-17.5", "normal"),
        ("Hematocrit", "42.1", "%", "36.0-51.0", "normal"),
        ("Platelets", "245", "x10^3/uL", "150-400", "normal"),
    ]),
    ("Basic Metabolic Panel", "BMP", [
        ("Glucose", "110", "mg/dL", "70-100", "high"),
        ("BUN", "18", "mg/dL", "7-20", "normal"),
        ("Creatinine", "1.1", "mg/dL", "0.7-1.3", "normal"),
        ("Sodium", "140", "mEq/L", "136-145", "normal"),
        ("Potassium", "4.2", "mEq/L", "3.5-5.0", "normal"),
        ("Chloride", "101", "mEq/L", "98-106", "normal"),
        ("CO2", "24", "mEq/L", "23-29", "normal"),
        ("Calcium", "9.5", "mg/dL", "8.5-10.5", "normal"),
    ]),
    ("Lipid Panel", "LIPID", [
        ("Total Cholesterol", "215", "mg/dL", "<200", "high"),
        ("HDL", "45", "mg/dL", ">40", "normal"),
        ("LDL", "140", "mg/dL", "<100", "high"),
        ("Triglycerides", "180", "mg/dL", "<150", "high"),
    ]),
    ("Hemoglobin A1c", "HBA1C", [
        ("HbA1c", "7.2", "%", "<5.7", "high"),
    ]),
    ("Thyroid Panel", "TSH", [
        ("TSH", "2.5", "mIU/L", "0.4-4.0", "normal"),
        ("Free T4", "1.2", "ng/dL", "0.8-1.8", "normal"),
        ("Free T3", "3.1", "pg/mL", "2.3-4.2", "normal"),
    ]),
    ("Cardiac Markers", "CARDIAC", [
        ("Troponin I", "0.02", "ng/mL", "<0.04", "normal"),
        ("BNP", "125", "pg/mL", "<100", "high"),
        ("CK-MB", "3.5", "ng/mL", "<5.0", "normal"),
    ]),
    ("Liver Function", "LFT", [
        ("ALT", "32", "U/L", "7-56", "normal"),
        ("AST", "28", "U/L", "10-40", "normal"),
        ("Alkaline Phosphatase", "85", "U/L", "44-147", "normal"),
        ("Total Bilirubin", "0.8", "mg/dL", "0.1-1.2", "normal"),
        ("Albumin", "4.0", "g/dL", "3.5-5.5", "normal"),
    ]),
]

DIAGNOSES_LIST = [
    ("E11.9", "Type 2 diabetes mellitus without complications", "chronic"),
    ("I10", "Essential hypertension", "chronic"),
    ("E78.5", "Hyperlipidemia, unspecified", "chronic"),
    ("J44.1", "Chronic obstructive pulmonary disease with acute exacerbation", "active"),
    ("I25.10", "Atherosclerotic heart disease of native coronary artery", "chronic"),
    ("K21.0", "Gastro-esophageal reflux disease with esophagitis", "active"),
    ("M54.5", "Low back pain", "active"),
    ("G43.909", "Migraine, unspecified, not intractable", "recurrent"),
    ("E03.9", "Hypothyroidism, unspecified", "chronic"),
    ("N18.3", "Chronic kidney disease, stage 3", "chronic"),
    ("I48.91", "Unspecified atrial fibrillation", "chronic"),
    ("J45.20", "Mild intermittent asthma, uncomplicated", "chronic"),
    ("F32.1", "Major depressive disorder, single episode, moderate", "active"),
    ("M17.11", "Primary osteoarthritis, right knee", "chronic"),
    ("I50.9", "Heart failure, unspecified", "active"),
]

ALLERGENS = [
    ("Penicillin", "drug", "Anaphylaxis", "severe"),
    ("Sulfa drugs", "drug", "Rash and hives", "moderate"),
    ("Latex", "environmental", "Contact dermatitis", "moderate"),
    ("Peanuts", "food", "Anaphylaxis", "life_threatening"),
    ("Codeine", "drug", "Nausea and vomiting", "mild"),
    ("Ibuprofen", "drug", "GI bleeding", "moderate"),
    ("Shellfish", "food", "Hives and swelling", "moderate"),
    ("Bee stings", "biological", "Anaphylaxis", "severe"),
    ("Contrast dye", "drug", "Anaphylactoid reaction", "severe"),
    ("Amoxicillin", "drug", "Rash", "mild"),
]

PROVIDERS = [
    "Dr. Sarah Chen", "Dr. Michael Roberts", "Dr. Aisha Patel",
    "Dr. James Wilson", "Dr. Maria Gonzalez", "Dr. David Kim",
    "Dr. Jennifer Lee", "Dr. Robert Thompson", "Dr. Emily Davis",
    "Dr. Ahmed Hassan", "Dr. Lisa Wang", "Dr. Mark Johnson",
]

INSURANCE_PROVIDERS = [
    "Blue Cross Blue Shield", "UnitedHealthcare", "Aetna", "Cigna",
    "Humana", "Kaiser Permanente", "Anthem", "Medicare", "Medicaid",
]


class MockHealthcareSources:
    """
    Simulates external healthcare data sources that Fivetran connectors
    would pull from. Generates realistic mock clinical data with proper
    medical terminology and temporal consistency.
    """

    def __init__(self, num_patients: int = 15):
        self._num_patients = num_patients
        self._patients_cache: List[Dict[str, Any]] = []
        self._rng = random.Random(42)  # Deterministic for reproducibility

    def _random_date(self, start_year: int = 1945, end_year: int = 2000) -> date:
        start = date(start_year, 1, 1)
        end = date(end_year, 12, 31)
        delta = (end - start).days
        return start + timedelta(days=self._rng.randint(0, delta))

    def _random_past_datetime(self, days_back: int = 730) -> datetime:
        return datetime.now(timezone.utc) - timedelta(
            days=self._rng.randint(1, days_back),
            hours=self._rng.randint(0, 23),
            minutes=self._rng.randint(0, 59),
        )

    def _generate_mrn(self) -> str:
        return f"MRN-{self._rng.randint(100000, 999999)}"

    # ── EHR Source: Patients ──────────────────────────────────────
    def get_patients(self) -> List[Dict[str, Any]]:
        """Simulate pulling patient records from an EHR system."""
        if self._patients_cache:
            return self._patients_cache

        patients = []
        for i in range(self._num_patients):
            gender = self._rng.choice(["Male", "Female"])
            first_names = [n for n in FIRST_NAMES]
            patient = {
                "source_id": f"EHR-PAT-{1000 + i}",
                "source_system": "ehr_mock",
                "mrn": self._generate_mrn(),
                "first_name": self._rng.choice(first_names),
                "last_name": self._rng.choice(LAST_NAMES),
                "date_of_birth": self._random_date().isoformat(),
                "gender": gender,
                "blood_type": self._rng.choice(BLOOD_TYPES),
                "phone": f"+1-{self._rng.randint(200,999)}-{self._rng.randint(100,999)}-{self._rng.randint(1000,9999)}",
                "email": None,  # Will be generated from name
                "address": f"{self._rng.randint(100,9999)} {self._rng.choice(['Oak', 'Elm', 'Main', 'Park', 'Cedar'])} {self._rng.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
                "emergency_contact": {
                    "name": f"{self._rng.choice(FIRST_NAMES)} {self._rng.choice(LAST_NAMES)}",
                    "relationship": self._rng.choice(["Spouse", "Parent", "Sibling", "Child"]),
                    "phone": f"+1-{self._rng.randint(200,999)}-{self._rng.randint(100,999)}-{self._rng.randint(1000,9999)}",
                },
                "insurance_provider": self._rng.choice(INSURANCE_PROVIDERS),
                "insurance_id": f"INS-{self._rng.randint(10000000, 99999999)}",
                "active": True,
            }
            patient["email"] = f"{patient['first_name'].lower()}.{patient['last_name'].lower()}@email.com"
            patients.append(patient)

        self._patients_cache = patients
        return patients

    # ── EHR Source: Encounters ────────────────────────────────────
    def get_encounters(self, patient_source_ids: List[str]) -> List[Dict[str, Any]]:
        """Simulate pulling encounter records from an EHR system."""
        encounters = []
        for pat_id in patient_source_ids:
            num_encounters = self._rng.randint(2, 6)
            for j in range(num_encounters):
                enc_date = self._random_past_datetime(days_back=365 * 2)
                encounters.append({
                    "source_id": f"EHR-ENC-{uuid.uuid4().hex[:8]}",
                    "source_system": "ehr_mock",
                    "patient_source_id": pat_id,
                    "encounter_type": self._rng.choice(["outpatient", "inpatient", "emergency", "telehealth", "lab_visit"]),
                    "encounter_date": enc_date.isoformat(),
                    "provider_name": self._rng.choice(PROVIDERS),
                    "department": self._rng.choice(DEPARTMENTS),
                    "chief_complaint": self._rng.choice(CHIEF_COMPLAINTS),
                    "disposition": self._rng.choice(["discharged", "admitted", "follow_up", "transferred"]),
                    "notes": f"Patient seen for {self._rng.choice(CHIEF_COMPLAINTS).lower()}. Assessment and plan documented.",
                })
        return encounters

    # ── Medication Source ─────────────────────────────────────────
    def get_medications(self, patient_source_ids: List[str]) -> List[Dict[str, Any]]:
        """Simulate pulling medication records from a pharmacy system."""
        medications = []
        for pat_id in patient_source_ids:
            num_meds = self._rng.randint(1, 5)
            selected = self._rng.sample(MEDICATIONS_LIST, min(num_meds, len(MEDICATIONS_LIST)))
            for name, dosage, freq, route, reason in selected:
                start = self._random_past_datetime(days_back=365).date()
                is_active = self._rng.random() > 0.3
                medications.append({
                    "source_id": f"MED-RX-{uuid.uuid4().hex[:8]}",
                    "source_system": "medication_mock",
                    "patient_source_id": pat_id,
                    "medication_name": name,
                    "generic_name": name,
                    "dosage": dosage,
                    "frequency": freq,
                    "route": route,
                    "start_date": start.isoformat(),
                    "end_date": None if is_active else (start + timedelta(days=self._rng.randint(30, 180))).isoformat(),
                    "status": "active" if is_active else "discontinued",
                    "prescribed_by": self._rng.choice(PROVIDERS),
                    "reason": reason,
                })
        return medications

    # ── Vitals Source ─────────────────────────────────────────────
    def get_vitals(self, patient_source_ids: List[str]) -> List[Dict[str, Any]]:
        """Simulate pulling vital signs from a vitals monitoring system."""
        vitals = []
        for pat_id in patient_source_ids:
            num_readings = self._rng.randint(3, 8)
            for _ in range(num_readings):
                vitals.append({
                    "source_id": f"VIT-{uuid.uuid4().hex[:8]}",
                    "source_system": "vitals_mock",
                    "patient_source_id": pat_id,
                    "heart_rate": round(self._rng.uniform(55, 110), 1),
                    "blood_pressure_systolic": self._rng.randint(100, 180),
                    "blood_pressure_diastolic": self._rng.randint(60, 110),
                    "temperature": round(self._rng.uniform(97.0, 101.5), 1),
                    "respiratory_rate": round(self._rng.uniform(12, 24), 1),
                    "oxygen_saturation": round(self._rng.uniform(92, 100), 1),
                    "weight_kg": round(self._rng.uniform(50, 120), 1),
                    "height_cm": round(self._rng.uniform(150, 195), 1),
                    "pain_level": self._rng.randint(0, 8),
                    "recorded_at": self._random_past_datetime(days_back=365).isoformat(),
                    "recorded_by": self._rng.choice(PROVIDERS),
                    "position": self._rng.choice(["sitting", "standing", "supine"]),
                })
        return vitals

    # ── Lab Source ────────────────────────────────────────────────
    def get_lab_results(self, patient_source_ids: List[str]) -> List[Dict[str, Any]]:
        """Simulate pulling lab results from a laboratory information system."""
        results = []
        for pat_id in patient_source_ids:
            num_panels = self._rng.randint(2, 5)
            selected_panels = self._rng.sample(LAB_TESTS, min(num_panels, len(LAB_TESTS)))
            for panel_name, panel_code, tests in selected_panels:
                collected = self._random_past_datetime(days_back=365)
                for test_name, base_val, unit, ref_range, base_flag in tests:
                    # Add some variation to values
                    try:
                        val = float(base_val)
                        variation = val * self._rng.uniform(-0.15, 0.15)
                        actual_val = str(round(val + variation, 1))
                    except ValueError:
                        actual_val = base_val

                    # Determine flag based on reference range
                    flag = self._rng.choice(["normal", "normal", "normal", "high", "low"]) if base_flag == "normal" else base_flag

                    results.append({
                        "source_id": f"LAB-{uuid.uuid4().hex[:8]}",
                        "source_system": "lab_mock",
                        "patient_source_id": pat_id,
                        "test_name": test_name,
                        "test_code": f"LOINC-{self._rng.randint(10000, 99999)}",
                        "panel_name": panel_name,
                        "result_value": actual_val,
                        "unit": unit,
                        "reference_range": ref_range,
                        "flag": flag,
                        "collected_at": collected.isoformat(),
                        "resulted_at": (collected + timedelta(hours=self._rng.randint(1, 48))).isoformat(),
                        "ordered_by": self._rng.choice(PROVIDERS),
                        "performing_lab": self._rng.choice(["Central Lab", "Quest Diagnostics", "LabCorp", "Hospital Lab"]),
                    })
        return results

    # ── Diagnosis Source ──────────────────────────────────────────
    def get_diagnoses(self, patient_source_ids: List[str]) -> List[Dict[str, Any]]:
        """Simulate pulling diagnosis records from a clinical system."""
        diagnoses = []
        for pat_id in patient_source_ids:
            num_dx = self._rng.randint(1, 5)
            selected = self._rng.sample(DIAGNOSES_LIST, min(num_dx, len(DIAGNOSES_LIST)))
            for icd, desc, status in selected:
                dx_date = self._random_past_datetime(days_back=365 * 3).date()
                diagnoses.append({
                    "source_id": f"DX-{uuid.uuid4().hex[:8]}",
                    "source_system": "diagnosis_mock",
                    "patient_source_id": pat_id,
                    "icd_code": icd,
                    "description": desc,
                    "severity": self._rng.choice(["mild", "moderate", "severe"]),
                    "diagnosis_type": self._rng.choice(["primary", "secondary"]),
                    "status": status,
                    "diagnosed_date": dx_date.isoformat(),
                    "resolved_date": None if status != "resolved" else (dx_date + timedelta(days=self._rng.randint(30, 365))).isoformat(),
                    "diagnosed_by": self._rng.choice(PROVIDERS),
                })
        return diagnoses

    # ── Allergy Source ────────────────────────────────────────────
    def get_allergies(self, patient_source_ids: List[str]) -> List[Dict[str, Any]]:
        """Simulate pulling allergy records from an EHR system."""
        allergies = []
        for pat_id in patient_source_ids:
            num_allergies = self._rng.randint(0, 3)
            if num_allergies == 0:
                continue
            selected = self._rng.sample(ALLERGENS, min(num_allergies, len(ALLERGENS)))
            for allergen, atype, reaction, severity in selected:
                allergies.append({
                    "source_id": f"ALG-{uuid.uuid4().hex[:8]}",
                    "source_system": "ehr_mock",
                    "patient_source_id": pat_id,
                    "allergen": allergen,
                    "allergen_type": atype,
                    "reaction": reaction,
                    "severity": severity,
                    "onset_date": self._random_date(1960, 2024).isoformat(),
                    "status": "active",
                    "verified": self._rng.random() > 0.3,
                })
        return allergies

    # ── Clinical Notes Source ─────────────────────────────────────
    def get_clinical_notes(self, patient_source_ids: List[str]) -> List[Dict[str, Any]]:
        """Simulate pulling clinical notes from an EHR system."""
        notes = []
        note_templates = [
            ("progress", "Progress Note", "Patient presents with {complaint}. Vital signs stable. {assessment}"),
            ("discharge_summary", "Discharge Summary", "Patient admitted for {complaint}. Hospital course uncomplicated. Discharged in stable condition with follow-up in 2 weeks."),
            ("consult", "Specialty Consultation", "Consulted for evaluation of {complaint}. Review of records and examination performed. {assessment}"),
            ("procedure", "Procedure Note", "Procedure performed without complications. Patient tolerated procedure well. Post-procedure vitals stable."),
        ]
        assessments = [
            "Continue current medications. Follow-up in 4 weeks.",
            "Labs ordered. Will adjust treatment based on results.",
            "Imaging recommended for further evaluation.",
            "Referral to specialist for further management.",
            "Condition stable. Continue monitoring.",
        ]

        for pat_id in patient_source_ids:
            num_notes = self._rng.randint(1, 4)
            for _ in range(num_notes):
                note_type, title, template = self._rng.choice(note_templates)
                content = template.format(
                    complaint=self._rng.choice(CHIEF_COMPLAINTS).lower(),
                    assessment=self._rng.choice(assessments),
                )
                authored = self._random_past_datetime(days_back=365)
                notes.append({
                    "source_id": f"NOTE-{uuid.uuid4().hex[:8]}",
                    "source_system": "ehr_mock",
                    "patient_source_id": pat_id,
                    "note_type": note_type,
                    "title": title,
                    "content": content,
                    "author": self._rng.choice(PROVIDERS),
                    "author_role": self._rng.choice(["physician", "nurse", "specialist"]),
                    "department": self._rng.choice(DEPARTMENTS),
                    "authored_at": authored.isoformat(),
                    "is_addendum": False,
                })
        return notes
