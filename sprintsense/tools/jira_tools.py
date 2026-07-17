"""Jira REST API wrappers as LangChain tools."""

import logging
from datetime import datetime, timezone
from typing import Optional

from jira import JIRA as JiraClient, JIRAError
from langchain_core.tools import tool

from config.settings import get_settings

logger = logging.getLogger(__name__)


def _get_jira_client() -> Optional[JiraClient]:
    """Create and return an authenticated Jira client."""
    settings = get_settings()
    if not settings.jira_base_url or not settings.jira_email or not settings.jira_api_token:
        logger.warning("Jira credentials not configured.")
        return None
    try:
        return JiraClient(
            server=settings.jira_base_url,
            basic_auth=(settings.jira_email, settings.jira_api_token),
            timeout=30,
        )
    except JIRAError as e:
        logger.error("Failed to connect to Jira: %s", e)
        return None


@tool
def fetch_active_sprint() -> dict:
    """Fetch the active sprint for the configured Jira project.

    Returns:
        dict with sprint info: {'id': str, 'name': str, 'state': str} or error dict.
    """
    jira = _get_jira_client()
    if not jira:
        return {"error": "Jira client not available", "sprint_found": False}

    try:
        settings = get_settings()
        boards = jira.boards(project=settings.jira_project_key)
        for board in boards:
            sprints = jira.sprints(board.id, state="active")
            for sprint in sprints:
                return {
                    "id": str(sprint.id),
                    "name": sprint.name,
                    "state": sprint.state,
                    "sprint_found": True,
                }
        return {"error": "No active sprint found", "sprint_found": False}
    except JIRAError as e:
        logger.error("Jira error fetching active sprint: %s", e)
        return {"error": str(e), "sprint_found": False}


@tool
def fetch_sprint_tickets(sprint_id: str) -> list[dict]:
    """Fetch all tickets in a given sprint.

    Args:
        sprint_id: The Jira sprint ID.

    Returns:
        List of normalized ticket dicts.
    """
    jira = _get_jira_client()
    if not jira:
        return []

    settings = get_settings()
    tickets = []
    try:
        jql = f"Sprint = {sprint_id} ORDER BY created ASC"
        issues = jira.search_issues(jql, maxResults=100, expand="renderedFields")
        for issue in issues:
            fields = issue.fields
            labels = getattr(fields, "labels", []) or []
            ticket = {
                "id": issue.key,
                "summary": getattr(fields, "summary", ""),
                "description": getattr(fields, "description", "") or "",
                "status": getattr(fields.status, "name", "Unknown") if fields.status else "Unknown",
                "assignee": getattr(fields.assignee, "displayName", None) if fields.assignee else None,
                "priority": getattr(fields.priority, "name", "Medium") if fields.priority else "Medium",
                "story_points": None,
                "labels": labels,
                "sprint_name": None,
                "created": getattr(fields, "created", None),
                "updated": getattr(fields, "updated", None),
                "due_date": getattr(fields, "duedate", None),
                "is_blocked": any(kw in " ".join(labels).lower() for kw in settings.get_blocker_keywords_list())
                or "blocked" in getattr(fields, "summary", "").lower(),
                "blocker_reason": None,
            }
            # Try to extract story points from custom fields
            try:
                if hasattr(fields, settings.jira_project_key.lower() + "_story_points"):
                    ticket["story_points"] = getattr(fields, settings.jira_project_key.lower() + "_story_points")
                else:
                    # Common field names for story points
                    for cf_name in ["customfield_10016", "customfield_10002", "customfield_10008"]:
                        cf_value = getattr(fields, cf_name, None)
                        if cf_value is not None:
                            ticket["story_points"] = float(cf_value)
                            break
            except (ValueError, TypeError, AttributeError):
                ticket["story_points"] = None

            if ticket["is_blocked"]:
                ticket["blocker_reason"] = f"Ticket {ticket['id']} has blocker label or keyword in summary."
            tickets.append(ticket)
    except JIRAError as e:
        logger.error("Jira error fetching sprint tickets: %s", e)
    return tickets


@tool
def get_sprint_by_id(sprint_id: str) -> dict:
    """Get a specific sprint's details by its ID.

    Args:
        sprint_id: The Jira sprint ID.

    Returns:
        Sprint info dict.
    """
    jira = _get_jira_client()
    if not jira:
        return {"error": "Jira client not available"}

    try:
        settings = get_settings()
        boards = jira.boards(project=settings.jira_project_key)
        for board in boards:
            sprints = jira.sprints(board.id)
            for sprint in sprints:
                if str(sprint.id) == sprint_id:
                    return {
                        "id": str(sprint.id),
                        "name": sprint.name,
                        "state": sprint.state,
                        "start_date": getattr(sprint, "startDate", None),
                        "end_date": getattr(sprint, "endDate", None),
                    }
        return {"error": f"Sprint {sprint_id} not found"}
    except JIRAError as e:
        logger.error("Jira error fetching sprint by ID: %s", e)
        return {"error": str(e)}
