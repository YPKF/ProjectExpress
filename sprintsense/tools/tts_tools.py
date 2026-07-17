"""Text-to-Speech tools for generating voice summaries."""

import logging
import os
from datetime import datetime
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio")


def _ensure_audio_dir() -> str:
    """Create and return the audio output directory path."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    return AUDIO_DIR


@tool
def generate_voice_summary(text: str, filename: Optional[str] = None) -> dict:
    """Convert text to speech using gTTS (Google Text-to-Speech, free).

    Args:
        text: The text content to convert to speech.
        filename: Optional output filename (without extension). Auto-generated if omitted.

    Returns:
        Dict with 'success', 'filepath', and 'error' fields.
    """
    try:
        from gtts import gTTS
    except ImportError:
        logger.error("gTTS not installed. Run: pip install gTTS")
        return {"success": False, "error": "gTTS not installed", "filepath": ""}

    audio_dir = _ensure_audio_dir()
    name = filename or f"standup_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    filepath = os.path.join(audio_dir, f"{name}.mp3")

    try:
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(filepath)
        logger.info("Voice summary saved to %s", filepath)
        return {"success": True, "filepath": filepath, "error": ""}
    except Exception as e:
        logger.error("TTS generation failed: %s", e)
        return {"success": False, "error": str(e), "filepath": ""}
