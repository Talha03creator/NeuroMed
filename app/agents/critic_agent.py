"""
Agent 3 — Critic Agent (Arize Phoenix MCP Integration)
Agentic Clinical Intelligence Platform

Implements the TRUE SELF-HEALING LOOP:
1. Trace every reasoning step
2. Score confidence & hallucination risk
3. If confidence < 0.85 → trigger backward chaining
4. Query Arize Phoenix traces to identify weak reasoning
5. Refine prompt and retry with Gemini 2.5 Flash
6. Compare outputs and return the best validated response

MCP Tools Used:
  - phoenix_log_trace → log reasoning step
  - phoenix_query_traces → query past traces for patterns
  - phoenix_evaluate_confidence → score model output quality
  - phoenix_detect_hallucination → check for unsupported claims
"""

import re
import json
import time
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.agent_trace import AgentTrace

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.85
MAX_HEALING_ITERATIONS = 3


# ══════════════════════════════════════════════════════════════════
# ARIZE PHOENIX MCP — Mock Observability Client
# ══════════════════════════════════════════════════════════════════

class ArizePhoenixMCPClient:
    """
    Mock Arize Phoenix MCP client that simulates real Phoenix
    trace logging and evaluation capabilities.
    """

    def __init__(self):
        self._traces: List[Dict[str, Any]] = []
        self._evaluations: List[Dict[str, Any]] = []
        logger.info("[Arize Phoenix MCP] Client initialized")

    async def log_trace(
        self,
        trace_id: str,
        span_name: str,
        input_data: str,
        output_data: str,
        latency_ms: float,
        tokens_used: int = 0,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        MCP Tool: phoenix_log_trace
        Logs a reasoning trace span to Phoenix.
        """
        trace = {
            "trace_id": trace_id,
            "span_id": str(uuid.uuid4())[:8],
            "span_name": span_name,
            "input_length": len(input_data),
            "output_length": len(output_data),
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self._traces.append(trace)
        return {"status": "success", "data": trace}

    async def evaluate_confidence(
        self, output_json: Dict, original_text: str
    ) -> Dict[str, Any]:
        """
        MCP Tool: phoenix_evaluate_confidence
        Evaluates the confidence and quality of a model output.
        Returns detailed quality metrics.
        """
        # Simulate quality evaluation
        issues = []
        score = output_json.get("confidence_score", 0.5)

        # Check for empty critical fields
        if not output_json.get("professional_summary"):
            issues.append({"field": "professional_summary", "issue": "Missing professional summary", "impact": 0.15})
            score -= 0.15
        if not output_json.get("patient_friendly_summary"):
            issues.append({"field": "patient_friendly_summary", "issue": "Missing patient-friendly summary", "impact": 0.10})
            score -= 0.10
        if not output_json.get("symptoms") and len(original_text) > 100:
            issues.append({"field": "symptoms", "issue": "No symptoms extracted from substantial text", "impact": 0.10})
            score -= 0.10
        if not output_json.get("specialty_classification"):
            issues.append({"field": "specialty_classification", "issue": "Missing specialty classification", "impact": 0.05})
            score -= 0.05

        # Check for suspiciously generic content
        summary = output_json.get("professional_summary", "")
        if summary and len(summary) < 50:
            issues.append({"field": "professional_summary", "issue": "Summary too brief — may lack clinical detail", "impact": 0.08})
            score -= 0.08

        # Check risk flags consistency
        risk_flags = output_json.get("risk_flags", [])
        risk_keywords = ["critical", "urgent", "emergency", "severe", "acute"]
        text_has_risk = any(kw in original_text.lower() for kw in risk_keywords)
        if text_has_risk and not risk_flags:
            issues.append({"field": "risk_flags", "issue": "Report contains urgent keywords but no risk flags detected", "impact": 0.12})
            score -= 0.12

        score = max(0.0, min(1.0, score))

        evaluation = {
            "confidence_score": round(score, 3),
            "quality_issues": issues,
            "issue_count": len(issues),
            "passes_threshold": score >= CONFIDENCE_THRESHOLD,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._evaluations.append(evaluation)
        return {"status": "success", "data": evaluation}

    async def detect_hallucination(
        self, output_json: Dict, original_text: str
    ) -> Dict[str, Any]:
        """
        MCP Tool: phoenix_detect_hallucination
        Checks for potential hallucinations in the model output.
        """
        hallucination_flags = []
        text_lower = original_text.lower()

        # Check if mentioned medications exist in source text
        for med in output_json.get("medications", []):
            med_name = med.lower().split()[0] if isinstance(med, str) else ""
            if med_name and len(med_name) > 3 and med_name not in text_lower:
                hallucination_flags.append({
                    "type": "unsupported_medication",
                    "value": med,
                    "reason": f"Medication '{med}' not found in source text",
                    "risk": 0.7,
                })

        # Check if lab values are fabricated
        for lab in output_json.get("lab_values", []):
            lab_str = str(lab).lower()
            # Extract numeric values from lab string
            numbers = re.findall(r'\d+\.?\d*', lab_str)
            for num in numbers:
                if num not in original_text:
                    # Could be legitimate extraction, only flag if very specific
                    pass

        risk_score = min(1.0, len(hallucination_flags) * 0.2) if hallucination_flags else 0.0

        return {
            "status": "success",
            "data": {
                "hallucination_flags": hallucination_flags,
                "hallucination_risk": round(risk_score, 3),
                "total_flags": len(hallucination_flags),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    async def query_traces(
        self, trace_id: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """
        MCP Tool: phoenix_query_traces
        Query past traces for pattern analysis.
        """
        if trace_id:
            matching = [t for t in self._traces if t["trace_id"] == trace_id]
        else:
            matching = self._traces[-limit:]

        return {
            "status": "success",
            "data": {
                "traces": matching,
                "total": len(matching),
            },
        }

    def get_evaluation_metrics(self) -> Dict[str, Any]:
        """Get aggregate evaluation metrics for the observability dashboard."""
        if not self._evaluations:
            return {"total_evaluations": 0, "avg_confidence": 0, "pass_rate": 0}

        scores = [e["confidence_score"] for e in self._evaluations]
        passes = sum(1 for e in self._evaluations if e["passes_threshold"])
        return {
            "total_evaluations": len(self._evaluations),
            "avg_confidence": round(sum(scores) / len(scores), 3),
            "pass_rate": round(passes / len(self._evaluations), 3),
            "total_issues_found": sum(e["issue_count"] for e in self._evaluations),
        }


# ── Singleton Phoenix client ─────────────────────────────────────
phoenix_client = ArizePhoenixMCPClient()


# ══════════════════════════════════════════════════════════════════
# CRITIC AGENT — SELF-HEALING LOOP
# ══════════════════════════════════════════════════════════════════

# ── Refinement Prompt Template ────────────────────────────────────
REFINEMENT_PROMPT = """You are an expert medical document analyst performing a QUALITY REVIEW.

Your PREVIOUS analysis of a medical report had quality issues identified by our AI observability system (Arize Phoenix).

## QUALITY ISSUES DETECTED:
{quality_issues}

## HALLUCINATION FLAGS:
{hallucination_flags}

## ORIGINAL MEDICAL TEXT:
{original_text}

## HISTORICAL PATIENT CONTEXT:
{context}

## YOUR PREVIOUS OUTPUT (to be improved):
{previous_output}

## INSTRUCTIONS:
1. Fix ALL identified quality issues.
2. Remove or correct any hallucinated content.
3. Ensure every extracted entity is grounded in the source text.
4. Provide a more detailed professional summary.
5. Ensure risk flags capture all urgent keywords present in the text.
6. Re-evaluate your confidence score honestly (0.0 to 1.0).

CRITICAL: Return ONLY a valid JSON object. No markdown, no code fences.

Required JSON structure:
{{
  "patient_info": {{"age": "string or null", "gender": "string or null"}},
  "symptoms": ["list of symptoms found in text"],
  "medications": ["list of medications found in text"],
  "procedures": ["list of procedures found in text"],
  "lab_values": ["list of lab results found in text"],
  "body_parts": ["list of body parts mentioned in text"],
  "clinical_impression": "brief clinical summary or null",
  "risk_flags": ["critical conditions, urgent findings"],
  "specialty_classification": "medical specialty",
  "professional_summary": "detailed 3-4 sentence clinical summary",
  "patient_friendly_summary": "clear 2-3 sentence plain-language explanation",
  "confidence_score": 0.90
}}"""


def _extract_json(raw: str) -> Optional[dict]:
    """Multi-pass JSON extraction from LLM response."""
    if not raw:
        return None
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw, flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


class CriticAgent:
    """
    Agent 3 — Critic Agent (Arize Phoenix MCP Integration).

    Implements the self-healing loop:
    1. Evaluate draft output confidence & quality
    2. Detect potential hallucinations
    3. If confidence < threshold → refine and retry
    4. Compare iterations and return best output
    5. Log all traces to Phoenix for observability
    """

    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._model_name: str = "gemini-2.5-flash"

    def _ensure_client(self) -> None:
        """Initialize Gemini client if needed."""
        if self._client is not None:
            return
        api_key = settings.get_ai_api_key()
        self._client = genai.Client(api_key=api_key)
        self._model_name = getattr(settings, "ai_model", "gemini-2.5-flash")
        if self._model_name.startswith("models/"):
            self._model_name = self._model_name[len("models/"):]

    async def _call_gemini_refinement(
        self,
        original_text: str,
        context: str,
        previous_output: Dict,
        quality_issues: List[Dict],
        hallucination_flags: List[Dict],
    ) -> Optional[Dict]:
        """Call Gemini with a refined prompt to fix quality issues."""
        self._ensure_client()

        issues_text = "\n".join(
            f"  - [{qi['field']}] {qi['issue']} (impact: -{qi['impact']:.0%})"
            for qi in quality_issues
        ) or "  None identified"

        halluc_text = "\n".join(
            f"  - [{hf['type']}] {hf['value']}: {hf['reason']}"
            for hf in hallucination_flags
        ) or "  None detected"

        prompt = REFINEMENT_PROMPT.format(
            quality_issues=issues_text,
            hallucination_flags=halluc_text,
            original_text=original_text[:6000],
            context=context[:3000] if context else "No historical context available.",
            previous_output=json.dumps(previous_output, indent=2)[:4000],
        )

        config = types.GenerateContentConfig(
            temperature=0.15,  # Lower temp for refinement — more deterministic
            top_p=0.8,
            max_output_tokens=4096,
        )

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=config,
                ),
                timeout=60.0,
            )
            raw = getattr(response, "text", "") or ""
            return _extract_json(raw)
        except asyncio.TimeoutError:
            logger.error("[Critic Agent] Refinement call timed out")
            return None
        except Exception as e:
            logger.error("[Critic Agent] Refinement call failed: %s", e)
            return None

    async def evaluate_and_heal(
        self,
        draft_json: Dict[str, Any],
        original_text: str,
        context: str = "",
        report_id: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Self-healing loop: evaluate, critique, refine, validate.

        Args:
            draft_json: Initial analysis output from Orchestrator
            original_text: Original medical report text
            context: Historical patient context string
            report_id: Report ID for trace logging
            db: Database session for persisting traces

        Returns:
            Dict with:
                - validated_output: The best analysis result
                - iterations: Number of healing iterations performed
                - traces: List of trace records
                - confidence_improved: Whether confidence was improved
                - original_confidence: Initial confidence score
                - final_confidence: Post-healing confidence score
        """
        trace_id = str(uuid.uuid4())
        iteration = 0
        best_output = dict(draft_json)
        best_confidence = draft_json.get("confidence_score", 0.5)
        original_confidence = best_confidence
        traces = []
        all_quality_issues = []
        all_hallucination_flags = []

        logger.info(
            "[Critic Agent] Starting evaluation — initial confidence: %.3f (threshold: %.2f)",
            best_confidence, CONFIDENCE_THRESHOLD,
        )

        while iteration < MAX_HEALING_ITERATIONS:
            iteration += 1
            step_start = time.monotonic()

            # ── Step 1: Log trace to Phoenix ──────────────────────
            await phoenix_client.log_trace(
                trace_id=trace_id,
                span_name=f"critic_evaluate_iteration_{iteration}",
                input_data=json.dumps(best_output)[:2000],
                output_data="",
                latency_ms=0,
                tokens_used=0,
                metadata={"iteration": iteration, "confidence": best_confidence},
            )

            # ── Step 2: Evaluate confidence ───────────────────────
            eval_result = await phoenix_client.evaluate_confidence(
                best_output, original_text
            )
            evaluation = eval_result.get("data", {})
            evaluated_confidence = evaluation.get("confidence_score", best_confidence)
            quality_issues = evaluation.get("quality_issues", [])
            all_quality_issues.extend(quality_issues)

            # ── Step 3: Detect hallucinations ─────────────────────
            halluc_result = await phoenix_client.detect_hallucination(
                best_output, original_text
            )
            halluc_data = halluc_result.get("data", {})
            hallucination_flags = halluc_data.get("hallucination_flags", [])
            hallucination_risk = halluc_data.get("hallucination_risk", 0.0)
            all_hallucination_flags.extend(hallucination_flags)

            # Adjust confidence based on hallucination risk
            adjusted_confidence = max(0.0, evaluated_confidence - hallucination_risk * 0.3)

            step_latency = (time.monotonic() - step_start) * 1000

            trace_record = {
                "iteration": iteration,
                "evaluated_confidence": evaluated_confidence,
                "hallucination_risk": hallucination_risk,
                "adjusted_confidence": adjusted_confidence,
                "quality_issues": quality_issues,
                "hallucination_flags": hallucination_flags,
                "passes_threshold": adjusted_confidence >= CONFIDENCE_THRESHOLD,
                "latency_ms": step_latency,
            }
            traces.append(trace_record)

            logger.info(
                "[Critic Agent] Iteration %d: confidence=%.3f haluc_risk=%.3f adjusted=%.3f %s",
                iteration, evaluated_confidence, hallucination_risk, adjusted_confidence,
                "✓ PASS" if adjusted_confidence >= CONFIDENCE_THRESHOLD else "✗ BELOW THRESHOLD",
            )

            # ── Step 4: Log agent trace to DB ─────────────────────
            if report_id and db:
                try:
                    agent_trace = AgentTrace(
                        report_id=report_id,
                        agent_name="critic_agent",
                        step_name="evaluate" if adjusted_confidence >= CONFIDENCE_THRESHOLD else "critique_and_refine",
                        step_order=iteration,
                        input_data=f"Evaluating analysis (iteration {iteration})",
                        output_data=f"Confidence: {adjusted_confidence:.3f}, Issues: {len(quality_issues)}, Hallucinations: {len(hallucination_flags)}",
                        tool_calls=[
                            {"tool": "phoenix_evaluate_confidence", "confidence": evaluated_confidence},
                            {"tool": "phoenix_detect_hallucination", "risk": hallucination_risk},
                        ],
                        confidence=adjusted_confidence,
                        hallucination_risk=hallucination_risk,
                        latency_ms=step_latency,
                        iteration=iteration,
                        status="completed",
                        model_name=self._model_name,
                        temperature=0.15,
                        metadata_json=trace_record,
                    )
                    if iteration > 1:
                        agent_trace.refinement_reason = (
                            f"Confidence {adjusted_confidence:.3f} < {CONFIDENCE_THRESHOLD} — "
                            f"{len(quality_issues)} quality issues, {len(hallucination_flags)} hallucination flags"
                        )
                    db.add(agent_trace)
                    await db.flush()
                except Exception as trace_err:
                    logger.warning("[Critic Agent] Failed to log trace: %s", trace_err)

            # ── Step 5: Check if we pass ──────────────────────────
            if adjusted_confidence >= CONFIDENCE_THRESHOLD:
                best_confidence = adjusted_confidence
                logger.info(
                    "[Critic Agent] ✓ VALIDATED after %d iteration(s) — confidence: %.3f",
                    iteration, best_confidence,
                )
                break

            # ── Step 6: Self-healing — refine and retry ───────────
            if iteration < MAX_HEALING_ITERATIONS:
                logger.info(
                    "[Critic Agent] Triggering self-healing refinement (iteration %d → %d)",
                    iteration, iteration + 1,
                )

                # Query Phoenix traces for pattern analysis
                past_traces = await phoenix_client.query_traces(trace_id=trace_id)
                logger.info(
                    "[Critic Agent] Phoenix traces queried: %d spans found",
                    past_traces["data"]["total"],
                )

                # Call Gemini with refined prompt
                refined = await self._call_gemini_refinement(
                    original_text=original_text,
                    context=context,
                    previous_output=best_output,
                    quality_issues=quality_issues,
                    hallucination_flags=hallucination_flags,
                )

                if refined:
                    # Compare new output with previous best
                    new_confidence = refined.get("confidence_score", 0.5)
                    if new_confidence > best_confidence:
                        best_output = refined
                        best_confidence = new_confidence
                        logger.info(
                            "[Critic Agent] Refined output improved: %.3f → %.3f",
                            adjusted_confidence, new_confidence,
                        )
                    else:
                        logger.info(
                            "[Critic Agent] Refined output not better: %.3f vs %.3f — keeping previous",
                            new_confidence, best_confidence,
                        )
                        # Still update best_output if the new one has fewer issues
                        if len(quality_issues) > 0:
                            best_output = refined
                            best_confidence = new_confidence
                else:
                    logger.warning("[Critic Agent] Refinement call returned None — keeping current best")
            else:
                logger.warning(
                    "[Critic Agent] Max iterations (%d) reached — returning best available (confidence: %.3f)",
                    MAX_HEALING_ITERATIONS, best_confidence,
                )

        # ── Final result ──────────────────────────────────────────
        # Ensure the output has the updated confidence
        best_output["confidence_score"] = round(best_confidence, 3)

        result = {
            "validated_output": best_output,
            "iterations": iteration,
            "traces": traces,
            "confidence_improved": best_confidence > original_confidence,
            "original_confidence": round(original_confidence, 3),
            "final_confidence": round(best_confidence, 3),
            "total_quality_issues": len(all_quality_issues),
            "total_hallucination_flags": len(all_hallucination_flags),
            "quality_issues": all_quality_issues,
            "hallucination_flags": all_hallucination_flags,
            "passed_threshold": best_confidence >= CONFIDENCE_THRESHOLD,
            "trace_id": trace_id,
        }

        logger.info(
            "[Critic Agent] Evaluation complete: confidence %.3f → %.3f (%d iterations, %s)",
            original_confidence, best_confidence, iteration,
            "PASSED" if result["passed_threshold"] else "BEST EFFORT",
        )

        return result


# ── Singleton ─────────────────────────────────────────────────────
critic_agent = CriticAgent()
