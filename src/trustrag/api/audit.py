"""Append-only, tamper-evident SHA-256 hash-chained audit logging store."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import IO

from trustrag.api.schemas import AuditQueryResponse, AuditRecordView

try:
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback
    _fcntl = None  # type: ignore[assignment]

LOGGER = logging.getLogger(__name__)


@contextmanager
def _advisory_file_lock(fh: IO[str]) -> Iterator[None]:
    """Acquire an exclusive OS file lock when supported, warning explicitly otherwise."""
    if _fcntl is not None:
        _fcntl.flock(fh.fileno(), _fcntl.LOCK_EX)
        try:
            yield
        finally:
            _fcntl.flock(fh.fileno(), _fcntl.LOCK_UN)
    else:  # pragma: no cover
        LOGGER.warning("fcntl unavailable on this platform; multi-process audit locking is disabled")
        yield

_SECRET_PATTERN = re.compile(
    r"(?i)(bearer\s+[a-z0-9\-._~+/]+=*|sk-[a-z0-9]{12,}|api[_-]?key\s*[:=]\s*['\"]?[^\s'\"]+)"
)


def _redact_text(text: str, *, max_len: int = 400) -> str:
    cleaned = _SECRET_PATTERN.sub("[REDACTED]", text or "")
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > max_len:
        return cleaned[: max_len - 3] + "..."
    return cleaned


class AuditLogStore:
    """Thread-safe append-only audit store with SHA-256 hash chain verification."""

    def __init__(
        self,
        log_path: str | Path | None = None,
        *,
        max_memory_records: int = 2000,
    ) -> None:
        self._lock = threading.RLock()
        self._log_path = Path(log_path) if log_path is not None else None
        self._records: deque[AuditRecordView] = deque(maxlen=max_memory_records)
        self._seq = 0
        self._last_hash = "GENESIS"

        if self._log_path is not None:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            if self._log_path.exists():
                self._load_existing()

    @staticmethod
    def _compute_entry_hash(
        *,
        seq: int,
        timestamp: str,
        request_id: str,
        event_category: str,
        component: str,
        decision: str,
        outcome: str,
        explanation: str,
        evidence_refs: list[str],
        prev_hash: str,
    ) -> str:
        payload = json.dumps(
            {
                "seq": seq,
                "timestamp": timestamp,
                "request_id": request_id,
                "event_category": event_category,
                "component": component,
                "decision": decision,
                "outcome": outcome,
                "explanation": explanation,
                "evidence_refs": evidence_refs,
                "prev_hash": prev_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load_existing(self) -> None:
        assert self._log_path is not None
        with self._log_path.open("r", encoding="utf-8") as fh, _advisory_file_lock(fh):
            for line in fh:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    rec = AuditRecordView.model_validate_json(raw)
                except Exception:
                    LOGGER.warning("Skipping malformed/interrupted audit log line during load")
                    continue
                self._records.append(rec)
                self._seq = rec.seq
                self._last_hash = rec.entry_hash

    def _sync_tail_locked(self, fh: IO[str]) -> None:
        """Sync in-memory seq/last_hash with any records appended by another process."""
        fh.seek(0)
        for line in fh:
            raw = line.strip()
            if not raw:
                continue
            try:
                rec = AuditRecordView.model_validate_json(raw)
            except Exception:
                continue
            if rec.seq > self._seq:
                self._records.append(rec)
                self._seq = rec.seq
                self._last_hash = rec.entry_hash

    def record(
        self,
        *,
        request_id: str,
        event_category: str,
        component: str,
        decision: str,
        outcome: str,
        explanation: str = "",
        evidence_refs: list[str] | None = None,
    ) -> AuditRecordView:
        """Append a redacted, hash-chained audit record (thread- and multi-process-safe)."""
        with self._lock:
            ts = datetime.now(UTC).isoformat()
            refs = [str(r)[:128] for r in (evidence_refs or [])[:20]]
            clean_exp = _redact_text(explanation)

            if self._log_path is not None:
                with self._log_path.open("a+", encoding="utf-8") as fh, _advisory_file_lock(fh):
                    self._sync_tail_locked(fh)
                    self._seq += 1
                    entry_hash = self._compute_entry_hash(
                        seq=self._seq,
                        timestamp=ts,
                        request_id=request_id,
                        event_category=event_category,
                        component=component,
                        decision=decision,
                        outcome=outcome,
                        explanation=clean_exp,
                        evidence_refs=refs,
                        prev_hash=self._last_hash,
                    )
                    entry = AuditRecordView(
                        seq=self._seq,
                        timestamp=ts,
                        request_id=request_id,
                        event_category=event_category,
                        component=component,
                        decision=decision,
                        outcome=outcome,
                        explanation=clean_exp,
                        evidence_refs=refs,
                        entry_hash=entry_hash,
                        prev_hash=self._last_hash,
                    )
                    fh.seek(0, os.SEEK_END)
                    fh.write(entry.model_dump_json() + "\n")
                    fh.flush()
                    os.fsync(fh.fileno())
                    self._last_hash = entry_hash
                    self._records.append(entry)
                    return entry

            self._seq += 1
            entry_hash = self._compute_entry_hash(
                seq=self._seq,
                timestamp=ts,
                request_id=request_id,
                event_category=event_category,
                component=component,
                decision=decision,
                outcome=outcome,
                explanation=clean_exp,
                evidence_refs=refs,
                prev_hash=self._last_hash,
            )
            entry = AuditRecordView(
                seq=self._seq,
                timestamp=ts,
                request_id=request_id,
                event_category=event_category,
                component=component,
                decision=decision,
                outcome=outcome,
                explanation=clean_exp,
                evidence_refs=refs,
                entry_hash=entry_hash,
                prev_hash=self._last_hash,
            )
            self._last_hash = entry_hash
            self._records.append(entry)
            return entry

    def verify_chain(self) -> bool:
        """Verify SHA-256 chain consistency across retained records."""
        with self._lock:
            if not self._records:
                return True
            prev = self._records[0].prev_hash
            for rec in self._records:
                if rec.prev_hash != prev:
                    return False
                expected = self._compute_entry_hash(
                    seq=rec.seq,
                    timestamp=rec.timestamp,
                    request_id=rec.request_id,
                    event_category=rec.event_category,
                    component=rec.component,
                    decision=rec.decision,
                    outcome=rec.outcome,
                    explanation=rec.explanation,
                    evidence_refs=rec.evidence_refs,
                    prev_hash=rec.prev_hash,
                )
                if rec.entry_hash != expected:
                    return False
                prev = rec.entry_hash
            return True

    def query(
        self,
        *,
        event_type: str | None = None,
        component: str | None = None,
        request_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AuditQueryResponse:
        """Return newest-first filtered and paginated audit records."""
        with self._lock:
            items = list(self._records)
            chain_ok = self.verify_chain()

        if event_type:
            et = event_type.strip().lower()
            items = [r for r in items if r.event_category.lower() == et]
        if component:
            comp = component.strip().lower()
            items = [r for r in items if r.component.lower() == comp]
        if request_id:
            rid = request_id.strip()
            items = [r for r in items if rid in r.request_id]
        if since:
            items = [r for r in items if r.timestamp >= since]
        if until:
            items = [r for r in items if r.timestamp <= until]

        items.reverse()
        total = len(items)
        safe_page = max(1, page)
        safe_size = max(1, min(200, page_size))
        start = (safe_page - 1) * safe_size
        end = start + safe_size
        return AuditQueryResponse(
            total=total,
            page=safe_page,
            page_size=safe_size,
            chain_valid=chain_ok,
            items=items[start:end],
        )
