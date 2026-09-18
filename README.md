# Executive Productivity Agent (Google ADK)

Complete working prototype of the **Executive Productivity Agent** for **Arjun Malhotra (VP Sales)**, built with Google Agent Development Kit (**ADK**) and Gemini 3.5 Flash.

👉 **Full Documentation, Architecture & Guide**: [executive_productivity_agent/README.md](file:///c:/Projects/cllg/executive_productivity_agent/README.md)

---

## Quick Start

### 1. Launch the Executive Dashboard UI (Recommended)
```bash
uv run python -m uvicorn executive_productivity_agent.app_server:app --port 8080
```
Open `http://127.0.0.1:8080` in your browser.

### 2. Run Automated Test Suite (13 Tests)
```bash
uv run pytest executive_productivity_agent/tests/ -v
```

### 3. Run Interactive Terminal CLI Demo & Q&A
```bash
uv run python executive_productivity_agent/demo.py
```

### 4. Run with Google ADK CLI
```bash
uv run adk run executive_productivity_agent "What did I promise Raghav?"
uv run adk run executive_productivity_agent "What is overdue?"
```
