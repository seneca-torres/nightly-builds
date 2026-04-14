from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event: str
    ts: str
    ok: bool
    actor_user_id: int | None
    actor_username: str | None
    chat_id: int | None
    chat_type: str | None
    callback_message_id: int | None
    template_id: str | None
    template_type: str | None
    action_id: str | None
    action_label: str | None
    detail: dict[str, Any]


class AuditLogger:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._lock = asyncio.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def write(self, *, event: str, ok: bool, detail: dict[str, Any], **fields: Any) -> None:
        record = AuditEvent(
            event=event,
            ts=self._now_iso(),
            ok=ok,
            actor_user_id=fields.get("actor_user_id"),
            actor_username=fields.get("actor_username"),
            chat_id=fields.get("chat_id"),
            chat_type=fields.get("chat_type"),
            callback_message_id=fields.get("callback_message_id"),
            template_id=fields.get("template_id"),
            template_type=fields.get("template_type"),
            action_id=fields.get("action_id"),
            action_label=fields.get("action_label"),
            detail=detail,
        )

        line = json.dumps(record.__dict__, ensure_ascii=False, separators=(",", ":")) + "\n"
        async with self._lock:
            # Open for each write to keep it robust across restarts/rotations.
            with self._path.open("a", encoding="utf-8") as f:
                f.write(line)


def parse_admin_user_ids(env: str | None) -> set[int]:
    if not env:
        return set()
    out: set[int] = set()
    for part in env.split(","):
        part = part.strip()
        if not part:
            continue
        out.add(int(part))
    return out
