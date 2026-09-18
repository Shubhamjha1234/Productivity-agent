"""Data loader for the Executive Productivity Agent.

Loads and validates multi-channel data (emails, meetings, calendar, voice notes)
from the assignment source of truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DatasetMetadata(BaseModel):
    target_user: str = "Arjun Malhotra"
    role: str = "VP Sales"
    company: str = "TechNova Solutions"
    reference_date: str = "2025-10-15T09:00:00"
    reference_day: str = "Wednesday"


class EmailThreadMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    from_sender: str = Field(alias="from")
    date: str
    body: str


class EmailItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    date: str
    from_sender: str = Field(alias="from")
    to_recipient: str = Field(alias="to")
    subject: str
    body: str
    thread: List[EmailThreadMessage] = Field(default_factory=list)


class MeetingTranscriptItem(BaseModel):
    id: str
    title: str
    date: str
    attendees: List[str]
    transcript: List[str]


class CalendarEventItem(BaseModel):
    id: str
    title: str
    start: str
    end: str
    attendees: List[str] = Field(default_factory=list)
    description: str = ""


class VoiceNoteItem(BaseModel):
    id: str
    title: str
    recorded_at: str
    speaker: str
    transcript: str


class AssignmentDataset(BaseModel):
    metadata: DatasetMetadata
    emails: List[EmailItem] = Field(default_factory=list)
    meeting_transcripts: List[MeetingTranscriptItem] = Field(default_factory=list)
    calendar_events: List[CalendarEventItem] = Field(default_factory=list)
    voice_notes: List[VoiceNoteItem] = Field(default_factory=list)


def get_default_data_path() -> Path:
    """Finds the default assignment_data.json path."""
    # Check relative to this file
    path = Path(__file__).resolve().parent.parent / "data" / "assignment_data.json"
    if path.exists():
        return path
    # Check root of cllg project
    alt_path = Path("c:/Projects/cllg/executive_productivity_agent/data/assignment_data.json")
    if alt_path.exists():
        return alt_path
    raise FileNotFoundError(f"Could not locate assignment_data.json at {path} or {alt_path}")


def load_dataset(file_path: Optional[str | Path] = None) -> AssignmentDataset:
    """Loads and validates the assignment dataset from JSON."""
    resolved_path = Path(file_path) if file_path else get_default_data_path()
    with open(resolved_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return AssignmentDataset.model_validate(data)


def get_all_raw_documents(dataset: Optional[AssignmentDataset] = None) -> List[dict[str, Any]]:
    """Returns a flattened list of normalized documents across all 4 channels."""
    ds = dataset or load_dataset()
    documents: List[dict[str, Any]] = []

    # 1. Emails
    for email in ds.emails:
        body_text = f"Subject: {email.subject}\nFrom: {email.from_sender}\nTo: {email.to_recipient}\nDate: {email.date}\nBody: {email.body}"
        if email.thread:
            for thread_msg in email.thread:
                body_text += f"\n--- Follow-up ({thread_msg.from_sender} at {thread_msg.date}) ---\n{thread_msg.body}"
        documents.append({
            "source_type": "email",
            "id": email.id,
            "title": f"Email: {email.subject}",
            "date": email.date,
            "participants": [email.from_sender, email.to_recipient],
            "text": body_text,
            "raw_item": email.model_dump(by_alias=True)
        })

    # 2. Meeting transcripts
    for mt in ds.meeting_transcripts:
        dialogue_text = "\n".join(mt.transcript)
        documents.append({
            "source_type": "meeting_transcript",
            "id": mt.id,
            "title": f"Meeting: {mt.title}",
            "date": mt.date,
            "participants": mt.attendees,
            "text": f"Meeting: {mt.title}\nDate: {mt.date}\nAttendees: {', '.join(mt.attendees)}\nTranscript:\n{dialogue_text}",
            "raw_item": mt.model_dump()
        })

    # 3. Calendar events
    for cal in ds.calendar_events:
        documents.append({
            "source_type": "calendar_event",
            "id": cal.id,
            "title": f"Calendar: {cal.title}",
            "date": cal.start,
            "participants": cal.attendees,
            "text": f"Event: {cal.title}\nStart: {cal.start}\nEnd: {cal.end}\nAttendees: {', '.join(cal.attendees)}\nDescription: {cal.description}",
            "raw_item": cal.model_dump()
        })

    # 4. Voice notes
    for vn in ds.voice_notes:
        documents.append({
            "source_type": "voice_note",
            "id": vn.id,
            "title": f"Voice Note: {vn.title}",
            "date": vn.recorded_at,
            "participants": [vn.speaker],
            "text": f"Voice Note: {vn.title}\nSpeaker: {vn.speaker}\nRecorded: {vn.recorded_at}\nTranscript:\n{vn.transcript}",
            "raw_item": vn.model_dump()
        })

    return documents
