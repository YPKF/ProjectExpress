"""Tests for the Slack agent."""

from unittest.mock import patch, MagicMock
import pytest

from agents.slack_agent import SlackAgent


@pytest.fixture
def slack_agent() -> SlackAgent:
    """Fixture providing a Slack agent instance."""
    agent = SlackAgent()
    agent.llm = MagicMock()
    return agent


@pytest.mark.asyncio
async def test_fetch_messages_success() -> None:
    """Test successful message fetch."""
    agent = SlackAgent()
    mock_messages = [
        {"user": "U001", "text": "Sprint looking good", "timestamp": "123.456", "is_bot": False},
        {"user": "U002", "text": "I'm blocked on PROJ-123", "timestamp": "123.789", "is_bot": False},
    ]

    with patch("agents.slack_agent.fetch_channel_messages") as mock_fetch:
        mock_fetch.invoke.return_value = mock_messages
        result = await agent.fetch_messages(limit=10)

    assert len(result) == 2
    assert result[1]["text"] == "I'm blocked on PROJ-123"


@pytest.mark.asyncio
async def test_send_alert_success() -> None:
    """Test successful alert sending."""
    agent = SlackAgent()

    with patch("agents.slack_agent.send_slack_message") as mock_send:
        mock_send.invoke.return_value = {"success": True, "ts": "123.456", "channel": "C001"}
        result = await agent.send_message("Test alert")

    assert result["success"] is True
    assert result["ts"] == "123.456"


@pytest.mark.asyncio
async def test_blocker_keyword_detected_in_message() -> None:
    """Test that messages can be scanned for blocker keywords."""
    agent = SlackAgent()
    messages = [
        {"user": "U001", "text": "I'm blocked on this dependency issue", "timestamp": "123.456"},
    ]

    from services.blocker_detector import BlockerDetector
    detector = BlockerDetector()
    blockers = detector.detect_from_slack(messages)

    assert len(blockers) > 0
    assert "blocked" in blockers[0].lower()


@pytest.mark.asyncio
async def test_empty_channel_handled() -> None:
    """Test that empty channel doesn't cause errors."""
    agent = SlackAgent()

    with patch("agents.slack_agent.fetch_channel_messages") as mock_fetch:
        mock_fetch.invoke.return_value = []
        result = await agent.fetch_messages()

    assert result == []


@pytest.mark.asyncio
async def test_send_standup_summary() -> None:
    """Test sending standup summary."""
    agent = SlackAgent()

    with patch("agents.slack_agent.send_slack_message") as mock_send:
        mock_send.invoke.return_value = {"success": True, "ts": "999.999"}
        result = await agent.send_standup_summary("Standup text", "Sprint 1")

    assert result["success"] is True
