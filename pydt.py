"""
Telegram bot for PYDT (Play Youyr Damn Turn) notiiifications
"""

import asyncio
import json
import logging
import os

from telegram import (
    Update,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from shared import (
    potz_error_handler,
    setup_logging,
)

from utils import get_client_help_message

logger = setup_logging(logging.INFO, __name__)

app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
is_initialized = False

async def tg_bot_main(application, event):
    async with application:
        await application.process_update(
            Update.de_json(json.loads(event["body"]), application.bot)
        )

def register_handlers(application):
    help_handler = CommandHandler("help", get_client_help_message)
    application.add_handler(help_handler)

    privacy_handler = CommandHandler("privacy", get_client_privacy_message)
    application.add_handler(privacy_handler)

    application.add_error_handler(potz_error_handler)

def lambda_handler(event, _context):
    global is_initialized # pylint: disable=global-statement
    try:
        if not is_initialized:
            register_handlers(app)
            is_initialized = True
        asyncio.run(tg_bot_main(app, event))
    except Exception as e: # pylint: disable=broad-except
        logger.error("Event handling failed", exc_info=True)
        return {"statusCode": 500, "body": str(e)}

    return {"statusCode": 200, "body": "ok"}