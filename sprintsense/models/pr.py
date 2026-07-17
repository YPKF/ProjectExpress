"""Pydantic model for GitHub Pull Requests."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PRStatus(str, Enum):
    """Normalized pull request status."""

    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    DRAFT = "draft"


class PR(BaseModel):
    """Normalized representation of a GitHub Pull Request."""

    id: int = Field(..., description="GitHub PR number")
    title: str = Field(default="", description="PR title")
    description: str = Field(default="", description="PR body/description")
    status: PRStatus = Field(default=PRStatus.OPEN, description="PR status")
    author: Optional[str] = Field(default=None, description="PR author username")
    branch: str = Field(default="", description="Source branch name")
    base_branch: str = Field(default="main", description="Target base branch")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    merged_at: Optional[datetime] = Field(default=None, description="Merge timestamp")
    is_draft: bool = Field(default=False, description="Whether PR is a draft")
    is_stale: bool = Field(default=False, description="Open > 3 days without update")
    labels: list[str] = Field(default_factory=list, description="PR labels")
    commits_count: int = Field(default=0, description="Number of commits")
    additions: int = Field(default=0, description="Lines added")
    deletions: int = Field(default=0, description="Lines deleted")
    url: str = Field(default="", description="PR URL")

    model_config = {"frozen": False}
