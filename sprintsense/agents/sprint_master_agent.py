"""LangGraph master orchestrator for the SprintSense agent pipeline."""

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from config.settings import get_settings
from models.sprint_state import SprintState
from agents.jira_agent import JiraAgent
from agents.github_agent import GitHubAgent
from agents.slack_agent import SlackAgent
from agents.vision_agent import VisionAgent
from agents.voice_agent import VoiceAgent
from agents.predictor_agent import PredictorAgent
from agents.retrospective_agent import RetrospectiveAgent
from services.blocker_detector import BlockerDetector
from services.velocity_calculator import VelocityCalculator
from services.report_generator import ReportGenerator
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def create_sprint_analysis_graph() -> StateGraph:
    """Construct the LangGraph for sprint analysis.

    Nodes:
    1. fetch_jira
    2. fetch_github
    3. fetch_slack
    4. vision_analysis
    5. blocker_detection
    6. velocity_prediction
    7. standup_summary
    8. voice_generation
    9. report_generation
    10. notification
    11. retrospective

    Conditional edges:
    - High risk → immediate notification
    - Last day of sprint → retrospective
    """

    # ── Node implementations ──────────────────────────────────────

    def fetch_jira_node(state: SprintState) -> dict:
        """Node 1: Fetch sprint tickets from Jira."""
        jira = JiraAgent()
        import asyncio
        try:
            loop = _get_event_loop()
            sprint_data = loop.run_until_complete(
                jira.fetch_sprint_data(state.get("sprint_id"))
            )
            return {
                "sprint_id": sprint_data.get("sprint_id", state.get("sprint_id", "")),
                "sprint_name": sprint_data.get("sprint_name", state.get("sprint_name", "")),
                "tickets": sprint_data.get("tickets", []),
                "errors": _append_error(state, sprint_data.get("error")),
            }
        except Exception as e:
            logger.error("fetch_jira_node failed: %s", e)
            return {"errors": _append_error(state, str(e))}

    def fetch_github_node(state: SprintState) -> dict:
        """Node 2: Fetch PRs and commits from GitHub."""
        github = GitHubAgent()
        import asyncio
        try:
            loop = _get_event_loop()
            prs = loop.run_until_complete(github.fetch_pr_data())
            return {"prs": prs}
        except Exception as e:
            logger.error("fetch_github_node failed: %s", e)
            return {"errors": _append_error(state, str(e))}

    def fetch_slack_node(state: SprintState) -> dict:
        """Node 3: Fetch recent Slack messages."""
        slack = SlackAgent()
        import asyncio
        try:
            loop = _get_event_loop()
            messages = loop.run_until_complete(slack.fetch_messages(limit=50))
            return {"slack_messages": [m.get("text", "") for m in messages]}
        except Exception as e:
            logger.error("fetch_slack_node failed: %s", e)
            return {"errors": _append_error(state, str(e))}

    def vision_analysis_node(state: SprintState) -> dict:
        """Node 4: Capture and analyze sprint board screenshot."""
        settings = get_settings()
        vision = VisionAgent()
        import asyncio
        try:
            loop = _get_event_loop()
            dashboard_url = (
                f"{settings.jira_base_url}/secure/RapidBoard.jspa?projectKey={settings.jira_project_key}"
                if settings.jira_base_url else ""
            )
            if dashboard_url:
                analysis = loop.run_until_complete(
                    vision.analyze_sprint_board(dashboard_url)
                )
            else:
                analysis = "Jira URL not configured; skipping vision analysis."
            return {"screenshot_analysis": analysis}
        except Exception as e:
            logger.warning("Vision analysis skipped: %s", e)
            return {"screenshot_analysis": "Vision analysis unavailable.", "errors": _append_error(state, str(e))}

    def blocker_detection_node(state: SprintState) -> dict:
        """Node 5: Detect blockers from tickets, PRs, and Slack."""
        detector = BlockerDetector()
        tickets = state.get("tickets", [])
        prs = state.get("prs", [])
        slack_msgs = [{"text": m} for m in state.get("slack_messages", [])]
        blockers = detector.detect_all(tickets, prs, slack_msgs)
        return {"blockers": blockers}

    def velocity_prediction_node(state: SprintState) -> dict:
        """Node 6: Calculate velocity and predict completion."""
        predictor = PredictorAgent()
        tickets = state.get("tickets", [])
        prediction = predictor.predict(tickets)
        return {
            "velocity": prediction["velocity"],
            "completion_probability": prediction["completion_probability"],
            "risk_level": prediction["risk_level"],
        }

    def standup_summary_node(state: SprintState) -> dict:
        """Node 7: Generate standup summary text."""
        tickets = state.get("tickets", [])
        prs = state.get("prs", [])
        blockers = state.get("blockers", [])
        velocity = state.get("velocity", 0.0)
        risk = state.get("risk_level", "MEDIUM")

        completed = sum(
            1 for t in tickets
            if (t.get("status") or "").lower() in ("done", "closed", "resolved")
        )
        total = len(tickets)
        in_progress = sum(
            1 for t in tickets
            if (t.get("status") or "").lower() == "in progress"
        )
        stale_prs = sum(1 for p in prs if p.get("is_stale"))

        summary_parts = [
            f"*Today's Standup — {state.get('sprint_name', 'Current Sprint')}*",
            f"",
            f"📊 *Progress:* {completed}/{total} tickets completed ({int(completed/total*100) if total else 0}%).",
            f"🔄 *In Progress:* {in_progress} tickets",
            f"⚡ *Velocity:* {velocity:.1f} story points",
            f"🎯 *Completion Probability:* {state.get('completion_probability', 0)*100:.0f}%",
            f"⚠️ *Risk Level:* {risk}",
        ]

        if blockers:
            summary_parts.append(f"\n🚨 *Blockers ({len(blockers)}):*")
            for b in blockers[:5]:
                summary_parts.append(f"  • {b}")

        if stale_prs > 0:
            summary_parts.append(f"\n⏰ *Stale PRs:* {stale_prs} need attention")

        if in_progress > 0:
            in_progress_tickets = [t for t in tickets if (t.get("status") or "").lower() == "in progress"]
            summary_parts.append(f"\n💪 *In Progress:*")
            for t in in_progress_tickets[:5]:
                summary_parts.append(f"  • {t.get('id', '')}: {t.get('summary', '')[:60]}")

        summary_parts.append(f"\n🤖 Generated by SprintSense")

        return {"standup_summary": "\n".join(summary_parts)}

    def voice_generation_node(state: SprintState) -> dict:
        """Node 8: Convert standup summary to audio."""
        voice = VoiceAgent()
        summary = state.get("standup_summary", "")
        import asyncio
        try:
            loop = _get_event_loop()
            result = loop.run_until_complete(
                voice.generate_summary_audio(summary)
            )
            return {"voice_summary_path": result.get("filepath", "")}
        except Exception as e:
            logger.warning("Voice generation skipped: %s", e)
            return {"voice_summary_path": "", "errors": _append_error(state, str(e))}

    def report_generation_node(state: SprintState) -> dict:
        """Node 9: Generate the full markdown sprint report."""
        generator = ReportGenerator()
        report = generator.generate_sprint_report(
            sprint_id=state.get("sprint_id", ""),
            sprint_name=state.get("sprint_name", "Unknown Sprint"),
            tickets=state.get("tickets", []),
            prs=state.get("prs", []),
            blockers=state.get("blockers", []),
            velocity=state.get("velocity", 0.0),
            completion_probability=state.get("completion_probability", 0.0),
            risk_level=state.get("risk_level", "MEDIUM"),
            standup_summary=state.get("standup_summary", ""),
            retrospective=state.get("retrospective", ""),
        )
        # Store report markdown on state for API use
        return {"report_markdown": report.markdown}

    def notification_node(state: SprintState) -> dict:
        """Node 10: Send alerts and notifications based on risk level."""
        notifications_sent = state.get("notifications_sent", False)
        if notifications_sent:
            return {}

        import asyncio
        try:
            loop = _get_event_loop()
            risk = state.get("risk_level", "MEDIUM")
            blockers = state.get("blockers", [])
            sprint_name = state.get("sprint_name", "Current Sprint")

            if risk == "HIGH" and blockers:
                loop.run_until_complete(
                    NotificationService.notify_risk_alert(
                        risk_level=risk,
                        sprint_name=sprint_name,
                        completion_probability=state.get("completion_probability", 0.0),
                    )
                )
                loop.run_until_complete(
                    NotificationService.notify_blockers(
                        blockers=blockers, sprint_name=sprint_name
                    )
                )
            elif risk == "MEDIUM":
                loop.run_until_complete(
                    NotificationService.notify_risk_alert(
                        risk_level=risk,
                        sprint_name=sprint_name,
                        completion_probability=state.get("completion_probability", 0.0),
                    )
                )

            loop.run_until_complete(
                NotificationService.notify_report_ready(sprint_name)
            )

        except Exception as e:
            logger.warning("Notification node had issues: %s", e)

        return {"notifications_sent": True}

    def retrospective_node(state: SprintState) -> dict:
        """Node 11: Generate sprint retrospective."""
        retro = RetrospectiveAgent()
        import asyncio
        try:
            loop = _get_event_loop()
            text = loop.run_until_complete(
                retro.generate_retrospective(
                    sprint_name=state.get("sprint_name", "Unknown Sprint"),
                    tickets=state.get("tickets", []),
                    prs=state.get("prs", []),
                    blockers=state.get("blockers", []),
                    velocity=state.get("velocity", 0.0),
                    completion_probability=state.get("completion_probability", 0.0),
                    risk_level=state.get("risk_level", "MEDIUM"),
                )
            )
            return {"retrospective": text}
        except Exception as e:
            logger.error("Retrospective generation failed: %s", e)
            return {"errors": _append_error(state, str(e))}

    # ── Conditional edge logic ────────────────────────────────────

    def should_notify_early(state: SprintState) -> Literal["notification", "standup_summary"]:
        """If risk is HIGH, notify immediately before standup."""
        if state.get("risk_level") == "HIGH":
            return "notification"
        return "standup_summary"

    def should_generate_retro(state: SprintState) -> Literal["retrospective", END]:
        """Generate retrospective if sprint is ending."""
        # For simplicity, always generate retrospective at end unless skipped
        return "retrospective"

    def should_notify_final(state: SprintState) -> Literal["notification", END]:
        """Send notifications unless already sent."""
        if not state.get("notifications_sent"):
            return "notification"
        return END

    # ── Build graph ───────────────────────────────────────────────

    workflow = StateGraph(SprintState)

    # Add nodes
    workflow.add_node("fetch_jira", fetch_jira_node)
    workflow.add_node("fetch_github", fetch_github_node)
    workflow.add_node("fetch_slack", fetch_slack_node)
    workflow.add_node("vision_analysis", vision_analysis_node)
    workflow.add_node("blocker_detection", blocker_detection_node)
    workflow.add_node("velocity_prediction", velocity_prediction_node)
    workflow.add_node("standup_summary", standup_summary_node)
    workflow.add_node("voice_generation", voice_generation_node)
    workflow.add_node("report_generation", report_generation_node)
    workflow.add_node("notification", notification_node)
    workflow.add_node("retrospective", retrospective_node)

    # Set entry point
    workflow.set_entry_point("fetch_jira")

    # Sequential edges with parallelism
    workflow.add_edge("fetch_jira", "fetch_github")
    workflow.add_edge("fetch_github", "fetch_slack")
    workflow.add_edge("fetch_slack", "vision_analysis")
    workflow.add_edge("vision_analysis", "blocker_detection")
    workflow.add_edge("blocker_detection", "velocity_prediction")

    # Conditional from velocity_prediction
    workflow.add_conditional_edges(
        "velocity_prediction",
        should_notify_early,
        {
            "notification": "notification",
            "standup_summary": "standup_summary",
        },
    )

    # Notified early → skip notification after voice
    def set_notified(state: SprintState) -> dict:
        return {"notifications_sent": True}

    workflow.add_node("mark_notified", set_notified)
    workflow.add_edge("notification", "mark_notified")
    workflow.add_edge("mark_notified", "standup_summary")

    # Standard path after standup
    workflow.add_edge("standup_summary", "voice_generation")
    workflow.add_edge("voice_generation", "report_generation")

    # Conditional: retrospective or not
    workflow.add_conditional_edges(
        "report_generation",
        should_generate_retro,
        {
            "retrospective": "retrospective",
            END: END,
        },
    )

    # After retrospective, notify if not already done
    workflow.add_conditional_edges(
        "retrospective",
        should_notify_final,
        {
            "notification": "notification",
            END: END,
        },
    )

    # Compile
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def _get_event_loop():
    """Get or create an asyncio event loop."""
    import asyncio
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def _append_error(state: SprintState, error: str | None) -> list[str]:
    """Append an error string to the state errors list."""
    if not error:
        return state.get("errors", [])
    current = state.get("errors", [])
    return current + [error]
