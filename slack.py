import os

import slack_sdk
from dotenv import load_dotenv

load_dotenv()


class Slack:
    def __init__(self):
        self.client = slack_sdk.WebClient(
            token=os.getenv("SLACK_BOT_TOKEN"),
        )

    def send_message(self, message):
        response = self.client.chat_postMessage(
            channel=os.getenv("SLACK_CHANNEL"), text=message
        )
        response
