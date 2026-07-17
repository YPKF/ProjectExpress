"""Sprint velocity calculation and completion probability prediction."""

import logging
from datetime import datetime, timezone
from typing import Optional

from config.settings import get_settings

logger = logging.getLogger(__name__)


class VelocityCalculator:
    """Calculates sprint velocity and predicts completion probability."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def calculate_velocity(self, tickets: list[dict]) -> float:
        """Calculate sprint velocity from completed tickets' story points.

        Args:
            tickets: List of normalized ticket dicts.

        Returns:
            Total story points completed (velocity).
        """
        total_points = 0.0
        for ticket in tickets:
            status = (ticket.get("status") or "").lower()
            points = ticket.get("story_points")
            if points is not None and status in ("done", "closed", "resolved"):
                try:
                    total_points += float(points)
                except (ValueError, TypeError):
                    continue
        logger.info("Calculated velocity: %.1f story points", total_points)
        return total_points

    def calculate_total_points(self, tickets: list[dict]) -> float:
        """Sum all story points across tickets.

        Args:
            tickets: List of normalized ticket dicts.

        Returns:
            Total story points in the sprint.
        """
        total = 0.0
        for ticket in tickets:
            points = ticket.get("story_points")
            if points is not None:
                try:
                    total += float(points)
                except (ValueError, TypeError):
                    continue
        return total

    def predict_completion_probability(
        self,
        velocity: float,
        total_points: float,
        days_elapsed: int,
        total_days: int,
    ) -> float:
        """Predict the probability of completing all sprint work.

        Uses velocity-to-target ratio adjusted by time remaining.

        Args:
            velocity: Story points completed so far.
            total_points: Total story points in sprint.
            days_elapsed: Days elapsed in the sprint.
            total_days: Total sprint duration in days.

        Returns:
            Probability between 0.0 and 1.0.
        """
        if total_points == 0:
            return 1.0

        if days_elapsed == 0:
            return 0.5  # No data yet, assume 50%

        # Projected velocity based on current pace
        daily_rate = velocity / days_elapsed
        remaining_points = total_points - velocity
        days_remaining = max(total_days - days_elapsed, 1)

        if daily_rate <= 0 and remaining_points > 0:
            return 0.0

        projected_completion = daily_rate * days_remaining
        if projected_completion >= remaining_points:
            # Likely to complete — scale from 0.5 to 1.0
            raw_prob = 0.5 + 0.5 * min(remaining_points / max(projected_completion, 0.01), 1.0)
        else:
            # Unlikely to complete — scale from 0.0 to 0.5
            raw_prob = 0.5 * max(projected_completion / max(remaining_points, 0.01), 0.0)

        return max(0.0, min(1.0, raw_prob))

    def assess_risk_level(self, completion_probability: float) -> str:
        """Determine sprint risk level based on completion probability.

        Args:
            completion_probability: Probability value between 0 and 1.

        Returns:
            'LOW', 'MEDIUM', or 'HIGH' risk level.
        """
        threshold = self.settings.sprint_risk_threshold
        if completion_probability >= threshold:
            return "LOW"
        elif completion_probability >= threshold * 0.5:
            return "MEDIUM"
        else:
            return "HIGH"

    def count_completed_tickets(self, tickets: list[dict]) -> int:
        """Count tickets with completed status.

        Args:
            tickets: List of ticket dicts.

        Returns:
            Count of completed tickets.
        """
        return sum(
            1 for t in tickets
            if (t.get("status") or "").lower() in ("done", "closed", "resolved")
        )

    def count_blocked_tickets(self, tickets: list[dict]) -> int:
        """Count blocked tickets.

        Args:
            tickets: List of ticket dicts.

        Returns:
            Count of blocked tickets.
        """
        return sum(
            1 for t in tickets
            if t.get("is_blocked") or (t.get("status") or "").lower() == "blocked"
        )
