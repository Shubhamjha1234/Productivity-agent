# Executive Productivity Agent — Technical Presentation

> **AI-Powered Executive Assistant using Google ADK, n8n, and RAG**  
> **Interactive Deck Available At:** `http://127.0.0.1:8080/slides`

---

## Slide 1: Title & Executive Overview

### **Executive Productivity Agent**
**AI-Powered Executive Assistant using Google ADK, n8n, RAG, Gmail & Google Calendar**

* **Presenter:** Shubham Jha
* **Domain:** Autonomous AI Agent Systems & Enterprise Workflow Automation
* **Target Executive:** Arjun Malhotra — VP Sales, TechNova Solutions
* **Frontend:** Modern HTML5 · CSS3 (Glassmorphism) · ES6 JavaScript

```
┌──────────────────────────────────────────────────────────────┐
│                  EXECUTIVE ACTION BRIEF                      │
│             Arjun Malhotra — VP Sales, TechNova              │
├──────────────────────────────┬───────────────────────────────┤
│   OVERDUE / AT RISK (2)      │      ACTION TODAY (3)         │
│   MY COMMITMENTS (6)         │      WAITING ON OTHERS (2)    │
│   UPCOMING (2)               │      UNCLEAR OWNERSHIP (2)    │
└──────────────────────────────┴───────────────────────────────┘
```

---

## Slide 2: Problem & Objective

### **The Problem: The Executive Cognitive Bottleneck**
Executives spend upwards of 3-4 hours daily managing fragmented communication:
* **Email Triage:** Sifting through lengthy threads for deliverables and requests.
* **Calendar Mismatches:** Scheduling updates received via email conflicting with calendar invites.
* **Meeting Commitments:** Verbal promises lost in meeting transcripts without follow-up.
* **Siloed Context:** Critical data trapped across isolated systems.

### **The Objective**
Create a single intelligent interface that understands natural-language requests and connects multiple enterprise productivity channels with **zero hallucination**.

```
  [ Emails ]   +   [ Transcripts ]   +   [ Calendar ]   +   [ Audio Memos ]
                            │
                            ▼
              ┌───────────────────────────┐
              │  Executive AI Assistant   │
              │   (Unified Action Brief)  │
              └───────────────────────────┘
```

---

## Slide 3: Proposed Solution

### **Combining Google ADK and n8n**

1. **Google ADK (AI Agent Reasoning):**
   * Complex intent parsing and multi-turn planning.
   * Tool orchestration with automated function calling.
   * Gemini 3.6 Flash reasoning with strict anti-hallucination guardrails.
2. **n8n Automation (Integration Layer):**
   * Deterministic workflows connecting Gmail, Google Calendar, and RAG pipelines.
   * Webhook routing and event-driven automation.
   * Human-in-the-Loop approval nodes before consequential actions.
3. **Executive Dashboard (HTML / CSS / JS):**
   * Single-page responsive cockpit with KPI metrics.
   * 6-section action item brief with verbatim evidence drawers.
   * Schedule conflict alert banner and interactive Q&A console.

```
[ Executive UI ] ──➔ [ Google ADK Agent ] ──➔ [ n8n Automation ] ──➔ [ Enterprise APIs ]
 (HTML/CSS/JS)         (Reasoning & Tools)       (Orchestration)       (Gmail/Cal/RAG)
```

---

## Slide 4: Technology Stack

### **Modular Enterprise Architecture**

| Layer | Technologies Used | Key Responsibility |
|---|---|---|
| **Frontend** | HTML5, Vanilla Modern CSS, ES6 JS | Fast, zero-bloat executive cockpit |
| **AI / Agent** | Google ADK (v2.9.1), Gemini 3.6 Flash | Function calling, reasoning, grounding |
| **Automation** | n8n Cloud | Gmail & Calendar integration workflows |
| **Knowledge / RAG**| Pinecone, Vector Embeddings, Docs | Enterprise document retrieval |
| **Backend API** | FastAPI, Uvicorn (ASGI), Pydantic v2 | High-performance REST endpoints |
| **Tooling** | Astral `uv`, Pytest (13 test cases) | Package management, test automation |

