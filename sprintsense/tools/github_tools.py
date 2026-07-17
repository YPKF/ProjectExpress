"""GitHub REST API wrappers as LangChain tools."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from github import Github, GithubException, Auth
from langchain_core.tools import tool

from config.settings import get_settings

logger = logging.getLogger(__name__)


def _get_github_client() -> Optional[Github]:
    """Create and return an authenticated GitHub client."""
    settings = get_settings()
    if not settings.github_token:
        logger.warning("GitHub token not configured.")
        return None
    try:
        auth = Auth.Token(settings.github_token)
        return Github(auth=auth, timeout=30)
    except Exception as e:
        logger.error("Failed to connect to GitHub: %s", e)
        return None


def _get_repo(github: Github) -> Optional[object]:
    """Get the configured repository object."""
    settings = get_settings()
    try:
        return github.get_repo(f"{settings.github_repo_owner}/{settings.github_repo_name}")
    except GithubException as e:
        logger.error("GitHub error accessing repo: %s", e)
        return None


@tool
def fetch_open_prs() -> list[dict]:
    """Fetch all open pull requests for the configured repository.

    Returns:
        List of normalized PR dicts with staleness info.
    """
    github = _get_github_client()
    if not github:
        return []

    repo = _get_repo(github)
    if not repo:
        return []

    prs = []
    try:
        three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
        open_prs = repo.get_pulls(state="open", sort="updated", direction="desc")
        for pr in open_prs:
            updated = pr.updated_at if pr.updated_at else datetime.now(timezone.utc)
            is_stale = updated < three_days_ago
            prs.append({
                "id": pr.number,
                "title": pr.title,
                "description": pr.body or "",
                "status": "draft" if pr.draft else "open",
                "author": pr.user.login if pr.user else "unknown",
                "branch": pr.head.ref,
                "base_branch": pr.base.ref,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                "is_draft": pr.draft,
                "is_stale": is_stale,
                "labels": [label.name for label in pr.labels],
                "commits_count": pr.commits,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "url": pr.html_url,
            })
    except GithubException as e:
        logger.error("GitHub error fetching PRs: %s", e)
    return prs


@tool
def fetch_recent_commits(hours: int = 24) -> list[dict]:
    """Fetch commits from the last N hours.

    Args:
        hours: How many hours back to look (default 24).

    Returns:
        List of commit dicts.
    """
    github = _get_github_client()
    if not github:
        return []

    repo = _get_repo(github)
    if not repo:
        return []

    commits = []
    try:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent = repo.get_commits(since=since)
        for commit in recent[:50]:
            commits.append({
                "sha": commit.sha,
                "message": commit.commit.message.split("\n")[0],
                "author": commit.commit.author.name if commit.commit.author else "unknown",
                "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None,
                "url": commit.html_url,
            })
    except GithubException as e:
        logger.error("GitHub error fetching commits: %s", e)
    return commits


@tool
def get_pr_details(pr_number: int) -> dict:
    """Get detailed information about a specific PR.

    Args:
        pr_number: The pull request number.

    Returns:
        Detailed PR info dict.
    """
    github = _get_github_client()
    if not github:
        return {"error": "GitHub client not available"}

    repo = _get_repo(github)
    if not repo:
        return {"error": "Repository not available"}

    try:
        pr = repo.get_pull(pr_number)
        return {
            "id": pr.number,
            "title": pr.title,
            "body": pr.body or "",
            "state": pr.state,
            "is_merged": pr.is_merged() if hasattr(pr, 'is_merged') else pr.merged,
            "mergeable": pr.mergeable,
            "author": pr.user.login if pr.user else "unknown",
            "created_at": pr.created_at.isoformat() if pr.created_at else None,
            "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
            "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
            "comments": pr.comments,
            "review_comments": pr.review_comments,
            "url": pr.html_url,
        }
    except GithubException as e:
        logger.error("GitHub error fetching PR details: %s", e)
        return {"error": str(e)}
