# Executive Productivity Agent (Google ADK)

An enterprise-grade AI Agent prototype built with the **Google Agent Development Kit (ADK)** and **Gemini 3.5 Flash** for **Arjun Malhotra**, VP of Sales at TechNova Solutions.

The agent ingests unstructured, messy, multi-channel communications (**Emails**, **Meeting Transcripts**, **Calendar Events**, and **Voice Notes**), filters noise, deduplicates overlapping commitments, flags schedule conflicts, classifies ownership without hallucinating, and generates a structured, reliable **Daily Executive Action Brief** with natural-language Q&A capabilities.

---

## 1. Problem Statement

Executives like Arjun Malhotra are flooded daily with communications across fragmented channels:
- Client negotiations and follow-ups in **Emails**
- Verbal commitments made during **Leadership & Cross-Functional Meetings**
- Deadlines and presentation slots recorded in **Calendar Invites**
- Ad-hoc thoughts recorded in **Voice Memos**

### Core Executive Challenges
1. **Scattered Commitments**: The same promise (e.g. sending a vendor list to Raghav) is discussed in a meeting, reiterated in an email thread, and captured in a commute voice note.
2. **Ambiguous Ownership**: Many action items in meetings or broadcast emails are suggestions or unassigned tasks ("Someone needs to audit duplicate CRM leads").
3. **Implicit & Conflicting Deadlines**: A client emails a rescheduled meeting time, but the calendar invite still shows the old time.
4. **Information Overload**: It is difficult to answer critical executive questions quickly:
   - *What did I personally promise Raghav?*
   - *What needs my attention today?*
   - *What deliverables am I waiting on from others?*
   - *What is overdue?*

---

## 2. Solution Architecture

The solution uses a hybrid architecture:
* **Deterministic Python Engine**: Handles cross-channel deduplication, source merging, conflict detection, date comparisons, and strict rule-based categorization to eliminate hallucinations.
* **Google ADK + Gemini 3.5 Flash**: Interprets user intent, powers natural-language reasoning, grounds answers in verified citations, and enforces safety guidelines.

```
                  Assignment Data Source (data/assignment_data.json)
                  [Emails | Transcripts | Calendar | Voice Notes]
                                         │
                                         ▼
                                 Data Loader Tool
                               (tools/data_loader.py)
                                         │
                                         ▼
                             Commitment Extractor Tool
                         (tools/commitment_extractor.py)
                                         │
                                         ▼
                              Action Processor Tool
                           (tools/action_processor.py)
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
   Deduplication                 Conflict Detection            Ownership & Urgency
(Multi-source Merge)         (Schedule Mismatch Check)           Classification
         │                               │                               │
         └───────────────────────────────┼───────────────────────────────┘
                                         │
                                         ▼
                              Structured Action Items
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     Daily Action Brief Tool                           Executive ADK Agent
    (tools/brief_generator.py)                                (agent.py)
                 │                                               │
                 ▼                                               ▼
      Formatted Executive Brief                        Natural Language Q&A
 (6 Priority Sections + Alerts)                    (Grounded in Exact Citations)
```

---

## 3. Project Structure

```
executive_productivity_agent/
│
├── agent.py                      # Google ADK root_agent definition & tools
├── __init__.py                   # Package initializer
├── .env                          # API credentials (GOOGLE_API_KEY)
├── demo.py                       # Interactive CLI demonstration interface
├── requirements.txt              # Core package dependencies
├── README.md                     # Comprehensive architecture and user guide
│
├── data/
│   └── assignment_data.json      # Verified multi-channel ground truth dataset
│
├── tools/
│   ├── __init__.py
│   ├── data_loader.py            # Pydantic schemas & JSON document loader
│   ├── commitment_extractor.py   # High-fidelity commitment extraction
│   ├── action_processor.py       # Deduplication, conflict detection, classification
│   └── brief_generator.py        # Formats the 6-section Executive Action Brief
│
└── tests/
    ├── __init__.py
    └── test_agent.py             # 10 automated test cases (6 core queries + integrity)
```

---

## 4. Structured Output Schema

Every extracted action item conforms to a strict structured schema:

```json
{
  "id": "ACT-001",
  "action": "Send updated vendor list to Raghav",
  "owner": "Arjun",
  "owner_reason": "Arjun explicitly agreed in leadership sync, email, and voice note.",
  "assigned_to_or_beneficiary": "Raghav Sharma",
  "deadline": "Wednesday morning",
  "status": "pending",
  "category": "my_action",
  "sources": [
    "Email: Follow-up: Vendor evaluation list & Q4 procurement",
    "Meeting: Executive Leadership Sync",
    "Voice Note: Morning Commute Note - Oct 14"
  ],
  "evidence": "[Email]: Arjun wrote: 'I will review the commercial terms...' | [Meeting]: Arjun: 'I agreed to send...' | [Voice Note]: 'I promised Raghav...'",
  "confidence": "high",
  "is_due_today": true,
  "is_overdue": false,
  "conflict": null
}
```

