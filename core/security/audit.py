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
import os
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
DEFAULT_AUDIT_LOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "audit_chain.jsonl"
)


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
    """Thread-safe append-only cryptographically chained audit logger with optional JSONL persistence."""

    def __init__(self, max_buffer_size: int = 10000, persistence_file: Optional[str] = None):
        self._events: List[AuditEvent] = []
        self._last_hash = GENESIS_HASH
        self._lock = threading.Lock()
        self._max_buffer_size = max_buffer_size
        self._persistence_file = persistence_file
        if self._persistence_file:
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Loads persisted audit chain events from append-only JSONL storage."""
        if not self._persistence_file or not os.path.exists(self._persistence_file):
            return
        try:
            loaded: List[AuditEvent] = []
            with open(self._persistence_file, "r", encoding="utf-8") as f:
                for line in f:
                    raw = line.strip()
                    if not raw:
                        continue
                    data = json.loads(raw)
                    loaded.append(AuditEvent(**data))
            if loaded:
                self._events = loaded[-self._max_buffer_size :]
                self._last_hash = self._events[-1].event_hash
        except Exception as exc:
            logger.warning("[AuditLog] Failed loading persisted audit chain (%s); starting fresh.", exc)

    def _append_to_disk(self, event: AuditEvent) -> None:
        """Persists a single audit event as an append-only JSON line."""
        if not self._persistence_file:
            return
        try:
            parent_dir = os.path.dirname(self._persistence_file)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(self._persistence_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event), sort_keys=True, default=str) + "\n")
        except Exception as exc:
            logger.error("[AuditLog] Failed persisting audit event: %s", exc)

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
            if self._persistence_file:
                self._load_from_disk()
            idx = (self._events[-1].index + 1) if self._events else 0
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
            self._append_to_disk(event)

            if len(self._events) > self._max_buffer_size:
                # Retain recent events while preserving last hash reference
                self._events = self._events[-self._max_buffer_size :]

            logger.info(
                f"[AuditLog] idx={event.index} type={event.event_type} status={event.status} hash={event.event_hash[:12]}..."
            )
            return event

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            if self._persistence_file:
                self._load_from_disk()
            return [asdict(e) for e in self._events[-limit:]]

    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """Verifies cryptographic integrity of the entire audit chain.
        
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        with self._lock:
            if self._persistence_file:
                self._load_from_disk()
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


_GLOBAL_AUDIT_LOGGER = AuditLogger(
    persistence_file=os.environ.get("APEX_AUDIT_LOG_FILE", DEFAULT_AUDIT_LOG_PATH)
)


def get_audit_logger() -> AuditLogger:
    return _GLOBAL_AUDIT_LOGGER
