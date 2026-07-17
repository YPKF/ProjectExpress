"""Sprint analysis API endpoints."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.settings import get_settings
from agents.jira_agent import JiraAgent
from agents.github_agent import GitHubAgent
from agents.slack_agent import SlackAgent
from agents.predictor_agent import PredictorAgent
from agents.retrospective_agent import RetrospectiveAgent
from services.blocker_detector import BlockerDetector
from services.velocity_calculator import VelocityCalculator
from services.report_generator import ReportGenerator
from services.notification_service import NotificationService
from agents.sprint_master_agent import create_sprint_analysis_graph
from models.sprint_state import SprintState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sprint", tags=["sprint"])


class AnalyzeRequest(BaseModel):
    """Request body for sprint analysis."""
    sprint_id: Optional[str] = None
    dashboard_url: Optional[str] = None


@router.post("/analyze")
async def analyze_sprint(request: AnalyzeRequest) -> dict:
    """Trigger a full sprint analysis pipeline.

    Args:
        request: Optional sprint_id and dashboard_url.

    Returns:
        Sprint analysis results.
    """
    try:
        graph = create_sprint_analysis_graph()
        initial_state: SprintState = {
            "sprint_id": request.sprint_id or "",
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
            "notifications_sent": False,
            "errors": [],
        }

        result = await graph.ainvoke(initial_state, {"configurable": {"thread_id": "sprint-analysis-1"}})

        return {
            "success": True,
            "sprint_id": result.get("sprint_id", ""),
            "sprint_name": result.get("sprint_name", ""),
            "total_tickets": len(result.get("tickets", [])),
            "velocity": result.get("velocity", 0.0),
            "completion_probability": result.get("completion_probability", 0.0),
            "risk_level": result.get("risk_level", "MEDIUM"),
            "blockers": result.get("blockers", []),
            "notifications_sent": result.get("notifications_sent", False),
            "errors": result.get("errors", []),
        }
    except Exception as e:
        logger.error("Sprint analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sprint analysis failed: {str(e)}")


@router.get("/{sprint_id}")
async def get_sprint_status(sprint_id: str) -> dict:
    """Get sprint status and metrics.

    Args:
        sprint_id: Jira sprint ID.

    Returns:
        Current sprint status.
    """
    try:
        jira = JiraAgent()
        sprint_data = await jira.fetch_sprint_data(sprint_id)
        tickets = sprint_data.get("tickets", [])

        predictor = PredictorAgent()
        prediction = predictor.predict(tickets)

        return {
            "success": True,
            "sprint_id": sprint_id,
            "sprint_name": sprint_data.get("sprint_name", ""),
            "total_tickets": len(tickets),
            "tickets": tickets,
            "velocity": prediction["velocity"],
            "completion_probability": prediction["completion_probability"],
            "risk_level": prediction["risk_level"],
        }
    except Exception as e:
        logger.error("Error fetching sprint status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sprint_id}/report")
async def get_sprint_report(sprint_id: str) -> dict:
    """Get the markdown sprint report.

    Args:
        sprint_id: Jira sprint ID.

    Returns:
        Sprint report with markdown content.
    """
    try:
        jira = JiraAgent()
        github = GitHubAgent()
        slack = SlackAgent()

        sprint_data = await jira.fetch_sprint_data(sprint_id)
        prs = await github.fetch_pr_data()
        slack_msgs = await slack.fetch_messages()

        tickets = sprint_data.get("tickets", [])
        sprint_name = sprint_data.get("sprint_name", "Unknown Sprint")

        detector = BlockerDetector()
        blockers = detector.detect_all(
            tickets, prs,
            [{"text": m.get("text", "")} for m in slack_msgs]
        )

        predictor = PredictorAgent()
        prediction = predictor.predict(tickets)

        generator = ReportGenerator()
        report = generator.generate_sprint_report(
            sprint_id=sprint_id,
            sprint_name=sprint_name,
            tickets=tickets,
            prs=prs,
            blockers=blockers,
            velocity=prediction["velocity"],
            completion_probability=prediction["completion_probability"],
            risk_level=prediction["risk_level"],
        )

        return {
            "success": True,
            "report": report.model_dump(),
            "markdown": report.markdown,
        }
    except Exception as e:
        logger.error("Error generating report: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sprint_id}/audio")
async def get_sprint_audio(sprint_id: str) -> dict:
    """Get the voice summary audio file path.

    Args:
        sprint_id: Jira sprint ID.

    Returns:
        Audio file path info.
    """
    try:
        from tools.tts_tools import generate_voice_summary

        jira = JiraAgent()
        sprint_data = await jira.fetch_sprint_data(sprint_id)
        tickets = sprint_data.get("tickets", [])

        completed = sum(1 for t in tickets if (t.get("status") or "").lower() in ("done", "closed", "resolved"))
        total = len(tickets)

        summary_text = (
            f"Sprint {sprint_data.get('sprint_name', sprint_id)} standup. "
            f"{completed} out of {total} tickets completed. "
        )

        result = generate_voice_summary.invoke({"text": summary_text, "filename": f"standup_{sprint_id}"})

        return {
            "success": result.get("success", False),
            "filepath": result.get("filepath", ""),
            "error": result.get("error"),
        }
    except Exception as e:
        logger.error("Error generating audio: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrospective")
async def generate_retrospective(sprint_id: Optional[str] = None) -> dict:
    """Generate a sprint retrospective document.

    Args:
        sprint_id: Optional sprint ID. Uses active sprint if not provided.

    Returns:
        Retrospective markdown document.
    """
    try:
        jira = JiraAgent()
        github = GitHubAgent()

        sprint_data = await jira.fetch_sprint_data(sprint_id)
        prs = await github.fetch_pr_data()
        tickets = sprint_data.get("tickets", [])

        predictor = PredictorAgent()
        prediction = predictor.predict(tickets)

        retro_agent = RetrospectiveAgent()
        retro_text = await retro_agent.generate_retrospective(
            sprint_name=sprint_data.get("sprint_name", "Unknown Sprint"),
            tickets=tickets,
            prs=prs,
            blockers=[],
            velocity=prediction["velocity"],
            completion_probability=prediction["completion_probability"],
            risk_level=prediction["risk_level"],
        )

        return {
            "success": True,
            "sprint_id": sprint_data.get("sprint_id", sprint_id or ""),
            "sprint_name": sprint_data.get("sprint_name", ""),
            "retrospective": retro_text,
        }
    except Exception as e:
        logger.error("Error generating retrospective: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
