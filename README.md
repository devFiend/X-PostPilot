<div align="center">

# 🚀 PostPilot (X-PostPilot)

### *Your Personal AI Content Management & Publishing Copilot for X (Twitter).*
**One Engine. Dual Interfaces (CLI + Telegram). 100% $0-First & Ban-Proof.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Architecture: Clean](https://img.shields.io/badge/Architecture-Clean%20%2F%20Modular-green.svg?style=for-the-badge)]()
[![Tests: Passing](https://img.shields.io/badge/Tests-11%2F11%20Passed-brightgreen.svg?style=for-the-badge)]()
[![Cost: $0-First](https://img.shields.io/badge/Cost-%240--First-success.svg?style=for-the-badge)]()

<br/>

> 💡 **The Reality:** Standard social tools either lock you into \$30-\$100/mo subscriptions, require expensive pay-per-use X API credits (\$0.015/post or \$0.20/link post), or use unofficial browser scrapers that get your personal account banned.  
> **PostPilot fixes this.** It lets you brainstorm, draft, review, schedule, and publish high-impact X content using **free AI quotas (Groq / Gemini / local Ollama)**, a crash-proof local scheduler, and a private Telegram control room — with **zero required API fees**.

---

[Features](#-key-features) •
[Architecture](#-system-architecture) •
[Quickstart](#-60-second-quickstart) •
[Telegram Setup](#-linking-your-telegram-bot) •
[CLI Cheatsheet](#-cli-cheatsheet) •
[Documentation](#-deep-documentation) •
[License](#-license)

</div>

---

## 🔥 Key Features

### 🧠 Multi-Provider AI Brain ($0-First)
- **Groq (Default):** Generates high-velocity, scroll-stopping post variants in $<2$ seconds using LLaMA-3 / GPT-OSS models.
- **Google Gemini:** Deep content planning and long-form breakdown using Gemini's generous free tier.
- **Ollama:** 100% private, offline generation with zero internet reliance.
- **Strict Guardrails:** Built-in validator guarantees every post stays strictly under 280 characters with no corporate fluff or repetitive buzzwords.

### 🧬 TweetDNA Creator Intelligence & Style Cloning
- **Anonymous Public Tweet Scraping ($0 Ban-Proof):** Scrapes recent public tweets from creators you admire (`@levelsio`, `@swyx`, `@shl`) without using your personal account or paid APIs.
- **4-Layer DNA Extraction:** Deconstructs Content Pillars, Tweet Formats, Writing Rhythm, and Hook Formulas.
- **Multi-Creator Synthesis:** Blends the best traits of 5-10 creators into original content tailored to your niche.

### ⏰ Hourly Content Delivery (8:00 AM – 11:59 PM)
- Automatically delivers **4–5 fresh post cards every hour** directly to your Telegram chat.
- Each card comes with a **`[🚀 Post to X Now (Auto-Approves)]`** button that opens the pre-filled X composer on your phone in 1 tap!
- On-demand requests anytime: `/ideas [count]` or `/inspire @creator [count]`.

### 🎭 CreatorDNA Content Profiling
- Generates posts that sound like **you**, not a boilerplate corporate bot.
- Configurable content pillars (e.g., *Software Engineering, AI Tools, Building in Public*), voice guidelines, and excluded phrases.

### 🛡️ $0 Dual-Mode Publishing (Zero Ban Risk)
- **Method A: Manual Handoff ($0 Cost - Recommended):**  
  When a scheduled post is due, PostPilot copies the post to your system clipboard and delivers a pre-formatted push notification to your phone via Telegram with a one-tap link to X's official web compose intent. No X API fees, zero chance of account suspension.
- **Method B: Official X API v2 (Optional):**  
  Supports OAuth 1.0a User-Context authentication for full programmatic publishing when official credits are available. Automatically falls back to manual handoff if credits run out.

### 📱 Private Telegram Remote Control
- Single-user authenticated bot locked to your personal `TELEGRAM_OWNER_ID`.
- Generate, inspect, approve, reject, and schedule posts directly from your phone while on the go.

### ⏰ Crash-Resilient Local Scheduler
- Powered by `APScheduler` backed by a persistent SQLite jobstore.
- If your laptop goes to sleep or restarts, pending jobs are automatically recovered and queued on boot.

### ⚡ Autopilot with Emergency Kill-Switch
- Rotates content pillars throughout the day.
- Supports **Assisted Autopilot** (drafts content automatically and pings you on Telegram for one-tap approval) and **Autonomous Autopilot** (auto-schedules directly).
- Instant emergency pause button (`postpilot autopilot pause` or Telegram `/pause`).

---

## 🏛️ System Architecture

PostPilot is built on a clean, decoupled modular architecture: **"One Engine, Multiple Interfaces."**

```
+-------------------------------------------------------------------------+
|                              INTERFACES                                 |
|                                                                         |
|      +---------------------------+     +--------------------------+     |
|      |         Typer CLI         |     |   Telegram Bot Engine    |     |
|      |    (Rich terminal UI)     |     | (Long-polling, Inline KB)|     |
|      +-------------+-------------+     +------------+-------------+     |
+--------------------|--------------------------------|-------------------+
                     |                                |
                     +---------------+----------------+
                                     |
+------------------------------------v------------------------------------+
|                         APPLICATION SERVICES                            |
|                                                                         |
|   +-------------------+  +-------------------+  +-------------------+   |
|   |   ContentService  |  |    DraftService   |  |    QueueService   |   |
|   +-------------------+  +-------------------+  +-------------------+   |
|   |  ApprovalService  |  | SchedulingService |  |  AutopilotService |   |
|   +-------------------+  +-------------------+  +-------------------+   |
|   |                       PublishingService                         |   |
|   +-----------------------------------------------------------------+   |
+--------------------|-------------------|--------------------|-----------+
                     |                   |                    |
     +---------------+                   |                    +---------------+
     |                                   |                                    |
+----v-----------------+      +----------v----------+      +------------------v---+
|       AI LAYER       |      |  PUBLISHING LAYER   |      |   DATA & SCHEDULER   |
|                      |      |                     |      |                      |
| +------------------+ |      | +-----------------+ |      | +------------------+ |
| |    AIRouter      | |      | | BasePublisher   | |      | | APScheduler      | |
| +------------------+ |      | +--------+--------+ |      | | (SQLite Store)   | |
| | Groq / Gemini /  | |      |          |          |      | +------------------+ |
| | Ollama Adapters  | |      |    +-----+----+     |      | | SQLAlchemy Repos | |
| +------------------+ |      | +--v----+ +---v---+ |      | +------------------+ |
|                      |      | |Manual | |X API  | |      | | SQLite DB        | |
|                      |      | |Handoff| |  v2   | |      | | (postpilot.db)   | |
|                      |      | +-------+ +-------+ |      | +------------------+ |
+----------------------+      +---------------------+      +----------------------+
```

---

## ⚡ 60-Second Quickstart

### 1. Clone the repository
```bash
git clone https://github.com/devFiend/X-PostPilot.git
cd X-PostPilot
```

### 2. Set up virtual environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate

# Activate on macOS/Linux:
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

### 3. Configure environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your free [Groq API Key](https://console.groq.com/keys):
```env
GROQ_API_KEY=gsk_your_free_key_here
```

### 4. Verify system with Doctor
```bash
python -m postpilot.cli doctor
```

### 5. Generate your first posts!
```bash
python -m postpilot.cli generate --topic "Why developers should write clean code" --count 3
```

---

## 🤖 Linking Your Telegram Bot

Manage your queue and approve posts from your couch in **under 2 minutes**:

1. **Create Bot:** Search for [@BotFather](https://t.me/BotFather) on Telegram $\rightarrow$ send `/newbot` $\rightarrow$ copy your **API Token**.
2. **Get Your User ID:** Search for [@userinfobot](https://t.me/userinfobot) on Telegram $\rightarrow$ click start $\rightarrow$ copy your numerical **ID**.
3. **Save to `.env`:**
   ```env
   TELEGRAM_BOT_TOKEN=7123456789:AAFlM_...
   TELEGRAM_OWNER_ID=123456789
   ```
4. **Launch Bot:**
   ```bash
   python -m postpilot.cli telegram
   ```
5. Open your bot in Telegram and send `/generate Why indie hacking is rewarding`. Click `[Approve]` or `[Copy Post]` right on your phone!

---

## ☁️ Deploying to Render (24/7 Hosting)

PostPilot includes native Render support (`render.yaml` Blueprint) so your Telegram Bot and Scheduler can run **24/7 in the cloud for free**:

1. Push this repository to your GitHub.
2. Log into **[Render.com](https://render.com/)**.
3. Click **New +** $\rightarrow$ **Blueprint**.
4. Connect your `X-PostPilot` repository.
5. Render will detect `render.yaml`. Fill in your environment variables:
   - `GROQ_API_KEY`: your free Groq key
   - `TELEGRAM_BOT_TOKEN`: your BotFather token
   - `TELEGRAM_OWNER_ID`: your numerical Telegram ID
6. Click **Apply**. Render will build and deploy PostPilot with automatic health checks!

---

## 💻 CLI Cheatsheet

| Command | Description | Example |
|---|---|---|
| `postpilot start` | Run unified daemon (Scheduler + Telegram + Health Check) | `postpilot start` |
| `postpilot doctor` | Run diagnostic check on AI keys, DB, and Telegram | `postpilot doctor` |
| `postpilot init` | Initialize profile, timezone, and database | `postpilot init` |
| `postpilot status` | Inspect system health, queue counts, and provider | `postpilot status` |
| `postpilot generate` | Generate multiple post options with AI | `postpilot generate -t "FastAPI vs Django" -c 3` |
| `postpilot drafts` | Browse all saved drafts | `postpilot drafts` |
| `postpilot approve` | Approve a draft for scheduling | `postpilot approve 1` |
| `postpilot schedule` | Schedule an approved post | `postpilot schedule 1 --at "2026-11-25 18:30"` |
| `postpilot queue` | View pending scheduled posts | `postpilot queue` |
| `postpilot publish` | Dispatch post (copies text & opens compose link) | `postpilot publish 1` |
| `postpilot run` | Run background scheduler worker loop | `postpilot run` |
| `postpilot telegram` | Run Telegram bot long-polling daemon | `postpilot telegram` |
| `postpilot autopilot` | Manage autopilot states & cycles | `postpilot autopilot run-cycle` |

---

## 📚 Deep Documentation

Comprehensive architectural design, specifications, and test documentation:
- 📖 **[Product Requirements Document (PRD)](docs/PRD.md):** Vision, functional scope, personas, and platform policies.
- 📐 **[System Architecture](docs/ARCHITECTURE.md):** Clean architecture layers, database schemas (ERD), and sequence diagrams.
- 🗺️ **[2-Phase Development Flow](docs/DEVELOPMENT_FLOW.md):** Full implementation roadmap and milestone verification.
- 🧪 **[Testing Strategy](docs/TESTING.md):** Test suite design, invariant testing, and mocking guide.

---

## 🧪 Testing

PostPilot includes a complete test suite covering AI parsing, database repositories, state machine invariants, scheduler recovery, and security firewalls:

```bash
# Run test suite
python -m pytest

# Run with verbose output
python -m pytest -v
```

---

## 🤝 Contributing

Contributions are what make the open-source community an incredible place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <b>Built with ❤️ by <a href="https://github.com/devFiend">DevFiend</a></b><br/>
  <i>Give this repository a ⭐ if it helps your content workflow!</i>
</div>
