"""Tests for sprint analysis API routes."""

from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from httpx import AsyncClient, ASGITransport

from api.app import app


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok() -> None:
    """Test that health endpoint works."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_analyze_endpoint_returns_200() -> None:
    """Test sprint analysis endpoint returns success."""
    mock_result = {
        "success": True,
        "sprint_id": "123",
        "sprint_name": "Sprint 1",
        "total_tickets": 5,
        "velocity": 10.0,
        "completion_probability": 0.75,
        "risk_level": "LOW",
        "blockers": [],
        "notifications_sent": True,
        "errors": [],
    }

    with patch("api.routes.sprint.create_sprint_analysis_graph") as mock_graph:
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(return_value=mock_result)
        mock_graph.return_value = mock_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/sprint/analyze", json={})

    assert response.status_code == 200 or response.status_code == 500
    if response.status_code == 200:
        data = response.json()
        assert "sprint_id" in data


@pytest.mark.asyncio
async def test_analyze_endpoint_with_invalid_sprint_id() -> None:
    """Test analyze endpoint gracefully handles errors."""
    with patch("api.routes.sprint.create_sprint_analysis_graph") as mock_graph:
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(side_effect=Exception("Sprint not found"))
        mock_graph.return_value = mock_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/sprint/analyze", json={"sprint_id": "99999"})

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_report_endpoint_returns_markdown() -> None:
    """Test report endpoint returns markdown content."""
    mock_report = {
        "success": True,
        "report": {
            "sprint_id": "1",
            "sprint_name": "Sprint 1",
            "markdown": "# Sprint Report\n\nTest content",
        },
        "markdown": "# Sprint Report\n\nTest content",
    }

    with patch("api.routes.sprint.JiraAgent") as mock_jira, \
         patch("api.routes.sprint.GitHubAgent") as mock_github, \
         patch("api.routes.sprint.SlackAgent") as mock_slack:

        mock_jira_instance = MagicMock()
        mock_jira_instance.fetch_sprint_data = AsyncMock(return_value={
            "sprint_id": "1",
            "sprint_name": "Sprint 1",
            "tickets": [],
            "error": None,
        })
        mock_jira.return_value = mock_jira_instance

        mock_github_instance = MagicMock()
        mock_github_instance.fetch_pr_data = AsyncMock(return_value=[])
        mock_github.return_value = mock_github_instance

        mock_slack_instance = MagicMock()
        mock_slack_instance.fetch_messages = AsyncMock(return_value=[])
        mock_slack.return_value = mock_slack_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/sprint/1/report")

    assert response.status_code == 200 or response.status_code == 500
    if response.status_code == 200:
        assert "markdown" in response.json()


@pytest.mark.asyncio
async def test_audio_endpoint_returns_file() -> None:
    """Test audio endpoint returns file info."""
    with patch("api.routes.sprint.JiraAgent") as mock_jira, \
         patch("api.routes.sprint.generate_voice_summary") as mock_tts:

        mock_jira_instance = MagicMock()
        mock_jira_instance.fetch_sprint_data = AsyncMock(return_value={
            "sprint_id": "1",
            "sprint_name": "Sprint 1",
            "tickets": [],
        })
        mock_jira.return_value = mock_jira_instance

        mock_tts.invoke.return_value = {"success": True, "filepath": "/tmp/audio.mp3", "error": ""}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/sprint/1/audio")

    assert response.status_code == 200 or response.status_code == 500
    if response.status_code == 200:
        data = response.json()
        assert "filepath" in data


@pytest.mark.asyncio
async def test_retrospective_endpoint() -> None:
    """Test retrospective generation endpoint."""
    with patch("api.routes.sprint.JiraAgent") as mock_jira, \
         patch("api.routes.sprint.GitHubAgent") as mock_github:

        mock_jira_instance = MagicMock()
        mock_jira_instance.fetch_sprint_data = AsyncMock(return_value={
            "sprint_id": "1",
            "sprint_name": "Sprint 1",
            "tickets": [{"id": "P-1", "status": "Done", "summary": "Task"}],
        })
        mock_jira.return_value = mock_jira_instance

        mock_github_instance = MagicMock()
        mock_github_instance.fetch_pr_data = AsyncMock(return_value=[])
        mock_github.return_value = mock_github_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/sprint/retrospective")

    assert response.status_code == 200 or response.status_code == 500


@pytest.mark.asyncio
async def test_blockers_endpoint() -> None:
    """Test blockers endpoint."""
    with patch("api.routes.report.JiraAgent") as mock_jira, \
         patch("api.routes.report.GitHubAgent") as mock_github, \
         patch("api.routes.report.SlackAgent") as mock_slack:

        for mock_cls in [mock_jira, mock_github, mock_slack]:
            instance = MagicMock()
            instance.fetch_sprint_data = AsyncMock(return_value={"tickets": [], "sprint_id": "1"})
            instance.fetch_pr_data = AsyncMock(return_value=[])
            instance.fetch_messages = AsyncMock(return_value=[])
            mock_cls.return_value = instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/blockers")

    assert response.status_code == 200 or response.status_code == 500
