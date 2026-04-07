#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


CONFIG_DEFAULT_PATH = "config.yml"
CALLBACK_PREFIX = "qr|"
CALLBACK_MAX_BYTES = 64


class ConfigError(RuntimeError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise ConfigError(
            "PyYAML is required. Install dependencies from requirements.txt."
        ) from exc

    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ConfigError("Config root must be a YAML mapping/object.")

    return data


def _dump_yaml(path: Path, data: Mapping[str, Any]) -> None:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise ConfigError(
            "PyYAML is required. Install dependencies from requirements.txt."
        ) from exc

    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            dict(data),
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )


def _get_mapping(obj: Any, where: str) -> dict[str, Any]:
    if obj is None:
        return {}
    if not isinstance(obj, dict):
        raise ConfigError(f"{where} must be a mapping/object.")
    return obj


def _get_list(obj: Any, where: str) -> list[Any]:
    if obj is None:
        return []
    if not isinstance(obj, list):
        raise ConfigError(f"{where} must be a list/array.")
    return obj


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _render_template(s: str, values: Mapping[str, Any]) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        raise ConfigError("Template text must be a string.")
    return s.format_map(_SafeFormatDict({k: str(v) for k, v in values.items()}))


@dataclass(frozen=True)
class Action:
    type: str
    text: str | None = None
    disable_buttons: bool = True
    remove_keyboard: bool = True


@dataclass(frozen=True)
class Button:
    id: str
    text: str
    style: str = "neutral"
    action: Action | None = None


@dataclass(frozen=True)
class Template:
    name: str
    text: str
    buttons: list[Button]


def _parse_action(obj: Any, where: str) -> Action | None:
    if obj is None:
        return None
    if not isinstance(obj, dict):
        raise ConfigError(f"{where} must be a mapping/object.")
    action_type = obj.get("type")
    if action_type not in {"message", "edit", "delete"}:
        raise ConfigError(f"{where}.type must be one of: message, edit, delete.")
    text = obj.get("text")
    if action_type in {"message", "edit"} and not isinstance(text, str):
        raise ConfigError(f"{where}.text is required for type={action_type}.")
    disable_buttons = obj.get("disable_buttons", True)
    remove_keyboard = obj.get("remove_keyboard", True)
    if not isinstance(disable_buttons, bool):
        raise ConfigError(f"{where}.disable_buttons must be boolean.")
    if not isinstance(remove_keyboard, bool):
        raise ConfigError(f"{where}.remove_keyboard must be boolean.")
    return Action(
        type=action_type,
        text=text,
        disable_buttons=disable_buttons,
        remove_keyboard=remove_keyboard,
    )


def _parse_template(name: str, obj: Any) -> Template:
    if not isinstance(obj, dict):
        raise ConfigError(f"templates.{name} must be a mapping/object.")
    text = obj.get("text", "")
    if not isinstance(text, str):
        raise ConfigError(f"templates.{name}.text must be a string.")
    buttons_obj = obj.get("buttons", [])
    buttons_list = _get_list(buttons_obj, f"templates.{name}.buttons")
    buttons: list[Button] = []
    for idx, b in enumerate(buttons_list):
        if not isinstance(b, dict):
            raise ConfigError(f"templates.{name}.buttons[{idx}] must be an object.")
        bid = b.get("id")
        btext = b.get("text")
        if not isinstance(bid, str) or not bid:
            raise ConfigError(f"templates.{name}.buttons[{idx}].id is required.")
        if not isinstance(btext, str) or not btext:
            raise ConfigError(f"templates.{name}.buttons[{idx}].text is required.")
        style = b.get("style", "neutral")
        if not isinstance(style, str):
            raise ConfigError(f"templates.{name}.buttons[{idx}].style must be string.")
        action = _parse_action(b.get("action"), f"templates.{name}.buttons[{idx}].action")
        buttons.append(Button(id=bid, text=btext, style=style, action=action))
    return Template(name=name, text=text, buttons=buttons)


