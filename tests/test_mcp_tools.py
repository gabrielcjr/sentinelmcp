"""Unit and integration tests for Sentinel MCP Tools."""

import pytest
from src.mcp_server.server import create_mcp_server
from src.mcp_server.tools.telemetry import query_telemetry
from src.mcp_server.tools.k8s_diag import diagnose_k8s_pods, fetch_container_logs
from src.mcp_server.tools.remediation import execute_remediation_runbook
from src.mcp_server.tools.postmortem import generate_postmortem_rca


@pytest.mark.asyncio
async def test_tool_query_telemetry():
    result = await query_telemetry("edgeshield", time_window_mins=15)
    assert result["service_name"] == "edgeshield"
    assert "error_rate_pct" in result
    assert "p99_latency_ms" in result
    assert result["error_rate_pct"] > 0


@pytest.mark.asyncio
async def test_tool_diagnose_k8s_pods():
    diagnostics = await diagnose_k8s_pods(service_name="edgeshield")
    assert isinstance(diagnostics, list)
    assert len(diagnostics) > 0
    pod = diagnostics[0]
    assert "pod_name" in pod
    assert "is_failing" in pod


@pytest.mark.asyncio
async def test_tool_fetch_container_logs():
    logs = await fetch_container_logs(pod_name="edgeshield-test-pod")
    assert isinstance(logs, str)
    assert "reverse_proxy" in logs or "INFO" in logs or "ERROR" in logs


@pytest.mark.asyncio
async def test_tool_execute_remediation_dry_run():
    result = await execute_remediation_runbook(
        incident_id="INC-TEST-1",
        action_type="scale",
        target="edgeshield",
        params={"replicas": 3},
        dry_run=True,
    )
    assert result["success"] is True
    assert result["dry_run"] is True
    assert "DRY-RUN" in result["message"]
    assert "replicas: 3" in result["diff"]


@pytest.mark.asyncio
async def test_tool_generate_postmortem_rca():
    report = await generate_postmortem_rca(
        incident_id="INC-RCA-99",
        service_name="edgeshield",
        root_cause="Memory exhaustion under traffic burst.",
    )
    assert report["incident_id"] == "INC-RCA-99"
    assert report["service_name"] == "edgeshield"
    assert "Memory exhaustion" in report["root_cause"]
    assert "# SRE Incident Post-Mortem" in report["markdown_content"]


@pytest.mark.asyncio
async def test_mcp_server_direct_call():
    server = create_mcp_server()
    res = await server.call_tool(
        "query_telemetry",
        {"service_name": "edgeshield", "time_window_mins": 10},
    )
    assert res.is_error is False
    assert res.structured_content["result"]["service_name"] == "edgeshield"
