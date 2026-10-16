"""Model Context Protocol (MCP) Server for Sentinel SRE tools."""

from typing import Any, Dict, List, Optional
from mcp.server.mcpserver import MCPServer
from src.config import settings
from src.mcp_server.tools.telemetry import query_telemetry
from src.mcp_server.tools.k8s_diag import diagnose_k8s_pods, fetch_container_logs
from src.mcp_server.tools.remediation import execute_remediation_runbook
from src.mcp_server.tools.postmortem import generate_postmortem_rca


def create_mcp_server() -> MCPServer:
    """Creates and configures the SentinelMCP Server with all SRE tools."""
    server = MCPServer(
        name=settings.mcp_server_name,
        instructions="Sentinel SRE Agent Tooling: Observability, Diagnostics, and Guarded Remediation",
    )

    # 1. Telemetry Query Tool
    @server.tool(
        name="query_telemetry",
        description="Query Jaeger / OpenTelemetry APM for P50/P95/P99 latency, HTTP error rate spikes, and active error traces.",
    )
    async def tool_query_telemetry(
        service_name: str,
        time_window_mins: int = 15,
        min_status_code: int = 500,
    ) -> Dict[str, Any]:
        """Query Jaeger / OpenTelemetry APM telemetry for latency percentiles and error rates."""
        return await query_telemetry(
            service_name=service_name,
            time_window_mins=time_window_mins,
            min_status_code=min_status_code,
        )

    # 2. Kubernetes Pod Diagnostics Tool
    @server.tool(
        name="diagnose_k8s_pods",
        description="Inspect Kubernetes pods for crash loops, OOMKilled events (exit code 137), and restart anomalies.",
    )
    async def tool_diagnose_k8s_pods(
        namespace: Optional[str] = None,
        service_name: Optional[str] = None,
        selector: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Diagnose Kubernetes pods for crash loops, exit codes, and health anomalies."""
        return await diagnose_k8s_pods(
            namespace=namespace,
            service_name=service_name,
            selector=selector,
        )

    # 3. Container Logs Tool
    @server.tool(
        name="fetch_container_logs",
        description="Fetch stdout/stderr logs from a specific pod or its previous terminated container.",
    )
    async def tool_fetch_container_logs(
        namespace: Optional[str] = None,
        pod_name: Optional[str] = None,
        tail_lines: int = 50,
        previous: bool = False,
    ) -> str:
        """Fetch stdout and stderr logs from pod containers."""
        return await fetch_container_logs(
            namespace=namespace,
            pod_name=pod_name,
            tail_lines=tail_lines,
            previous=previous,
        )

    # 4. Guarded Remediation Runbook Tool
    @server.tool(
        name="execute_remediation_runbook",
        description="Safely execute guarded remediation runbooks (restart, scale, flush_cache, enable_fallback) with dry-run support.",
    )
    async def tool_execute_remediation_runbook(
        incident_id: str,
        action_type: str,
        target: str,
        params: Optional[Dict[str, Any]] = None,
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Execute validated remediation runbooks against Kubernetes workloads."""
        return await execute_remediation_runbook(
            incident_id=incident_id,
            action_type=action_type,
            target=target,
            params=params,
            dry_run=dry_run,
        )

    # 5. Automated Post-Mortem & RCA Tool
    @server.tool(
        name="generate_postmortem_rca",
        description="Generate an executive-ready Markdown Root Cause Analysis (RCA) Post-Mortem report.",
    )
    async def tool_generate_postmortem_rca(
        incident_id: str,
        service_name: str,
        root_cause: str,
        timeline: Optional[List[Dict[str, str]]] = None,
        actions_taken: Optional[List[str]] = None,
        preventative_recommendations: Optional[List[str]] = None,
        severity: str = "SEV-2",
    ) -> Dict[str, Any]:
        """Generate structured Markdown Root Cause Analysis and Post-Mortem report."""
        return await generate_postmortem_rca(
            incident_id=incident_id,
            service_name=service_name,
            root_cause=root_cause,
            timeline=timeline,
            actions_taken=actions_taken,
            preventative_recommendations=preventative_recommendations,
            severity=severity,
        )

    return server


mcp_server = create_mcp_server()
