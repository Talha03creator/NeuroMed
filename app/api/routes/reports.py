"""
Reports API Routes
AI Medical Report Analyzer

Endpoints:
  POST   /api/v1/reports/upload   - Upload and analyze a medical report
  GET    /api/v1/reports          - List analysis history (paginated)
  GET    /api/v1/reports/{id}     - Get single report analysis
  GET    /api/v1/reports/{id}/export - Export report as JSON
  DELETE /api/v1/reports/{id}     - Delete a report
"""

import io
import json
import logging
from math import ceil
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.extraction_service import ExtractionService
from app.utils.file_handler import extract_text
from app.schemas.report import (
    ReportResponse,
    ReportListItem,
    PaginatedReports,
    ErrorResponse,
    ReportStatus,
)
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reports", tags=["Medical Reports"])


# ── Upload & Analyze ───────────────────────────────────────────────
@router.post(
    "/upload",
    response_model=ReportResponse,
    summary="Upload and analyze a medical report",
    description=(
        "Upload a TXT or PDF medical transcription. "
        "The system extracts structured entities using AI and returns full analysis. "
        "**Disclaimer:** This system is for informational purposes only and does not provide medical diagnosis."
    ),
    responses={
        200: {"model": ReportResponse},
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def upload_report(
    file: UploadFile = File(..., description="Medical report (TXT or PDF, max 10MB)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a medical transcription file for AI analysis.
    
    Returns structured JSON with:
    - Extracted entities (symptoms, medications, procedures, etc.)
    - Specialty classification
    - Risk flags
    - Professional and patient-friendly summaries
    - Confidence score
    """
    # MOCK MODE FOR HACKATHON DEMO
    # Returns the exact mock JSON structure requested by the user with list arrays
    mock_analysis = {
        "summary": "Patient exhibits severe neurological degradation consistent with advanced Parkinsonian traits. Fivetran historical EHR confirms a contradiction with newly prescribed dopamine antagonists.",
        "risk_flags": [
            "High Fall Risk due to motor symptom exacerbation.",
            "Medication Contradiction identified in Fivetran EHR logs.",
            "Rapid Neurological Decline over the last 3 months."
        ],
        "recommended_steps": [
            "Initiate Levodopa protocol immediately.",
            "Schedule emergency Neurology board review.",
            "Create priority GitLab Escalation Ticket for the clinical team."
        ]
    }
    
    return JSONResponse(status_code=200, content={
        "id": "c91f3a32-0a6d-4511-890c-0dd304de55d8",
        "filename": file.filename,
        "file_type": "pdf",
        "status": "completed",
        "patient_age": "58",
        "patient_gender": "male",
        "symptoms": ["Neurological Decline", "Motor Degradation"],
        "medications": ["Dopamine Antagonists"],
        "procedures": ["Neurology Board Review"],
        "lab_values": ["LDL: 160 mg/dL"],
        "body_parts": ["Brain", "Nervous System"],
        "clinical_impression": "Severe Neurological Decline",
        "risk_flags": mock_analysis["risk_flags"],
        "specialty_classification": "Neurology",
        "professional_summary": mock_analysis["summary"],
        "patient_friendly_summary": mock_analysis["summary"],
        "confidence_score": 0.98,
        "full_analysis_json": {
            "analysis": mock_analysis,
            "recommended_next_steps": mock_analysis["recommended_steps"]
        },
        "processing_time_ms": 120.0,
        "tokens_used": 1500,
        "cached": False,
        "error_message": None,
        "created_at": "2026-05-26T15:22:54Z",
        "updated_at": "2026-05-26T15:22:54Z",
        "disclaimer": "This system is for informational purposes only and does not provide medical diagnosis."
    })
    
    # ── Validate file type ─────────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = file.filename.rsplit(".", 1)[-1].lower()
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{file_ext}'. Allowed: {', '.join(settings.allowed_extensions_list)}",
        )

    # ── Validate file size ─────────────────────────────────────────
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
        )

    # ── Extract text ───────────────────────────────────────────────
    try:
        raw_text, file_type = await extract_text(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(raw_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="File contains too little text for analysis (minimum 50 characters)",
        )

    # ── Create DB record ───────────────────────────────────────────
    report = await ExtractionService.create_pending_report(
        db=db,
        filename=file.filename,
        file_type=file_type,
        file_size=file_size,
        raw_text=raw_text,
    )

    # ── Run AI analysis ────────────────────────────────────────────
    logger.info(f"Starting analysis for report {report.id} ({file.filename})")
    report = await ExtractionService.process_report(db=db, report=report)

    if report.status == ReportStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {report.error_message}",
        )

    return ReportResponse.model_validate(report)


# ── List History ───────────────────────────────────────────────────
@router.get(
    "",
    response_model=PaginatedReports,
    summary="Get report analysis history",
)
async def list_reports(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated list of all analyzed medical reports."""
    items, total = await ExtractionService.get_reports_paginated(
        db=db, page=page, per_page=per_page
    )
    pages = ceil(total / per_page) if total > 0 else 0

    return PaginatedReports(
        items=[ReportListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ── Get Single Report ──────────────────────────────────────────────
@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get a specific report analysis",
)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the full analysis of a specific report by ID."""
    report = await ExtractionService.get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return ReportResponse.model_validate(report)


# ── Export JSON ────────────────────────────────────────────────────
@router.get(
    "/{report_id}/export",
    summary="Export report analysis as JSON file",
)
async def export_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download the complete analysis JSON for a specific report."""
    report = await ExtractionService.get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    export_data = {
        "id": str(report.id),
        "filename": report.filename,
        "status": report.status,
        "disclaimer": settings.disclaimer,
        "analysis": {
            "patient_info": {
                "age": report.patient_age,
                "gender": report.patient_gender,
            },
            "symptoms": report.symptoms or [],
            "medications": report.medications or [],
            "procedures": report.procedures or [],
            "lab_values": report.lab_values or [],
            "body_parts": report.body_parts or [],
            "clinical_impression": report.clinical_impression,
            "risk_flags": report.risk_flags or [],
            "specialty_classification": report.specialty_classification,
            "professional_summary": report.professional_summary,
            "patient_friendly_summary": report.patient_friendly_summary,
            "confidence_score": report.confidence_score,
        },
        "metadata": {
            "processing_time_ms": report.processing_time_ms,
            "tokens_used": report.tokens_used,
            "cached": report.cached,
            "created_at": report.created_at.isoformat(),
        },
    }

    json_bytes = json.dumps(export_data, indent=2, default=str).encode("utf-8")
    filename = f"medical_analysis_{str(report.id)[:8]}.json"

    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


# ── Delete Report ──────────────────────────────────────────────────
@router.delete(
    "/{report_id}",
    status_code=204,
    summary="Delete a report",
)
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a report and its analysis from the database."""
    deleted = await ExtractionService.delete_report(db=db, report_id=report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
