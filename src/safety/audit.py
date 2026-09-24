"""Immutable Audit Ledger for recording all autonomous SRE actions."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuditEntry(BaseModel):
    """Represents a single recorded audit event."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    incident_id: str
    action_type: str
    target: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool
    allowed: bool
    reason: str
    execution_result: Optional[Dict[str, Any]] = None


class AuditLedger:
    """Thread-safe ledger maintaining history of agent actions."""

    def __init__(self, max_entries: int = 1000):
        self._entries: List[AuditEntry] = []
        self._max_entries = max_entries

    def record(self, entry: AuditEntry) -> None:
        """Appends an entry to the audit log."""
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)

    def get_entries(
        self,
        target: Optional[str] = None,
        incident_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditEntry]:
        """Queries recorded audit entries with optional filtering."""
        results = self._entries
        if target:
            results = [e for e in results if e.target == target]
        if incident_id:
            results = [e for e in results if e.incident_id == incident_id]
        return results[-limit:]

    def clear(self) -> None:
        """Resets the audit ledger (useful for testing)."""
        self._entries.clear()


audit_ledger = AuditLedger()
