"""Tests for the GitHub agent."""

from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
import pytest

from agents.github_agent import GitHubAgent


@pytest.fixture
def github_agent() -> GitHubAgent:
    """Fixture providing a GitHub agent instance."""
    agent = GitHubAgent()
    agent.llm = MagicMock()
    return agent


@pytest.mark.asyncio
async def test_fetch_open_prs_success() -> None:
    """Test successful PR fetch."""
    agent = GitHubAgent()
    mock_prs = [
        {"id": 1, "title": "Fix bug", "status": "open", "is_stale": False, "author": "dev1"},
        {"id": 2, "title": "Add feature", "status": "open", "is_stale": False, "author": "dev2"},
    ]

    with patch("agents.github_agent.fetch_open_prs") as mock_fetch:
        mock_fetch.invoke.return_value = mock_prs
        result = await agent.fetch_pr_data()

    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["title"] == "Add feature"


@pytest.mark.asyncio
async def test_fetch_commits_last_24_hours() -> None:
    """Test recent commit fetching."""
    agent = GitHubAgent()
    mock_commits = [
        {"sha": "abc123", "message": "Fix login", "author": "dev1", "date": datetime.now(timezone.utc).isoformat()},
    ]

    with patch("agents.github_agent.fetch_recent_commits") as mock_fetch:
        mock_fetch.invoke.return_value = mock_commits
        result = await agent.fetch_commit_data(hours=24)

    assert len(result) == 1
    assert result[0]["sha"] == "abc123"


@pytest.mark.asyncio
async def test_stale_pr_detection() -> None:
    """Test that stale PRs are properly flagged."""
    agent = GitHubAgent()
    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()

    with patch("agents.github_agent.fetch_open_prs") as mock_fetch:
        mock_fetch.invoke.return_value = [
            {"id": 1, "title": "Stale PR", "status": "open", "is_stale": True,
             "author": "dev1", "updated_at": three_days_ago},
            {"id": 2, "title": "Fresh PR", "status": "open", "is_stale": False,
             "author": "dev2", "updated_at": datetime.now(timezone.utc).isoformat()},
        ]
        result = await agent.fetch_pr_data()

    stale_prs = [p for p in result if p.get("is_stale")]
    fresh_prs = [p for p in result if not p.get("is_stale")]
    assert len(stale_prs) == 1
    assert stale_prs[0]["id"] == 1
    assert len(fresh_prs) == 1
    assert fresh_prs[0]["id"] == 2


@pytest.mark.asyncio
async def test_github_auth_failure_handled() -> None:
    """Test that GitHub auth errors don't crash the agent."""
    agent = GitHubAgent()

    with patch("agents.github_agent.fetch_open_prs") as mock_fetch:
        mock_fetch.invoke.side_effect = Exception("Bad credentials")
        result = await agent.fetch_pr_data()

    assert result == []


@pytest.mark.asyncio
async def test_analyze_prs_empty() -> None:
    """Test PR analysis with empty list."""
    agent = GitHubAgent()
    result = await agent.analyze_prs([])
    assert "No open pull requests" in result
