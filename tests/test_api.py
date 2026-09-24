"""Integration tests for FastAPI webhook receiver and audit endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sentinelmcp"


@pytest.mark.asyncio
async def test_receive_alert_webhook():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "service_name": "edgeshield",
            "alert_name": "P99LatencyBreach",
            "severity": "SEV-2",
            "dry_run": True,
        }
        resp = await client.post("/api/v1/incidents/webhook", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["service_name"] == "edgeshield"
        assert data["status"] in ("MITIGATED", "RESOLVED")
        assert data["steps_count"] >= 4
        assert "INC-" in data["incident_id"]


@pytest.mark.asyncio
async def test_audit_trail_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger an incident to generate audit records
        payload = {
            "service_name": "edgeshield",
            "alert_name": "AuditVerificationTest",
            "dry_run": True,
        }
        await client.post("/api/v1/incidents/webhook", json=payload)

        resp = await client.get("/api/v1/audit?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert len(data["entries"]) > 0
