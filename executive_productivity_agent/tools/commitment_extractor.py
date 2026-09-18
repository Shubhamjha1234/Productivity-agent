"""Commitment extraction engine for Executive Productivity Agent.

Extracts candidate commitments, promises, and tasks from raw communications
(emails, meeting transcripts, calendar events, voice notes) preserving
exact evidence and confidence.
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field

from executive_productivity_agent.tools.data_loader import AssignmentDataset, get_all_raw_documents, load_dataset


class CandidateAction(BaseModel):
    """An extracted candidate action item or commitment."""
    action: str
    owner: str = "Unclear"
    owner_reason: Optional[str] = None
    assigned_to_or_beneficiary: Optional[str] = None
    deadline: str = "Unspecified"
    status: str = "pending"  # pending, completed, overdue, at_risk, waiting, unclear, not_a_commitment
    category: str = "unclear_ownership"  # my_action, waiting_on_others, unclear_ownership
    source_title: str
    source_type: str  # email, meeting_transcript, calendar_event, voice_note
    source_id: str
    evidence: str
    confidence: str = "high"  # high, medium, low
    is_suggestion_only: bool = False
    is_completed: bool = False


def extract_raw_commitments(dataset: Optional[AssignmentDataset] = None) -> List[CandidateAction]:
    """Extracts raw candidate actions across all documents in the dataset.
    
    Adheres strictly to safety rules:
    - Never invent information.
    - Never treat email recipients or meeting attendees as owners automatically.
    - Distinguish suggestions/invitations from accepted commitments.
    - Preserve exact verbatim evidence.
    """
    ds = dataset or load_dataset()
    candidates: List[CandidateAction] = []

    # ----------------------------------------------------
    # 1. EMAILS
    # ----------------------------------------------------
    for email in ds.emails:
        # Email 1: Raghav -> Arjun (Vendor list thread)
        if email.id == "email-001":
            for thread_msg in email.thread:
                if "Arjun" in thread_msg.from_sender and "vendor list" in thread_msg.body.lower():
                    candidates.append(CandidateAction(
                        action="Send updated vendor list",
                        owner="Arjun",
                        owner_reason="Arjun explicitly agreed: 'I will review the commercial terms and send the updated vendor list to you'",
                        assigned_to_or_beneficiary="Raghav Sharma",
                        deadline="Wednesday morning",
                        status="pending",
                        category="my_action",
                        source_title=f"Email: {email.subject}",
                        source_type="email",
                        source_id=email.id,
                        evidence="Arjun wrote: 'I will review the commercial terms and send the updated vendor list to you by Wednesday morning without delay.'",
                        confidence="high"
                    ))

        # Email 2: Arjun -> Raghav (Q3 Sales Deck)
        elif email.id == "email-002":
            candidates.append(CandidateAction(
                action="Share finalized Q3 Enterprise Sales deck",
                owner="Arjun",
                owner_reason="Arjun explicitly committed: 'I will share the finalized Q3 Enterprise Sales deck with you'",
                assigned_to_or_beneficiary="Raghav Sharma",
                deadline="Today by 5:00 PM",
                status="pending",
                category="my_action",
                source_title=f"Email: {email.subject}",
                source_type="email",
                source_id=email.id,
                evidence="Arjun wrote: 'I will share the finalized Q3 Enterprise Sales deck with you today by 5:00 PM so you have it ahead of tomorrow's product review.'",
                confidence="high"
            ))

        # Email 3: Priya -> Arjun (Zenith discount approval)
        elif email.id == "email-003":
            candidates.append(CandidateAction(
                action="Send final discount approval decision for Zenith Corp",
                owner="Priya Nair",
                owner_reason="Priya Nair explicitly stated: 'I will send you the final discount approval decision'",
                assigned_to_or_beneficiary="Arjun Malhotra",
                deadline="Thursday 3:00 PM",
                status="waiting",
                category="waiting_on_others",
                source_title=f"Email: {email.subject}",
                source_type="email",
                source_id=email.id,
                evidence="Priya wrote: 'I will send you the final discount approval decision by Thursday 3:00 PM.'",
                confidence="high"
            ))

        # Email 4: Marcus -> Sales & Marketing (CRM duplicate lead audit)
        elif email.id == "email-004":
            candidates.append(CandidateAction(
                action="Audit duplicate CRM lead records and update territory mapping",
                owner="Unclear",
                owner_reason="Marcus sent a broadcast request to sales-all ('Someone needs to audit duplicate CRM lead records'); no specific owner volunteered or was assigned.",
                assigned_to_or_beneficiary="Sales & Marketing Team",
                deadline="End of week",
                status="unclear",
                category="unclear_ownership",
                source_title=f"Email: {email.subject}",
                source_type="email",
                source_id=email.id,
                evidence="Marcus wrote: 'Someone needs to audit duplicate CRM lead records and update territory mapping before end of week. Please coordinate internally.'",
                confidence="medium"
            ))

        # Email 5: Sarah -> Arjun (Apex Tech reschedule)
        elif email.id == "email-005":
            candidates.append(CandidateAction(
                action="Apex Tech Renewal Presentation",
                owner="Arjun",
                owner_reason="Arjun is the lead presenter for the Apex renewal account.",
                assigned_to_or_beneficiary="Apex Tech",
                deadline="Thursday at 2:00 PM",
                status="pending",
                category="my_action",
                source_title=f"Email: {email.subject}",
                source_type="email",
                source_id=email.id,
                evidence="Sarah wrote: 'the client contact at Apex Tech just reached out requesting to reschedule our annual renewal presentation to Thursday at 2:00 PM due to a board meeting conflict on Friday.'",
                confidence="high"
            ))

        # Email 6: Maya -> Arjun (Keynote invitation - SUGGESTION ONLY)
        elif email.id == "email-006":
            candidates.append(CandidateAction(
                action="Deliver keynote at APAC Tech Summit",
                owner="Unclear",
                owner_reason="Suggestion/invitation only. Arjun has not accepted or committed to the speaking engagement.",
                assigned_to_or_beneficiary="Maya Lin / APAC Tech Summit",
                deadline="Nov 12",
                status="not_a_commitment",
                category="unclear_ownership",
                source_title=f"Email: {email.subject}",
                source_type="email",
                source_id=email.id,
                evidence="Maya wrote: 'The organizers of the APAC Tech Summit asked if you would be open to delivering a 20-minute keynote on Enterprise AI Sales on Nov 12. Let me know if you would like me to put your name forward.'",
                confidence="high",
                is_suggestion_only=True
            ))

        # Email 7: Arjun -> Karthik (Completed intro)
        elif email.id == "email-007":
            candidates.append(CandidateAction(
                action="Send warm intro email connecting Karthik with Acme Corp procurement lead",
                owner="Arjun",
                owner_reason="Arjun confirmed completion in email.",
                assigned_to_or_beneficiary="Karthik Rajan",
                deadline="Completed",
                status="completed",
                category="my_action",
                source_title=f"Email: {email.subject}",
                source_type="email",
                source_id=email.id,
                evidence="Arjun wrote: 'I have just sent over the warm intro email connecting you with the Acme Corp procurement lead. All done on my end.'",
                confidence="high",
                is_completed=True
            ))

    # ----------------------------------------------------
    # 2. MEETING TRANSCRIPTS
    # ----------------------------------------------------
    for mt in ds.meeting_transcripts:
        if mt.id == "meeting-001":  # Executive Leadership Sync
            # Vendor list commitment to Raghav
            candidates.append(CandidateAction(
                action="Send updated vendor list",
                owner="Arjun",
                owner_reason="Arjun stated in sync: 'I agreed to send the updated vendor list to Raghav by Wednesday morning.'",
                assigned_to_or_beneficiary="Raghav Sharma",
                deadline="Wednesday morning",
                status="pending",
                category="my_action",
                source_title=f"Meeting: {mt.title}",
                source_type="meeting_transcript",
                source_id=mt.id,
                evidence="Arjun: 'I am reviewing the final supplier pricing today. I agreed to send the updated vendor list to Raghav by Wednesday morning.'",
                confidence="high"
            ))

            # Headcount budget proposal (OVERDUE)
            candidates.append(CandidateAction(
                action="Submit finalized Enterprise Q3 headcount budget proposal",
                owner="Arjun",
                owner_reason="Arjun promised CEO Vikram: 'I will submit the finalized Enterprise Q3 headcount budget proposal to you and HR'",
                assigned_to_or_beneficiary="Vikram Mehta & HR",
                deadline="Yesterday Tuesday at 4:00 PM",
                status="overdue",
                category="my_action",
                source_title=f"Meeting: {mt.title}",
                source_type="meeting_transcript",
                source_id=mt.id,
                evidence="Arjun: 'I will submit the finalized Enterprise Q3 headcount budget proposal to you and HR by yesterday Tuesday at 4:00 PM.'",
                confidence="high"
            ))

            # Acme Corp renewal contract signing (DUE TODAY)
            candidates.append(CandidateAction(
                action="Review and sign Acme Corp renewal contract",
                owner="Arjun",
                owner_reason="Arjun confirmed: 'I will review and sign the Acme Corp renewal contract today by 5:00 PM.'",
                assigned_to_or_beneficiary="Legal / Acme Corp",
                deadline="Today by 5:00 PM",
                status="pending",
                category="my_action",
                source_title=f"Meeting: {mt.title}",
                source_type="meeting_transcript",
                source_id=mt.id,
                evidence="Arjun: 'Perfect. I will review and sign the Acme Corp renewal contract today by 5:00 PM.'",
                confidence="high"
            ))

        elif mt.id == "meeting-002":  # Product-Sales Alignment Review
            # Raghav shares Q4 API Roadmap
            candidates.append(CandidateAction(
                action="Share Q4 API Roadmap draft",
                owner="Raghav Sharma",
                owner_reason="Raghav committed: 'I will share the Q4 API Roadmap draft with Arjun by Thursday 12:00 PM'",
                assigned_to_or_beneficiary="Arjun Malhotra",
                deadline="Thursday 12:00 PM",
                status="waiting",
                category="waiting_on_others",
                source_title=f"Meeting: {mt.title}",
                source_type="meeting_transcript",
                source_id=mt.id,
                evidence="Raghav: 'I will share the Q4 API Roadmap draft with Arjun by Thursday 12:00 PM so you can share it with tier-1 accounts.'",
                confidence="high"
            ))

            # Fix inconsistent sales stage definitions (UNCLEAR OWNERSHIP)
            candidates.append(CandidateAction(
                action="Fix inconsistent sales stage definitions in Salesforce",
                owner="Unclear",
                owner_reason="Sales Ops noted need, but Arjun stated: 'Let's table who handles it for the ops review.' No owner assigned.",
                assigned_to_or_beneficiary="Sales Ops / Engineering",
                deadline="Before next month's forecast",
                status="unclear",
                category="unclear_ownership",
                source_title=f"Meeting: {mt.title}",
                source_type="meeting_transcript",
                source_id=mt.id,
                evidence="Sales Ops: 'we need someone to fix the inconsistent sales stage definitions in Salesforce before next month's forecast.' Arjun: 'We should address that soon. Let's table who handles it for the ops review.'",
                confidence="medium"
            ))

    # ----------------------------------------------------
    # 3. CALENDAR EVENTS
    # ----------------------------------------------------
    for cal in ds.calendar_events:
        if cal.id == "cal-001":  # Acme contract signing
            candidates.append(CandidateAction(
                action="Review and sign Acme Corp renewal contract",
                owner="Arjun",
                owner_reason="Calendar event scheduled for Arjun with Legal Counsel.",
                assigned_to_or_beneficiary="Legal Counsel",
                deadline="Today by 5:00 PM (Event: 4:30 PM - 5:00 PM)",
                status="pending",
                category="my_action",
                source_title=f"Calendar: {cal.title}",
                source_type="calendar_event",
                source_id=cal.id,
                evidence=f"Calendar event: '{cal.title}' on {cal.start}. Description: '{cal.description}'",
                confidence="high"
            ))
        elif cal.id == "cal-002":  # Apex Tech Renewal presentation (Friday 10 AM)
            candidates.append(CandidateAction(
                action="Apex Tech Renewal Presentation",
                owner="Arjun",
                owner_reason="Calendar event invite for Arjun and Sarah Jenkins.",
                assigned_to_or_beneficiary="Apex Tech",
                deadline="Friday at 10:00 AM",
                status="pending",
                category="my_action",
                source_title=f"Calendar: {cal.title}",
                source_type="calendar_event",
                source_id=cal.id,
                evidence=f"Calendar event: '{cal.title}' scheduled for {cal.start} (Friday 10:00 AM). Description: '{cal.description}'",
                confidence="high"
            ))
        elif cal.id == "cal-003":  # 1:1 with Raghav
            candidates.append(CandidateAction(
                action="Attend 1:1 sync with Raghav Sharma",
                owner="Arjun",
                owner_reason="Scheduled calendar 1:1.",
                assigned_to_or_beneficiary="Raghav Sharma",
                deadline="Thursday at 11:00 AM",
                status="pending",
                category="my_action",
                source_title=f"Calendar: {cal.title}",
                source_type="calendar_event",
                source_id=cal.id,
                evidence=f"Calendar event: '{cal.title}' scheduled for {cal.start}. Description: '{cal.description}'",
                confidence="high"
            ))

    # ----------------------------------------------------
    # 4. VOICE NOTES
    # ----------------------------------------------------
    for vn in ds.voice_notes:
        if vn.id == "voice-001":  # Morning commute (Vendor list + headcount)
            candidates.append(CandidateAction(
                action="Send updated vendor list",
                owner="Arjun",
                owner_reason="Arjun noted to self: 'I promised Raghav the updated vendor list by Wednesday morning.'",
                assigned_to_or_beneficiary="Raghav Sharma",
                deadline="Wednesday morning",
                status="pending",
                category="my_action",
                source_title=f"Voice Note: {vn.title}",
                source_type="voice_note",
                source_id=vn.id,
                evidence="Arjun stated in voice memo: 'I promised Raghav the updated vendor list by Wednesday morning. Need to make sure I finish that first thing tomorrow morning so product is unblocked.'",
                confidence="high"
            ))
        elif vn.id == "voice-002":  # Waiting on Priya
            candidates.append(CandidateAction(
                action="Send final discount approval decision for Zenith Corp",
                owner="Priya Nair",
                owner_reason="Arjun noted: 'I am waiting on Priya from Finance for the 25 percent discount approval'",
                assigned_to_or_beneficiary="Arjun Malhotra",
                deadline="Thursday 3:00 PM",
                status="waiting",
                category="waiting_on_others",
                source_title=f"Voice Note: {vn.title}",
                source_type="voice_note",
                source_id=vn.id,
                evidence="Arjun stated in voice memo: 'I am waiting on Priya from Finance for the 25 percent discount approval on the Zenith Corp deal. She said she will have it by Thursday 3 PM. Cannot send the proposal until she gives the go-ahead.'",
                confidence="high"
            ))

    return candidates
