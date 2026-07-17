"""LangGraph SprintState TypedDict for agent orchestration."""

from typing import TypedDict, List


class SprintState(TypedDict):
    """State passed through the LangGraph agent pipeline."""

    sprint_id: str
    sprint_name: str
    tickets: List[dict]
    prs: List[dict]
    slack_messages: List[str]
    blockers: List[str]
    velocity: float
    completion_probability: float
    risk_level: str  # LOW / MEDIUM / HIGH
    screenshot_analysis: str
    standup_summary: str
    voice_summary_path: str
    retrospective: str
    notifications_sent: bool
    errors: List[str]
