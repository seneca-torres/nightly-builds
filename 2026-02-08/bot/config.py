from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class SecurityConfig:
    callback_secret: str
    callback_ttl_seconds: int = 900


@dataclass(frozen=True)
class AuditConfig:
    log_path: str = "logs/audit.jsonl"


@dataclass(frozen=True)
class AppConfig:
    security: SecurityConfig
    audit: AuditConfig
    templates: list[dict[str, Any]]


def _coerce_int(value: Any, *, field: str) -> int:
    try:
        return int(value)
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"Invalid int for {field!r}: {value!r}") from exc


def load_config(path: str | Path, *, callback_secret: str | None = None) -> AppConfig:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    templates = raw.get("templates")
    if not isinstance(templates, list) or not templates:
        raise ConfigError("Config must include a non-empty 'templates' list")

    secret = callback_secret or os.getenv("CALLBACK_SECRET", "")
    if not secret:
        raise ConfigError(
            "Missing CALLBACK_SECRET. Set env var CALLBACK_SECRET (recommended) "
            "or pass callback_secret to load_config()."
        )

    ttl = _coerce_int(os.getenv("CALLBACK_TTL_SECONDS", 900), field="CALLBACK_TTL_SECONDS")
    ttl = max(60, ttl)

    audit_path = os.getenv("AUDIT_LOG_PATH", "logs/audit.jsonl")
    return AppConfig(
        security=SecurityConfig(callback_secret=secret, callback_ttl_seconds=ttl),
        audit=AuditConfig(log_path=audit_path),
        templates=templates,
    )

