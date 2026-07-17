#!/usr/bin/env python3
"""SprintSense — AI Sprint Intelligence Agent.

Entry point for manual agent runs (non-API mode).
Runs the full LangGraph pipeline and prints results.

Usage:
    python main.py [--sprint-id SPRINT_ID] [--dashboard-url URL] [--skip-notifications]

Examples:
    python main.py
    python main.py --sprint-id 123
    python main.py --skip-notifications
"""

import argparse
import asyncio
import json
import logging
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import get_settings, setup_logging
from agents.sprint_master_agent import create_sprint_analysis_graph
from models.sprint_state import SprintState

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="SprintSense — AI Sprint Intelligence Agent",
    )
    parser.add_argument(
        "--sprint-id",
        type=str,
        default=None,
        help="Jira sprint ID to analyze (default: active sprint)",
    )
    parser.add_argument(
        "--dashboard-url",
        type=str,
        default=None,
        help="Dashboard URL for screenshot capture (default: Jira board URL from config)",
    )
    parser.add_argument(
        "--skip-notifications",
        action="store_true",
        help="Skip sending Slack/email notifications",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for the report (default: print to stdout)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    return parser.parse_args()


async def main() -> None:
    """Run the SprintSense agent pipeline."""
    args = parse_args()
    setup_logging()
    settings = get_settings()

    print("=" * 60)
    print("  SprintSense — AI Sprint Intelligence Agent")
    print("=" * 60)
    print()
    print(f"Environment:    {settings.app_env}")
    print(f"Jira Project:   {settings.jira_project_key}")
    print(f"GitHub Repo:    {settings.github_repo_owner}/{settings.github_repo_name}")
    print(f"Sprint ID:      {args.sprint_id or '(active sprint)'}")
    print()

    # Validate configuration
    missing_keys = []
    if not settings.openai_api_key:
        missing_keys.append("OPENAI_API_KEY")
    if not settings.jira_base_url:
        missing_keys.append("JIRA_BASE_URL")
    if not settings.github_token:
        missing_keys.append("GITHUB_TOKEN")
    if not settings.slack_bot_token:
        missing_keys.append("SLACK_BOT_TOKEN")

    if missing_keys:
        print(f"⚠️  WARNING: Missing API keys: {', '.join(missing_keys)}")
        print(f"   Some features may not work. Update .env file.")
        print()

    # Build initial state
    initial_state: SprintState = {
        "sprint_id": args.sprint_id or "",
        "sprint_name": "",
        "tickets": [],
        "prs": [],
        "slack_messages": [],
        "blockers": [],
        "velocity": 0.0,
        "completion_probability": 0.0,
        "risk_level": "MEDIUM",
        "screenshot_analysis": "",
        "standup_summary": "",
        "voice_summary_path": "",
        "retrospective": "",
        "notifications_sent": not args.skip_notifications,
        "errors": [],
    }

    print("🚀 Starting sprint analysis pipeline...")
    print()

    try:
        graph = create_sprint_analysis_graph()
        result = await graph.ainvoke(
            initial_state,
            {"configurable": {"thread_id": "sprint-analysis-cli"}},
        )

        print()
        print("=" * 60)
        print("  ✅ ANALYSIS COMPLETE")
        print("=" * 60)
        print()

        sprint_name = result.get("sprint_name", "Unknown Sprint")
        tickets = result.get("tickets", [])
        prs = result.get("prs", [])
        blockers = result.get("blockers", [])
        velocity = result.get("velocity", 0.0)
        completion_prob = result.get("completion_probability", 0.0)
        risk_level = result.get("risk_level", "MEDIUM")

        print(f"Sprint:         {sprint_name}")
        print(f"Tickets:        {len(tickets)}")
        print(f"PRs:            {len(prs)}")
        print(f"Blockers:       {len(blockers)}")
        print(f"Velocity:       {velocity:.1f} story points")
        print(f"Completion:     {completion_prob:.1%}")
        print(f"Risk Level:     {risk_level}")
        print()

        if blockers:
            print("🚨 BLOCKERS:")
            for b in blockers:
                print(f"  • {b}")
            print()

        if result.get("standup_summary"):
            print("📋 STANDUP SUMMARY:")
            print(result["standup_summary"])
            print()

        if result.get("voice_summary_path"):
            print(f"🔊 Voice summary: {result['voice_summary_path']}")

        if result.get("retrospective"):
            print(f"🔄 Retrospective generated ({len(result['retrospective'])} chars)")

        if result.get("errors"):
            print(f"\n⚠️  Errors ({len(result['errors'])}):")
            for err in result["errors"]:
                print(f"  • {err}")

        # Save report if output file specified
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                # Generate markdown report
                from services.report_generator import ReportGenerator
                generator = ReportGenerator()
                report = generator.generate_sprint_report(
                    sprint_id=result.get("sprint_id", ""),
                    sprint_name=sprint_name,
                    tickets=tickets,
                    prs=prs,
                    blockers=blockers,
                    velocity=velocity,
                    completion_probability=completion_prob,
                    risk_level=risk_level,
                    standup_summary=result.get("standup_summary", ""),
                    retrospective=result.get("retrospective", ""),
                )
                f.write(report.markdown)
            print(f"\n📄 Report saved to: {args.output}")

        # JSON output
        if args.json:
            output = {
                "success": True,
                "sprint_id": result.get("sprint_id", ""),
                "sprint_name": sprint_name,
                "total_tickets": len(tickets),
                "total_prs": len(prs),
                "blockers": blockers,
                "velocity": velocity,
                "completion_probability": completion_prob,
                "risk_level": risk_level,
                "standup_summary": result.get("standup_summary", ""),
                "retrospective": result.get("retrospective", ""),
                "errors": result.get("errors", []),
            }
            print()
            print(json.dumps(output, indent=2))

    except Exception as e:
        logger.error("Pipeline failed: %s", e, exc_info=True)
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
