"""Automated test suite for Executive Productivity Agent.

Validates all 6 mandatory demo questions, deduplication, conflict detection,
and safety against hallucination grounded in the assignment dataset.
"""

from __future__ import annotations

import pytest
from executive_productivity_agent.tools.data_loader import load_dataset, get_all_raw_documents
from executive_productivity_agent.tools.commitment_extractor import extract_raw_commitments
from executive_productivity_agent.tools.action_processor import (
    process_and_deduplicate_actions,
    get_actions_by_filter,
)
from executive_productivity_agent.tools.brief_generator import generate_executive_brief
from executive_productivity_agent.agent import (
    get_daily_action_brief,
    search_commitments,
    get_conflict_report,
    inspect_source_evidence,
)


def test_data_loader_integrity():
    """Verifies that the dataset loads properly across all 4 communication channels."""
    ds = load_dataset()
    assert ds.metadata.target_user == "Arjun Malhotra"
    assert len(ds.emails) == 7
    assert len(ds.meeting_transcripts) == 2
    assert len(ds.calendar_events) == 3
    assert len(ds.voice_notes) == 2

    raw_docs = get_all_raw_documents(ds)
    assert len(raw_docs) == 14


def test_q1_what_did_i_promise_raghav():
    """Question 1: 'What did I promise Raghav?'
    Verifies that all commitments made to Raghav are extracted,
    deduplicated, and supported by evidence."""
    actions = get_actions_by_filter(person="Raghav")
    action_titles = [a.action for a in actions]

    # Arjun's promises to Raghav
    assert any("vendor list" in t.lower() for t in action_titles), "Vendor list commitment missing"
    assert any("sales deck" in t.lower() for t in action_titles), "Sales deck commitment missing"

    # Verify deduplication for vendor list across Email, Meeting, and Voice Note
    vendor_action = next(a for a in actions if "vendor list" in a.action.lower())
    assert vendor_action.owner == "Arjun"
    assert len(vendor_action.sources) == 3, f"Expected 3 deduplicated sources, got {len(vendor_action.sources)}"
    assert any("Email" in s for s in vendor_action.sources)
    assert any("Meeting" in s for s in vendor_action.sources)
    assert any("Voice Note" in s for s in vendor_action.sources)
    assert "Wednesday morning" in vendor_action.deadline


def test_q2_what_needs_action_today():
    """Question 2: 'What needs action today?'
    Verifies that actions due today (Wednesday) are identified."""
    all_actions = process_and_deduplicate_actions()
    today_actions = [a for a in all_actions if a.is_due_today and a.category == "my_action"]

    titles = [a.action.lower() for a in today_actions]
    assert any("vendor list" in t for t in titles), "Vendor list due today missing"
    assert any("sales deck" in t for t in titles), "Sales deck due today missing"
    assert any("acme corp renewal" in t for t in titles), "Acme contract due today missing"


def test_q3_what_am_i_waiting_on():
    """Question 3: 'What am I waiting on?'
    Verifies external deliverables owned by others where Arjun is the beneficiary."""
    waiting_actions = get_actions_by_filter(category="waiting_on_others")
    owners = [a.owner for a in waiting_actions]

    assert "Priya Nair" in owners, "Waiting on Priya Nair for discount approval missing"
    assert "Raghav Sharma" in owners, "Waiting on Raghav Sharma for API roadmap missing"

    priya_action = next(a for a in waiting_actions if a.owner == "Priya Nair")
    assert "Zenith" in priya_action.action or "discount" in priya_action.action.lower()
    assert "Thursday 3:00 PM" in priya_action.deadline


def test_q4_what_is_overdue():
    """Question 4: 'What is overdue?'
    Verifies that actions with past deadlines (Tuesday 4 PM) are flagged overdue."""
    overdue_actions = get_actions_by_filter(status="overdue")
    assert len(overdue_actions) >= 1

    headcount_action = overdue_actions[0]
    assert "headcount budget" in headcount_action.action.lower()
    assert headcount_action.owner == "Arjun"
    assert headcount_action.status == "overdue"
    assert "Yesterday Tuesday at 4:00 PM" in headcount_action.deadline


def test_q5_which_actions_have_unclear_ownership():
    """Question 5: 'Which actions have unclear ownership?'
    Verifies that actions without assigned or accepted owners are marked owner='Unclear'."""
    unclear_actions = get_actions_by_filter(category="unclear_ownership")
    assert len(unclear_actions) >= 2

    for a in unclear_actions:
        assert a.owner == "Unclear", f"Owner should be Unclear, got {a.owner}"
        assert a.owner_reason is not None and len(a.owner_reason) > 0, "Missing reason for unclear ownership"

    titles = [a.action.lower() for a in unclear_actions]
    assert any("crm lead" in t for t in titles), "CRM lead audit missing from unclear ownership"
    assert any("sales stage" in t or "salesforce" in t for t in titles), "Salesforce stage definitions missing"


def test_q6_what_commitments_do_i_have_this_week():
    """Question 6: 'What commitments do I have this week?'
    Verifies all valid, active commitments owned by Arjun."""
    my_actions = get_actions_by_filter(category="my_action", include_completed=False)
    assert len(my_actions) >= 4

    for a in my_actions:
        assert a.owner == "Arjun"
        assert a.status in ["pending", "overdue", "at_risk"]


def test_conflict_detection_apex_renewal():
    """Validates conflict detection between Email (Thursday 2 PM) and Calendar (Friday 10 AM)."""
    report = get_conflict_report()
    assert "Conflict Report" in report
    assert "Apex Tech" in report
    assert "Thursday at 2:00 PM" in report or "Thursday 2:00 PM" in report
    assert "Friday at 10:00 AM" in report or "Friday 10:00 AM" in report


def test_safety_against_hallucination_and_suggestions():
    """Anti-hallucination tests:
    - Maya's keynote invite is a suggestion and NOT an active commitment.
    - Completed actions are not reported as active pending commitments.
    """
    raw_candidates = extract_raw_commitments()
    keynote_cand = [c for c in raw_candidates if "keynote" in c.action.lower() or "apac" in c.action.lower()]
    assert len(keynote_cand) == 1
    assert keynote_cand[0].is_suggestion_only is True

    # Ensure it did not enter active structured actions
    active_actions = process_and_deduplicate_actions()
    assert not any("keynote" in a.action.lower() for a in active_actions if a.status != "not_a_commitment")

    # Completed actions are flagged completed
    intro_action = next((a for a in active_actions if "karthik" in a.action.lower() or "intro" in a.action.lower()), None)
    assert intro_action is not None
    assert intro_action.status == "completed"


def test_executive_brief_sections():
    """Verifies that generate_executive_brief contains all 6 required sections."""
    brief = generate_executive_brief()
    assert "### 1. OVERDUE / AT RISK" in brief
    assert "### 2. NEEDS ACTION TODAY" in brief
    assert "### 3. MY COMMITMENTS" in brief
    assert "### 4. WAITING ON OTHERS" in brief
    assert "### 5. UPCOMING" in brief
    assert "### 6. UNCLEAR OWNERSHIP" in brief
    assert "[CONFLICT ALERT]" in brief or "Conflict" in brief
