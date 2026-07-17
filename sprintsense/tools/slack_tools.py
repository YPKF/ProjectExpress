"""Slack API wrappers as LangChain tools."""

import logging
from datetime import datetime, timezone
from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from langchain_core.tools import tool

from config.settings import get_settings

logger = logging.getLogger(__name__)


def _get_slack_client() -> Optional[WebClient]:
    """Create and return an authenticated Slack client."""
    settings = get_settings()
    if not settings.slack_bot_token:
        logger.warning("Slack bot token not configured.")
        return None
    return WebClient(token=settings.slack_bot_token)


@tool
def fetch_channel_messages(limit: int = 50) -> list[dict]:
    """Fetch recent messages from the configured Slack channel.

    Args:
        limit: Maximum number of messages to fetch (default 50).

    Returns:
        List of message dicts with user, text, and timestamp.
    """
    client = _get_slack_client()
    if not client:
        return []

    settings = get_settings()
    try:
        result = client.conversations_history(
            channel=settings.slack_channel_id,
            limit=limit,
        )
        messages = []
        for msg in result.get("messages", []):
            messages.append({
                "user": msg.get("user", "unknown"),
                "text": msg.get("text", ""),
                "timestamp": msg.get("ts", ""),
                "is_bot": msg.get("bot_id") is not None,
                "thread_ts": msg.get("thread_ts"),
            })
        return messages
    except SlackApiError as e:
        logger.error("Slack API error fetching messages: %s", e)
        return []


@tool
def send_slack_message(text: str) -> dict:
    """Send a plain text message to the configured Slack channel.

    Args:
        text: The message text to send.

    Returns:
        Dict with 'success' bool and message timestamp.
    """
    client = _get_slack_client()
    if not client:
        return {"success": False, "error": "Slack client not available"}

    settings = get_settings()
    try:
        result = client.chat_postMessage(
            channel=settings.slack_channel_id,
            text=text,
            mrkdwn=True,
        )
        return {
            "success": True,
            "ts": result.get("ts", ""),
            "channel": result.get("channel", ""),
        }
    except SlackApiError as e:
        logger.error("Slack API error sending message: %s", e)
        return {"success": False, "error": str(e)}


@tool
def send_blocker_alert(blockers: list[str], sprint_name: str) -> dict:
    """Send a formatted blocker alert to the configured Slack channel.

    Args:
        blockers: List of blocker descriptions.
        sprint_name: Current sprint name for context.

    Returns:
        Dict with 'success' bool and message timestamp.
    """
    if not blockers:
        logger.info("No blockers to report.")
        return {"success": True, "message": "No blockers to report."}

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🚨 Sprint Blocker Alert — {sprint_name}"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{len(blockers)} blocker(s) detected:*",
            },
        },
    ]

    for b in blockers:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"• {b}"},
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"🤖 SprintSense • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            }
        ],
    })

    client = _get_slack_client()
    if not client:
        return {"success": False, "error": "Slack client not available"}

    settings = get_settings()
    try:
        result = client.chat_postMessage(
            channel=settings.slack_channel_id,
            text=f"🚨 {len(blockers)} blocker(s) detected in {sprint_name}",
            blocks=blocks,
        )
        return {
            "success": True,
            "ts": result.get("ts", ""),
            "channel": result.get("channel", ""),
        }
    except SlackApiError as e:
        logger.error("Slack API error sending blocker alert: %s", e)
        return {"success": False, "error": str(e)}