def _load_templates(cfg: Mapping[str, Any]) -> dict[str, Template]:
    templates_obj = _get_mapping(cfg.get("templates"), "templates")
    templates: dict[str, Template] = {}
    for name, obj in templates_obj.items():
        if not isinstance(name, str) or not name:
            raise ConfigError("templates keys must be non-empty strings.")
        templates[name] = _parse_template(name, obj)
    return templates


def _style_prefixes(cfg: Mapping[str, Any]) -> dict[str, str]:
    styles = _get_mapping(cfg.get("styles"), "styles")
    out: dict[str, str] = {}
    for k, v in styles.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ConfigError("styles must map strings to strings.")
        out[k] = v
    return out


def _allowed_chat_ids(cfg: Mapping[str, Any]) -> set[int] | None:
    security = _get_mapping(cfg.get("security"), "security")
    allowed = security.get("allowed_chat_ids")
    if allowed is None:
        return None
    allowed_list = _get_list(allowed, "security.allowed_chat_ids")
    out: set[int] = set()
    for idx, v in enumerate(allowed_list):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ConfigError(f"security.allowed_chat_ids[{idx}] must be an integer.")
        out.add(v)
    return out


def _bot_token(cfg: Mapping[str, Any]) -> str:
    bot = _get_mapping(cfg.get("bot"), "bot")
    token = bot.get("token")
    if not isinstance(token, str) or not token.strip():
        raise ConfigError("bot.token is required.")
    return token.strip()


def _callback_data(template_name: str, button_id: str) -> str:
    data = f"{CALLBACK_PREFIX}{template_name}|{button_id}"
    if len(data.encode("utf-8")) > CALLBACK_MAX_BYTES:
        raise ConfigError(
            f"callback_data too long for template={template_name} button={button_id}. "
            "Shorten template/button ids."
        )
    return data


def _parse_callback_data(data: str) -> tuple[str, str] | None:
    if not isinstance(data, str) or not data.startswith(CALLBACK_PREFIX):
        return None
    rest = data[len(CALLBACK_PREFIX) :]
    parts = rest.split("|", 1)
    if len(parts) != 2:
        return None
    t, b = parts[0], parts[1]
    if not t or not b:
        return None
    return t, b


def cmd_config_init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.exists() and not args.force:
        raise ConfigError(f"Refusing to overwrite existing file: {path} (use --force)")

    example = {
        "bot": {"token": "PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE"},
        "security": {"allowed_chat_ids": []},
        "styles": {
            "primary": "✅ ",
            "danger": "❌ ",
            "secondary": "⏸ ",
            "neutral": "",
        },
        "templates": {
            "approve_reject_snooze": {
                "text": "Please review this request.",
                "buttons": [
                    {
                        "id": "approve",
                        "text": "Approve",
                        "style": "primary",
                        "action": {"type": "message", "text": "Approved."},
                    },
                    {
                        "id": "reject",
                        "text": "Reject",
                        "style": "danger",
                        "action": {"type": "message", "text": "Rejected."},
                    },
                    {
                        "id": "snooze",
                        "text": "Snooze 1h",
                        "style": "secondary",
                        "action": {"type": "edit", "text": "Snoozed for 1 hour."},
                    },
                ],
            }
        },
    }
    _dump_yaml(path, example)
    print(f"Wrote {path}")
    return 0


def _load_config_for_cli(path_str: str) -> dict[str, Any]:
    path = Path(path_str)
    cfg = _load_yaml(path)
    cfg.setdefault("templates", {})
    if not isinstance(cfg["templates"], dict):
        raise ConfigError("templates must be a mapping/object.")
    return cfg


def cmd_template_list(args: argparse.Namespace) -> int:
    cfg = _load_config_for_cli(args.config)
    templates = _load_templates(cfg)
    for name in sorted(templates.keys()):
        print(name)
    return 0


