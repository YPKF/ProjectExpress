"""Tests for the ReportGenerator service."""

import pytest
from services.report_generator import ReportGenerator


@pytest.fixture
def generator() -> ReportGenerator:
    """Fixture providing a ReportGenerator instance."""
    return ReportGenerator()


def test_report_generated_as_markdown(generator: ReportGenerator) -> None:
    """Test that report is generated as markdown."""
    report = generator.generate_sprint_report(
        sprint_id="1",
        sprint_name="Sprint 1",
        tickets=[],
        prs=[],
        blockers=[],
        velocity=0.0,
        completion_probability=0.0,
        risk_level="LOW",
    )
    assert report.markdown.startswith("#")
    assert len(report.markdown) > 50


def test_report_contains_sprint_name(generator: ReportGenerator) -> None:
    """Test that report contains the sprint name."""
    report = generator.generate_sprint_report(
        sprint_id="1",
        sprint_name="Sprint 42",
        tickets=[],
        prs=[],
        blockers=[],
        velocity=0.0,
        completion_probability=0.0,
        risk_level="LOW",
    )
    assert "Sprint 42" in report.markdown


def test_report_contains_blocker_section(generator: ReportGenerator) -> None:
    """Test that report includes blockers section."""
    report = generator.generate_sprint_report(
        sprint_id="1",
        sprint_name="Sprint 1",
        tickets=[],
        prs=[],
        blockers=["Blocked on database migration"],
        velocity=0.0,
        completion_probability=0.0,
        risk_level="HIGH",
    )
    assert "Blockers" in report.markdown
    assert "database migration" in report.markdown


def test_report_contains_velocity_section(generator: ReportGenerator) -> None:
    """Test that report includes velocity data."""
    report = generator.generate_sprint_report(
        sprint_id="1",
        sprint_name="Sprint 1",
        tickets=[],
        prs=[],
        blockers=[],
        velocity=15.5,
        completion_probability=0.75,
        risk_level="LOW",
    )
    assert "15.5" in report.markdown
    assert "Velocity" in report.markdown


def test_empty_sprint_report_generated(generator: ReportGenerator) -> None:
    """Test report generation with no data."""
    report = generator.generate_sprint_report(
        sprint_id="0",
        sprint_name="Empty Sprint",
        tickets=[],
        prs=[],
        blockers=[],
        velocity=0.0,
        completion_probability=1.0,
        risk_level="LOW",
    )
    assert report.total_tickets == 0
    assert report.completed_tickets == 0
    assert report.markdown is not None
    assert len(report.markdown) > 0


def test_report_with_tickets(generator: ReportGenerator) -> None:
    """Test report with ticket data."""
    tickets = [
        {"id": "P-1", "summary": "Task one", "status": "Done", "assignee": "Alice", "priority": "High"},
        {"id": "P-2", "summary": "Task two", "status": "In Progress", "assignee": "Bob", "priority": "Medium"},
    ]
    report = generator.generate_sprint_report(
        sprint_id="1",
        sprint_name="Sprint 1",
        tickets=tickets,
        prs=[],
        blockers=[],
        velocity=5.0,
        completion_probability=0.5,
        risk_level="MEDIUM",
    )
    assert report.total_tickets == 2
    assert report.completed_tickets == 1
    assert report.in_progress_tickets == 1
    assert "P-1" in report.markdown
    assert "P-2" in report.markdown


def test_report_mixed_data(generator: ReportGenerator) -> None:
    """Test report with mixed data including PRs and blockers."""
    tickets = [
        {"id": "P-1", "summary": "Done task", "status": "Done", "assignee": "Alice", "priority": "High"},
    ]
    prs = [
        {"id": 1, "title": "Feature PR", "status": "open", "author": "dev1", "is_stale": False},
    ]
    report = generator.generate_sprint_report(
        sprint_id="1",
        sprint_name="Sprint 1",
        tickets=tickets,
        prs=prs,
        blockers=["Blocker: database"],
        velocity=3.0,
        completion_probability=0.8,
        risk_level="LOW",
        standup_summary="Good progress today.",
        retrospective="Sprint went well.",
    )
    assert report.total_prs == 1
    assert "Good progress" in report.markdown
    assert "Sprint went well" in report.markdown
    assert "Blocker: database" in report.markdown
