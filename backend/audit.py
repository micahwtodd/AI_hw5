"""Append-preserving, redacted audit logging for agent runs."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .models import AgentName, AuditEvent

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AUDIT_PATH = ROOT / "output" / "audit_trail.json"
_LOCK = threading.Lock()
_SENSITIVE_KEYS = ("api_key", "apikey", "password", "secret", "token")


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def _known_secrets() -> list[str]:
    values = []
    for name in ("PORTKEY_API_KEY", "OPENAI_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            values.append(value)
    return values


def redact(value: Any, limit: int = 1_000) -> Any:
    """Remove configured credentials and truncate large audit values."""
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            key_text = str(key)
            if any(marker in key_text.casefold() for marker in _SENSITIVE_KEYS):
                cleaned[key_text] = "[REDACTED]"
            else:
                cleaned[key_text] = redact(item, limit)
        return cleaned
    if isinstance(value, (list, tuple)):
        return [redact(item, limit) for item in value]
    if hasattr(value, "model_dump"):
        return redact(value.model_dump(mode="json"), limit)
    if isinstance(value, str):
        text = value
        for secret in _known_secrets():
            text = text.replace(secret, "[REDACTED]")
        return text if len(text) <= limit else text[:limit] + "…"
    return value


def summarize(value: Any, limit: int = 500) -> str:
    cleaned = redact(value, limit)
    if isinstance(cleaned, str):
        text = cleaned
    else:
        text = json.dumps(cleaned, default=str, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "…"


class AuditTrail:
    """Preserve prior events and atomically append each new event."""

    def __init__(self, path: Path = DEFAULT_AUDIT_PATH) -> None:
        self.path = path
        self._steps: dict[tuple[str, AgentName], int] = {}

    def next_step(self, run_id: str, agent_name: AgentName) -> int:
        key = (run_id, agent_name)
        with _LOCK:
            step = self._steps.get(key, 0) + 1
            self._steps[key] = step
        return step

    def append(
        self,
        *,
        run_id: str,
        agent_name: AgentName,
        event_type: str,
        ticket_id: int | None = None,
        delegated_by: AgentName | None = None,
        delegated_to: AgentName | None = None,
        delegation_depth: int = 0,
        tool_name: str | None = None,
        tool_call_id: str | None = None,
        tool_arguments: dict[str, Any] | str | None = None,
        result_summary: str | None = None,
        status: str | None = None,
        stop_reason: str | None = None,
        duration_ms: int | None = None,
        usage: dict[str, Any] | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            timestamp=_timestamp(),
            run_id=run_id,
            event_id=str(uuid4()),
            agent_name=agent_name,
            event_type=event_type,
            loop_step=self.next_step(run_id, agent_name),
            ticket_id=ticket_id,
            delegated_by=delegated_by,
            delegated_to=delegated_to,
            delegation_depth=delegation_depth,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            tool_arguments=redact(tool_arguments),
            result_summary=summarize(result_summary) if result_summary else None,
            status=status,
            stop_reason=stop_reason,
            duration_ms=duration_ms,
            usage=redact(usage),
            error_type=error_type,
            error_message=summarize(error_message) if error_message else None,
        )
        self._write(event)
        return event

    def _write(self, event: AuditEvent) -> None:
        with _LOCK:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.is_file() and self.path.stat().st_size:
                try:
                    existing = json.loads(self.path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise RuntimeError(
                        "Audit trail is unreadable; refusing to overwrite prior evidence."
                    ) from exc
                if not isinstance(existing, list):
                    raise RuntimeError(
                        "Audit trail must be a JSON list; refusing to overwrite it."
                    )
            else:
                existing = []

            existing.append(event.model_dump(mode="json"))
            temporary = self.path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            temporary.replace(self.path)
