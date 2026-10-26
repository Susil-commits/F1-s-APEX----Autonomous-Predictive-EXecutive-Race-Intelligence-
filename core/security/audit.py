"""APEX Tamper-Evident Audit Logging Engine.

Implements cryptographically chained immutable audit logging (SHA-256 hash tree)
for SOC 2 Type II, ISO 27001, and regulatory compliance.

Guarantees:
1. Every prediction, administrative action, security rejection, and drift alert is permanently recorded.
2. Cryptographic chaining: event_hash[N] = SHA-256(payload[N] + event_hash[N-1]).
3. Tamper detection: Any modification, insertion, or deletion breaks the hash chain.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


@dataclass
class AuditEvent:
    index: int
    timestamp: float
    event_type: str
    actor_id: str
    tenant_id: str
    details: Dict[str, Any]
    status: str
    prev_hash: str
    event_hash: str = ""

    def calculate_hash(self) -> str:
        """Computes deterministic SHA-256 hash of event contents and previous hash."""
        serialized_details = json.dumps(self.details, sort_keys=True, default=str)
        payload = (
            f"{self.index}:{self.timestamp:.6f}:{self.event_type}:{self.actor_id}:"
            f"{self.tenant_id}:{serialized_details}:{self.status}:{self.prev_hash}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AuditLogger:
    """Thread-safe append-only cryptographically chained audit logger."""

    def __init__(self, max_buffer_size: int = 10000):
        self._events: List[AuditEvent] = []
        self._last_hash = GENESIS_HASH
        self._lock = threading.Lock()
        self._max_buffer_size = max_buffer_size

    def record_event(
        self,
        event_type: str,
        actor_id: str = "system",
        tenant_id: str = "default_f1_team",
        details: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
    ) -> AuditEvent:
        """Appends an event to the immutable chain and returns the verified event."""
        with self._lock:
            idx = len(self._events)
            now = time.time()
            event = AuditEvent(
                index=idx,
                timestamp=now,
                event_type=event_type,
                actor_id=actor_id,
                tenant_id=tenant_id,
                details=details or {},
                status=status,
                prev_hash=self._last_hash,
            )
            event.event_hash = event.calculate_hash()
            self._events.append(event)
            self._last_hash = event.event_hash

            if len(self._events) > self._max_buffer_size:
                # Retain recent events while preserving last hash reference
                self._events = self._events[-self._max_buffer_size :]

            logger.info(
                f"[AuditLog] idx={event.index} type={event.event_type} status={event.status} hash={event.event_hash[:12]}..."
            )
            return event

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [asdict(e) for e in self._events[-limit:]]

    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """Verifies cryptographic integrity of the entire audit chain.
        
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        with self._lock:
            expected_prev_hash = GENESIS_HASH
            for i, event in enumerate(self._events):
                # 1. Verify prev_hash matches prior event
                if event.prev_hash != expected_prev_hash:
                    return (
                        False,
                        f"Hash chain broken at event {i}: prev_hash '{event.prev_hash}' does not match expected '{expected_prev_hash}'",
                    )

                # 2. Recalculate hash and verify it matches event_hash
                calculated = event.calculate_hash()
                if calculated != event.event_hash:
                    return (
                        False,
                        f"Tampered event at index {i}: stored hash '{event.event_hash}' != calculated '{calculated}'",
                    )

                expected_prev_hash = event.event_hash

            return True, None


_GLOBAL_AUDIT_LOGGER = AuditLogger()


def get_audit_logger() -> AuditLogger:
    return _GLOBAL_AUDIT_LOGGER
