"""Vision agent — captures and analyzes screenshots via GPT-4o Vision."""

import logging
import base64
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from config.settings import get_settings
from tools.screenshot_tools import capture_screenshot

logger = logging.getLogger(__name__)


class VisionAgent:
    """Agent responsible for capturing screenshots and analyzing them via Vision LLM."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            base_url=self.settings.llm_api_base_url,
            temperature=0.2,
            max_tokens=1024,
        )

    async def capture_and_analyze(self, dashboard_url: str) -> dict:
        """Capture a dashboard screenshot and analyze it with GPT-4o Vision.

        Args:
            dashboard_url: URL of the dashboard/sprint board to capture.

        Returns:
            Dict with 'analysis' text, 'screenshot_path', and 'success' bool.
        """
        result: dict = {
            "analysis": "",
            "screenshot_path": "",
            "success": False,
            "error": None,
        }

        # Capture screenshot
        screenshot = capture_screenshot.invoke({"url": dashboard_url})
        if not screenshot.get("success"):
            error_msg = screenshot.get("error", "Unknown screenshot error")
            logger.error("Screenshot capture failed: %s", error_msg)
            result["error"] = error_msg
            return result

        result["screenshot_path"] = screenshot["filepath"]

        # Analyze with Vision
        try:
            analysis = await self._analyze_image(screenshot["filepath"])
            result["analysis"] = analysis
            result["success"] = True
        except Exception as e:
            logger.error("Vision analysis failed: %s", e, exc_info=True)
            result["error"] = str(e)

        return result

    async def analyze_sprint_board(self, dashboard_url: str) -> str:
        """Convenience wrapper to just get the analysis text.

        Args:
            dashboard_url: URL to capture.

        Returns:
            Analysis text.
        """
        result = await self.capture_and_analyze(dashboard_url)
        return result.get("analysis") or "Vision analysis was not available."

    async def _analyze_image(self, image_path: str) -> str:
        """Send a screenshot image to GPT-4o Vision for analysis.

        Args:
            image_path: Path to the screenshot file.

        Returns:
            Analysis text describing the sprint board state.
        """
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            image_url = f"data:image/png;base64,{image_data}"

            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": (
                            "Analyze this sprint board screenshot. Identify:\n"
                            "1. Number of tickets in each column (To Do, In Progress, Done)\n"
                            "2. Any tickets that appear blocked or stuck\n"
                            "3. Overall sprint progress and health\n"
                            "4. Any visual indicators of risk or delay\n\n"
                            "Provide a concise summary."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "high"},
                    },
                ]
            )

            response = await self.llm.ainvoke([message])
            return response.content

        except FileNotFoundError:
            logger.error("Screenshot file not found: %s", image_path)
            return "Screenshot file not found for analysis."
        except Exception as e:
            logger.error("Image analysis error: %s", e)
            raise
