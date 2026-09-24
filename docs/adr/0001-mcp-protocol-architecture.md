# ADR 0001: Model Context Protocol (MCP) for Autonomous SRE Tooling

## Status
Accepted

## Context
Site Reliability Engineering (SRE) workflows require inspecting telemetry, querying cluster state, analyzing logs, and executing remediations. Historically, automated remediation scripts are tightly coupled, monolithic, and lack interoperability across different reasoning agents (e.g. Anthropic Claude, Cursor, Antigravity, or in-house LLMs).

Anthropic's **Model Context Protocol (MCP)** provides an open, standardized JSON-RPC 2.0 specification for exposing tools, resources, and prompt templates to AI clients.

## Decision
We decouple SentinelMCP's diagnostic and remediation capabilities into a standalone **Model Context Protocol (MCP) Server**.
1. All SRE capabilities (`query_signoz_telemetry`, `diagnose_k8s_pods`, `fetch_container_logs`, `execute_remediation_runbook`, `generate_postmortem_rca`) are authored as pure MCP tool endpoints with strict JSON Schema parameter validation.
2. The MCP Server operates over standard transport mechanisms (stdio and Server-Sent Events / HTTP), allowing direct integration with both our autonomous internal agent orchestrator and external developer tools (Claude Desktop, Antigravity IDE, Cursor).
3. The server core has zero dependency on LLM tokens; tool execution is strictly deterministic and observable.

## Consequences
### Positive
* **Client-Agnostic Interoperability:** Any MCP-compliant client can leverage SentinelMCP's cluster diagnostics and runbooks.
* **Separation of Concerns:** The MCP server strictly defines *what actions are possible* and validates parameters, while the orchestrator focuses on *reasoning*.
* **Local Developer Ergonomics:** Developers can debug incidents interactively inside their IDE via MCP without triggering automated scripts.

### Negative / Trade-offs
* Requires adhering to MCP JSON-RPC protocol contracts and schemas, which introduces a layer of serialization overhead compared to in-process function calls.
