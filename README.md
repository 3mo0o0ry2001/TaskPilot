# TaskPilot

A personal productivity agent built from scratch using Python, Groq (gpt-oss-120b), Gmail API, and Google Calendar API. No LangChain, no LangGraph. Just a raw agentic loop with tool use, hallucination detection, and eval-driven development.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Groq](https://img.shields.io/badge/LLM-gpt--oss--120b-orange) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-red) ![Gmail](https://img.shields.io/badge/Gmail-API-green) ![Calendar](https://img.shields.io/badge/Google_Calendar-API-blue)

---

## What it does

You type something like:

> "Send Ahmed an email saying tomorrow's meeting is rescheduled to Friday, and add a reminder next Monday to follow up"

TaskPilot figures out the plan, calls the right tools in the right order, and actually does it. Emails land in Gmail. Events appear in Google Calendar.

It handles:
- Sending real emails via Gmail API
- Creating real calendar events via Google Calendar API
- Managing a local task list (SQLite)
- Looking up contacts by name before sending emails
- Parsing relative dates ("tomorrow", "next week", "بكرة") correctly
- Responding in Arabic or English depending on what you write

---

## Why I built it without frameworks

Most agent tutorials throw you into LangChain or LangGraph on day one. The agent loop becomes a black box. When something breaks, you don't know where to look.

Building the loop manually means:
- You see every tool call and every response
- Tracing is something you control, not something a library decides for you
- Debugging is faster because there's no magic between you and the model

---

## Architecture

```
User Input
    ↓
Intent Detection (tool_choice: required / auto)
    ↓
LLM (gpt-oss-120b via Groq)
    ↓
Tool Call → Tool Handler → Tool Result
    ↓
Validation Layer (hallucination detection)
    ↓
Final Response
```

The agent loop runs up to 10 iterations per request. Each iteration either calls a tool or returns a final response.

**Tools available:**
- `find_contact` — search contacts by name
- `send_email` — send via Gmail API (with mock fallback)
- `create_event` — add to Google Calendar (with mock fallback)
- `create_task` — add to local SQLite task list
- `list_tasks` — list tasks filtered by status
- `get_current_datetime` — needed for relative date parsing

---

## Hallucination mitigation

The model sometimes claims it sent an email without actually calling `send_email`. This is a known failure mode in small models during multi-step tasks.

Three layers of defense:

**1. System Prompt rules** — explicit instructions not to claim an action without calling the tool

**2. Intent detection + tool forcing** — when the user message contains action words ("send", "create", "add"), `tool_choice` is set to `"required"` on the first iteration

**3. Validation layer** — before accepting a final response, the agent checks if the text claims a completed action without a corresponding tool call in the trace. If it catches a mismatch, it re-prompts the model to actually execute.

---

## Eval-driven development

The project follows the build/analyze loop from Andrew Ng's agentic AI course.

Test suite: 15 cases across 6 categories (task management, chained tools, error handling, relative dates, direct email, multi-action).

Results after iterating:

| Stage | Pass Rate |
|-------|-----------|
| Initial build | 33.3% (mostly network noise) |
| After retry logic + noise filtering | 84.6% adjusted |
| After hallucination fixes | 92.3% |
| After relative date fix | 93.3% |
| After validation phrase fix | **100%** |

The error analysis script (`evals/error_analysis.py`) separates real agent failures from network/infra failures, which matters when you're on a free-tier API with rate limits.

---

## Project structure

```
taskpilot/
├── agent.py              # Agent loop, tool forcing, validation layer
├── tools.py              # Tool schemas (Groq/OpenAI format)
├── tool_handlers.py      # Tool implementations (real + mock)
├── google_tools.py       # Gmail and Calendar API calls
├── google_auth.py        # OAuth2 flow
├── tracer.py             # Trace logging (JSON + Rich console output)
├── db.py                 # SQLite setup and seed data
├── app.py                # Streamlit UI
├── evals/
│   ├── dataset.json      # 15 test cases
│   ├── run_evals.py      # Eval runner with retry logic
│   └── error_analysis.py # Error analysis and category breakdown
├── traces/               # Saved JSON traces per session
├── credentials.json      # Google OAuth credentials (not committed)
├── token.json            # OAuth token (not committed)
└── .env                  # GROQ_API_KEY (not committed)
```

---

## Setup

**1. Clone the repo:**

```bash
git clone https://github.com/YOUR_USERNAME/taskpilot.git
cd taskpilot
```

**2. Create a virtual environment inside the project folder:**

```bash
# macOS / Linux
python -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> **Important (Windows):** Create the `venv` folder *inside* the cloned repo — not somewhere else and not moved later. The venv stores absolute paths internally and will break if the folder is relocated.

**3. Install dependencies:**

```bash
pip install -r requirements.txt
```

**4. Set your API key:**

```bash
# macOS / Linux
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Open `.env` and add your Groq API key (free at [console.groq.com](https://console.groq.com)):

```
GROQ_API_KEY=your_key_here
```

**5. Run:**

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. It works immediately with a mock fallback for Gmail and Calendar — no Google setup needed to try it out.

---

## Google APIs (optional)

Without this step, emails and calendar events are saved locally (mock mode). To connect real Gmail and Google Calendar:

1. Go to [Google Cloud Console](https://console.cloud.google.com) and create a project
2. Enable **Gmail API** and **Google Calendar API**
3. Create **OAuth 2.0 Desktop** credentials and download as `credentials.json`
4. Place `credentials.json` in the project root
5. Run the auth flow once:

```bash
python -c "from google_auth import get_credentials; get_credentials()"
```

A `token.json` file will be created. After that, emails and events go through the real APIs.

---

## Run evals

```bash
cd evals
python run_evals.py
python error_analysis.py
```

---

## What's next

- Read emails tool (fetch recent inbox)
- Web search tool
- Multi-turn conversation memory
- FastAPI backend
- Docker + deployment