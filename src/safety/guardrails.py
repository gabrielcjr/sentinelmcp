"""Blast-radius protection and remediation safety guardrails."""

import time
from typing import Any, Dict, List
from src.config import settings
from src.safety.audit import AuditEntry, audit_ledger


class SafetyVerificationError(Exception):
    """Raised when a proposed remediation violates safety policies."""
    pass


class GuardrailPolicy:
    """Enforces safety constraints and rate-limits on autonomous mutations."""

    def __init__(
        self,
        max_restarts_per_hour: int = settings.max_restarts_per_hour,
        max_replicas_limit: int = settings.max_replicas_limit,
        min_replicas_limit: int = settings.min_replicas_limit,
        cooldown_seconds: int = settings.remediation_cooldown_seconds,
    ):
        self.max_restarts_per_hour = max_restarts_per_hour
        self.max_replicas_limit = max_replicas_limit
        self.min_replicas_limit = min_replicas_limit
        self.cooldown_seconds = cooldown_seconds

        # In-memory tracking of recent actions per target: target -> list of timestamps
        self._restart_history: Dict[str, List[float]] = {}
        self._last_action_timestamp: Dict[str, float] = {}

    def validate_action(
        self,
        incident_id: str,
        action_type: str,
        target: str,
        params: Dict[str, Any],
        dry_run: bool = True,
    ) -> bool:
        """Validates a proposed remediation action against safety policies.

        Raises:
            SafetyVerificationError: If the action violates policy and cannot proceed.

        Returns:
            bool: True if permitted.
        """
        now = time.time()

        # 1. Check target-level cooldown
        last_action = self._last_action_timestamp.get(target)
        if last_action and (now - last_action < self.cooldown_seconds):
            remaining = int(self.cooldown_seconds - (now - last_action))
            reason = f"Target '{target}' is in cooldown. Please wait {remaining}s."
            audit_ledger.record(
                AuditEntry(
                    incident_id=incident_id,
                    action_type=action_type,
                    target=target,
                    parameters=params,
                    dry_run=dry_run,
                    allowed=False,
                    reason=reason,
                )
            )
            raise SafetyVerificationError(reason)

        # 2. Check action-specific constraints
        if action_type == "restart":
            # Clean history older than 3600 seconds
            history = self._restart_history.get(target, [])
            valid_history = [t for t in history if (now - t) < 3600]
            self._restart_history[target] = valid_history

            if len(valid_history) >= self.max_restarts_per_hour:
                reason = (
                    f"Restart rate-limit exceeded for '{target}': "
                    f"{len(valid_history)}/{self.max_restarts_per_hour} restarts in the past hour."
                )
                audit_ledger.record(
                    AuditEntry(
                        incident_id=incident_id,
                        action_type=action_type,
                        target=target,
                        parameters=params,
                        dry_run=dry_run,
                        allowed=False,
                        reason=reason,
                    )
                )
                raise SafetyVerificationError(reason)

        elif action_type == "scale":
            replicas = params.get("replicas")
            if replicas is None or not isinstance(replicas, int):
                reason = "Scale action requires an integer 'replicas' parameter."
                raise SafetyVerificationError(reason)

            if replicas < self.min_replicas_limit:
                reason = (
                    f"Requested replicas ({replicas}) is below minimum limit ({self.min_replicas_limit})."
                )
                audit_ledger.record(
                    AuditEntry(
                        incident_id=incident_id,
                        action_type=action_type,
                        target=target,
                        parameters=params,
                        dry_run=dry_run,
                        allowed=False,
                        reason=reason,
                    )
                )
                raise SafetyVerificationError(reason)

            if replicas > self.max_replicas_limit:
                reason = (
                    f"Requested replicas ({replicas}) exceeds maximum safe ceiling ({self.max_replicas_limit})."
                )
                audit_ledger.record(
                    AuditEntry(
                        incident_id=incident_id,
                        action_type=action_type,
                        target=target,
                        parameters=params,
                        dry_run=dry_run,
                        allowed=False,
                        reason=reason,
                    )
                )
                raise SafetyVerificationError(reason)

        elif action_type in ("flush_cache", "drain_traffic", "enable_fallback"):
            # Allowed standard operational runbook actions
            pass
        else:
            reason = f"Unknown or unapproved remediation action_type: '{action_type}'."
            raise SafetyVerificationError(reason)

        # 3. If live execution (not dry-run), record state change
        if not dry_run:
            self._last_action_timestamp[target] = now
            if action_type == "restart":
                self._restart_history.setdefault(target, []).append(now)

        audit_ledger.record(
            AuditEntry(
                incident_id=incident_id,
                action_type=action_type,
                target=target,
                parameters=params,
                dry_run=dry_run,
                allowed=True,
                reason="Passed all guardrail validation checks.",
            )
        )
        return True

    def reset_state(self) -> None:
        """Clears in-memory history (for test isolation)."""
        self._restart_history.clear()
        self._last_action_timestamp.clear()


default_guardrails = GuardrailPolicy()
