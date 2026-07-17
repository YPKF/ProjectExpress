"""Pydantic model for Jira tickets."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    """Jira ticket statuses mapped to a normalized enum."""

    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    BLOCKED = "Blocked"
    BACKLOG = "Backlog"
    CANCELLED = "Cancelled"

    @classmethod
    def from_jira(cls, status_name: str) -> "TicketStatus":
        """Map a Jira status name to a normalized TicketStatus."""
        mapping = {
            "to do": cls.TODO,
            "todo": cls.TODO,
            "open": cls.TODO,
            "in progress": cls.IN_PROGRESS,
            "in review": cls.IN_REVIEW,
            "code review": cls.IN_REVIEW,
            "done": cls.DONE,
            "closed": cls.DONE,
            "resolved": cls.DONE,
            "blocked": cls.BLOCKED,
            "blocker": cls.BLOCKED,
            "backlog": cls.BACKLOG,
            "cancelled": cls.CANCELLED,
            "canceled": cls.CANCELLED,
        }
        return mapping.get(status_name.strip().lower(), cls.TODO)


class Ticket(BaseModel):
    """Normalized representation of a Jira ticket."""

    id: str = Field(..., description="Jira issue key, e.g. PROJ-123")
    summary: str = Field(default="", description="Ticket summary/title")
    description: str = Field(default="", description="Full ticket description")
    status: TicketStatus = Field(default=TicketStatus.TODO, description="Current status")
    assignee: Optional[str] = Field(default=None, description="Assigned user display name")
    priority: str = Field(default="Medium", description="Priority: High, Medium, Low")
    story_points: Optional[float] = Field(default=None, description="Story point estimate")
    labels: list[str] = Field(default_factory=list, description="Jira labels")
    sprint_name: Optional[str] = Field(default=None, description="Sprint name")
    created: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated: Optional[datetime] = Field(default=None, description="Last update timestamp")
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    is_blocked: bool = Field(default=False, description="Whether this ticket is blocked")
    blocker_reason: Optional[str] = Field(default=None, description="Why the ticket is blocked")

    model_config = {"frozen": False}
