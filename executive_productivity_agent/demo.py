"""Interactive Demo and CLI Interface for Executive Productivity Agent.

Displays the Executive Action Brief and provides natural-language Q&A
powered by Google ADK and Gemini.
"""

from __future__ import annotations

import sys
import asyncio
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from executive_productivity_agent.agent import root_agent
from executive_productivity_agent.tools.brief_generator import generate_executive_brief


async def query_agent(runner: Runner, session_id: str, prompt: str) -> str:
    """Sends a query to the ADK agent and aggregates text responses."""
    try:
        content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        response_parts = []
        async for event in runner.run_async(user_id="executive_user", session_id=session_id, new_message=content):
            if event.content and event.content.parts:
                for p in event.content.parts:
                    if p.text:
                        response_parts.append(p.text)
        return "".join(response_parts).strip()
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            return (
                "[RATE LIMIT / QUOTA NOTE]: Google AI free-tier quota was reached for the current model.\n"
                "Please wait 30-60 seconds before making additional LLM queries, or configure a paid key.\n"
                "Note: The Executive Action Brief above is deterministic and requires zero API calls."
            )
        return f"Error executing query: {e}"


async def run_demo(interactive: bool = True, run_samples: bool = False, single_query: Optional[str] = None):
    """Executes the demonstration workflow."""
    # 1. Display Header and Brief (Requires 0 API calls - 100% deterministic)
    print("\n" + "-" * 50)
    print("EXECUTIVE ACTION BRIEF")
    print("Arjun Malhotra - VP Sales, TechNova Solutions")
    print("-" * 50)

    brief_text = generate_executive_brief()
    print(brief_text)
    print("-" * 50)
    print("ASK YOUR EXECUTIVE AGENT")
    print("-" * 50)

    # Initialize ADK Runner session
    ss = InMemorySessionService()
    session = await ss.create_session(app_name="executive_productivity_agent", user_id="executive_user")
    runner = Runner(agent=root_agent, session_service=ss, app_name="executive_productivity_agent")

    # If a single query was passed via command line
    if single_query:
        print(f"\nUser: {single_query}\n")
        reply = await query_agent(runner, session.id, single_query)
        print(f"Agent:\n{reply}\n")
        return

    # If sample automated demonstration requested
    if run_samples:
        sample_questions = [
            "What did I promise Raghav?",
            "What needs action today?",
            "What am I waiting on?",
            "What is overdue?",
            "Which actions have unclear ownership?",
            "What commitments do I have this week?",
            "Are there any conflicting deadlines across my emails and calendar?",
        ]
        for q in sample_questions:
            print(f"\n[DEMO QUERY]: \"{q}\"")
            print("=" * 50)
            reply = await query_agent(runner, session.id, q)
            print(f"{reply}\n")
            await asyncio.sleep(1)
        return

    if interactive:
        print("\nType your executive question below, or 'samples' to run demos, or 'exit' to quit:\n")
        while True:
            try:
                user_input = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSession ended.")
                break

            if not user_input or user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting Executive Productivity Agent. Have a productive day!")
                break

            if user_input.lower() == "brief":
                print("\n" + generate_executive_brief() + "\n")
                continue

            if user_input.lower() == "samples":
                await run_demo(interactive=False, run_samples=True)
                continue

            print("\nThinking...")
            reply = await query_agent(runner, session.id, user_input)
            print(f"\n[Agent]:\n{reply}\n")


def main():
    args = sys.argv[1:]
    if "--samples" in args:
        asyncio.run(run_demo(interactive=False, run_samples=True))
    elif len(args) > 0 and not args[0].startswith("--"):
        query = " ".join(args)
        asyncio.run(run_demo(interactive=False, single_query=query))
    else:
        # If in interactive terminal, prompt user. Otherwise just show the brief.
        if sys.stdin.isatty():
            asyncio.run(run_demo(interactive=True))
        else:
            asyncio.run(run_demo(interactive=False, single_query=None))


if __name__ == "__main__":
    main()