---

## Slide 5: System Architecture & Governance

```
                    ┌────────────────────────┐
                    │    Executive User      │
                    └───────────┬────────────┘
                                │ Natural Language Query
                                ▼
                    ┌────────────────────────┐
                    │   HTML / CSS / JS UI   │
                    └───────────┬────────────┘
                                │ REST / JSON
                                ▼
                    ┌────────────────────────┐
                    │      FastAPI App       │
                    └───────────┬────────────┘
                                │ Function Calling
                                ▼
                    ┌────────────────────────┐
                    │    Google ADK Agent    │
                    │   (Gemini 3.6 Flash)   │
                    └───────────┬────────────┘
                                │ Orchestration
                                ▼
                    ┌────────────────────────┐
                    │     n8n Workflows      │
                    └─────┬────────────┬─────┘
                          │            │
             ┌────────────┴──┐      ┌──┴────────────┐
             ▼               ▼      ▼               ▼
      ┌────────────┐   ┌──────────────┐   ┌────────────────┐
      │   Gmail    │   │   Calendar   │   │  RAG Knowledge │
      │ - Drafting │   │ - Meetings   │   │ - Vector DB    │
      │ - Threads  │   │ - Conflicts  │   │ - Documents    │
      └──────┬─────┘   └──────┬───────┘   └────────┬───────┘
             │                │                    │
             └────────────────┼────────────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │ Human-in-the-Loop Approval   │
               │ (Arjun Confirms Consequence) │
               └──────────────┬───────────────┘
                              │
                              ▼
                      [ Execute Action ]
                              │
                              ▼
                     [ UI Response Render ]
```

---

## Slide 6: Key Use Case & Workflow

### **Scenario: "Prepare me for my next meeting."**

1. **Context Aggregation:**
   * **Google Calendar:** Detects *Apex Tech Renewal Presentation* listed for Friday at 10:00 AM.
   * **Gmail:** Finds email from Sarah Jenkins stating the client requested to reschedule to Thursday at 2:00 PM.
   * **RAG:** Pulls historical contract terms and margin models for Apex Tech.
2. **ADK Agent Reasoning:**
   * Detects schedule conflict between Calendar and Email.
   * Sets status to `AT_RISK` and flags `[CONFLICT ALERT]` with exact citations from both sources.
   * Does not hallucinate or guess which time is correct.
3. **Execution & Approval:**
   * Generates a 1-click clarification email draft for Sarah Jenkins.
   * Waits for Arjun's signoff (**Human-in-the-Loop**) before sending.

---

## Slide 7: UI, Benefits & Conclusion

### **Executive Dashboard Capabilities**
* **6 Mandatory Brief Sections:** Overdue/At Risk, Action Today, My Commitments, Waiting on Others, Upcoming, Unclear Ownership.
* **Traceable Grounding:** Every item includes verifiable quotes and channel provenance.
* **Conversational Speed:** Instant answers to *"What did I promise Raghav?"*, *"What needs action today?"*, and *"What am I waiting on?"*.

### **Key Benefits**
* **Reduces Cognitive Overhead:** Eliminates manual scanning of emails and meeting notes.
* **Zero Missed Deadlines:** Flags overdue deliverables and imminent obligations.
* **Proactive Risk Prevention:** Alerts on schedule mismatches before they cause missed meetings.
* **Keeps Humans in Control:** AI recommends, human decides.

### **Conclusion**
> *"One intelligent, grounded interface for the executive's daily workflow."*

**Thank You! Questions & Discussion.**  
*Repository:* [https://github.com/Shubhamjha1234/Productivity-agent](https://github.com/Shubhamjha1234/Productivity-agent)
