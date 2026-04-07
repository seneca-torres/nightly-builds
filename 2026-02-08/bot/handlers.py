from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from .audit import AuditLogger, parse_admin_user_ids
from .config import AppConfig, ConfigError, load_config
from .security import CallbackError, parse_and_verify_callback_data
from .templates import TemplateError, build_quick_reply_keyboard, load_templates


@dataclass
class RuntimeState:
    config_path: Path
    app_config: AppConfig
    templates: list[Any]


def _actor_fields(update: Update) -> dict[str, Any]:
    user = update.effective_user
    chat = update.effective_chat
    return {
        "actor_user_id": user.id if user else None,
        "actor_username": user.username if user else None,
        "chat_id": chat.id if chat else None,
        "chat_type": chat.type if chat else None,
    }


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Quick Reply System\n\n"
        "Commands:\n"
        "/panel – send a quick reply panel\n"
        "/reload – reload YAML templates (admin)\n"
        "/help – show help",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Usage:\n"
        "- Reply to a message and run /panel to post a button panel tied to that thread.\n"
        "- Tap a button to send the configured response.\n\n"
        "Admin:\n"
        "- Set ADMIN_USER_IDS and use /reload after editing config/templates.yml",
    )


async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state: RuntimeState = context.application.bot_data["state"]
    keyboard = build_quick_reply_keyboard(
        state.templates,
        secret=state.app_config.security.callback_secret,
        ttl_seconds=state.app_config.security.callback_ttl_seconds,
    )
    msg = update.effective_message
    kwargs: dict[str, Any] = {"reply_markup": keyboard}
    if msg.reply_to_message:
        kwargs["reply_to_message_id"] = msg.reply_to_message.message_id
    await msg.reply_text("Quick replies:", **kwargs)


async def cmd_reload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    audit: AuditLogger = context.application.bot_data["audit"]
    state: RuntimeState = context.application.bot_data["state"]
    admins = context.application.bot_data.get("admins", set())
    actor = update.effective_user

    if admins and (not actor or actor.id not in admins):
        await audit.write(event="reload", ok=False, detail={"reason": "not_admin"}, **_actor_fields(update))
        await update.effective_message.reply_text("Not authorized.")
        return

    try:
        cfg = load_config(state.config_path)
        templates = load_templates(cfg.templates)
    except (ConfigError, TemplateError) as exc:
        await audit.write(event="reload", ok=False, detail={"error": str(exc)}, **_actor_fields(update))
        await update.effective_message.reply_text(f"Reload failed: {exc}")
        return

    state.app_config = cfg
    state.templates = templates
    await audit.write(event="reload", ok=True, detail={}, **_actor_fields(update))
    await update.effective_message.reply_text("Reloaded.")


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    audit: AuditLogger = context.application.bot_data["audit"]
    state: RuntimeState = context.application.bot_data["state"]
    query = update.callback_query
    if not query or not query.data:
        return

    fields = _actor_fields(update)
    fields["callback_message_id"] = query.message.message_id if query.message else None

    try:
        cb = parse_and_verify_callback_data(query.data, secret=state.app_config.security.callback_secret)
        template = state.templates[cb.template_index]
        action = template.actions[cb.action_index]
    except (CallbackError, IndexError) as exc:
        await audit.write(
            event="callback",
            ok=False,
            template_id=None,
            template_type=None,
            action_id=None,
            action_label=None,
            detail={"error": str(exc)},
            **fields,
        )
        await query.answer("Invalid or expired action.", show_alert=True)
        return

    try:
        await query.answer()
        target = query.message.reply_to_message if query.message else None
        if target:
            await target.reply_text(action.message)
        else:
            chat_id = update.effective_chat.id if update.effective_chat else None
            if chat_id is None:
                raise RuntimeError("Missing chat")
            await context.bot.send_message(chat_id=chat_id, text=action.message)

        await audit.write(
            event="callback",
            ok=True,
            template_id=template.id,
            template_type=template.type,
            action_id=action.id,
            action_label=action.label,
            detail={"sent": True},
            **fields,
        )
    except Exception as exc:  # noqa: BLE001
        await audit.write(
            event="callback",
            ok=False,
            template_id=template.id,
            template_type=template.type,
            action_id=action.id,
            action_label=action.label,
            detail={"error": str(exc)},
            **fields,
        )
        await query.answer("Failed to send.", show_alert=True)


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("panel", cmd_panel))
    application.add_handler(CommandHandler("reload", cmd_reload))
    application.add_handler(CallbackQueryHandler(on_callback, pattern=r"^qrs:"))


def init_runtime(*, config_path: str | Path) -> tuple[RuntimeState, AuditLogger, set[int]]:
    config_path = Path(config_path)
    cfg = load_config(config_path)
    templates = load_templates(cfg.templates)
    audit = AuditLogger(cfg.audit.log_path)
    admins = parse_admin_user_ids(os.getenv("ADMIN_USER_IDS"))
    return RuntimeState(config_path=config_path, app_config=cfg, templates=templates), audit, admins
