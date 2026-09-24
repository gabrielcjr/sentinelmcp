"""Pytest fixtures and configuration."""

import pytest
from src.safety.guardrails import default_guardrails
from src.safety.audit import audit_ledger


@pytest.fixture(autouse=True)
def reset_safety_and_audit():
    """Resets safety guardrail in-memory states and audit logs before every test."""
    default_guardrails.reset_state()
    audit_ledger.clear()
    yield
    default_guardrails.reset_state()
    audit_ledger.clear()
