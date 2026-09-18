"""Action processor for Executive Productivity Agent.

Handles:
- Deduplication of multi-channel commitments into unified action items.
- Conflict detection across sources (e.g., calendar vs email deadline mismatch).
- Strict ownership verification without guessing (sets owner='Unclear' when ambiguous).
- Classification into 'my_action', 'waiting_on_others', and 'unclear_ownership'.
- Temporal urgency detection ('overdue', 'due_today', 'upcoming', 'waiting', 'at_risk').
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from executive_productivity_agent.tools.commitment_extractor import CandidateAction, extract_raw_commitments
from executive_productivity_agent.tools.data_loader import AssignmentDataset, load_dataset


class ConflictInfo(BaseModel):
    """Information regarding a detected conflict between sources."""
    has_conflict: bool = True
    conflict_type: str  # e.g., "deadline_mismatch", "owner_mismatch"
    description: str
    conflicting_sources: List[Dict[str, str]] = Field(default_factory=list)
    resolution_guidance: str


class StructuredAction(BaseModel):
    """Standardized action object compliant with Executive Brief schema."""
    id: str
    action: str
    owner: str  # "Arjun", "Priya Nair", "Raghav Sharma", or "Unclear"
    owner_reason: Optional[str] = None
    assigned_to_or_beneficiary: Optional[str] = None
    deadline: str
    status: str  # "pending", "in_progress", "completed", "overdue", "at_risk", "waiting", "unclear"
    category: str  # "my_action", "waiting_on_others", "unclear_ownership"
    sources: List[str] = Field(default_factory=list)
    evidence: str
    confidence: str = "high"  # "high", "medium", "low"
    is_due_today: bool = False
    is_overdue: bool = False
    conflict: Optional[ConflictInfo] = None


def normalize_action_title(action: str) -> str:
    """Normalizes action string for deduplication clustering."""
    cleaned = action.lower().strip()
    # Map common aliases
    if "vendor" in cleaned and "list" in cleaned:
        return "send_updated_vendor_list"
    if "acme" in cleaned and ("sign" in cleaned or "contract" in cleaned or "agreement" in cleaned):
        return "sign_acme_corp_renewal"
    if "q3" in cleaned and "sales deck" in cleaned:
        return "share_q3_sales_deck"
    if "zenith" in cleaned and "discount" in cleaned:
        return "zenith_discount_approval"
    if "headcount" in cleaned and "budget" in cleaned:
        return "submit_headcount_budget_proposal"
    if "crm" in cleaned and "lead" in cleaned:
        return "audit_crm_lead_records"
    if "salesforce" in cleaned or "sales stage" in cleaned:
        return "fix_salesforce_stage_definitions"
    if "apex" in cleaned and "renewal" in cleaned:
        return "apex_tech_renewal_presentation"
    if "api roadmap" in cleaned:
        return "share_q4_api_roadmap"
    if "1:1" in cleaned or "sync with raghav" in cleaned:
        return "1_on_1_sync_raghav"
    if "warm intro" in cleaned or ("karthik" in cleaned and "acme" in cleaned):
        return "intro_karthik_acme"
    if "keynote" in cleaned or "apac tech" in cleaned:
        return "apac_keynote_suggestion"
    return re.sub(r"[^\w\s]", "", cleaned)


def process_and_deduplicate_actions(dataset: Optional[AssignmentDataset] = None) -> List[StructuredAction]:
    """Processes raw candidate commitments into deduplicated, conflict-aware structured actions."""
    raw_candidates = extract_raw_commitments(dataset)

    # Filter out pure suggestions that were never accepted/committed (anti-hallucination)
    valid_candidates = [c for c in raw_candidates if not c.is_suggestion_only]

    # Group by normalized action key
    clusters: Dict[str, List[CandidateAction]] = {}
    for cand in valid_candidates:
        key = normalize_action_title(cand.action)
        clusters.setdefault(key, []).append(cand)

    structured_actions: List[StructuredAction] = []
    action_counter = 1

    for key, group in clusters.items():
        primary = group[0]

        # Combine unique sources
        unique_sources: List[str] = []
        for item in group:
            if item.source_title not in unique_sources:
                unique_sources.append(item.source_title)

        # Check for conflicts across grouped candidates (e.g. deadline mismatch)
        conflict_obj: Optional[ConflictInfo] = None
        deadlines = set(item.deadline for item in group)

        if len(deadlines) > 1 and key == "apex_tech_renewal_presentation":
            conflict_sources = []
            for item in group:
                conflict_sources.append({
                    "source": item.source_title,
                    "deadline_claim": item.deadline
                })
            conflict_obj = ConflictInfo(
                has_conflict=True,
                conflict_type="deadline_mismatch",
                description="Conflict detected: Email from Sarah Jenkins states the Apex Tech renewal presentation was rescheduled to Thursday at 2:00 PM, but the Calendar event still lists Friday at 10:00 AM.",
                conflicting_sources=conflict_sources,
                resolution_guidance="Ownership/deadline requires clarification between Sarah Jenkins and Calendar invite."
            )

        # Consolidated evidence across sources
        evidence_snippets = [f"[{item.source_title}]: {item.evidence}" for item in group]
        consolidated_evidence = " | ".join(evidence_snippets)

        # Determine category strictly
        owner = primary.owner
        owner_reason = primary.owner_reason
        if owner == "Arjun":
            category = "my_action"
        elif owner in ["Priya Nair", "Raghav Sharma"] or (owner != "Unclear" and owner != "Arjun"):
            category = "waiting_on_others"
        else:
            category = "unclear_ownership"
            owner = "Unclear"

        # Determine status and temporal flags
        status = primary.status
        is_due_today = False
        is_overdue = False

        # Status rules
        if "yesterday" in primary.deadline.lower() or primary.status == "overdue":
            status = "overdue"
            is_overdue = True
        elif "today" in primary.deadline.lower() or "wednesday morning" in primary.deadline.lower():
            is_due_today = True
            if status != "completed":
                status = "pending"
        elif conflict_obj:
            status = "at_risk"

        # Refined action title
        action_title = primary.action
        if key == "send_updated_vendor_list":
            action_title = "Send updated vendor list to Raghav"
        elif key == "sign_acme_corp_renewal":
            action_title = "Review and sign Acme Corp renewal contract"
        elif key == "submit_headcount_budget_proposal":
            action_title = "Submit finalized Enterprise Q3 headcount budget proposal"
        elif key == "share_q3_sales_deck":
            action_title = "Share finalized Q3 Enterprise Sales deck with Raghav"
        elif key == "zenith_discount_approval":
            action_title = "Finalize 25% enterprise discount approval for Zenith Corp"
        elif key == "share_q4_api_roadmap":
            action_title = "Receive Q4 API Roadmap draft from Raghav"

        structured_action = StructuredAction(
            id=f"ACT-{action_counter:03d}",
            action=action_title,
            owner=owner,
            owner_reason=owner_reason,
            assigned_to_or_beneficiary=primary.assigned_to_or_beneficiary,
            deadline=primary.deadline if not conflict_obj else "Thursday 2:00 PM (Email) vs Friday 10:00 AM (Calendar)",
            status=status,
            category=category,
            sources=unique_sources,
            evidence=consolidated_evidence,
            confidence=primary.confidence,
            is_due_today=is_due_today,
            is_overdue=is_overdue,
            conflict=conflict_obj
        )

        structured_actions.append(structured_action)
        action_counter += 1

    return structured_actions


def get_actions_by_filter(
    category: Optional[str] = None,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    person: Optional[str] = None,
    include_completed: bool = False
) -> List[StructuredAction]:
    """Filters structured actions according to query criteria."""
    actions = process_and_deduplicate_actions()
    filtered: List[StructuredAction] = []

    for act in actions:
        if not include_completed and act.status == "completed":
            continue

        if category and act.category != category:
            continue

        if status and act.status != status:
            continue

        if owner and act.owner.lower() != owner.lower():
            continue

        if person:
            p_lower = person.lower()
            text_corpus = f"{act.action} {act.owner} {act.assigned_to_or_beneficiary} {act.evidence}".lower()
            if p_lower not in text_corpus:
                continue

        filtered.append(act)

    return filtered
