"""
Clinical Copilot Route
Stateful Interactive Conversational Assistant for clinicians.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from google import genai
from app.core.config import settings
from app.api.dependencies import get_db_session
from app.models.report import MedicalReport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Clinical Copilot"])

class ChatRequest(BaseModel):
    message: str
    report_id: Optional[str] = None
    session_id: Optional[str] = None

@router.post("/", summary="Chat with the Clinical Copilot")
async def copilot_chat(request: ChatRequest, db: AsyncSession = Depends(get_db_session)):
    logger.info(f"Received chat request: {request.message}")
    
    context_str = "No specific clinical report context provided."
    if request.report_id:
        stmt = select(MedicalReport).where(MedicalReport.id == request.report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        
        if report:
            context_str = f"Report Executive Summary: {report.executive_summary}\n" \
                          f"Critical Risks: {report.critical_risks}\n" \
                          f"EHR Context: {report.ehr_context}"
    
    prompt = f"""You are the NeuroMed Clinical Copilot. 
    A clinician is asking you a question. Use the following context from their current session:
    
    CONTEXT:
    {context_str}
    
    CLINICIAN QUESTION:
    {request.message}
    
    Provide a concise, professional, and explainable answer based ONLY on the provided context.
    """
    
    api_key = settings.get_ai_api_key()
    client = genai.Client(api_key=api_key)
    model_name = getattr(settings, "ai_model", "gemini-2.5-flash")
    if model_name.startswith("models/"):
        model_name = model_name[len("models/"):]
        
    import asyncio
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                ),
                timeout=20.0
            )
            return {"response": response.text}
        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str) and attempt < max_retries - 1:
                logger.warning(f"Chat rate limit hit. Retrying in 45s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(45)
                continue
            logger.error(f"Copilot Chat Error: {e}")
            raise HTTPException(status_code=500, detail="Copilot failed to generate a response.")
