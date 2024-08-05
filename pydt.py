"""
Telegram bot for PYDT (Play Youyr Damn Turn) notiiifications
"""

import asyncio
import json
import logging
import os

import requests
from telegram import (
    Update,
)

from telegram.error import RetryAfter

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from shared import (
    potz_error_handler,
    setup_logging,
)

from utils import (
    get_client_help_message,
    get_client_privacy_message,
    get_pydt_notification_message,
)

from pydtdata import PydtData

logger = setup_logging(logging.INFO, __name__)

app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
TELEGRAM_SEND_MESSAGE_URL = "https://api.telegram.org/bot{}/sendMessage".format(os.getenv('TELEGRAM_TOKEN'))
is_initialized = False

async def tg_bot_main(application, event):
    async with application:
        await application.process_update(
            Update.de_json(json.loads(event["body"]), application.bot)
        )

async def parse_update(update: Update) -> PydtData:
    pydt = PydtData(update)
    await pydt.throttle()
    return pydt

async def reply(text: str, update: Update, context: ContextTypes.DEFAULT_TYPE, parse_mode: str = "Markdown"):
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=parse_mode,
        )
    except RetryAfter:
        logger.error("Rate limited by telegram, exiting without saving", exc_info=True)
        return

def send_telegram_message(chat_id, message):
    try:
        data = {
            "chat_id": chat_id,
            "text": message,
        }
        requests.post(TELEGRAM_SEND_MESSAGE_URL, data=data, timeout=5)
        logger.info("Sent notification to telegram chat %s", chat_id)
    except Exception: # pylint: disable=broad-except
        logger.error("Failed to send message to telegram chat %s", chat_id, exc_info=True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = get_client_help_message()
    await reply(help_text, update, context)

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    privacy_text = get_client_privacy_message()
    await reply(privacy_text, update, context)

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pydt = await parse_update(update)
    text = pydt.register()
    await reply(text, update, context, "MarkdownV2")

async def deregister_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pydt = await parse_update(update)
    text = pydt.deregister()
    await reply(text, update, context)

def register_handlers(application):
    help_handler = CommandHandler("help", help_command)
    application.add_handler(help_handler)

    privacy_handler = CommandHandler("privacy", privacy_command)
    application.add_handler(privacy_handler)

    register_handler = CommandHandler("register", register_command)
    application.add_handler(register_handler)

    deregister_handler = CommandHandler("deregister", deregister_command)
    application.add_handler(deregister_handler)

    application.add_error_handler(potz_error_handler)

async def handle_pydt_webhook(qsp, body):
    token = qsp["token"]
    if not token:
        logger.error("Empty token in query string parameters")
        return

    chat_id = PydtData.fetch_chat_id(token)
    if not chat_id:
        logger.error("Failed to fetch chat id from database")
        return

    send_telegram_message(chat_id, get_pydt_notification_message(body))

def lambda_handler(event, _context):
    try:
        if "body" not in event or event['body'] is None:
            logger.error("Missing request body")
            return {"statusCode": 500, "body": "Missing request body"}
        body = json.loads(event['body'])
        if "update_id" not in body and "queryStringParameters" in event:
            # this must be a PYDT webhook call
            logger.info("Received PYDT webhook call: %s", event)
            qsp = event["queryStringParameters"]
            if "token" not in qsp:
                logger.error("Missing token in query string parameters")
                return {"statusCode": 400, "body": "Missing token in query string parameters"}

            asyncio.run(handle_pydt_webhook(qsp, body))
            return {"statusCode": 200, "body": "ok"}
    except Exception as e: # pylint: disable=broad-except
        logger.error("Event handling failed for suspected PYDT message", exc_info=True)
        return {"statusCode": 500, "body": str(e)}

    # this is a telegram update
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