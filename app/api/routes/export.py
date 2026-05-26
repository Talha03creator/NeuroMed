"""
Export Route — Medical Report Outputs
Generates Clinician-Ready PDFs and JSON exports.
"""

import json
import logging
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.dependencies import get_db_session
from app.models.report import MedicalReport
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/export", tags=["Enterprise Export Actions"])

@router.get("/{report_id}/json", summary="Export Clinical Analysis as JSON")
async def export_json(report_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = select(MedicalReport).where(MedicalReport.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    export_data = {
        "report_id": str(report.id),
        "filename": report.filename,
        "executive_summary": report.executive_summary,
        "extracted_biomarkers": report.extracted_biomarkers,
        "critical_risks": report.critical_risks,
        "recommended_next_steps": report.recommended_next_steps,
        "ehr_context": report.ehr_context,
        "incident_report": report.incident_report,
        "confidence_score": report.confidence_score
    }
    
    return JSONResponse(
        content=export_data, 
        headers={"Content-Disposition": f"attachment; filename=neuromed_{report_id}.json"}
    )

@router.get("/{report_id}/pdf", summary="Export Clinician-Ready PDF")
async def export_pdf(report_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = select(MedicalReport).where(MedicalReport.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # PDF Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "NeuroMed Autonomous Clinical Intelligence Report")
    
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, f"Report ID: {report.id}")
    p.drawString(50, height - 85, f"Filename: {report.filename}")
    
    # Executive Summary
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 120, "Executive Clinical Summary")
    p.setFont("Helvetica", 10)
    
    # simple text wrapping workaround for demo
    text_obj = p.beginText(50, height - 140)
    text_obj.setFont("Helvetica", 10)
    summary = str(report.executive_summary or "None")
    for line in summary.split('\\n'):
        text_obj.textLine(line)
    p.drawText(text_obj)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=clinician_report_{report_id}.pdf"}
    )
