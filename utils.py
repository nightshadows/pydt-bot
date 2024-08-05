"""
d20potz specific utilities
"""

import json
import logging
import random
import string
from shared import setup_logging


logger = setup_logging(logging.INFO, __name__)


def get_client_help_message() -> str:
    """
    Returns the help message for the client
    Telegram commands blob:

    register - Register to receive notifications and get a token for PYDT webhook
    deregister - Deregister your token
    help - Show help message
    privacy - Show the privacy disclaimer
    """
    help_text = """
What can this bot do?

1. /register - Register to receive notifications and get a token for PYDT webhook
2. /deregister - Deregister your token
3. /help - Show help message
4. /privacy - Show the privacy disclaimer

Once you have registered, you will receive notifications when it is your turn to play.
Only one token can be registered per user.
""".strip()
    return help_text

def get_client_privacy_message() -> str:
    """
    Returns the privacy message for the client
    """
    privacy_text = """
This bot does not store or process any personal data.
"""
    return privacy_text

def get_pydt_notification_message(body: json) -> str:
    """
    Forms a pretty notification message for the client
    """
    notification_text = f"""
Dear {body['userName']}, it's your damn turn to play in the game {body['gameName']}!
(round {body['round']})
"""
    return notification_text

def generate_token() -> str:
    """
    Generates a random token
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=16))
