"""
Internal logic for PYDT bot
"""

import os
import boto3
from botocore.exceptions import ClientError
import logging

from shared import (
    setup_logging,
    throttle_telegram,
)
from utils import generate_token

logger = setup_logging(logging.INFO, __name__)
PYDT_TABLE = "pydt"
dynamobd = boto3.resource("dynamodb")
pydttable = dynamobd.Table(PYDT_TABLE)


class PydtData:
    user_id: int
    chat_id: str
    token: str
    params: list[str]
    last_calls: list[int]

    def __init__(self, update = None):
        self.user_id = 0
        self.chat_id = update.effective_chat.id
        self.token = ""
        self.params = []
        self.last_calls = []

        if not(message := update.message):
            message = update.edited_message
        if message:
            self.user_id = message.from_user.id
            self.params = message.text.split() if message.text else []
        elif (callback_query := update.callback_query):
            self.user_id = callback_query.from_user.id
            self.params = callback_query.data.split() if callback_query.data else []
        self.load()

    async def throttle(self):
        # this bot can only be used in private chats
        await throttle_telegram(self.last_calls, "private")

    def save(self):
        """
        Save the data to the database
        """
        try:
            pydttable.put_item(
                Item={
                    "user_id": str(self.user_id),
                    "pydt_token": self.token,
                    "chat_id": self.chat_id,
                }
            )
        except ClientError:
            logger.error("Failed to save data to the database", exc_info=True)

    def load(self):
        """
        Load the data from the database
        """
        try:
            response = pydttable.get_item(
                Key={
                    "user_id": str(self.user_id),
                }
            )
            item = response.get("Item")
            if item:
                token = item.get("pydt_token")
                self.token = token if token else ""
                chat_id = item.get("chat_id")
                self.chat_id = chat_id if chat_id else ""
        except ClientError:
            logger.error("Failed to load data from the database", exc_info=True)

    @classmethod
    def fetch_chat_id(cls, token: str) -> str:
        """
        Fetch the chat id from the database
        """
        try:
            response = pydttable.query(
                IndexName="pydt_token-index",
                KeyConditionExpression="pydt_token = :t",
                ExpressionAttributeValues={
                    ":t": token,
                }
            )
        except ClientError:
            logger.error("Failed to fetch chat id by token %s from the database", token, exc_info=True)
            return None
        if "Items" not in response or len(response["Items"]) != 1:
            logger.error("Invalid response while trying to fetch chat id for token %s", token)
            return None
        return response["Items"][0]["chat_id"]

    def register(self) -> str:
        """
        Register the user
        """
        if self.token == "":
            token = generate_token()
            self.token = token
        self.save()
        webhook_url = os.getenv("WEBHOOK_TEMPLATE") + self.token
        reply_text = f"""
You have been registered in the bot.
In order to receive notifications, go to "https://www.playyourdamnturn.com/user/profile" and paste the following url in the "Webhook Notifications" field:
```{webhook_url}```
Remember to click submit to save the changes.
To stop recieving notifications, use the /deregister command.
""".replace(".", "\\.") # escape the dot
        return reply_text

    def deregister(self) -> str:
        """
        Deregister the user
        """
        self.token = ""
        self.save()
        return "You have been deregistered. You will no longer recieve any notifications. Remember to also remove the webhook from your PYDT website profile."