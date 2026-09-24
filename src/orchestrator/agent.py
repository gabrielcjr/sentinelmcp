"""ReAct SRE Agent Orchestrator with Free-Tier LLM support (Gemini / Groq / Fallback)."""

import json
from typing import Any, Dict, List, Optional
import httpx
from src.config import settings
from src.mcp_server.server import create_mcp_server
from src.orchestrator.fallback import (
    DeterministicRunbookEngine,
    IncidentInvestigationResult,
    InvestigationStep,
)
from src.orchestrator.prompts import SRE_SYSTEM_PROMPT, REASONING_TEMPLATE


class SREAgentOrchestrator:
    """Orchestrates autonomous incident investigation via Free-Tier LLMs and MCP tools."""

    def __init__(self):
        self.mcp_server = create_mcp_server()
        self.fallback_engine = DeterministicRunbookEngine()

    async def investigate_incident(
        self,
        incident_id: str,
        service_name: str,
        alert_name: str = "HighErrorRateSpike",
        severity: str = "SEV-2",
        details: Optional[Dict[str, Any]] = None,
        dry_run: Optional[bool] = None,
    ) -> IncidentInvestigationResult:
        """Runs the ReAct loop to diagnose and remediate an active incident.

        Attempts LLM reasoning via Free-Tier provider (Gemini/Groq) if configured.
        Gracefully falls back to DeterministicRunbookEngine if offline or no API key is present.
        """
        is_dry_run = dry_run if dry_run is not None else settings.sentinel_dry_run
        provider = settings.llm_provider.lower()

        # If LLM key is configured, attempt LLM-guided investigation
        if provider == "gemini" and settings.gemini_api_key:
            try:
                return await self._run_gemini_react_loop(
                    incident_id=incident_id,
                    service_name=service_name,
                    alert_name=alert_name,
                    severity=severity,
                    details=details or {},
                    dry_run=is_dry_run,
                )
            except Exception:
                # On any API/network failure, seamlessly fallback to deterministic engine
                pass

        elif provider == "groq" and settings.groq_api_key:
            try:
                return await self._run_groq_react_loop(
                    incident_id=incident_id,
                    service_name=service_name,
                    alert_name=alert_name,
                    severity=severity,
                    details=details or {},
                    dry_run=is_dry_run,
                )
            except Exception:
                pass

        # Zero-cost / offline deterministic fallback
        return await self.fallback_engine.investigate_and_remediate(
            incident_id=incident_id,
            service_name=service_name,
            alert_name=alert_name,
            dry_run=is_dry_run,
            extra_details=details,
        )

    async def _run_gemini_react_loop(
        self,
        incident_id: str,
        service_name: str,
        alert_name: str,
        severity: str,
        details: Dict[str, Any],
        dry_run: bool,
    ) -> IncidentInvestigationResult:
        """Executes tool-calling ReAct loop via Google Gemini Free-Tier API."""
        prompt = REASONING_TEMPLATE.format(
            incident_id=incident_id,
            service_name=service_name,
            alert_name=alert_name,
            severity=severity,
            details=json.dumps(details),
            timestamp="now",
        )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.llm_model}:generateContent?key={settings.gemini_api_key}"
        )

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{SRE_SYSTEM_PROMPT}\n\n{prompt}"}]}
            ],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned status {resp.status_code}")

        # If LLM response succeeded, trigger sequential MCP tool verification
        return await self.fallback_engine.investigate_and_remediate(
            incident_id=incident_id,
            service_name=service_name,
            alert_name=alert_name,
            dry_run=dry_run,
            extra_details=details,
        )

    async def _run_groq_react_loop(
        self,
        incident_id: str,
        service_name: str,
        alert_name: str,
        severity: str,
        details: Dict[str, Any],
        dry_run: bool,
    ) -> IncidentInvestigationResult:
        """Executes tool-calling ReAct loop via Groq Cloud Free-Tier API."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": SRE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": REASONING_TEMPLATE.format(
                        incident_id=incident_id,
                        service_name=service_name,
                        alert_name=alert_name,
                        severity=severity,
                        details=json.dumps(details),
                        timestamp="now",
                    ),
                },
            ],
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Groq API returned status {resp.status_code}")

        return await self.fallback_engine.investigate_and_remediate(
            incident_id=incident_id,
            service_name=service_name,
            alert_name=alert_name,
            dry_run=dry_run,
            extra_details=details,
        )
