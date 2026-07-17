"""Tests for the Jira agent."""

from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from agents.jira_agent import JiraAgent


@pytest.fixture
def jira_agent() -> JiraAgent:
    """Fixture providing a Jira agent instance with mocked LLM."""
    agent = JiraAgent()
    agent.llm = MagicMock()
    return agent


@pytest.mark.asyncio
async def test_fetch_active_sprint_success() -> None:
    """Test successful active sprint fetch."""
    agent = JiraAgent()
    mock_sprint = {"id": "123", "name": "Sprint 1", "state": "active", "sprint_found": True}

    with patch("agents.jira_agent.fetch_active_sprint") as mock_fetch:
        mock_fetch.invoke.return_value = mock_sprint
        with patch("agents.jira_agent.fetch_sprint_tickets") as mock_tickets:
            mock_tickets.invoke.return_value = [{"id": "PROJ-1", "summary": "Test ticket"}]
            result = await agent.fetch_sprint_data(None)

    assert result["sprint_id"] == "123"
    assert result["sprint_name"] == "Sprint 1"
    assert len(result["tickets"]) == 1
    assert result["error"] is None


@pytest.mark.asyncio
async def test_fetch_active_sprint_no_sprint_found() -> None:
    """Test handling when no active sprint exists."""
    agent = JiraAgent()

    with patch("agents.jira_agent.fetch_active_sprint") as mock_fetch:
        mock_fetch.invoke.return_value = {"error": "No active sprint found", "sprint_found": False}
        result = await agent.fetch_sprint_data(None)

    assert result["error"] is not None
    assert "No active sprint found" in result["error"]
    assert result["tickets"] == []


@pytest.mark.asyncio
async def test_fetch_tickets_returns_list() -> None:
    """Test that ticket fetching returns a list."""
    agent = JiraAgent()

    with patch("agents.jira_agent.fetch_active_sprint") as mock_sprint:
        mock_sprint.invoke.return_value = {"id": "1", "name": "Sprint 1", "state": "active", "sprint_found": True}
        with patch("agents.jira_agent.fetch_sprint_tickets") as mock_tickets:
            mock_tickets.invoke.return_value = [
                {"id": "PROJ-1", "summary": "First", "status": "To Do"},
                {"id": "PROJ-2", "summary": "Second", "status": "In Progress"},
            ]
            result = await agent.fetch_sprint_data(None)

    assert isinstance(result["tickets"], list)
    assert len(result["tickets"]) == 2


@pytest.mark.asyncio
async def test_ticket_status_mapping() -> None:
    """Test that ticket status values are properly returned."""
    agent = JiraAgent()

    with patch("agents.jira_agent.fetch_active_sprint") as mock_sprint:
        mock_sprint.invoke.return_value = {"id": "1", "name": "Sprint 1", "state": "active", "sprint_found": True}
        with patch("agents.jira_agent.fetch_sprint_tickets") as mock_tickets:
            mock_tickets.invoke.return_value = [
                {"id": "PROJ-1", "summary": "Task", "status": "In Progress", "assignee": "Alice"},
            ]
            result = await agent.fetch_sprint_data(None)

    ticket = result["tickets"][0]
    assert ticket["status"] == "In Progress"
    assert ticket["assignee"] == "Alice"


@pytest.mark.asyncio
async def test_jira_connection_failure_handled_gracefully() -> None:
    """Test that Jira connection errors don't crash the agent."""
    agent = JiraAgent()

    with patch("agents.jira_agent.fetch_active_sprint") as mock_fetch:
        mock_fetch.invoke.side_effect = Exception("Connection refused")
        result = await agent.fetch_sprint_data(None)

    assert result["error"] is not None
    assert result["tickets"] == []


@pytest.mark.asyncio
async def test_analyze_tickets_empty() -> None:
    """Test ticket analysis with no tickets."""
    agent = JiraAgent()
    result = await agent.analyze_tickets([])
    assert "No tickets" in result
