"""Tests for the Vision agent."""

from unittest.mock import patch, MagicMock, AsyncMock, mock_open
import pytest

from agents.vision_agent import VisionAgent


@pytest.fixture
def vision_agent() -> VisionAgent:
    """Fixture providing a Vision agent instance."""
    agent = VisionAgent()
    agent.llm = MagicMock()
    return agent


@pytest.mark.asyncio
async def test_screenshot_captured_successfully() -> None:
    """Test successful screenshot capture."""
    agent = VisionAgent()

    with patch("agents.vision_agent.capture_screenshot") as mock_capture:
        mock_capture.invoke.return_value = {
            "success": True,
            "filepath": "/tmp/screenshot.png",
            "error": "",
        }
        with patch.object(agent, '_analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = "Analysis result"
            result = await agent.capture_and_analyze("https://jira.example.com/board")

    assert result["success"] is True
    assert result["screenshot_path"] == "/tmp/screenshot.png"
    assert result["analysis"] == "Analysis result"


@pytest.mark.asyncio
async def test_gpt4o_vision_returns_analysis() -> None:
    """Test that vision analysis returns text."""
    agent = VisionAgent()
    mock_response = MagicMock()
    mock_response.content = "Sprint board shows 5 tickets in progress, 3 done."

    agent.llm.ainvoke = AsyncMock(return_value=mock_response)

    with patch("agents.vision_agent.capture_screenshot") as mock_capture:
        mock_capture.invoke.return_value = {
            "success": True,
            "filepath": "/tmp/board.png",
            "error": "",
        }
        with patch("builtins.open", mock_open(read_data=b"fake-image-data")):
            result = await agent.capture_and_analyze("https://jira.example.com/board")

    assert len(result["analysis"]) > 0
    assert "tickets" in result["analysis"]


@pytest.mark.asyncio
async def test_invalid_screenshot_handled() -> None:
    """Test handling of screenshot capture failure."""
    agent = VisionAgent()

    with patch("agents.vision_agent.capture_screenshot") as mock_capture:
        mock_capture.invoke.return_value = {
            "success": False,
            "filepath": "",
            "error": "Navigation timeout",
        }
        result = await agent.capture_and_analyze("https://invalid-url.com")

    assert result["success"] is False
    assert result["error"] is not None


@pytest.mark.asyncio
async def test_vision_analysis_contains_keywords() -> None:
    """Test that vision analysis contains expected keywords."""
    agent = VisionAgent()

    with patch("agents.vision_agent.capture_screenshot") as mock_capture:
        mock_capture.invoke.return_value = {
            "success": True,
            "filepath": "/tmp/board.png",
            "error": "",
        }
        mock_response = MagicMock()
        mock_response.content = "Analysis: 5 tickets To Do, 3 In Progress, 2 Done. Sprint progress is on track."
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch("builtins.open", mock_open(read_data=b"fake-image-data")):
            result = await agent.capture_and_analyze("https://jira.example.com/board")

    analysis = result["analysis"].lower()
    keywords = ["ticket", "progress", "sprint"]
    for kw in keywords:
        assert kw in analysis, f"Expected '{kw}' in analysis"