def cmd_template_show(args: argparse.Namespace) -> int:
    cfg = _load_config_for_cli(args.config)
    templates_obj = _get_mapping(cfg.get("templates"), "templates")
    if args.name not in templates_obj:
        raise ConfigError(f"Template not found: {args.name}")
    print(json.dumps(templates_obj[args.name], indent=2, ensure_ascii=False))
    return 0


def _read_yaml_snippet(path: Path) -> dict[str, Any]:
    snippet = _load_yaml(path)
    if "template" in snippet and isinstance(snippet["template"], dict):
        snippet = snippet["template"]
    if not isinstance(snippet, dict):
        raise ConfigError("Template snippet must be a YAML object.")
    return snippet


def cmd_template_set(args: argparse.Namespace) -> int:
    cfg_path = Path(args.config)
    cfg = _load_config_for_cli(args.config)
    snippet = _read_yaml_snippet(Path(args.file))
    # Validate by parsing
    _parse_template(args.name, snippet)
    cfg["templates"][args.name] = snippet
    _dump_yaml(cfg_path, cfg)
    print(f"Upserted template {args.name} in {cfg_path}")
    return 0


def cmd_template_delete(args: argparse.Namespace) -> int:
    cfg_path = Path(args.config)
    cfg = _load_config_for_cli(args.config)
    templates_obj = _get_mapping(cfg.get("templates"), "templates")
    if args.name not in templates_obj:
        raise ConfigError(f"Template not found: {args.name}")
    del templates_obj[args.name]
    cfg["templates"] = templates_obj
    _dump_yaml(cfg_path, cfg)
    print(f"Deleted template {args.name} from {cfg_path}")
    return 0


