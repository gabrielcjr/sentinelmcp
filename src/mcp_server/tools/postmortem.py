"""Automated Root Cause Analysis (RCA) and Markdown Post-Mortem Generator."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class PostMortemReport(BaseModel):
    """Structured post-mortem incident report."""
    incident_id: str
    service_name: str
    severity: str
    generated_at: str
    root_cause: str
    timeline: List[Dict[str, str]]
    actions_taken: List[str]
    preventative_recommendations: List[str]
    markdown_content: str


async def generate_postmortem_rca(
    incident_id: str,
    service_name: str,
    root_cause: str,
    timeline: Optional[List[Dict[str, str]]] = None,
    actions_taken: Optional[List[str]] = None,
    preventative_recommendations: Optional[List[str]] = None,
    severity: str = "SEV-2",
) -> Dict[str, Any]:
    """Generates an executive-ready Markdown Root Cause Analysis (RCA) Post-Mortem report.

    Args:
        incident_id: Unique identifier of incident
        service_name: Affected microservice name
        root_cause: Detailed technical summary of root cause
        timeline: Key chronological events of the incident
        actions_taken: Remediation actions dispatched by SentinelMCP
        preventative_recommendations: Actionable improvements to avoid recurrence
        severity: Incident severity level (e.g. SEV-1, SEV-2)

    Returns:
        Structured report dictionary containing formatted Markdown text.
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    tl = timeline or [
        {"time": "-15m", "description": "Jaeger APM detected HTTP 5xx error rate spike (> 5%)."},
        {"time": "-12m", "description": "Kubernetes pod diagnostic identified OOMKilled exit code 137."},
        {"time": "-8m", "description": "SentinelMCP evaluated blast radius and dispatched guarded remediation."},
        {"time": "-3m", "description": "Workload recovered, error rate normalized below 0.1%."},
    ]
    actions = actions_taken or [
        f"Simulated horizontal scaling of deployment/{service_name} to 3 replicas.",
        f"Verified in-memory circuit breaker fallback readiness.",
    ]
    recs = preventative_recommendations or [
        "Increase container memory limit from 256Mi to 512Mi in Helm values / K8s manifest.",
        "Tune EdgeShield Redis sliding-window pipeline batch size to throttle sudden burst allocations.",
        "Implement predictive autoscaling (HPA) based on Jaeger / OpenTelemetry request volume metrics.",
    ]

    # Format Markdown
    timeline_md = "\n".join([f"- **{t.get('time', 'T-0')}**: {t.get('description', '')}" for t in tl])
    actions_md = "\n".join([f"- {a}" for a in actions])
    recs_md = "\n".join([f"- [ ] {r}" for r in recs])

    markdown = f"""# SRE Incident Post-Mortem: {incident_id}
**Service:** `{service_name}` | **Severity:** `{severity}` | **Generated:** `{now_iso}`

---

## 1. Executive Summary
During this incident, `{service_name}` experienced degraded performance leading to elevated error rates and container restart loops. SentinelMCP autonomously intercepted the alert, performed trace-to-log correlation, identified the failure mode, and applied guarded remediation runbooks.

---

## 2. Root Cause Analysis (RCA)
{root_cause}

---

## 3. Incident Timeline
{timeline_md}

---

## 4. Remediation Actions Taken (Guarded Runbooks)
{actions_md}

---

## 5. Preventative Action Items
{recs_md}

---
*Generated autonomously by SentinelMCP Engine (Model Context Protocol SRE Agent)*
"""

    return PostMortemReport(
        incident_id=incident_id,
        service_name=service_name,
        severity=severity,
        generated_at=now_iso,
        root_cause=root_cause,
        timeline=tl,
        actions_taken=actions,
        preventative_recommendations=recs,
        markdown_content=markdown,
    ).model_dump()
