"""Pydantic model for sprint reports."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SprintReport(BaseModel):
    """Complete sprint analysis report."""

    sprint_id: str = Field(..., description="Sprint identifier")
    sprint_name: str = Field(..., description="Sprint name")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation timestamp")
    total_tickets: int = Field(default=0, description="Total number of tickets")
    completed_tickets: int = Field(default=0, description="Completed tickets")
    in_progress_tickets: int = Field(default=0, description="Tickets in progress")
    blocked_tickets: int = Field(default=0, description="Blocked tickets")
    total_prs: int = Field(default=0, description="Total pull requests")
    open_prs: int = Field(default=0, description="Open pull requests")
    stale_prs: int = Field(default=0, description="Stale pull requests (>3 days)")
    velocity: float = Field(default=0.0, description="Sprint velocity in story points")
    completion_probability: float = Field(default=0.0, description="Predicted completion probability (0-1)")
    risk_level: str = Field(default="MEDIUM", description="Risk level: LOW, MEDIUM, HIGH")
    blockers: list[str] = Field(default_factory=list, description="Detected blockers")
    standup_summary: str = Field(default="", description="Auto-generated standup text")
    voice_summary_path: str = Field(default="", description="Path to generated audio file")
    retrospective: str = Field(default="", description="Auto-generated retrospective")
    markdown: str = Field(default="", description="Full markdown report text")

    model_config = {"frozen": False}
