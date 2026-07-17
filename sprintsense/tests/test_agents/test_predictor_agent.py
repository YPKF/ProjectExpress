"""Tests for the Predictor agent."""

import pytest
from agents.predictor_agent import PredictorAgent


@pytest.fixture
def predictor() -> PredictorAgent:
    """Fixture providing a PredictorAgent instance."""
    return PredictorAgent()


def test_completion_probability_high_velocity(predictor: PredictorAgent) -> None:
    """Test high completion probability with good velocity."""
    tickets = [
        {"id": "P-1", "status": "Done", "story_points": 5},
        {"id": "P-2", "status": "Done", "story_points": 3},
        {"id": "P-3", "status": "In Progress", "story_points": 2},
    ]
    result = predictor.predict(tickets, sprint_days=10, days_elapsed=5)
    assert result["completion_probability"] > 0.5
    assert result["risk_level"] in ("LOW", "MEDIUM")


def test_completion_probability_low_velocity(predictor: PredictorAgent) -> None:
    """Test low completion probability with poor velocity."""
    tickets = [
        {"id": "P-1", "status": "Done", "story_points": 1},
        {"id": "P-2", "status": "To Do", "story_points": 13},
        {"id": "P-3", "status": "To Do", "story_points": 8},
        {"id": "P-4", "status": "To Do", "story_points": 5},
    ]
    result = predictor.predict(tickets, sprint_days=10, days_elapsed=8)
    assert result["completion_probability"] < 0.5


def test_risk_level_returns_high_when_probability_low(predictor: PredictorAgent) -> None:
    """Test HIGH risk when completion probability is low."""
    for config in [("HIGH", 0.0), ("HIGH", 0.2), ("HIGH", 0.29)]:
        expected_risk = config[0]
        prob = config[1]
        risk = predictor.calculator.assess_risk_level(prob)
        assert risk == expected_risk, f"Expected {expected_risk} for prob={prob}, got {risk}"


def test_risk_level_returns_low_when_probability_high(predictor: PredictorAgent) -> None:
    """Test LOW risk when completion probability is high."""
    for prob in [0.7, 0.85, 1.0]:
        risk = predictor.calculator.assess_risk_level(prob)
        assert risk == "LOW", f"Expected LOW for prob={prob}, got {risk}"


def test_velocity_calculation_with_no_completed_tickets(predictor: PredictorAgent) -> None:
    """Test velocity when no tickets are completed."""
    tickets = [
        {"id": "P-1", "status": "To Do", "story_points": 5},
        {"id": "P-2", "status": "In Progress", "story_points": 3},
    ]
    result = predictor.predict(tickets)
    assert result["velocity"] == 0.0
    assert result["completed_tickets"] == 0


def test_medium_risk_for_mid_probability(predictor: PredictorAgent) -> None:
    """Test MEDIUM risk for borderline probabilities."""
    for prob in [0.3, 0.4, 0.5]:
        risk = predictor.calculator.assess_risk_level(prob)
        assert risk == "MEDIUM", f"Expected MEDIUM for prob={prob}, got {risk}"
