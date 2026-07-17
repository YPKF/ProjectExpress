"""Tests for the VelocityCalculator service."""

import pytest
from services.velocity_calculator import VelocityCalculator


@pytest.fixture
def calculator() -> VelocityCalculator:
    """Fixture providing a VelocityCalculator instance."""
    return VelocityCalculator()


def test_velocity_calculated_correctly(calculator: VelocityCalculator) -> None:
    """Test velocity calculation from completed tickets."""
    tickets = [
        {"id": "P-1", "status": "Done", "story_points": 5},
        {"id": "P-2", "status": "Done", "story_points": 3},
        {"id": "P-3", "status": "In Progress", "story_points": 8},
        {"id": "P-4", "status": "To Do", "story_points": 2},
    ]
    velocity = calculator.calculate_velocity(tickets)
    assert velocity == 8.0  # 5 + 3


def test_zero_completed_tickets_returns_zero_velocity(calculator: VelocityCalculator) -> None:
    """Test velocity is zero when no tickets completed."""
    tickets = [
        {"id": "P-1", "status": "To Do", "story_points": 5},
        {"id": "P-2", "status": "In Progress", "story_points": 3},
    ]
    velocity = calculator.calculate_velocity(tickets)
    assert velocity == 0.0


def test_sprint_days_remaining_calculated(calculator: VelocityCalculator) -> None:
    """Test completion probability with specific day parameters."""
    # 5 points done in 5 days out of 10, 10 points remaining
    prob = calculator.predict_completion_probability(
        velocity=5.0,
        total_points=15.0,
        days_elapsed=5,
        total_days=10,
    )
    # Daily rate = 1 point/day, remaining = 10, remaining days = 5
    # Projected = 5, remaining = 10 → below 0.5
    assert prob <= 0.5


def test_story_points_summed_correctly(calculator: VelocityCalculator) -> None:
    """Test total story points calculation."""
    tickets = [
        {"id": "P-1", "status": "Done", "story_points": 5},
        {"id": "P-2", "status": "Done", "story_points": None},
        {"id": "P-3", "status": "In Progress", "story_points": 3},
    ]
    total = calculator.calculate_total_points(tickets)
    assert total == 8.0  # 5 + 0 (None) + 3


def test_high_completion_probability(calculator: VelocityCalculator) -> None:
    """Test high completion probability scenario."""
    prob = calculator.predict_completion_probability(
        velocity=18.0,
        total_points=20.0,
        days_elapsed=5,
        total_days=10,
    )
    # Daily rate = 3.6/day, remaining = 2, remaining days = 5
    # Projected = 18 >> remaining → high probability
    assert prob > 0.5


def test_total_points_zero(calculator: VelocityCalculator) -> None:
    """Test probability when total points is zero."""
    prob = calculator.predict_completion_probability(
        velocity=0.0,
        total_points=0.0,
        days_elapsed=5,
        total_days=10,
    )
    assert prob == 1.0


def test_no_elapsed_time(calculator: VelocityCalculator) -> None:
    """Test probability when sprint just started."""
    prob = calculator.predict_completion_probability(
        velocity=0.0,
        total_points=20.0,
        days_elapsed=0,
        total_days=10,
    )
    assert prob == 0.5  # No data, assume 50%


def test_count_completed_tickets(calculator: VelocityCalculator) -> None:
    """Test counting completed tickets."""
    tickets = [
        {"id": "P-1", "status": "Done"},
        {"id": "P-2", "status": "Resolved"},
        {"id": "P-3", "status": "In Progress"},
    ]
    assert calculator.count_completed_tickets(tickets) == 2


def test_count_blocked_tickets(calculator: VelocityCalculator) -> None:
    """Test counting blocked tickets."""
    tickets = [
        {"id": "P-1", "status": "Blocked", "is_blocked": True},
        {"id": "P-2", "status": "In Progress", "is_blocked": False},
        {"id": "P-3", "status": "Blocked", "is_blocked": True},
    ]
    assert calculator.count_blocked_tickets(tickets) == 3
