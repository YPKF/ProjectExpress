"""Notification service for sending alerts via Slack and other channels."""

import logging
from typing import Optional

from tools.slack_tools import send_slack_message, send_blocker_alert

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles sending notifications about sprint events, blockers, and reports."""

    @staticmethod
    async def notify_blockers(blockers: list[str], sprint_name: str) -> dict:
        """Send blocker alert to Slack.

        Args:
            blockers: List of blocker descriptions.
            sprint_name: Current sprint name.

        Returns:
            Result dict from Slack API.
        """
        if not blockers:
            logger.info("No blockers to notify about.")
            return {"success": True, "message": "No blockers to report."}

        result = send_blocker_alert.invoke({"blockers": blockers, "sprint_name": sprint_name})
        if result.get("success"):
            logger.info("Blocker alert sent to Slack for %d blocker(s).", len(blockers))
        else:
            logger.error("Failed to send blocker alert: %s", result.get("error"))
        return result

    @staticmethod
    async def notify_report_ready(sprint_name: str, report_url: str = "") -> dict:
        """Notify team that a sprint report is ready.

        Args:
            sprint_name: Sprint name.
            report_url: Optional URL to the report.

        Returns:
            Result dict from Slack API.
        """
        message = (
            f"📋 *Sprint Report Ready — {sprint_name}*\n"
            f"The SprintSense analysis is complete. "
        )
        if report_url:
            message += f"View report: {report_url}\n"
        message += "\n_Reply to this thread for details._"

        result = send_slack_message.invoke({"text": message})
        return result

    @staticmethod
    async def notify_risk_alert(
        risk_level: str,
        sprint_name: str,
        completion_probability: float,
    ) -> dict:
        """Send a risk alert notification.

        Args:
            risk_level: 'LOW', 'MEDIUM', or 'HIGH'.
            sprint_name: Sprint name.
            completion_probability: Current completion probability.

        Returns:
            Result dict.
        """
        if risk_level == "LOW":
            return {"success": True, "message": "Risk level is LOW, no alert needed."}

        emoji = "⚠️" if risk_level == "MEDIUM" else "🚨"
        message = (
            f"{emoji} *Sprint Risk Alert — {sprint_name}*\n"
            f"Risk Level: *{risk_level}*\n"
            f"Completion Probability: *{completion_probability:.1%}*\n"
            f"\n_Immediate attention may be required._"
        )

        result = send_slack_message.invoke({"text": message})
        return result
