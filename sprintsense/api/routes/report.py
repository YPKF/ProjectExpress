"""Report and blockers API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from agents.jira_agent import JiraAgent
from agents.github_agent import GitHubAgent
from agents.slack_agent import SlackAgent
from agents.predictor_agent import PredictorAgent
from services.blocker_detector import BlockerDetector
from services.velocity_calculator import VelocityCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/blockers")
async def get_blockers(sprint_id: Optional[str] = None) -> dict:
    """Get current blockers across all sources.

    Args:
        sprint_id: Optional sprint ID. Uses active sprint if not provided.

    Returns:
        List of detected blockers.
    """
    try:
        jira = JiraAgent()
        github = GitHubAgent()
        slack = SlackAgent()

        sprint_data = await jira.fetch_sprint_data(sprint_id)
        prs = await github.fetch_pr_data()
        slack_msgs = await slack.fetch_messages()

        detector = BlockerDetector()
        ticket_blockers = detector.detect_from_tickets(sprint_data.get("tickets", []))
        pr_blockers = detector.detect_from_prs(prs)
        slack_blockers = detector.detect_from_slack(
            [{"text": m.get("text", "")} for m in slack_msgs]
        )

        all_blockers = BlockerDetector.deduplicate(
            ticket_blockers + pr_blockers + slack_blockers
        )

        return {
            "success": True,
            "total_blockers": len(all_blockers),
            "blockers": all_blockers,
            "sources": {
                "jira": len(ticket_blockers),
                "github": len(pr_blockers),
                "slack": len(slack_blockers),
            },
        }
    except Exception as e:
        logger.error("Error fetching blockers: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/velocity")
async def get_velocity(sprint_id: Optional[str] = None) -> dict:
    """Get velocity and completion prediction.

    Args:
        sprint_id: Optional sprint ID. Uses active sprint if not provided.

    Returns:
        Velocity and prediction data.
    """
    try:
        jira = JiraAgent()
        sprint_data = await jira.fetch_sprint_data(sprint_id)

        predictor = PredictorAgent()
        prediction = predictor.predict(sprint_data.get("tickets", []))

        prediction_summary = await predictor.generate_prediction_summary(prediction)

        return {
            "success": True,
            **prediction,
            "summary": prediction_summary,
        }
    except Exception as e:
        logger.error("Error calculating velocity: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
