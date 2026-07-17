"""GitHub agent — fetches and analyzes PRs and commits."""

import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import get_settings
from tools.github_tools import fetch_open_prs, fetch_recent_commits

logger = logging.getLogger(__name__)


class GitHubAgent:
    """Agent responsible for fetching and analyzing GitHub PR/commit data."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            base_url=self.settings.llm_api_base_url,
            temperature=0.1,
        )

    async def fetch_pr_data(self) -> list[dict]:
        """Fetch open pull requests from GitHub.

        Returns:
            List of normalized PR dicts.
        """
        try:
            prs = fetch_open_prs.invoke({})
            logger.info("Fetched %d open PRs", len(prs))
            return prs
        except Exception as e:
            logger.error("GitHub agent error fetching PRs: %s", e, exc_info=True)
            return []

    async def fetch_commit_data(self, hours: int = 24) -> list[dict]:
        """Fetch recent commits.

        Args:
            hours: How many hours back to look.

        Returns:
            List of commit dicts.
        """
        try:
            commits = fetch_recent_commits.invoke({"hours": hours})
            logger.info("Fetched %d recent commits", len(commits))
            return commits
        except Exception as e:
            logger.error("GitHub agent error fetching commits: %s", e, exc_info=True)
            return []

    async def analyze_prs(self, prs: list[dict]) -> str:
        """Use LLM to analyze PR activity and code review health.

        Args:
            prs: List of PR dicts.

        Returns:
            Analysis text.
        """
        if not prs:
            return "No open pull requests."

        try:
            pr_summary = "\n".join(
                f"- PR #{p['id']}: {p['title']} (Author: {p.get('author', 'unknown')}, "
                f"Stale: {'⚠️' if p.get('is_stale') else '✓'})"
                for p in prs[:15]
            )

            messages = [
                SystemMessage(
                    content="You are a code review and engineering workflow analyst. "
                            "Analyze the following pull requests and provide insights."
                ),
                HumanMessage(
                    content=f"Current open PRs:\n\n{pr_summary}\n\n"
                            f"Total PRs: {len(prs)}\n"
                            f"Please analyze the PR health and workflow efficiency."
                ),
            ]

            response = await self.llm.ainvoke(messages)
            return response.content

        except Exception as e:
            logger.error("Error analyzing PRs: %s", e)
            return f"PR analysis available but LLM call failed: {e}"
