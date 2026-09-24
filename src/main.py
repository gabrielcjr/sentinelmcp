"""SentinelMCP Main Entrypoint: FastAPI Webhook Receiver, MCP Server & CLI Runner."""

import argparse
import asyncio
import sys
import uuid
from typing import Any, Dict, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from src.config import settings
from src.orchestrator.agent import SREAgentOrchestrator
from src.safety.audit import audit_ledger


# -----------------------------------------------------------------------------
# FastAPI Application & Webhook Models
# -----------------------------------------------------------------------------
app = FastAPI(
    title="SentinelMCP - Autonomous SRE Agent",
    description="Incident webhook receiver and MCP-based self-healing orchestrator",
    version="0.1.0",
)

console = Console()
orchestrator = SREAgentOrchestrator()


class AlertWebhookPayload(BaseModel):
    """SigNoz / Prometheus Alertmanager inbound webhook schema."""
    service_name: str = Field(..., description="Target service (e.g. 'edgeshield')")
    alert_name: str = Field(default="HighErrorRateAlert")
    severity: str = Field(default="SEV-2")
    details: Dict[str, Any] = Field(default_factory=dict)
    dry_run: Optional[bool] = Field(default=None)


class IncidentTriggerResponse(BaseModel):
    """Response returned upon incident processing."""
    incident_id: str
    service_name: str
    status: str
    root_cause: str
    engine: str
    steps_count: int


@app.get("/healthz")
async def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    return {
        "status": "healthy",
        "service": "sentinelmcp",
        "version": "0.1.0",
        "dry_run": settings.sentinel_dry_run,
        "llm_provider": settings.llm_provider,
    }


@app.post("/api/v1/incidents/webhook", response_model=IncidentTriggerResponse)
async def receive_alert_webhook(payload: AlertWebhookPayload):
    """Receives inbound alert webhooks from SigNoz, Prometheus, or manual triggers."""
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

    res = await orchestrator.investigate_incident(
        incident_id=incident_id,
        service_name=payload.service_name,
        alert_name=payload.alert_name,
        severity=payload.severity,
        details=payload.details,
        dry_run=payload.dry_run,
    )

    return IncidentTriggerResponse(
        incident_id=res.incident_id,
        service_name=res.service_name,
        status=res.status,
        root_cause=res.root_cause,
        engine=res.engine,
        steps_count=len(res.steps),
    )


@app.get("/api/v1/audit")
async def get_audit_trail(limit: int = 50):
    """Retrieves recent actions recorded in the immutable audit ledger."""
    return {"entries": [e.model_dump() for e in audit_ledger.get_entries(limit=limit)]}


# -----------------------------------------------------------------------------
# Rich Terminal CLI Runner
# -----------------------------------------------------------------------------
async def run_cli_investigation(service: str, alert: str, live: bool):
    """Executes an interactive SRE investigation with Rich terminal formatting."""
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    dry_run = not live

    console.print(
        Panel(
            f"[bold cyan]SentinelMCP Autonomous SRE Agent[/bold cyan]\n"
            f"[yellow]Incident ID:[/yellow] {incident_id} | [yellow]Target:[/yellow] {service} | "
            f"[yellow]Mode:[/yellow] {'[red]LIVE MUTATION[/red]' if live else '[green]DRY-RUN (SAFE)[/green]'}",
            title="⚡ SRE INVESTIGATION TRIGGERED",
            border_style="cyan",
        )
    )

    with console.status("[bold green]Executing ReAct SRE Loop via Model Context Protocol..."):
        res = await orchestrator.investigate_incident(
            incident_id=incident_id,
            service_name=service,
            alert_name=alert,
            dry_run=dry_run,
        )

    # Display steps table
    table = Table(title="Executed Investigation & Remediation Steps", border_style="blue")
    table.add_column("Step", style="dim", width=6)
    table.add_column("Action / Tool", style="cyan")
    table.add_column("Agent Reasoning / Verdict", style="white")

    for s in res.steps:
        table.add_row(str(s.step_number), s.action_name, s.thought)

    console.print(table)

    # Display RCA Post-Mortem summary
    console.print(
        Panel(
            f"[bold white]{res.root_cause}[/bold white]\n\n"
            f"[dim]Status: [bold green]{res.status}[/bold green] | Engine: {res.engine}[/dim]",
            title="🎯 ROOT CAUSE ANALYSIS (RCA)",
            border_style="green",
        )
    )

    pm = res.postmortem.get("markdown_content")
    if pm:
        console.print("\n[bold yellow]Generated Post-Mortem Document Preview:[/bold yellow]\n")
        console.print(pm[:600] + "\n...[truncated]...")


def main():
    """CLI parser entrypoint."""
    parser = argparse.ArgumentParser(description="SentinelMCP SRE Autonomous Agent")
    subparsers = parser.add_subparsers(dest="command")

    # Command: cli
    cli_parser = subparsers.add_parser("cli", help="Run interactive CLI investigation")
    cli_parser.add_argument("--service", default="edgeshield", help="Target microservice name")
    cli_parser.add_argument("--alert", default="HighErrorRateAlert", help="Alert name")
    cli_parser.add_argument("--live", action="store_true", help="Execute live mutations (disables dry-run)")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Run FastAPI Webhook Server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    serve_parser.add_argument("--port", type=int, default=8000, help="Bind port")

    # Command: mcp-stdio
    subparsers.add_parser("mcp-stdio", help="Run as stdio MCP server for Claude/Cursor/IDE")

    args = parser.parse_args()

    if args.command == "cli" or not args.command:
        svc = getattr(args, "service", "edgeshield")
        alert = getattr(args, "alert", "HighErrorRateAlert")
        live = getattr(args, "live", False)
        asyncio.run(run_cli_investigation(svc, alert, live))

    elif args.command == "serve":
        import uvicorn
        uvicorn.run("src.main:app", host=args.host, port=args.port, reload=False)

    elif args.command == "mcp-stdio":
        from src.mcp_server.server import create_mcp_server
        srv = create_mcp_server()
        asyncio.run(srv.run_stdio_async())


if __name__ == "__main__":
    main()
