"""
Agent 4 — DevSecOps Agent (GitLab MCP Integration)
Agentic Clinical Intelligence Platform

Monitors backend failures, tracks AI pipeline exceptions, and
auto-generates GitLab issues with incident summaries. Demonstrates
enterprise AI operations maturity through automated incident response.

MCP Tools Used:
  - gitlab_create_issue → create incident issue
  - gitlab_add_comment → attach logs to issue
  - gitlab_list_issues → check for duplicate incidents
"""

import uuid
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


# ── Mock GitLab MCP Client ────────────────────────────────────────

class GitLabMCPClient:
    """
    Mock GitLab MCP client that simulates real GitLab API operations.
    In production, this would connect to the GitLab MCP server.
    """

    def __init__(self):
        self._issues: List[Dict[str, Any]] = []
        self._project_id = "clinical-intelligence/platform"
        self._issue_counter = 1000
        logger.info("[GitLab MCP] Client initialized for project: %s", self._project_id)

    async def create_issue(
        self,
        title: str,
        description: str,
        labels: List[str],
        priority: str = "high",
        assignee: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        MCP Tool: gitlab_create_issue
        Creates a new issue in the GitLab project.
        """
        self._issue_counter += 1
        issue = {
            "issue_id": self._issue_counter,
            "iid": self._issue_counter,
            "project_id": self._project_id,
            "title": title,
            "description": description,
            "labels": labels,
            "priority": priority,
            "state": "opened",
            "assignee": assignee or "on-call-engineer",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "web_url": f"https://gitlab.com/{self._project_id}/-/issues/{self._issue_counter}",
            "severity": "s1" if priority == "critical" else "s2",
        }
        self._issues.append(issue)
        logger.info(
            "[GitLab MCP] Issue #%d created: %s [%s]",
            issue["iid"], title, priority,
        )
        return {"status": "success", "data": issue}

    async def add_comment(
        self, issue_id: int, body: str
    ) -> Dict[str, Any]:
        """
        MCP Tool: gitlab_add_comment
        Adds a comment to an existing issue.
        """
        comment = {
            "issue_id": issue_id,
            "body": body,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "author": "devsecops-agent",
        }
        logger.info("[GitLab MCP] Comment added to issue #%d", issue_id)
        return {"status": "success", "data": comment}

    async def list_issues(
        self,
        labels: Optional[List[str]] = None,
        state: str = "opened",
    ) -> Dict[str, Any]:
        """
        MCP Tool: gitlab_list_issues
        Lists issues in the project, optionally filtered by labels/state.
        """
        filtered = [
            i for i in self._issues
            if i["state"] == state
            and (not labels or any(l in i["labels"] for l in labels))
        ]
        return {
            "status": "success",
            "data": {
                "issues": filtered,
                "total": len(filtered),
            },
        }

    async def get_issue(self, issue_id: int) -> Dict[str, Any]:
        """Get a specific issue by ID."""
        for issue in self._issues:
            if issue["iid"] == issue_id:
                return {"status": "success", "data": issue}
        return {"status": "error", "error": f"Issue #{issue_id} not found"}


# ── Singleton GitLab client ───────────────────────────────────────
gitlab_client = GitLabMCPClient()


# ── Incident Severity Classification ─────────────────────────────

SEVERITY_MAP = {
    "TimeoutError": ("critical", "AI Pipeline Timeout"),
    "asyncio.TimeoutError": ("critical", "AI Pipeline Timeout"),
    "ConnectionError": ("critical", "Service Connection Failure"),
    "google.api_core.exceptions.ResourceExhausted": ("high", "API Rate Limit Exceeded"),
    "google.api_core.exceptions.InternalServerError": ("high", "Upstream AI Service Error"),
    "json.JSONDecodeError": ("medium", "AI Response Parse Failure"),
    "ValueError": ("medium", "Validation Error"),
    "KeyError": ("low", "Missing Data Field"),
    "Exception": ("medium", "Unclassified Error"),
}


def _classify_severity(exc_type: str) -> tuple:
    """Classify exception severity and category."""
    for key, (severity, category) in SEVERITY_MAP.items():
        if key in exc_type:
            return severity, category
    return "medium", "Unclassified Error"


class DevSecOpsAgent:
    """
    Agent 4 — DevSecOps Agent (GitLab MCP Integration).

    Responsibilities:
    1. Monitor backend failures and AI pipeline exceptions
    2. Classify incident severity automatically
    3. Generate structured GitLab issues with context
    4. Attach diagnostic logs and request traces
    5. Suggest mitigation strategies
    6. Track incident patterns for proactive alerting
    7. Create audit trail entries for compliance
    """

    def __init__(self):
        self._incident_count = 0
        self._recent_errors: List[Dict[str, Any]] = []

    def _build_incident_description(
        self, error_context: Dict[str, Any]
    ) -> str:
        """Build a detailed GitLab issue description from error context."""
        exc_type = error_context.get("exception_type", "Unknown")
        exc_msg = error_context.get("exception_message", "No message")
        stack_trace = error_context.get("stack_trace", "Not available")
        request_id = error_context.get("request_id", "N/A")
        endpoint = error_context.get("endpoint", "N/A")
        report_id = error_context.get("report_id", "N/A")
        timestamp = error_context.get("timestamp", datetime.now(timezone.utc).isoformat())
        latency_ms = error_context.get("latency_ms", "N/A")
        model_name = error_context.get("model_name", "gemini-2.5-flash")

        severity, category = _classify_severity(exc_type)

        description = f"""## 🚨 Automated Incident Report — DevSecOps Agent

**Category:** {category}
**Severity:** {severity.upper()}
**Timestamp:** {timestamp}
**Request ID:** `{request_id}`

---

### Environment
| Key | Value |
|-----|-------|
| Endpoint | `{endpoint}` |
| Report ID | `{report_id}` |
| AI Model | `{model_name}` |
| Latency | {latency_ms}ms |
| Agent | DevSecOps Agent v1.0 |

---

### Exception Details
**Type:** `{exc_type}`
**Message:** {exc_msg}

### Stack Trace
```python
{stack_trace}
```

---

### Impact Assessment
- **User Impact:** Analysis request failed — user received error response
- **Data Impact:** No data corruption — report saved with FAILED status
- **System Impact:** Single request failure — system remains operational

---

### Suggested Mitigation
{self._suggest_mitigation(exc_type, exc_msg)}

---

### AI Pipeline Context
- **Step Failed:** {error_context.get('failed_step', 'Unknown')}
- **Agent:** {error_context.get('agent_name', 'Orchestrator')}
- **Retry Attempted:** {error_context.get('retried', False)}
- **Tokens Used Before Failure:** {error_context.get('tokens_used', 'N/A')}

---

*Generated automatically by the DevSecOps Agent (GitLab MCP Integration)*
"""
        return description.strip(), severity, category

    def _suggest_mitigation(self, exc_type: str, exc_msg: str) -> str:
        """Generate mitigation suggestions based on error type."""
        if "Timeout" in exc_type:
            return """1. **Immediate:** Increase timeout threshold from 50s → 90s
2. **Short-term:** Implement request queuing for large reports
3. **Long-term:** Add streaming response support to reduce TTFB
4. **Monitor:** Set up Cloud Monitoring alert for p95 latency > 30s"""

        if "ResourceExhausted" in exc_type or "rate" in exc_msg.lower():
            return """1. **Immediate:** Activate rate-limit backoff (exponential)
2. **Short-term:** Implement request queue with Redis
3. **Long-term:** Negotiate higher API quotas with Google
4. **Monitor:** Track RPM metrics and set threshold alerts"""

        if "Connection" in exc_type:
            return """1. **Immediate:** Verify Cloud Run ↔ Cloud SQL connectivity
2. **Short-term:** Check VPC connector and firewall rules
3. **Long-term:** Implement circuit breaker pattern
4. **Monitor:** Add uptime checks for all dependencies"""

        if "JSONDecode" in exc_type:
            return """1. **Immediate:** Strengthen JSON extraction regex
2. **Short-term:** Add response format validation middleware
3. **Long-term:** Use Gemini structured output mode (response_schema)
4. **Monitor:** Track JSON parse failure rate"""

        return """1. **Immediate:** Review logs for root cause
2. **Short-term:** Add specific error handling for this exception type
3. **Long-term:** Implement comprehensive error taxonomy
4. **Monitor:** Set up alerting for this error pattern"""

    # ── Main Exception Handler ────────────────────────────────────
    async def handle_system_exception(
        self,
        error_context: Dict[str, Any],
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Handle a system exception by creating a GitLab incident.

        Args:
            error_context: Dict containing exception details:
                - exception_type: str
                - exception_message: str
                - stack_trace: str
                - request_id: str
                - endpoint: str
                - report_id: str (optional)
                - timestamp: str
                - latency_ms: float
                - model_name: str
                - failed_step: str
                - agent_name: str
                - retried: bool

        Returns:
            Dict with incident details and GitLab issue reference.
        """
        self._incident_count += 1
        request_id = error_context.get("request_id", str(uuid.uuid4()))
        logger.error(
            "[DevSecOps Agent] Handling exception — request_id=%s type=%s",
            request_id, error_context.get("exception_type", "Unknown"),
        )

        # ── Step 1: Build incident description ───────────────────
        description, severity, category = self._build_incident_description(error_context)

        # ── Step 2: Check for duplicate open issues ───────────────
        existing = await gitlab_client.list_issues(
            labels=["incident", category.lower().replace(" ", "-")],
            state="opened",
        )
        duplicate_count = existing["data"]["total"]

        # ── Step 3: Create GitLab issue ───────────────────────────
        title = (
            f"[{severity.upper()}] {category} — "
            f"{error_context.get('exception_type', 'Error')} "
            f"(req: {request_id[:8]})"
        )
        labels = [
            "incident",
            f"severity:{severity}",
            category.lower().replace(" ", "-"),
            "auto-generated",
            "devsecops-agent",
        ]

        issue_result = await gitlab_client.create_issue(
            title=title,
            description=description,
            labels=labels,
            priority=severity,
        )

        issue_data = issue_result.get("data", {})
        issue_id = issue_data.get("iid", 0)

        # ── Step 4: Add diagnostic comment ────────────────────────
        if duplicate_count > 0:
            await gitlab_client.add_comment(
                issue_id,
                f"⚠️ **Note:** {duplicate_count} similar open issue(s) detected. "
                f"This may be a recurring pattern requiring architectural review.",
            )

        # ── Step 5: Track in recent errors ────────────────────────
        incident_record = {
            "incident_id": self._incident_count,
            "gitlab_issue_id": issue_id,
            "gitlab_url": issue_data.get("web_url", ""),
            "severity": severity,
            "category": category,
            "request_id": request_id,
            "exception_type": error_context.get("exception_type"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duplicate_count": duplicate_count,
        }
        self._recent_errors.append(incident_record)
        # Keep only last 100 incidents in memory
        if len(self._recent_errors) > 100:
            self._recent_errors = self._recent_errors[-100:]

        # ── Step 6: Create audit log entry ────────────────────────
        if db is not None:
            try:
                audit = AuditLog(
                    event_type="system",
                    action="incident_created",
                    entity_type="gitlab_issue",
                    entity_id=str(issue_id),
                    description=f"DevSecOps Agent auto-created GitLab issue #{issue_id}: {title}",
                    details={
                        "severity": severity,
                        "category": category,
                        "request_id": request_id,
                        "exception_type": error_context.get("exception_type"),
                    },
                    actor_type="agent",
                    actor_id="devsecops_agent",
                    severity="critical" if severity == "critical" else "warning",
                )
                db.add(audit)
                await db.flush()
            except Exception as audit_err:
                logger.warning("[DevSecOps Agent] Failed to create audit log: %s", audit_err)

        logger.info(
            "[DevSecOps Agent] Incident #%d created → GitLab issue #%d [%s] %s",
            self._incident_count, issue_id, severity.upper(), issue_data.get("web_url", ""),
        )

        return {
            "incident_created": True,
            "incident_id": self._incident_count,
            "gitlab_issue": issue_data,
            "severity": severity,
            "category": category,
            "mitigation_suggested": True,
            "duplicate_warning": duplicate_count > 0,
        }

    # ── Build error context from exception ────────────────────────
    @staticmethod
    def build_error_context(
        exception: Exception,
        request_id: Optional[str] = None,
        report_id: Optional[str] = None,
        endpoint: str = "/api/v1/reports/analyze",
        failed_step: str = "unknown",
        agent_name: str = "orchestrator",
        latency_ms: float = 0,
        model_name: str = "gemini-2.5-flash",
        retried: bool = False,
    ) -> Dict[str, Any]:
        """Build a structured error context dict from an exception."""
        return {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception) or repr(exception),
            "stack_trace": traceback.format_exc(),
            "request_id": request_id or str(uuid.uuid4()),
            "endpoint": endpoint,
            "report_id": report_id or "N/A",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_ms": latency_ms,
            "model_name": model_name,
            "failed_step": failed_step,
            "agent_name": agent_name,
            "retried": retried,
        }

    # ── Health & Metrics ──────────────────────────────────────────
    def get_incident_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for the observability dashboard."""
        if not self._recent_errors:
            return {
                "total_incidents": 0,
                "recent_incidents": [],
                "severity_breakdown": {},
            }

        severity_counts: Dict[str, int] = {}
        for err in self._recent_errors:
            sev = err.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "total_incidents": self._incident_count,
            "recent_incidents": self._recent_errors[-10:],  # Last 10
            "severity_breakdown": severity_counts,
        }


# ── Singleton ─────────────────────────────────────────────────────
devsecops_agent = DevSecOpsAgent()
