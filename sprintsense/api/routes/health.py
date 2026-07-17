"""Health check endpoint."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint returning service status."""
    return {
        "status": "ok",
        "service": "SprintSense AI Sprint Intelligence Agent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }
