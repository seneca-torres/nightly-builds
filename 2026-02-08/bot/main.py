from __future__ import annotations

import os
from pathlib import Path

from telegram.ext import ApplicationBuilder

from .handlers import init_runtime, register_handlers


def main() -> None:
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise SystemExit("Missing env var BOT_TOKEN")

    config_path = Path(os.getenv("TEMPLATES_CONFIG", "config/templates.yml"))
    state, audit, admins = init_runtime(config_path=config_path)

    app = ApplicationBuilder().token(token).build()
    app.bot_data["state"] = state
    app.bot_data["audit"] = audit
    app.bot_data["admins"] = admins

    register_handlers(app)
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()

