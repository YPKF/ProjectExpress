"""Slack agent — reads messages and sends notifications."""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from config.settings import get_settings
from tools.slack_tools import fetch_channel_messages, send_slack_message

logger = logging.getLogger(__name__)


class SlackAgent:
    """Agent responsible for Slack interactions — reading messages and sending alerts."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            base_url=self.settings.llm_api_base_url,
            temperature=0.1,
        )

    async def fetch_messages(self, limit: int = 50) -> list[dict]:
        """Fetch recent messages from the configured Slack channel.

        Args:
            limit: Maximum number of messages.

        Returns:
            List of message dicts.
        """
        try:
            messages = fetch_channel_messages.invoke({"limit": limit})
            logger.info("Fetched %d Slack messages", len(messages))
            return messages
        except Exception as e:
            logger.error("Slack agent error fetching messages: %s", e, exc_info=True)
            return []

    async def send_message(self, text: str) -> dict:
        """Send a message to the configured Slack channel.

        Args:
            text: Message text.

        Returns:
            Result dict.
        """
        try:
            result = send_slack_message.invoke({"text": text})
            return result
        except Exception as e:
            logger.error("Slack agent error sending message: %s", e)
            return {"success": False, "error": str(e)}

    async def send_standup_summary(self, summary: str, sprint_name: str) -> dict:
        """Send the daily standup summary to Slack.

        Args:
            summary: Generated standup text.
            sprint_name: Current sprint name.

        Returns:
            Result dict.
        """
        header = f"📋 *Daily Standup — {sprint_name}*\n\n"
        message = header + summary
        return await self.send_message(message)
