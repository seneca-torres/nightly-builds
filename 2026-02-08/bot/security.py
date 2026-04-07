from __future__ import annotations

import base64
import hmac
import os
import struct
import time
from dataclasses import dataclass
from hashlib import sha256


class CallbackError(RuntimeError):
    pass


CALLBACK_PREFIX = "qrs:"
CALLBACK_VERSION = 1
_PAYLOAD_STRUCT = struct.Struct(">BHHI")  # v, template_idx, action_idx, expires_at
_SIG_LEN = 8  # bytes, truncated HMAC-SHA256


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii"))


def _hmac(secret: bytes, payload: bytes) -> bytes:
    return hmac.new(secret, payload, sha256).digest()


@dataclass(frozen=True)
class CallbackData:
    template_index: int
    action_index: int


def make_callback_data(
    *,
    secret: str,
    template_index: int,
    action_index: int,
    ttl_seconds: int,
    now: int | None = None,
) -> str:
    if template_index < 0 or template_index > 0xFFFF:
        raise ValueError("template_index out of range (0..65535)")
    if action_index < 0 or action_index > 0xFFFF:
        raise ValueError("action_index out of range (0..65535)")

    now = int(now or time.time())
    expires_at = now + max(60, int(ttl_seconds))

    payload = _PAYLOAD_STRUCT.pack(CALLBACK_VERSION, template_index, action_index, expires_at)
    sig = _hmac(secret.encode("utf-8"), payload)[:_SIG_LEN]
    return CALLBACK_PREFIX + _b64url_encode(payload + sig)


def parse_and_verify_callback_data(
    callback_data: str,
    *,
    secret: str,
    now: int | None = None,
) -> CallbackData:
    if not callback_data.startswith(CALLBACK_PREFIX):
        raise CallbackError("Bad callback prefix")

    token = callback_data.removeprefix(CALLBACK_PREFIX)
    raw = _b64url_decode(token)
    if len(raw) != _PAYLOAD_STRUCT.size + _SIG_LEN:
        raise CallbackError("Bad callback size")

    payload = raw[: _PAYLOAD_STRUCT.size]
    sig = raw[_PAYLOAD_STRUCT.size :]

    expected = _hmac(secret.encode("utf-8"), payload)[:_SIG_LEN]
    if not hmac.compare_digest(sig, expected):
        raise CallbackError("Bad callback signature")

    version, template_index, action_index, expires_at = _PAYLOAD_STRUCT.unpack(payload)
    if version != CALLBACK_VERSION:
        raise CallbackError("Unsupported callback version")

    now = int(now or time.time())
    if now > expires_at:
        raise CallbackError("Expired callback")

    return CallbackData(template_index=template_index, action_index=action_index)


def load_secret_from_env() -> str:
    secret = os.getenv("CALLBACK_SECRET", "")
    if not secret:
        raise CallbackError("Missing env var CALLBACK_SECRET")
    return secret

