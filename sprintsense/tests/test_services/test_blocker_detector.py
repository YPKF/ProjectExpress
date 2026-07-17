"""Tests for the BlockerDetector service."""

import pytest
from services.blocker_detector import BlockerDetector


@pytest.fixture
def detector() -> BlockerDetector:
    """Fixture providing a BlockerDetector instance."""
    return BlockerDetector()


def test_blocker_detected_from_jira_label(detector: BlockerDetector) -> None:
    """Test blocker detection from Jira ticket labels."""
    tickets = [
        {
            "id": "PROJ-1",
            "summary": "Fix login issue",
            "description": "Users cannot log in",
            "labels": ["blocked"],
            "assignee": "Alice",
        }
    ]
    blockers = detector.detect_from_tickets(tickets)
    assert len(blockers) == 1
    assert "PROJ-1" in blockers[0]


def test_blocker_detected_from_slack_keyword(detector: BlockerDetector) -> None:
    """Test blocker detection from Slack messages."""
    messages = [
        {"user": "U001", "text": "I'm blocked on the database migration"},
        {"user": "U002", "text": "Everything is going well"},
    ]
    blockers = detector.detect_from_slack(messages)
    assert len(blockers) == 1
    assert "blocked" in blockers[0].lower()


def test_no_blocker_when_clean_sprint(detector: BlockerDetector) -> None:
    """Test no false positives with clean data."""
    tickets = [
        {"id": "PROJ-1", "summary": "Build feature X", "description": "Implement feature", "labels": [], "assignee": "Bob"},
    ]
    messages = [
        {"user": "U001", "text": "Great progress today!"},
    ]
    prs = [
        {"id": 1, "title": "Add feature", "description": "All good", "labels": [], "is_stale": False, "author": "dev"},
    ]
    blockers = detector.detect_all(tickets=tickets, prs=prs, slack_messages=messages)
    assert len(blockers) == 0


def test_multiple_blockers_detected(detector: BlockerDetector) -> None:
    """Test detection of multiple blockers."""
    tickets = [
        {"id": "PROJ-1", "summary": "Blocked by API", "description": "", "labels": [], "assignee": "Alice"},
        {"id": "PROJ-2", "summary": "Normal task", "description": "", "labels": ["blocker"], "assignee": "Bob"},
        {"id": "PROJ-3", "summary": "Another task", "description": "", "labels": [], "assignee": "Charlie"},
    ]
    blockers = detector.detect_from_tickets(tickets)
    assert len(blockers) >= 2


def test_blocker_deduplication(detector: BlockerDetector) -> None:
    """Test that duplicate blockers are removed."""
    blockers = ["Blocker A", "Blocker B", "Blocker A"]
    deduped = BlockerDetector.deduplicate(blockers)
    assert len(deduped) == 2
    assert deduped == ["Blocker A", "Blocker B"]


def test_blocker_detection_from_stale_pr(detector: BlockerDetector) -> None:
    """Test stale PRs are detected as blockers."""
    prs = [
        {"id": 1, "title": "Old feature branch", "description": "", "labels": [],
         "is_stale": True, "is_draft": False, "author": "dev1"},
    ]
    blockers = detector.detect_from_prs(prs)
    assert len(blockers) == 1
    assert "Stale" in blockers[0]


def test_blocker_keyword_in_summary(detector: BlockerDetector) -> None:
    """Test blocker keyword detection in ticket summary."""
    tickets = [
        {"id": "PROJ-1", "summary": "Fix waiting for deployment", "description": "", "labels": [], "assignee": "Alice"},
    ]
    blockers = detector.detect_from_tickets(tickets)
    assert len(blockers) == 1
    assert "PROJ-1" in blockers[0]
