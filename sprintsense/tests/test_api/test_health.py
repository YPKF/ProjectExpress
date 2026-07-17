"""Tests for the health check endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport

from api.app import app


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok() -> None:
    """Test that health endpoint returns 200 with status ok."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "SprintSense" in data["service"]


@pytest.mark.asyncio
async def test_health_endpoint_returns_version() -> None:
    """Test that health endpoint returns version info."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    data = response.json()
    assert "version" in data
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_endpoint_returns_timestamp() -> None:
    """Test that health endpoint includes timestamp."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    data = response.json()
    assert "timestamp" in data
    assert "T" in data["timestamp"]  # ISO format
