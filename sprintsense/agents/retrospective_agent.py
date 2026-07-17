"""Retrospective agent — auto-generates sprint retrospective documents."""

import logging
from datetime import datetime
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import get_settings

logger = logging.getLogger(__name__)


class RetrospectiveAgent:
    """Agent responsible for generating sprint retrospective documents."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            base_url=self.settings.llm_api_base_url,
            temperature=0.3,
            max_tokens=2048,
        )

    async def generate_retrospective(
        self,
        sprint_name: str,
        tickets: list[dict],
        prs: list[dict],
        blockers: list[str],
        velocity: float,
        completion_probability: float,
        risk_level: str,
    ) -> str:
        """Generate a sprint retrospective using LLM.

        Args:
            sprint_name: Sprint name.
            tickets: List of ticket dicts.
            prs: List of PR dicts.
            blockers: List of blocker descriptions.
            velocity: Sprint velocity.
            completion_probability: Completion probability.
            risk_level: Risk level.

        Returns:
            Markdown retrospective document.
        """
        # Build summary data
        total_tickets = len(tickets)
        completed = sum(
            1 for t in tickets
            if (t.get("status") or "").lower() in ("done", "closed", "resolved")
        )
        in_progress = sum(
            1 for t in tickets
            if (t.get("status") or "").lower() == "in progress"
        )
        blocked_count = sum(
            1 for t in tickets
            if t.get("is_blocked") or (t.get("status") or "").lower() == "blocked"
        )

        ticket_lines = "\n".join(
            f"- {t['id']}: {t['summary']} [{t['status']}]"
            for t in tickets[:30]
        ) if tickets else "No tickets."

        pr_lines = "\n".join(
            f"- PR #{p['id']}: {p['title']} ({p.get('status', 'unknown')})"
            for p in prs[:15]
        ) if prs else "No PRs."

        blocker_lines = "\n".join(f"- {b}" for b in blockers) if blockers else "No blockers."

        try:
            messages = [
                SystemMessage(
                    content="You are an agile retrospective facilitator. Generate a detailed sprint "
                            "retrospective document in markdown format. Include sections for:\n"
                            "1. Sprint Overview\n"
                            "2. What Went Well\n"
                            "3. What Could Be Improved\n"
                            "4. Action Items\n"
                            "5. Blockers and Risks\n"
                            "6. Team Health\n\n"
                            "Be constructive, specific, and data-driven."
                ),
                HumanMessage(content=(
                    f"Generate a retrospective for {sprint_name}.\n\n"
                    f"Sprint Data:\n"
                    f"- Total Tickets: {total_tickets}\n"
                    f"- Completed: {completed}\n"
                    f"- In Progress: {in_progress}\n"
                    f"- Blocked: {blocked_count}\n"
                    f"- Velocity: {velocity:.1f} story points\n"
                    f"- Completion Probability: {completion_probability:.1%}\n"
                    f"- Risk Level: {risk_level}\n\n"
                    f"Tickets:\n{ticket_lines}\n\n"
                    f"PRs:\n{pr_lines}\n\n"
                    f"Blockers:\n{blocker_lines}\n\n"
                    f"Generate a comprehensive markdown retrospective based on this data."
                )),
            ]

            response = await self.llm.ainvoke(messages)
            retrospective_text = response.content

            # Add metadata header
            header = (
                f"# Sprint Retrospective: {sprint_name}\n"
                f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} by SprintSense*\n\n"
                f"---\n\n"
            )
            return header + retrospective_text

        except Exception as e:
            logger.error("Error generating retrospective: %s", e)
            return self._generate_fallback_retrospective(
                sprint_name, total_tickets, completed, velocity, blockers
            )

    def _generate_fallback_retrospective(
        self,
        sprint_name: str,
        total_tickets: int,
        completed: int,
        velocity: float,
        blockers: list[str],
    ) -> str:
        """Generate a basic retrospective without LLM (fallback).

        Args:
            sprint_name: Sprint name.
            total_tickets: Total ticket count.
            completed: Completed ticket count.
            velocity: Sprint velocity.
            blockers: List of blockers.

        Returns:
            Basic markdown retrospective.
        """
        lines = [
            f"# Sprint Retrospective: {sprint_name}",
            f"*Auto-generated by SprintSense*",
            "",
            f"## Sprint Overview",
            f"- Total Tickets: {total_tickets}",
            f"- Completed: {completed}",
            f"- Velocity: {velocity:.1f} story points",
            "",
            f"## What Went Well",
            f"- {completed}/{total_tickets} tickets completed ({int(completed/total_tickets*100) if total_tickets else 0}%)",
            "",
            f"## What Could Be Improved",
            f"- Sprint velocity tracking and forecasting accuracy",
            "",
            f"## Action Items",
            f"- Review blocker resolution process",
            f"- Improve ticket estimation accuracy",
            "",
        ]
        if blockers:
            lines.extend([
                f"## Blockers and Risks",
            ])
            for b in blockers:
                lines.append(f"- {b}")
            lines.append("")

        return "\n".join(lines)
