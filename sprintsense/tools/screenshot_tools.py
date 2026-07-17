"""Playwright-based screenshot capture tool."""

import logging
import os
from datetime import datetime
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshots")


def _ensure_screenshots_dir() -> str:
    """Create and return the screenshots directory path."""
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    return SCREENSHOTS_DIR


@tool
def capture_screenshot(url: str, output_name: Optional[str] = None) -> dict:
    """Capture a screenshot of a given URL using Playwright.

    Args:
        url: The URL to capture.
        output_name: Optional filename (without extension). Auto-generated if omitted.

    Returns:
        Dict with 'success', 'filepath', and 'error' fields.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("playwright not installed. Run: pip install playwright && playwright install chromium")
        return {"success": False, "error": "playwright not installed", "filepath": ""}

    screenshots_dir = _ensure_screenshots_dir()
    filename = output_name or f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    filepath = os.path.join(screenshots_dir, f"{filename}.png")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.screenshot(path=filepath, full_page=True)
            browser.close()

        logger.info("Screenshot saved to %s", filepath)
        return {"success": True, "filepath": filepath, "error": ""}
    except Exception as e:
        logger.error("Screenshot capture failed: %s", e)
        return {"success": False, "error": str(e), "filepath": ""}
