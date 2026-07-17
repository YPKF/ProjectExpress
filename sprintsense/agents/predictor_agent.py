"""Predictor agent — sprint completion prediction and risk assessment."""

import logging
from datetime import datetime
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import get_settings
from services.velocity_calculator import VelocityCalculator

logger = logging.getLogger(__name__)


class PredictorAgent:
    """Agent responsible for predicting sprint completion probability and risk."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.calculator = VelocityCalculator()
        self.llm = ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            base_url=self.settings.llm_api_base_url,
            temperature=0.2,
        )

    def predict(self, tickets: list[dict], sprint_days: int = 14, days_elapsed: int | None = None) -> dict[str, Any]:
        """Predict sprint completion probability and assess risk.

        Args:
            tickets: List of ticket dicts.
            sprint_days: Total sprint duration in days (default 14).
            days_elapsed: Days elapsed (default: auto-calculated as halfway).

        Returns:
            Dict with velocity, completion_probability, risk_level.
        """
        if days_elapsed is None:
            days_elapsed = max(1, sprint_days // 2)

        velocity = self.calculator.calculate_velocity(tickets)
        total_points = self.calculator.calculate_total_points(tickets)
        completion_probability = self.calculator.predict_completion_probability(
            velocity=velocity,
            total_points=total_points,
            days_elapsed=days_elapsed,
            total_days=sprint_days,
        )
        risk_level = self.calculator.assess_risk_level(completion_probability)

        logger.info(
            "Prediction: velocity=%.1f, total=%.1f, prob=%.2f, risk=%s",
            velocity, total_points, completion_probability, risk_level,
        )

        return {
            "velocity": velocity,
            "total_points": total_points,
            "completion_probability": round(completion_probability, 4),
            "risk_level": risk_level,
            "completed_tickets": self.calculator.count_completed_tickets(tickets),
            "total_tickets": len(tickets),
        }

    async def generate_prediction_summary(self, prediction: dict[str, Any]) -> str:
        """Generate a natural-language prediction summary using LLM.

        Args:
            prediction: Prediction dict from self.predict().

        Returns:
            Human-readable prediction summary.
        """
        try:
            messages = [
                SystemMessage(content="You are a sprint forecasting assistant. Given sprint metrics, "
                                      "provide a clear, concise prediction of sprint outcome."),
                HumanMessage(content=(
                    f"Sprint Metrics:\n"
                    f"- Velocity: {prediction['velocity']:.1f} story points\n"
                    f"- Total Points: {prediction['total_points']:.1f}\n"
                    f"- Completion Probability: {prediction['completion_probability']:.1%}\n"
                    f"- Risk Level: {prediction['risk_level']}\n"
                    f"- Tickets Completed: {prediction['completed_tickets']}/{prediction['total_tickets']}\n\n"
                    f"Provide a brief prediction about sprint completion outlook."
                )),
            ]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error("Error generating prediction summary: %s", e)
            return (
                f"Sprint completion probability is {prediction['completion_probability']:.1%} "
                f"with {prediction['risk_level']} risk level."
            )
