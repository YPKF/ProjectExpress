"""Blocker detection logic — scans tickets, PRs, and Slack messages for blockers."""

import logging
from typing import List

from config.settings import get_settings

logger = logging.getLogger(__name__)


class BlockerDetector:
    """Detects sprint blockers from Jira tickets, GitHub PRs, and Slack messages."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.keywords = self.settings.get_blocker_keywords_list()

    def detect_from_tickets(self, tickets: list[dict]) -> list[str]:
        """Scan Jira tickets for blocker indicators.

        Args:
            tickets: List of normalized ticket dicts.

        Returns:
            List of blocker description strings.
        """
        blockers: list[str] = []
        for ticket in tickets:
            summary = (ticket.get("summary") or "").lower()
            description = (ticket.get("description") or "").lower()
            labels = [l.lower() for l in ticket.get("labels", [])]
            combined_text = f"{summary} {description} {' '.join(labels)}"

            if any(kw in combined_text for kw in self.keywords):
                assignee = ticket.get("assignee") or "Unassigned"
                blocker_desc = (
                    f"[{ticket['id']}] {ticket.get('summary', '')} — "
                    f"Assigned to: {assignee}"
                )
                blockers.append(blocker_desc)
                logger.info("Blocker detected from ticket %s", ticket["id"])

        return blockers

    def detect_from_slack(self, messages: list[dict]) -> list[str]:
        """Scan Slack messages for blocker keywords.

        Args:
            messages: List of Slack message dicts.

        Returns:
            List of blocker description strings.
        """
        blockers: list[str] = []
        for msg in messages:
            text = (msg.get("text") or "").lower()
            if any(kw in text for kw in self.keywords):
                user = msg.get("user", "unknown")
                blocker_desc = (
                    f"[Slack] Message from <@{user}>: "
                    f"{msg.get('text', '')[:200]}"
                )
                blockers.append(blocker_desc)

        return blockers

    def detect_from_prs(self, prs: list[dict]) -> list[str]:
        """Scan GitHub PRs for blocker indicators.

        Args:
            prs: List of normalized PR dicts.

        Returns:
            List of blocker description strings.
        """
        blockers: list[str] = []
        for pr in prs:
            title = (pr.get("title") or "").lower()
            description = (pr.get("description") or "").lower()
            labels = [l.lower() for l in pr.get("labels", [])]
            combined = f"{title} {description} {' '.join(labels)}"

            if any(kw in combined for kw in self.keywords):
                blocker_desc = (
                    f"[PR #{pr['id']}] {pr.get('title', '')} — "
                    f"Author: {pr.get('author', 'unknown')}"
                )
                blockers.append(blocker_desc)

            # Stale PRs (open > 3 days) are potential blockers
            if pr.get("is_stale") and not pr.get("is_draft"):
                blocker_desc = (
                    f"[PR #{pr['id']}] Stale PR — {pr.get('title', '')} "
                    f"(open > 3 days, Author: {pr.get('author', 'unknown')})"
                )
                blockers.append(blocker_desc)

        return blockers

    def detect_all(self, tickets: list[dict], prs: list[dict], slack_messages: list[dict]) -> list[str]:
        """Run all blocker detectors and return deduplicated results.

        Args:
            tickets: List of ticket dicts.
            prs: List of PR dicts.
            slack_messages: List of Slack message dicts.

        Returns:
            Deduplicated list of blocker descriptions.
        """
        blockers: list[str] = []
        blockers.extend(self.detect_from_tickets(tickets))
        blockers.extend(self.detect_from_prs(prs))
        blockers.extend(self.detect_from_slack(slack_messages))
        return self.deduplicate(blockers)

    @staticmethod
    def deduplicate(blockers: list[str]) -> list[str]:
        """Remove duplicate blocker entries while preserving order.

        Args:
            blockers: List of blocker strings, possibly with duplicates.

        Returns:
            Deduplicated list.
        """
        seen: set[str] = set()
        result: list[str] = []
        for b in blockers:
            if b not in seen:
                seen.add(b)
                result.append(b)
        return result