### Supported Categories:
* `my_action`: Deliverables where Arjun is the confirmed, active owner.
* `waiting_on_others`: Deliverables owned by others (e.g. Priya Nair, Raghav Sharma) where Arjun is the beneficiary.
* `unclear_ownership`: Action items raised without a confirmed or accepted owner. Owner is marked `"Unclear"` with a documented explanation.

### Supported Statuses:
* `pending`: Active commitment pending completion.
* `in_progress`: Under active execution.
* `completed`: Verified as finished (e.g., warm intro email sent to Karthik).
* `overdue`: Deadline elapsed (e.g., Headcount budget proposal was due Tuesday 4 PM).
* `at_risk`: Blocked or subject to conflicting schedules (e.g., Apex presentation).
* `waiting`: Blocked on another team member's input.
* `unclear`: Ownership or scope requires executive clarification.

---

## 5. Daily Executive Action Brief

The agent generates a structured brief partitioned into 6 executive sections:

1. **OVERDUE / AT RISK**
   - *Overdue*: Q3 Headcount budget proposal (past Tuesday 4 PM deadline).
   - *At Risk*: Apex Tech renewal presentation (conflicting email vs calendar schedule).
2. **NEEDS ACTION TODAY**
   - Review and sign Acme Corp renewal contract (by 5:00 PM).
   - Share finalized Q3 Enterprise Sales deck with Raghav (by 5:00 PM).
   - Send updated vendor list to Raghav (Wednesday morning).
3. **MY COMMITMENTS**
   - Comprehensive inventory of active personal commitments for Arjun Malhotra.
4. **WAITING ON OTHERS**
   - Finalize 25% discount approval for Zenith Corp (Waiting on Priya Nair in Finance).
   - Receive Q4 API Roadmap draft (Waiting on Raghav Sharma in Product).
5. **UPCOMING**
   - 1:1 Sync with Raghav Sharma (Thursday 11:00 AM).
   - Apex Tech Renewal presentation (Upcoming slot pending clarification).
6. **UNCLEAR OWNERSHIP**
   - Audit duplicate CRM lead records (broadcast email to distribution list; no assignee).
   - Fix inconsistent sales stage definitions in Salesforce (tabled in sync; no owner).

---

## 6. Safety Against Hallucination & Edge Cases

| Challenge | How the Agent Handles It |
|---|---|
| **Ambiguous Ownership** | Never infers ownership from job title or meeting attendance. Sets `owner = "Unclear"` and documents why. |
| **Suggestion vs Commitment** | Distinguishes invitations (e.g. Maya's keynote speaker invite) from commitments. Rejects unaccepted proposals. |
| **Conflicting Information** | Never silently guesses a winner. Formulates a `[CONFLICT ALERT]` citing both sources and claims. |
| **Multi-channel Duplication** | Merges items sharing normalized keys into a single structured action listing all source citations. |
| **Completed vs Planned** | Detects completed work (e.g. intro email to Karthik) and separates it from pending deliverables. |

---

## 7. How to Run

### Prerequisites
* Python 3.10+
* `uv` package manager (or standard `pip`)
* Active `GOOGLE_API_KEY` (configured in `.env`)

### 1. Run Automated Test Suite
Verify all 10 automated test cases covering the assignment requirements:
```bash
uv run pytest executive_productivity_agent/tests/test_agent.py -v
```

### 2. Run Interactive Demo & Executive Brief
Launch the executive CLI view and conversational interface:
```bash
uv run python executive_productivity_agent/demo.py
```
To run automated query demonstrations:
```bash
uv run python executive_productivity_agent/demo.py --samples
```
To ask a single question directly:
```bash
uv run python executive_productivity_agent/demo.py "What did I promise Raghav?"
```

### 3. Run with Google ADK CLI
Run queries directly through Google ADK's native CLI:
```bash
uv run adk run executive_productivity_agent "What did I promise Raghav?"
uv run adk run executive_productivity_agent "What is overdue?"
uv run adk run executive_productivity_agent "What am I waiting on?"
```

### 4. Launch ADK Web UI / Playground
Start the built-in ADK Web interface:
```bash
uv run adk web
```
Navigate to `http://127.0.0.1:8000` in your browser to interact with the agent visually.

---

## 8. Example Queries Supported

* `"What did I promise Raghav?"`
* `"What needs action today?"`
* `"What am I waiting on?"`
* `"What is overdue?"`
* `"Which actions have unclear ownership?"`
* `"What commitments do I have this week?"`
* `"Are there any conflicting deadlines across my emails and calendar?"`
* `"Show me the full executive action brief."`
* `"Inspect the source evidence for the vendor list."`

---

## 9. Assumptions & Limitations

* **Fixed Assignment Dataset**: Operates on verified structured communications provided in `data/assignment_data.json`.
* **Reference Timeline**: Anchor date is set to Wednesday, October 15, 2025 at 9:00 AM.
* **Scope**: Designed as a high-fidelity, deterministic executive prototype focusing on reasoning quality, source traceability, and zero hallucination.