def cmd_template_export(args: argparse.Namespace) -> int:
    cfg = _load_config_for_cli(args.config)
    templates_obj = _get_mapping(cfg.get("templates"), "templates")
    if args.name not in templates_obj:
        raise ConfigError(f"Template not found: {args.name}")
    out = {"template": templates_obj[args.name]}
    _dump_yaml(Path(args.out), out)
    print(f"Wrote {args.out}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = _load_yaml(Path(args.config))
    token = _bot_token(cfg)
    templates = _load_templates(cfg)
    styles = _style_prefixes(cfg)
    allowed = _allowed_chat_ids(cfg)

    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
        from telegram.constants import ParseMode
        from telegram.ext import (
            ApplicationBuilder,
            CallbackQueryHandler,
            CommandHandler,
            ContextTypes,
        )
    except Exception as exc:  # pragma: no cover
        raise ConfigError(
            "python-telegram-bot is required for `run`. Install requirements.txt."
        ) from exc

    async def _send_template(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str, payload: str) -> None:
        if update.effective_chat is None or update.effective_user is None:
            return
        if allowed is not None and update.effective_chat.id not in allowed:
            return
        if name not in templates:
            await update.effective_message.reply_text(
                f"Unknown template: {name}\nAvailable: {', '.join(sorted(templates.keys()))}"
            )
            return

        t = templates[name]
        values = {
            "user_id": update.effective_user.id,
            "user_name": update.effective_user.username or "",
            "user_first_name": update.effective_user.first_name or "",
            "chat_id": update.effective_chat.id,
            "template": t.name,
            "payload": payload,
            "now_iso": _now_iso(),
        }

        keyboard: list[list[InlineKeyboardButton]] = []
        row: list[InlineKeyboardButton] = []
        for b in t.buttons:
            prefix = styles.get(b.style, "")
            text = prefix + _render_template(b.text, values)
            row.append(InlineKeyboardButton(text=text, callback_data=_callback_data(t.name, b.id)))
        if row:
            keyboard.append(row)

        msg_text = _render_template(t.text, values)
        await update.effective_message.reply_text(
            msg_text,
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
            parse_mode=ParseMode.HTML if args.html else None,
            disable_web_page_preview=True,
        )

    async def cmd_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None:
            return
        text = update.effective_message.text or ""
        parts = text.split(maxsplit=2)
        if len(parts) == 1:
            await update.effective_message.reply_text(
                "Usage: /qr <template> [payload]\nTemplates: " + ", ".join(sorted(templates.keys()))
            )
            return
        name = parts[1]
        payload = parts[2] if len(parts) >= 3 else ""
        await _send_template(update, context, name, payload)

    async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query is None:
            return
        if query.message is None or query.data is None:
            return
        if allowed is not None and query.message.chat_id not in allowed:
            await query.answer()
            return

        parsed = _parse_callback_data(query.data)
        if parsed is None:
            await query.answer()
            return
        tname, bid = parsed
        t = templates.get(tname)
        if t is None:
            await query.answer("Template no longer exists.", show_alert=False)
            return

        button = next((b for b in t.buttons if b.id == bid), None)
        if button is None:
            await query.answer("Button no longer exists.", show_alert=False)
            return

        values = {
            "user_id": query.from_user.id,
            "user_name": query.from_user.username or "",
            "user_first_name": query.from_user.first_name or "",
            "chat_id": query.message.chat_id,
            "template": t.name,
            "button_id": button.id,
            "button_text": button.text,
            "now_iso": _now_iso(),
        }

        action = button.action
        await query.answer()

        if action is None:
            return

        if action.type == "message":
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=_render_template(action.text or "", values),
                disable_web_page_preview=True,
            )
            if action.disable_buttons:
                await query.edit_message_reply_markup(reply_markup=None)
            return

        if action.type == "edit":
            new_text = _render_template(action.text or "", values)
            await query.edit_message_text(
                new_text,
                reply_markup=None if action.remove_keyboard else query.message.reply_markup,
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML if args.html else None,
            )
            return

        if action.type == "delete":
            await query.message.delete()
            return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("qr", cmd_qr))
    app.add_handler(CallbackQueryHandler(on_callback))

    if not templates:
        print("Warning: no templates found in config.yml (templates: {}).", file=sys.stderr)

    print("Bot running. Press Ctrl+C to stop.", file=sys.stderr)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="telegram_quick_replies",
        description="Telegram Quick Reply Buttons: templates + one-tap actions via YAML config.",
    )
    p.add_argument("--config", default=CONFIG_DEFAULT_PATH, help=f"YAML config path (default: {CONFIG_DEFAULT_PATH})")

    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("run", help="Run the Telegram bot (polling).")
    sp.add_argument("--html", action="store_true", help="Enable HTML parse mode for template texts.")
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("config", help="Config utilities.")
    sub2 = sp.add_subparsers(dest="config_cmd", required=True)
    sp2 = sub2.add_parser("init", help="Write a starter config.yml.")
    sp2.add_argument("--path", default=CONFIG_DEFAULT_PATH, help="Output path.")
    sp2.add_argument("--force", action="store_true", help="Overwrite if exists.")
    sp2.set_defaults(func=cmd_config_init)

    sp = sub.add_parser("template", help="Manage button templates inside the config file.")
    sub2 = sp.add_subparsers(dest="template_cmd", required=True)

    sp2 = sub2.add_parser("list", help="List templates.")
    sp2.set_defaults(func=cmd_template_list)

    sp2 = sub2.add_parser("show", help="Show a template as JSON.")
    sp2.add_argument("name")
    sp2.set_defaults(func=cmd_template_show)

    sp2 = sub2.add_parser("set", help="Upsert a template from a YAML snippet file.")
    sp2.add_argument("name", help="Template name (key under templates:).")
    sp2.add_argument("--file", required=True, help="YAML file containing the template object.")
    sp2.set_defaults(func=cmd_template_set)

    sp2 = sub2.add_parser("delete", help="Delete a template.")
    sp2.add_argument("name")
    sp2.set_defaults(func=cmd_template_delete)

    sp2 = sub2.add_parser("export", help="Export a template into a YAML snippet file.")
    sp2.add_argument("name")
    sp2.add_argument("--out", required=True)
    sp2.set_defaults(func=cmd_template_export)

    return p


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

