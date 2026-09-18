"""Google ADK Executive Productivity Agent for Arjun Malhotra (VP Sales).

Extracts commitments, deduplicates across channels, classifies ownership and timing,
detects source conflicts, generates executive action briefs, and answers natural-language Q&A.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from google.adk.agents.llm_agent import Agent

# Load environment variables (.env in this directory)
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from executive_productivity_agent.tools.action_processor import (
    process_and_deduplicate_actions,
    get_actions_by_filter,
)
from executive_productivity_agent.tools.brief_generator import (
    generate_executive_brief,
    format_action_item,
)


def get_daily_action_brief() -> str:
    """Generates and returns the complete Daily Executive Action Brief for Arjun Malhotra.

    Covers all 6 mandatory executive categories:
    1. OVERDUE / AT RISK
    2. NEEDS ACTION TODAY
    3. MY COMMITMENTS
    4. WAITING ON OTHERS
    5. UPCOMING
    6. UNCLEAR OWNERSHIP
    """
    return generate_executive_brief()


def search_commitments(
    person: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    query: Optional[str] = None,
    include_completed: bool = False,
) -> str:
    """Searches and filters verified commitments from the assignment dataset.

    Args:
        person: Filter by person mentioned or involved (e.g., 'Raghav', 'Priya', 'Arjun').
        category: Filter by category: 'my_action', 'waiting_on_others', or 'unclear_ownership'.
        status: Filter by status: 'pending', 'overdue', 'at_risk', 'waiting', 'completed', or 'unclear'.
        query: Free text search term across action title and evidence.
        include_completed: Whether to include already completed commitments.

    Returns:
        Formatted summary of matching commitments with owner, deadline, status, sources, and evidence.
    """
    actions = get_actions_by_filter(
        category=category,
        status=status,
        person=person,
        include_completed=include_completed
    )

    if query:
        q_lower = query.lower()
        actions = [
            a for a in actions
            if q_lower in a.action.lower() or q_lower in a.evidence.lower() or any(q_lower in s.lower() for s in a.sources)
        ]

    if not actions:
        criteria = []
        if person: criteria.append(f"person='{person}'")
        if category: criteria.append(f"category='{category}'")
        if status: criteria.append(f"status='{status}'")
        if query: criteria.append(f"query='{query}'")
        return f"No commitments found matching criteria: {', '.join(criteria) if criteria else 'all'}."

    results = [f"Found {len(actions)} matching commitment(s):\n"]
    for a in actions:
        results.append(format_action_item(a))
    return "\n\n".join(results)


def get_conflict_report() -> str:
    """Identifies and details any conflicting information detected across communication channels.

    Returns:
        Detailed report showing conflicting sources, differing statements, and required clarification.
    """
    actions = process_and_deduplicate_actions()
    conflicts = [a for a in actions if a.conflict and a.conflict.has_conflict]

    if not conflicts:
        return "No conflicts detected across sources. All deadlines and instructions are consistent."

    report_lines = [f"Conflict Report: {len(conflicts)} conflict(s) detected:\n"]
    for act in conflicts:
        c = act.conflict
        report_lines.append(f"• Action: {act.action}")
        report_lines.append(f"  Issue: {c.description}")
        report_lines.append("  Conflicting Claims:")
        for cs in c.conflicting_sources:
            report_lines.append(f"    - [{cs.get('source')}]: {cs.get('deadline_claim')}")
        report_lines.append(f"  Resolution Guidance: {c.resolution_guidance}\n")

    return "\n".join(report_lines)


def inspect_source_evidence(action_keyword: str) -> str:
    """Retrieves full verbatim evidence and multi-channel provenance for a given action keyword.

    Args:
        action_keyword: Keyword to match against action names (e.g., 'vendor', 'headcount', 'acme', 'crm').
    """
    actions = process_and_deduplicate_actions()
    matched = [a for a in actions if action_keyword.lower() in a.action.lower()]

    if not matched:
        return f"No action item matched keyword: '{action_keyword}'."

    output = []
    for a in matched:
        output.append(f"Action: {a.action}")
        output.append(f"Owner: {a.owner}")
        output.append(f"Deadline: {a.deadline}")
        output.append(f"Status: {a.status}")
        output.append(f"Sources ({len(a.sources)}):")
        for s in a.sources:
            output.append(f"  - {s}")
        output.append(f"Verbatim Evidence:\n  \"{a.evidence}\"")
        if a.conflict:
            output.append(f"Conflict Note: {a.conflict.description}")
        output.append("-" * 40)
    return "\n".join(output)


AGENT_INSTRUCTION = """\
You are the Executive Action Brief Agent for Arjun Malhotra, VP Sales at TechNova Solutions.
Your role is to analyze multi-channel communications (emails, meeting transcripts, calendar events, voice notes) and provide a reliable, grounded executive action brief and Q&A.

==================================================
OPERATING RULES & SAFETY AGAINST HALLUCINATION:
==================================================
1. SOURCE OF TRUTH:
   - The provided data tools are the ONLY source of truth.
   - NEVER invent people, dates, deadlines, commitments, ownership, events, or statuses.
   - If information is missing, explicitly say that it is missing.

2. OWNERSHIP:
   - Never guess ownership.
   - Never infer ownership from job title or meeting attendance alone.
   - If ownership is not explicitly accepted or assigned, state that owner is "Unclear" and explain why.
   - Distinguish "Arjun was asked to do X" from "Arjun agreed/committed to do X".

3. SUGGESTIONS VS COMMITMENTS:
   - Never convert a suggestion or invitation into a commitment (e.g. speaking invitations where Arjun never agreed).

4. CONFLICT HANDLING:
   - If sources conflict (e.g. Email says presentation is Thursday 2 PM but Calendar says Friday 10 AM), DO NOT choose one silently.
   - State: "Conflict detected" and cite both sources.

5. DEDUPLICATION:
   - Multiple mentions of the same commitment across different sources must be reported as a single action with all sources listed.

6. FORMAT FOR ANSWERS:
   - Always clearly state: Action, Owner, Deadline, Status, Source(s), and Evidence.
   - When asked for the executive brief, use get_daily_action_brief tool.
   - When asked specific questions (e.g., promises to Raghav, what is overdue, waiting on others, unclear ownership), call search_commitments with appropriate arguments.
"""

root_agent = Agent(
    model="gemini-3.6-flash",
    name="executive_action_brief_agent",
    description="Executive Productivity Agent for Arjun Malhotra (VP Sales), extracting grounded commitments, handling deduplication, conflict detection, and executive briefings.",
    instruction=AGENT_INSTRUCTION,
    tools=[
        get_daily_action_brief,
        search_commitments,
        get_conflict_report,
        inspect_source_evidence,
    ],
)
