# ADR 0002: Zero-Cost Free-Tier LLM Architecture with Deterministic Fallback

## Status
Accepted

## Context
Deploying autonomous SRE agents in staging and personal portfolio environments often faces cost friction due to recurring paid LLM API token consumption (OpenAI, Anthropic Claude). Furthermore, continuous integration (CI) test suites and offline environments cannot rely on paid, network-bound cloud endpoints for predictable execution.

## Decision
We adopt a multi-tier LLM architecture with **Zero Token Cost** as a primary design constraint:
1. **Primary Reasoning Engine:** Free-tier Cloud LLM providers:
   - **Google Gemini 2.0 / 1.5 Flash:** Provides high-throughput structured tool calling with 15 RPM free tier and a 1M+ token context window.
   - **Groq Cloud API:** Provides ultra-low latency inference (Llama 3.3 70B / Qwen 2.5) with a generous free tier.
2. **Deterministic Heuristic Runbook Fallback (Offline Mode):**
   - Implements a rule-based finite state machine (FSM) that processes alert signatures (e.g., `OOMKilled`, `CrashLoopBackOff`, `HighP99Latency`) and invokes the identical sequence of MCP tools without initiating external LLM API calls.
   - Used for all automated unit tests, CI/CD test runs, and emergency offline remediation.

## Consequences
### Positive
* **Zero Infrastructure Operating Cost:** The entire system runs in production at $0 token expense.
* **100% Deterministic CI/CD Testing:** Test suites validate tool calling contracts and safety guardrails reliably in offline environments.
* **Provider Portability:** Standardized tool definitions allow switching between Gemini, Groq, local Ollama, or deterministic fallback transparently.

### Negative / Trade-offs
* Free-tier APIs have rate limits (e.g., 15 RPM on Gemini Flash); rate-limit backoff and jitter must be handled gracefully.
