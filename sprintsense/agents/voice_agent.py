"""Voice agent — generates TTS audio summaries."""

import logging
from typing import Optional

from config.settings import get_settings
from tools.tts_tools import generate_voice_summary

logger = logging.getLogger(__name__)


class VoiceAgent:
    """Agent responsible for converting text summaries to speech."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_summary_audio(self, text: str, filename: Optional[str] = None) -> dict:
        """Generate a voice audio file from text.

        Args:
            text: Text content to convert to speech.
            filename: Optional output filename.

        Returns:
            Dict with 'success', 'filepath', and 'error' fields.
        """
        try:
            result = generate_voice_summary.invoke({
                "text": text,
                "filename": filename,
            })
            if result.get("success"):
                logger.info("Voice summary generated: %s", result["filepath"])
            else:
                logger.error("Voice generation failed: %s", result.get("error"))
            return result
        except Exception as e:
            logger.error("Voice agent error: %s", e, exc_info=True)
            return {"success": False, "error": str(e), "filepath": ""}
