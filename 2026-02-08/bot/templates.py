from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .security import make_callback_data


class TemplateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Action:
    id: str
    label: str
    message: str


@dataclass(frozen=True)
class Template:
    id: str
    type: str
    label: str
    actions: list[Action]


def _require_str(obj: dict[str, Any], key: str) -> str:
    v = obj.get(key)
    if not isinstance(v, str) or not v.strip():
        raise TemplateError(f"Template field {key!r} must be a non-empty string")
    return v


def _build_standard(t: dict[str, Any]) -> Template:
    tid = _require_str(t, "id")
    label = _require_str(t, "label")
    msg = _require_str(t, "message")
    return Template(
        id=tid,
        type="standard",
        label=label,
        actions=[Action(id="send", label=label, message=msg)],
    )


def _build_approve_reject(t: dict[str, Any]) -> Template:
    tid = _require_str(t, "id")
    label = _require_str(t, "label")
    approve = t.get("approve") or {}
    reject = t.get("reject") or {}
    if not isinstance(approve, dict) or not isinstance(reject, dict):
        raise TemplateError("approve/reject must be objects")
    return Template(
        id=tid,
        type="approve_reject",
        label=label,
        actions=[
            Action(
                id="approve",
                label=_require_str(approve, "label"),
                message=_require_str(approve, "message"),
            ),
            Action(
                id="reject",
                label=_require_str(reject, "label"),
                message=_require_str(reject, "message"),
            ),
        ],
    )


def _build_snooze(t: dict[str, Any]) -> Template:
    tid = _require_str(t, "id")
    label = _require_str(t, "label")
    msg_tmpl = _require_str(t, "message_template")
    options = t.get("options")
    if not isinstance(options, list) or not options:
        raise TemplateError("snooze.options must be a non-empty list")

    actions: list[Action] = []
    for opt in options:
        if not isinstance(opt, dict):
            raise TemplateError("snooze.options entries must be objects")
        opt_label = _require_str(opt, "label")
        minutes = opt.get("minutes")
        if not isinstance(minutes, int) and not (isinstance(minutes, str) and minutes.isdigit()):
            raise TemplateError("snooze.options.minutes must be an int")
        minutes_int = int(minutes)
        actions.append(
            Action(
                id=f"snooze_{minutes_int}",
                label=opt_label,
                message=msg_tmpl.format(minutes=minutes_int),
            )
        )

    return Template(id=tid, type="snooze", label=label, actions=actions)


_BUILDERS = {
    "standard": _build_standard,
    "approve_reject": _build_approve_reject,
    "snooze": _build_snooze,
}


def load_templates(raw_templates: list[dict[str, Any]]) -> list[Template]:
    templates: list[Template] = []
    for i, t in enumerate(raw_templates):
        if not isinstance(t, dict):
            raise TemplateError(f"Template at index {i} must be an object")
        ttype = t.get("type")
        if ttype not in _BUILDERS:
            raise TemplateError(f"Unsupported template type: {ttype!r}")
        templates.append(_BUILDERS[ttype](t))

    ids = [t.id for t in templates]
    if len(ids) != len(set(ids)):
        raise TemplateError("Template ids must be unique")
    return templates


def build_quick_reply_keyboard(
    templates: list[Template],
    *,
    secret: str,
    ttl_seconds: int,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for template_index, template in enumerate(templates):
        row: list[InlineKeyboardButton] = []
        for action_index, action in enumerate(template.actions):
            row.append(
                InlineKeyboardButton(
                    text=action.label,
                    callback_data=make_callback_data(
                        secret=secret,
                        template_index=template_index,
                        action_index=action_index,
                        ttl_seconds=ttl_seconds,
                    ),
                )
            )
        rows.append(row)
    return InlineKeyboardMarkup(rows)

