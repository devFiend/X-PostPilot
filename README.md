# PostPilot 🚀

> Personal AI-powered content management and publishing assistant for X (Twitter).  
> **One Engine, Dual Interfaces (CLI + Telegram), 100% $0-First.**

---

## 💡 Why PostPilot?

PostPilot is not an engagement-farming bot or an unauthorized web-scraper. It is your personal content strategist and publisher:
- **Idea to Post in Seconds:** Generate high-impact X posts across educational, contrarian, developer observations, and build-in-public formats using free AI providers (Groq, Gemini, or local Ollama).
- **CreatorDNA Profiles:** Posts sound like *you* — maintaining your voice, topics, and avoiding generic corporate AI buzzwords.
- **Strict Approval Engine:** Content only moves forward when you approve it.
- **$0-First Dual Publishing:**
  - **Manual Mode ($0 Free, Zero Ban Risk):** Automatically notifies you via Telegram or CLI clipboard with pre-formatted text and one-click X compose links when scheduled. No X API fees.
  - **Official X API Mode:** Automated direct posting via official X API v2 when configured.
- **Crash-Proof Local Scheduler:** SQLite-backed APScheduler jobs that recover after computer sleep or reboots.

---

## 📁 Project Architecture & Documentation

Comprehensive architectural design and product specifications are located in [`docs/`](docs/):
- **[Product Requirements Document (PRD)](docs/PRD.md)**: Full scope, user personas, functional specifications, and non-goals.
- **[System Architecture](docs/ARCHITECTURE.md)**: Clean architecture diagrams, component boundaries, database schemas, and sequence flows.
- **[2-Phase Development Flow](docs/DEVELOPMENT_FLOW.md)**: Step-by-step breakdown across Phase 1 (Core & Manual) and Phase 2 (Remote & Autopilot).
- **[Testing Strategy](docs/TESTING.md)**: Pytest suite guidelines, mocks, and invariants.

---

## 🛠️ Directory Structure

```
postpilot/
├── docs/
│   ├── PRD.md                   # Complete Product Requirements Document
│   ├── ARCHITECTURE.md          # Architectural blueprints and diagrams
│   ├── DEVELOPMENT_FLOW.md      # 2-Phase implementation roadmap
│   └── TESTING.md               # Quality assurance & testing guide
├── src/
│   └── postpilot/
│       ├── cli.py               # Typer CLI application entry point
│       ├── main.py              # Application orchestrator
│       ├── commands/            # CLI command implementations (init, generate, drafts, etc.)
│       ├── ai/                  # Provider implementations (Groq, Gemini, Ollama, Router)
│       ├── services/            # Core business logic (content, drafts, queue, publishing)
│       ├── publishers/          # Publishing adapters (Manual clipboard/intent & official X API)
│       ├── scheduler/           # APScheduler background workers & recovery
│       ├── database/            # SQLite models, DB connection & repositories
│       ├── telegram/            # Telegram bot engine, keyboards & security
│       └── utils/               # Config, logging, validation, error definitions
├── tests/                       # Unit & integration test suites
├── pyproject.toml               # Project metadata & dependencies
├── .env.example                 # Configuration template
└── README.md
```

---

## 🚀 Quickstart

### 1. Installation

```bash
# Clone or navigate to the directory
cd postpilot

# Create virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"
```

### 2. Configuration

```bash
cp .env.example .env
# Edit .env with your free Groq/Gemini key or set up local Ollama
```

### 3. Initialize & Status

```bash
# Initialize database and creator profile
postpilot init

# Check system readiness
postpilot status
```

### 4. Workflow Demonstration

```bash
# 1. Generate 3 draft posts on a topic
postpilot generate --topic "Clean code vs shipping fast" --count 3

# 2. View generated drafts
postpilot drafts

# 3. Approve a draft
postpilot approve 1

# 4. Schedule post
postpilot schedule 1 --at "2026-11-22 18:30"

# 5. Run scheduler worker
postpilot run
```
