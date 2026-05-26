from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ReasoningStep(BaseModel):
    step: str = Field(description="The name of the reasoning step or tool invoked.")
    thought: str = Field(description="The detailed thought or action taken during this step.")

class ClinicalAnalysisResponse(BaseModel):
    executive_summary: str = Field(description="Max 2 precise clinical sentences summarizing the report.")
    patient_friendly_summary: str = Field(description="A brief, easy-to-understand summary for the patient.", default="N/A")
    extracted_biomarkers: str = Field(description="Markdown table of extracted metrics (e.g., | Metric | Value |).")
    critical_risks: str = Field(description="Bulleted string of critical risks/contradictions based on context.")
    recommended_next_steps: str = Field(description="Bulleted string of actionable items.")
    reasoning_timeline: Optional[List[ReasoningStep]] = Field(description="Chronological timeline of reasoning steps taken.", default_factory=list)
    ehr_context: Dict[str, Any] = Field(description="Historical EHR context retrieved for the patient.", default_factory=dict)
    confidence_score: float = Field(description="Confidence score of the analysis between 0.0 and 1.0.", default=0.95)
    gitlab_escalation: Optional[Dict[str, Any]] = Field(description="Details of any incident escalation, if triggered.", default=None)
    agent_actions: List[str] = Field(description="List of system actions taken by the agent.", default_factory=list)
    escalation_reason: str = Field(description="Explanation of why escalation is needed, or empty if none.", default="")
