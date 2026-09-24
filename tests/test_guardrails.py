"""Tests for Safety Guardrails and Blast-Radius Protection."""

import pytest
from src.safety.guardrails import GuardrailPolicy, SafetyVerificationError
from src.safety.audit import audit_ledger


def test_guardrail_scale_within_limits():
    policy = GuardrailPolicy(max_replicas_limit=5, min_replicas_limit=1, cooldown_seconds=0)
    result = policy.validate_action(
        incident_id="INC-1",
        action_type="scale",
        target="edgeshield",
        params={"replicas": 3},
        dry_run=True,
    )
    assert result is True


def test_guardrail_scale_exceeds_ceiling():
    policy = GuardrailPolicy(max_replicas_limit=5, min_replicas_limit=1, cooldown_seconds=0)
    with pytest.raises(SafetyVerificationError) as exc_info:
        policy.validate_action(
            incident_id="INC-2",
            action_type="scale",
            target="edgeshield",
            params={"replicas": 15},
            dry_run=True,
        )
    assert "exceeds maximum safe ceiling" in str(exc_info.value)


def test_guardrail_scale_below_minimum():
    policy = GuardrailPolicy(max_replicas_limit=5, min_replicas_limit=1, cooldown_seconds=0)
    with pytest.raises(SafetyVerificationError) as exc_info:
        policy.validate_action(
            incident_id="INC-3",
            action_type="scale",
            target="edgeshield",
            params={"replicas": 0},
            dry_run=True,
        )
    assert "below minimum limit" in str(exc_info.value)


def test_guardrail_restart_rate_limit():
    policy = GuardrailPolicy(max_restarts_per_hour=2, cooldown_seconds=0)
    
    # 1st live restart -> OK
    policy.validate_action("INC-4", "restart", "devats", {}, dry_run=False)
    # 2nd live restart -> OK
    policy.validate_action("INC-5", "restart", "devats", {}, dry_run=False)

    # 3rd restart -> Exceeds rate limit
    with pytest.raises(SafetyVerificationError) as exc_info:
        policy.validate_action("INC-6", "restart", "devats", {}, dry_run=False)
    assert "Restart rate-limit exceeded" in str(exc_info.value)


def test_guardrail_cooldown_window():
    policy = GuardrailPolicy(cooldown_seconds=60)
    policy.validate_action("INC-7", "restart", "amae", {}, dry_run=False)

    with pytest.raises(SafetyVerificationError) as exc_info:
        policy.validate_action("INC-8", "scale", "amae", {"replicas": 2}, dry_run=False)
    assert "is in cooldown" in str(exc_info.value)


def test_audit_ledger_recording():
    policy = GuardrailPolicy(cooldown_seconds=0)
    policy.validate_action("INC-9", "restart", "edgeshield", {}, dry_run=True)

    entries = audit_ledger.get_entries(target="edgeshield")
    assert len(entries) >= 1
    assert entries[-1].incident_id == "INC-9"
    assert entries[-1].action_type == "restart"
    assert entries[-1].allowed is True
