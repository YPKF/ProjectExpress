"""Markdown report generation for sprint analysis."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from models.report import SprintReport

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates markdown sprint reports from analysis data."""

    @staticmethod
    def generate_sprint_report(
        sprint_id: str,
        sprint_name: str,
        tickets: list[dict],
        prs: list[dict],
        blockers: list[str],
        velocity: float,
        completion_probability: float,
        risk_level: str,
        standup_summary: str = "",
        retrospective: str = "",
    ) -> SprintReport:
        """Generate a full SprintReport with markdown content.

        Args:
            sprint_id: Sprint identifier.
            sprint_name: Sprint name.
            tickets: List of ticket dicts.
            prs: List of PR dicts.
            blockers: List of blockers.
            velocity: Sprint velocity.
            completion_probability: Completion probability (0-1).
            risk_level: Risk level string.
            standup_summary: Generated standup text.
            retrospective: Generated retrospective text.

        Returns:
            Populated SprintReport instance.
        """
        total_tickets = len(tickets)
        completed_tickets = sum(
            1 for t in tickets
            if (t.get("status") or "").lower() in ("done", "closed", "resolved")
        )
        in_progress_tickets = sum(
            1 for t in tickets
            if (t.get("status") or "").lower() == "in progress"
        )
        blocked_tickets = sum(
            1 for t in tickets
            if t.get("is_blocked") or (t.get("status") or "").lower() == "blocked"
        )

        open_prs_list = [p for p in prs if p.get("status") == "open"]
        stale_prs_list = [p for p in prs if p.get("is_stale")]

        risk_emoji = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🚨"}.get(risk_level, "❓")

        # Build markdown
        markdown_lines = [
            f"# Sprint Report: {sprint_name}",
            f"",
            f"**Sprint ID:** {sprint_id}  ",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"**Risk Level:** {risk_emoji} {risk_level}  ",
            f"**Completion Probability:** {completion_probability:.1%}  ",
            f"",
            f"---",
            f"",
            f"## 📊 Sprint Overview",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Tickets | {total_tickets} |",
            f"| Completed | {completed_tickets} |",
            f"| In Progress | {in_progress_tickets} |",
            f"| Blocked | {blocked_tickets} |",
            f"| Velocity (story points) | {velocity:.1f} |",
            f"| Open PRs | {len(open_prs_list)} |",
            f"| Stale PRs | {len(stale_prs_list)} |",
            f"",
        ]

        # Blockers section
        if blockers:
            markdown_lines.extend([
                f"## 🚨 Blockers ({len(blockers)})",
                f"",
            ])
            for b in blockers:
                markdown_lines.append(f"- {b}")
            markdown_lines.append("")
        else:
            markdown_lines.extend([
                f"## ✅ Blockers",
                f"",
                f"No blockers detected. Sprint is on track.",
                f"",
            ])

        # Tickets section
        markdown_lines.extend([
            f"## 🎫 Tickets",
            f"",
            f"| ID | Summary | Status | Assignee | Priority |",
            f"|----|---------|--------|----------|----------|",
        ])
        for t in tickets:
            markdown_lines.append(
                f"| {t.get('id', '')} | {t.get('summary', '')[:60]} | "
                f"{t.get('status', '')} | {t.get('assignee', 'Unassigned')} | "
                f"{t.get('priority', '')} |"
            )
        markdown_lines.append("")

        # PRs section
        if prs:
            markdown_lines.extend([
                f"## 🔀 Pull Requests",
                f"",
                f"| # | Title | Status | Author | Stale |",
                f"|---|-------|--------|--------|-------|",
            ])
            for p in prs:
                stale_mark = "⚠️" if p.get("is_stale") else "✓"
                markdown_lines.append(
                    f"| #{p.get('id', '')} | {p.get('title', '')[:60]} | "
                    f"{p.get('status', '')} | {p.get('author', 'unknown')} | {stale_mark} |"
                )
            markdown_lines.append("")

        # Standup summary
        if standup_summary:
            markdown_lines.extend([
                f"## 🗣️ Standup Summary",
                f"",
                f"{standup_summary}",
                f"",
            ])

        # Retrospective
        if retrospective:
            markdown_lines.extend([
                f"## 🔄 Retrospective",
                f"",
                f"{retrospective}",
                f"",
            ])

        markdown_lines.append(
            f"---\n*Report generated by SprintSense 🤖*"
        )

        return SprintReport(
            sprint_id=sprint_id,
            sprint_name=sprint_name,
            total_tickets=total_tickets,
            completed_tickets=completed_tickets,
            in_progress_tickets=in_progress_tickets,
            blocked_tickets=blocked_tickets,
            total_prs=len(prs),
            open_prs=len(open_prs_list),
            stale_prs=len(stale_prs_list),
            velocity=velocity,
            completion_probability=completion_probability,
            risk_level=risk_level,
            blockers=blockers,
            standup_summary=standup_summary,
            retrospective=retrospective,
            markdown="\n".join(markdown_lines),
        )
