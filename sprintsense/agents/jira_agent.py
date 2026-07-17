"""Jira agent — fetches and analyzes sprint tickets."""

import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import get_settings
from tools.jira_tools import fetch_active_sprint, fetch_sprint_tickets

logger = logging.getLogger(__name__)


class JiraAgent:
    """Agent responsible for fetching and analyzing Jira sprint data."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            base_url=self.settings.llm_api_base_url,
            temperature=0.1,
        )

    async def fetch_sprint_data(self, sprint_id: str | None = None) -> dict[str, Any]:
        """Fetch sprint data from Jira.

        Args:
            sprint_id: Optional sprint ID. If None, fetches the active sprint.

        Returns:
            Dict with 'sprint_info', 'tickets', and 'error' keys.
        """
        result: dict[str, Any] = {
            "sprint_id": sprint_id or "",
            "sprint_name": "",
            "tickets": [],
            "error": None,
        }

        try:
            # Resolve sprint if not provided
            if not sprint_id:
                sprint_info = fetch_active_sprint.invoke({})
                if not sprint_info.get("sprint_found"):
                    result["error"] = sprint_info.get("error", "No active sprint found.")
                    logger.warning("No active sprint found: %s", result["error"])
                    return result
                sprint_id = sprint_info["id"]
                result["sprint_id"] = sprint_id
                result["sprint_name"] = sprint_info["name"]
            else:
                # Try to get sprint name from Jira
                from tools.jira_tools import get_sprint_by_id
                sprint_info = get_sprint_by_id.invoke({"sprint_id": sprint_id})
                if "name" in sprint_info:
                    result["sprint_name"] = sprint_info["name"]
                elif "error" in sprint_info:
                    logger.warning("Could not get sprint info: %s", sprint_info["error"])

            # Fetch tickets
            tickets = fetch_sprint_tickets.invoke({"sprint_id": sprint_id})
            result["tickets"] = tickets
            logger.info("Fetched %d tickets from sprint %s", len(tickets), sprint_id)

        except Exception as e:
            logger.error("Jira agent error: %s", e, exc_info=True)
            result["error"] = str(e)

        return result

    async def analyze_tickets(self, tickets: list[dict]) -> str:
        """Use LLM to analyze ticket data and extract insights.

        Args:
            tickets: List of ticket dicts.

        Returns:
            Analysis text with key observations.
        """
        if not tickets:
            return "No tickets found in the sprint."

        try:
            ticket_summary = "\n".join(
                f"- {t['id']}: {t['summary']} [{t['status']}] "
                f"(Assignee: {t.get('assignee', 'Unassigned')})"
                for t in tickets[:20]  # Limit context
            )

            messages = [
                SystemMessage(
                    content="You are a sprint analysis expert. Analyze the following Jira tickets "
                            "and provide key observations about the sprint health, work distribution, "
                            "and any patterns you notice."
                ),
                HumanMessage(
                    content=f"Here are the tickets for the current sprint:\n\n{ticket_summary}\n\n"
                            f"Total tickets: {len(tickets)}\n"
                            f"Please provide a concise analysis."
                ),
            ]

            response = await self.llm.ainvoke(messages)
            return response.content

        except Exception as e:
            logger.error("Error analyzing tickets: %s", e)
            return f"Analysis available but LLM call failed: {e}"
