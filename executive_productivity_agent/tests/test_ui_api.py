"""Automated tests for the Executive Dashboard UI API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from executive_productivity_agent.app_server import app

client = TestClient(app)


def test_serve_dashboard_html():
    """Verifies that the root URL serves the executive dashboard HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Executive Action Brief" in response.text
    assert "Arjun Malhotra" in response.text
    assert "Daily Action Brief" in response.text
    assert "Ask Your Executive Agent" in response.text


def test_get_brief_api():
    """Verifies that /api/brief returns summary counts, conflicts, and 6 sections."""
    response = client.get("/api/brief")
    assert response.status_code == 200
    data = response.json()

    # Verify summary counts
    summary = data["summary"]
    assert summary["overdue_at_risk"] >= 1
    assert summary["needs_action_today"] >= 2
    assert summary["my_commitments"] >= 4
    assert summary["waiting_on_others"] >= 2
    assert summary["unclear_ownership"] >= 2

    # Verify conflict alert data
    conflicts = data["conflicts"]
    assert len(conflicts) >= 1
    apex_conflict = next(c for c in conflicts if "Apex" in c["description"])
    assert "Thursday at 2:00 PM" in str(apex_conflict["conflicting_sources"])
    assert "Friday at 10:00 AM" in str(apex_conflict["conflicting_sources"])

    # Verify sections exist and contain required action keys
    sections = data["sections"]
    assert "overdue_at_risk" in sections
    assert "needs_action_today" in sections
    assert "my_commitments" in sections
    assert "waiting_on_others" in sections
    assert "upcoming" in sections
    assert "unclear_ownership" in sections

    sample_action = sections["needs_action_today"][0]
    for key in ["action", "owner", "deadline", "status", "sources", "evidence", "confidence"]:
        assert key in sample_action, f"Missing key {key} in action card"


def test_ask_agent_api():
    """Verifies that /api/ask responds with grounded answers."""
    response = client.post("/api/ask", json={"question": "What is overdue?"})
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is overdue?"
    assert "headcount budget" in data["answer"].lower() or "overdue" in data["answer"].lower()
    assert len(data["evidence_matches"]) >= 1
