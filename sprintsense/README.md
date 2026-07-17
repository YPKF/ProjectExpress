# 🚀 SprintSense — AI Sprint Intelligence Agent

**SprintSense** is a multimodal agentic AI system that autonomously monitors sprint health across **Jira**, **GitHub**, and **Slack** in real time. It reads tickets, PRs, and conversations, analyzes dashboards visually, delivers voice standup summaries, detects blockers, predicts sprint completion, and auto-generates retrospectives.

## ✨ Features

- **🔗 Jira Integration** — Fetch active sprint tickets, track status, detect blockers
- **📝 GitHub Integration** — Analyze open PRs, detect stale branches, review commits
- **💬 Slack Integration** — Read channel messages, send alerts and blocker notifications
- **👁️ Vision Analysis** — Capture Jira board screenshots and analyze them with GPT-4o Vision
- **🗣️ Voice Summaries** — Generate TTS audio standup summaries (gTTS, free)
- **📊 Sprint Prediction** — Predict completion probability and risk levels
- **🚨 Blocker Detection** — Multi-source blocker detection (tickets, PRs, Slack)
- **🔄 Retrospectives** — Auto-generate sprint retrospective documents with LLM
- **📡 REST API** — FastAPI backend with full endpoint suite
- **📈 React Dashboard** — Real-time UI with charts, blocker alerts, and standup viewer

## 📋 Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for frontend)
- **API Keys:**
  - OpenAI API key (GPT-4o for Vision + LLM analysis)
  - Jira API token (Atlassian)
  - GitHub Personal Access Token
  - Slack Bot Token

## 🛠️ Installation

### 1. Clone and setup

```bash
git clone <your-repo-url>
cd sprintsense
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys and project configuration
```

### 3. Install Playwright (for screenshot capture)

```bash
playwright install chromium
```

### 4. Run Backend

```bash
uvicorn api.app:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 5. Run Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend at: http://localhost:5173

### 6. Run Tests

```bash
pytest tests/ -v --asyncio-mode=auto
```

### 7. Run Full Agent (CLI)

```bash
python main.py
```

## 🧠 LangGraph Agent Pipeline

SprintSense uses LangGraph for deterministic agent orchestration:

```
fetch_jira → fetch_github → fetch_slack → vision_analysis
    → blocker_detection → velocity_prediction
        → [HIGH risk? → immediate notification]
        → standup_summary → voice_generation
    → report_generation → [end of sprint? → retrospective]
    → final notification
```

### Node Details

| Node | Agent | Description |
|------|-------|-------------|
| fetch_jira | JiraAgent | Fetches tickets from active Jira sprint |
| fetch_github | GitHubAgent | Fetches open PRs and recent commits |
| fetch_slack | SlackAgent | Reads recent channel messages |
| vision_analysis | VisionAgent | Captures sprint board screenshot → GPT-4o Vision |
| blocker_detection | BlockerDetector | Scans all sources for blocker keywords |
| velocity_prediction | PredictorAgent | Calculates velocity + completion probability |
| standup_summary | — | Generates daily standup markdown |
| voice_generation | VoiceAgent | Converts summary to audio (gTTS) |
| report_generation | ReportGenerator | Builds full markdown report |
| notification | NotificationService | Sends Slack alerts |
| retrospective | RetrospectiveAgent | LLM-generated sprint retrospective |

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/sprint/analyze` | Trigger full sprint analysis pipeline |
| GET | `/api/sprint/{sprint_id}` | Get sprint status and metrics |
| GET | `/api/sprint/{sprint_id}/report` | Get markdown sprint report |
| GET | `/api/sprint/{sprint_id}/audio` | Get voice summary audio file |
| POST | `/api/sprint/retrospective` | Generate retrospective document |
| GET | `/api/blockers` | Get all current blockers |
| GET | `/api/velocity` | Get velocity and prediction |

## 🧪 Test Suite

```bash
# Run all tests
pytest tests/ -v --asyncio-mode=auto

# Run specific test categories
pytest tests/test_agents/ -v
pytest tests/test_services/ -v
pytest tests/test_api/ -v

# With coverage
pytest tests/ --cov=. --cov-report=term-missing
```

## 🏗️ Project Structure

```
sprintsense/
├── config/settings.py       # Environment config loader
├── agents/                  # LangGraph agents
│   ├── sprint_master_agent.py  # Orchestrator graph
│   ├── jira_agent.py
│   ├── github_agent.py
│   ├── slack_agent.py
│   ├── vision_agent.py
│   ├── voice_agent.py
│   ├── predictor_agent.py
│   └── retrospective_agent.py
├── tools/                   # LangChain @tool functions
│   ├── jira_tools.py
│   ├── github_tools.py
│   ├── slack_tools.py
│   ├── screenshot_tools.py
│   └── tts_tools.py
├── models/                  # Pydantic data models
│   ├── sprint_state.py      # LangGraph state
│   ├── ticket.py
│   ├── pr.py
│   └── report.py
├── services/                # Business logic
│   ├── blocker_detector.py
│   ├── velocity_calculator.py
│   ├── report_generator.py
│   └── notification_service.py
├── api/                     # FastAPI backend
│   ├── app.py
│   └── routes/
│       ├── health.py
│       ├── sprint.py
│       └── report.py
├── frontend/                # React dashboard
│   └── src/
│       ├── App.jsx
│       ├── components/
│       └── services/api.js
├── tests/                   # Test suite
├── main.py                  # CLI entry point
└── requirements.txt
```

## 🔑 Environment Variables

See [.env.example](.env.example) for all required variables.

## 🤝 Contributing

Contributions welcome! Please ensure:
- All functions have type hints
- All classes have docstrings
- Tests pass before submitting PRs
- No hardcoded API keys

## 📄 License

MIT
