"""Tests for SRE Agent Orchestrator and Deterministic Runbook Engine."""

import pytest
from src.orchestrator.fallback import DeterministicRunbookEngine
from src.orchestrator.agent import SREAgentOrchestrator


@pytest.mark.asyncio
async def test_deterministic_engine_full_investigation():
    engine = DeterministicRunbookEngine()
    result = await engine.investigate_and_remediate(
        incident_id="INC-ORCH-1",
        service_name="edgeshield",
        alert_name="HighErrorRateSpike",
        dry_run=True,
    )

    assert result.incident_id == "INC-ORCH-1"
    assert result.service_name == "edgeshield"
    assert result.status == "MITIGATED"
    assert len(result.steps) == 5

    step_actions = [s.action_name for s in result.steps]
    assert step_actions == [
        "query_signoz_telemetry",
        "diagnose_k8s_pods",
        "fetch_container_logs",
        "execute_remediation_runbook",
        "generate_postmortem_rca",
    ]

    assert "OOMKilled" in result.root_cause or "memory" in result.root_cause.lower()
    assert "markdown_content" in result.postmortem


@pytest.mark.asyncio
async def test_agent_orchestrator_fallback_mode():
    orchestrator = SREAgentOrchestrator()
    result = await orchestrator.investigate_incident(
        incident_id="INC-ORCH-2",
        service_name="devats",
        alert_name="HighLatencyP99",
        dry_run=True,
    )

    assert result.incident_id == "INC-ORCH-2"
    assert result.service_name == "devats"
    assert len(result.steps) >= 4
    assert result.status in ("MITIGATED", "RESOLVED")
