"""
d20potz specific utilities
"""

import logging
from shared import setup_logging


logger = setup_logging(logging.INFO, __name__)


def get_client_help_message() -> str:
    """
    Returns the help message for the client
    Telegram commands blob:

    register - <token> - Register a token to receive notifications
    deregister - Deregister your token
    help - Show help message
    privacy - Show the privacy disclaimer
    """
    help_text = """
What can this bot do?

1. /register <token> - Register a token to receive notifications
2. /deregsiter - Deregister your token
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
This bot does not store any personal data.
It only stores the token you provide to receive notifications.
The token is never shared with anyone.
You can permanently delete the token by using the /deregister command.
"""
    return privacy_text
