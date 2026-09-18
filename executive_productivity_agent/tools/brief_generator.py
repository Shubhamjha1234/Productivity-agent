"""Executive Brief Generator for Executive Productivity Agent.

Constructs the standardized 6-section Daily Executive Action Brief:
1. OVERDUE / AT RISK
2. NEEDS ACTION TODAY
3. MY COMMITMENTS
4. WAITING ON OTHERS
5. UPCOMING
6. UNCLEAR OWNERSHIP
"""

from __future__ import annotations

from typing import List, Optional
from executive_productivity_agent.tools.action_processor import (
    StructuredAction,
    process_and_deduplicate_actions,
)


def format_action_item(action: StructuredAction) -> str:
    """Formats an individual structured action for executive presentation."""
    sources_str = ", ".join(action.sources)
    lines = [
        f"- Action: {action.action}",
        f"  * Owner: {action.owner}" + (f" ({action.owner_reason})" if action.owner == "Unclear" and action.owner_reason else ""),
        f"  * Deadline: {action.deadline}",
        f"  * Status: {action.status.upper()}",
        f"  * Source(s): {sources_str}",
        f"  * Evidence: \"{action.evidence}\"",
    ]
    if action.conflict and action.conflict.has_conflict:
        lines.append(f"  * [CONFLICT ALERT]: {action.conflict.description}")
        lines.append(f"    - Guidance: {action.conflict.resolution_guidance}")
    return "\n".join(lines)


def generate_executive_brief(actions: Optional[List[StructuredAction]] = None) -> str:
    """Generates the full Executive Action Brief across the 6 required sections."""
    all_actions = actions if actions is not None else process_and_deduplicate_actions()

    # Partition into sections
    overdue_or_at_risk: List[StructuredAction] = []
    needs_action_today: List[StructuredAction] = []
    my_commitments: List[StructuredAction] = []
    waiting_on_others: List[StructuredAction] = []
    upcoming: List[StructuredAction] = []
    unclear_ownership: List[StructuredAction] = []

    for act in all_actions:
        if act.status == "completed":
            continue

        # 1. Overdue or At Risk
        if act.status in ["overdue", "at_risk"] or act.is_overdue:
            overdue_or_at_risk.append(act)

        # 2. Needs Action Today
        if act.is_due_today and act.category == "my_action":
            needs_action_today.append(act)

        # 3. My Commitments (All active personal actions)
        if act.category == "my_action":
            my_commitments.append(act)

        # 4. Waiting on Others
        if act.category == "waiting_on_others":
            waiting_on_others.append(act)

        # 5. Upcoming (Due after today)
        if ("thursday" in act.deadline.lower() or "friday" in act.deadline.lower()) and act.category == "my_action":
            upcoming.append(act)

        # 6. Unclear Ownership
        if act.category == "unclear_ownership" or act.owner == "Unclear":
            unclear_ownership.append(act)

    # Build formatted markdown brief
    sections = [
        "==================================================",
        "DAILY EXECUTIVE ACTION BRIEF",
        "Target: Arjun Malhotra (VP Sales)",
        "Source of Truth: Verified Communications (Multi-channel)",
        "==================================================\n",
        "### 1. OVERDUE / AT RISK",
    ]

    if overdue_or_at_risk:
        sections.extend([format_action_item(a) for a in overdue_or_at_risk])
    else:
        sections.append("_No overdue or at-risk commitments._")

    sections.append("\n### 2. NEEDS ACTION TODAY")
    if needs_action_today:
        sections.extend([format_action_item(a) for a in needs_action_today])
    else:
        sections.append("_No immediate deliverables due today._")

    sections.append("\n### 3. MY COMMITMENTS")
    if my_commitments:
        sections.extend([format_action_item(a) for a in my_commitments])
    else:
        sections.append("_No active personal commitments._")

    sections.append("\n### 4. WAITING ON OTHERS")
    if waiting_on_others:
        sections.extend([format_action_item(a) for a in waiting_on_others])
    else:
        sections.append("_Not currently waiting on any external deliverables._")

    sections.append("\n### 5. UPCOMING")
    if upcoming:
        sections.extend([format_action_item(a) for a in upcoming])
    else:
        sections.append("_No upcoming commitments later this week._")

    sections.append("\n### 6. UNCLEAR OWNERSHIP")
    if unclear_ownership:
        sections.extend([format_action_item(a) for a in unclear_ownership])
    else:
        sections.append("_All action items have verified ownership._")

    sections.append("\n==================================================")
    return "\n".join(sections)
