"""FastAPI server for the Executive Productivity Agent dashboard.

Serves the executive web UI, brief API endpoints, and natural-language Q&A
powered by Google ADK and Gemini.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from executive_productivity_agent.agent import root_agent
from executive_productivity_agent.tools.action_processor import (
    StructuredAction,
    process_and_deduplicate_actions,
    get_actions_by_filter,
)
from executive_productivity_agent.tools.brief_generator import generate_executive_brief

app = FastAPI(
    title="Executive Action Brief API",
    description="Backend for Arjun Malhotra's Executive Productivity Dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent session service for ADK
_session_service = InMemorySessionService()
_runner = Runner(agent=root_agent, session_service=_session_service, app_name="executive_dashboard")
_session_id: Optional[str] = None


async def get_or_create_session() -> str:
    global _session_id
    if not _session_id:
        session = await _session_service.create_session(app_name="executive_dashboard", user_id="arjun_malhotra")
        _session_id = session.id
    return _session_id


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    answer: str
    evidence_matches: List[Dict[str, Any]] = []


@app.get("/api/brief")
async def get_brief_data() -> Dict[str, Any]:
    """Returns structured data for the executive dashboard."""
    all_actions = process_and_deduplicate_actions()

    overdue_or_at_risk = []
    needs_action_today = []
    my_commitments = []
    waiting_on_others = []
    upcoming = []
    unclear_ownership = []
    conflicts = []

    for act in all_actions:
        act_dict = act.model_dump()

        if act.conflict and act.conflict.has_conflict:
            conflicts.append(act.conflict.model_dump())

        if act.status == "completed":
            continue

        # 1. Overdue or At Risk
        if act.status in ["overdue", "at_risk"] or act.is_overdue:
            overdue_or_at_risk.append(act_dict)

        # 2. Needs Action Today
        if act.is_due_today and act.category == "my_action":
            needs_action_today.append(act_dict)

        # 3. My Commitments
        if act.category == "my_action":
            my_commitments.append(act_dict)

        # 4. Waiting on Others
        if act.category == "waiting_on_others":
            waiting_on_others.append(act_dict)

        # 5. Upcoming
        if ("thursday" in act.deadline.lower() or "friday" in act.deadline.lower()) and act.category == "my_action":
            upcoming.append(act_dict)

        # 6. Unclear Ownership
        if act.category == "unclear_ownership" or act.owner == "Unclear":
            unclear_ownership.append(act_dict)

    return {
        "metadata": {
            "target_user": "Arjun Malhotra",
            "role": "VP Sales",
            "company": "TechNova Solutions",
            "reference_date": "Wednesday, October 15, 2025",
        },
        "summary": {
            "overdue_at_risk": len(overdue_or_at_risk),
            "needs_action_today": len(needs_action_today),
            "my_commitments": len(my_commitments),
            "waiting_on_others": len(waiting_on_others),
            "upcoming": len(upcoming),
            "unclear_ownership": len(unclear_ownership),
        },
        "conflicts": conflicts,
        "sections": {
            "overdue_at_risk": overdue_or_at_risk,
            "needs_action_today": needs_action_today,
            "my_commitments": my_commitments,
            "waiting_on_others": waiting_on_others,
            "upcoming": upcoming,
            "unclear_ownership": unclear_ownership,
        },
    }


@app.post("/api/ask", response_model=AskResponse)
async def ask_agent(req: AskRequest) -> AskResponse:
    """Invokes the Google ADK Agent for conversational queries."""
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    session_id = await get_or_create_session()
    content = types.Content(role="user", parts=[types.Part.from_text(text=question)])

    response_parts = []
    try:
        async for event in _runner.run_async(user_id="arjun_malhotra", session_id=session_id, new_message=content):
            if event.content and event.content.parts:
                for p in event.content.parts:
                    if p.text:
                        response_parts.append(p.text)
        answer = "".join(response_parts).strip()
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            answer = (
                "[Notice]: Google AI Studio free tier rate limit was temporarily reached. "
                "Please wait 30 seconds before asking another query. "
                "Note: The Executive Action Brief above is fully active and loaded."
            )
        else:
            answer = f"Error processing query: {e}"

    # Extract relevant matching actions as structured evidence chips
    matched_actions = []
    all_actions = process_and_deduplicate_actions()
    q_lower = question.lower()
    for a in all_actions:
        if any(term in q_lower for term in ["raghav", "promise"]) and "raghav" in (a.action + a.assigned_to_or_beneficiary + a.owner).lower():
            matched_actions.append(a.model_dump())
        elif "overdue" in q_lower and a.status == "overdue":
            matched_actions.append(a.model_dump())
        elif "today" in q_lower and a.is_due_today:
            matched_actions.append(a.model_dump())
        elif ("waiting" in q_lower or "wait" in q_lower) and a.category == "waiting_on_others":
            matched_actions.append(a.model_dump())
        elif "unclear" in q_lower and a.owner == "Unclear":
            matched_actions.append(a.model_dump())

    return AskResponse(
        question=question,
        answer=answer,
        evidence_matches=matched_actions[:5],
    )


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard() -> HTMLResponse:
    """Serves the single-page executive dashboard HTML."""
    html_path = Path(__file__).resolve().parent / "ui" / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard UI file not found.")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/slides", response_class=HTMLResponse)
async def serve_slides() -> HTMLResponse:
    """Serves the 7-slide technical presentation deck."""
    slides_path = Path(__file__).resolve().parent / "ui" / "slides.html"
    if not slides_path.exists():
        raise HTTPException(status_code=404, detail="Slides presentation file not found.")
    with open(slides_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Executive Productivity Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    args = parser.parse_args()

    print(f"\n=======================================================")
    print(f"EXECUTIVE PRODUCTIVITY AGENT - DASHBOARD")
    print(f"Target: Arjun Malhotra (VP Sales)")
    print(f"Dashboard available at: http://{args.host}:{args.port}")
    print(f"=======================================================\n")

    uvicorn.run("executive_productivity_agent.app_server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
