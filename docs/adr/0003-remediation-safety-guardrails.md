# ADR 0003: Remediation Safety Guardrails & Blast-Radius Protection

## Status
Accepted

## Context
Granting an AI agent write permissions to a Kubernetes cluster carries catastrophic failure risks if the agent hallucinates or enters an unconstrained remediation loop (e.g., repeatedly restarting a database or scaling replicas beyond cluster node capacity).

## Decision
We enforce a hard, non-bypassable **Safety Guardrail Engine** at the tool execution boundary:
1. **Dry-Run by Default:** The environment variable `SENTINEL_DRY_RUN=true` is the default. In dry-run mode, remediation commands compute Kubernetes diffs and expected impacts without applying cluster mutations.
2. **Rate Limits & Cooldowns:**
   - **Deployment Restarts:** Capped at a maximum of `MAX_RESTARTS_PER_HOUR` (default: 3) per service.
   - **Horizontal Scaling:** Clamped strictly between `MIN_REPLICAS_LIMIT` (1) and `MAX_REPLICAS_LIMIT` (10).
   - **Remediation Cooldown:** Minimum 120 seconds between mutating actions on the same workload.
3. **Structured Audit Ledger:**
   - Every mutation attempt (both simulated and live) generates an immutable structured audit log recording the incident ID, initiator, action, diff, and safety policy verdict.

## Consequences
### Positive
* **Zero Accidental Outages:** Prevents cluster destabilization from agent hallucination or cascading failure loops.
* **Audit Compliance:** Full traceability of all autonomous actions taken on the cluster.
* **Safe Sandbox Testing:** Developers and recruiters can trigger live chaos scenarios safely in Dry-Run mode.

### Negative / Trade-offs
* Urgent multi-step remediations might encounter rate limits if an incident requires rapid sequential adjustments; requires manual administrative override capability.
