# SentinelMCP — Autonomous SRE & Self-Healing Incident Engine

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-2.x-black.svg?logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-K3s_Native-326CE5.svg?logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![SigNoz](https://img.shields.io/badge/SigNoz-OpenTelemetry_APM-F5A800.svg?logo=opentelemetry&logoColor=white)](https://signoz.io)
[![LLM](https://img.shields.io/badge/LLM_Tier-Google_Gemini_Flash_%7C_Groq-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**SentinelMCP** is an autonomous Site Reliability Engineering (SRE) agent designed to detect, investigate, and remediate microservice incidents on Kubernetes clusters. 

Powered by Anthropic's **Model Context Protocol (MCP)** and built for **Zero-Cost Operation** using free-tier LLM providers (**Google Gemini 2.0 / 1.5 Flash** and **Groq**) with a deterministic offline heuristic fallback, SentinelMCP bridges observability platforms (**SigNoz / ClickHouse**) and orchestration platforms (**Kubernetes / K3s**) into an autonomous closed-loop self-healing ecosystem.

---

## Architecture Overview

```
                      [ Incoming Alert / Chaos Event ]
                     (SigNoz Alertmanager / Webhook)
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   SentinelMCP SRE Orchestrator Core                         │
│                                                                             │
│  ┌─────────────────────────┐     ┌───────────────────────────────────────┐  │
│  │ Inbound Alert Webhook   │ ──> │ ReAct SRE Reasoning Loop              │  │
│  │ (FastAPI /healthz API)  │     │ • Google Gemini 2.0 Flash (Free Tier) │  │
│  └─────────────────────────┘     │ • Groq Cloud (Free Tier)              │  │
│                                  │ • Deterministic Heuristic Fallback    │  │
│                                  └───────────────────────────────────────┘  │
│                                                      │                      │
│                                                      ▼                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │            Model Context Protocol (MCP) SRE Tool Server               │  │
│  │                                                                       │  │
│  │   [query_signoz_telemetry]      [diagnose_k8s_pods]                   │  │
│  │   P50/P95/P99 latency & traces  Exit codes (137 OOMKilled), Pod phase │  │
│  │                                                                       │  │
│  │   [fetch_container_logs]        [execute_remediation_runbook]         │  │
│  │   Stdout/stderr failure traces  Guarded rollouts, scaling, fallback   │  │
│  │                                                                       │  │
│  │   [generate_postmortem_rca]     [audit_ledger]                        │  │
│  │   Executive Markdown reports    Immutable action history              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │             Blast-Radius Protection & Safety Guardrails               │  │
│  │  • Dry-Run Enforcement by Default (SENTINEL_DRY_RUN=true)             │  │
│  │  • Restart Rate Limiting: Max 3 restarts/hr per service               │  │
│  │  • Scaled Replica Ceilings: Min 1, Max 10 pods                        │  │
│  │  • Cooldown Period: 120s between mutating actions on same target      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────┬──────────────────┘
                        │                                  │
      Cluster Mutations ▼                                  ▼ Telemetry & Traces
┌───────────────────────────────┐                  ┌──────────────────────────┐
│  Kubernetes (K3s) Cluster     │                  │  SigNoz APM / ClickHouse │
│  • EdgeShield (API Gateway)   │                  │  • Distributed Traces    │
│  • DevATS (Job Ingestion)     │                  │  • Error Rate Spikes     │
│  • AMAE (Financial Ledger)    │                  │  • Container Metrics     │
└───────────────────────────────┘                  └──────────────────────────┘
```

---

## Key Features

1. **Standardized Model Context Protocol (MCP) Server:** Exposes all observability and cluster remediation tools as standard MCP JSON-RPC tools, making them universally usable by Claude Desktop, Cursor, Antigravity IDE, or any custom agent.
2. **$0 Operating Cost (Free-Tier Architecture):** Integrates directly with Google Gemini 2.0 / 1.5 Flash (15 RPM free tier) and Groq. Zero paid tokens required.
3. **Deterministic Heuristic Runbook Fallback:** Features an offline rule-based state machine that ensures 100% of unit tests, CI/CD pipelines, and local dev environments execute predictably with zero network latency or API keys.
4. **Non-Bypassable Safety Guardrails:** Prevents cluster destabilization with automatic dry-run verification, target cooldown windows, bounded replica ceilings, and restart rate limits.
5. **Trace-to-Log Correlation & Automated Post-Mortem:** Cross-correlates SigNoz distributed trace IDs with Kubernetes container exit codes (e.g. exit code 137 OOMKilled) and outputs formatted Markdown Root Cause Analysis (RCA) documents.

---

## MCP Tools Reference

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `query_signoz_telemetry` | `service_name`, `time_window_mins`, `min_status_code` | Queries SigNoz for latency percentiles (P50/P95/P99), error rates, and active error trace IDs. |
| `diagnose_k8s_pods` | `namespace`, `service_name`, `selector` | Inspects pod lifecycle states, restart counts, and container termination exit codes. |
| `fetch_container_logs` | `namespace`, `pod_name`, `tail_lines`, `previous` | Retrieves stdout/stderr logs from active or crashed previous container instances. |
| `execute_remediation_runbook` | `incident_id`, `action_type`, `target`, `params`, `dry_run` | Applies guarded remediation (restart, scale, flush_cache, enable_fallback) with diff previews. |
| `generate_postmortem_rca` | `incident_id`, `service_name`, `root_cause`, `timeline`, `actions_taken` | Produces an executive-ready Markdown Root Cause Analysis (RCA) Post-Mortem document. |

---

## Quickstart

### 1. Installation

```bash
cd /home/ubuntu/sentinelmcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Interactive CLI Investigation

Run an autonomous SRE investigation against a target microservice in safe Dry-Run mode:

```bash
python -m src.main cli --service edgeshield
```

To execute with live cluster mutations:
```bash
python -m src.main cli --service edgeshield --live
```

### 3. Run FastAPI Alert Webhook Server

```bash
python -m src.main serve --host 0.0.0.0 --port 8000
```

Verify health:
```bash
curl -s http://localhost:8000/healthz | jq
```

Dispatch simulated incident alert:
```bash
curl -X POST http://localhost:8000/api/v1/incidents/webhook \
  -H "Content-Type: application/json" \
  -d '{"service_name": "edgeshield", "alert_name": "HighErrorRateAlert", "severity": "SEV-2"}' | jq
```

Inspect audit ledger:
```bash
curl -s http://localhost:8000/api/v1/audit | jq
```

### 4. Connect to Claude Desktop / Cursor / Antigravity IDE

Configure SentinelMCP as an MCP server in your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sentinelmcp": {
      "command": "/home/ubuntu/sentinelmcp/.venv/bin/python",
      "args": ["-m", "src.main", "mcp-stdio"]
    }
  }
}
```

---

## Testing & Quality Assurance

Run the comprehensive test suite with coverage:

```bash
pytest --cov=src tests/
```

Test Results:
* **17/17 tests passing** (100% pass rate)
* Covers safety guardrail bounds, MCP tool contracts, ReAct reasoning, and FastAPI endpoints.

---

## Architecture Decision Records (ADRs)

* [ADR 0001: Model Context Protocol (MCP) for Autonomous SRE Tooling](docs/adr/0001-mcp-protocol-architecture.md)
* [ADR 0002: Zero-Cost Free-Tier LLM Architecture with Deterministic Fallback](docs/adr/0002-zero-cost-free-tier-llm-strategy.md)
* [ADR 0003: Remediation Safety Guardrails & Blast-Radius Protection](docs/adr/0003-remediation-safety-guardrails.md)

---

## License

MIT © [Gabriel Carneiro Jr.](https://github.com/gabrielcjr)
