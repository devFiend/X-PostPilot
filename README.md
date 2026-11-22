<div align="center">

# 🚀 PostPilot (X-PostPilot)

### *Your Personal AI Content Management & Publishing Copilot for X (Twitter).*
**One Engine. Dual Interfaces (CLI + Telegram). 100% $0-First & Ban-Proof.**

[![PyPI Version](https://img.shields.io/pypi/v/postpilot.svg?style=for-the-badge&color=blue)](https://pypi.org/project/postpilot/)
[![GitHub Release](https://img.shields.io/github/v/release/devFiend/X-PostPilot?style=for-the-badge&color=blue)](https://github.com/devFiend/X-PostPilot/releases)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Architecture: Clean](https://img.shields.io/badge/Architecture-Clean%20%2F%20Modular-green.svg?style=for-the-badge)]()
[![Tests: Passing](https://img.shields.io/badge/Tests-19%2F19%20Passed-brightgreen.svg?style=for-the-badge)]()
[![Cost: $0-First](https://img.shields.io/badge/Cost-%240--First-success.svg?style=for-the-badge)]()

<br/>

> 💡 **The Reality:** Standard social tools either lock you into \$30-\$100/mo subscriptions, require expensive pay-per-use X API credits (\$0.015/post or \$0.20/link post), or use unofficial browser scrapers that get your personal account banned.  
> **PostPilot fixes this.** It lets you brainstorm, draft, review, schedule, and publish high-impact X content using **free AI quotas (Groq / Gemini / local Ollama)**, a crash-proof local scheduler, and a private Telegram control room — with **zero required API fees**.

---

[Features](#-key-features) •
[Architecture](#-system-architecture) •
[Quickstart](#-60-second-quickstart) •
[Telegram Setup](#-linking-your-telegram-bot) •
[TweetDNA Intelligence](#-tweetdna-creator-intelligence) •
[CLI Cheatsheet](#-cli-cheatsheet) •
[Deploy to Render](#-deploying-to-render-247-hosting) •
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
- **Anonymous Public Tweet Scraping ($0 Ban-Proof):** Scrapes recent public tweets from creators you admire (`@levelsio`, `@swyx`, `@shl`, `@karpathy`) without using your personal account or paid APIs.
- **4-Layer DNA Extraction:** Deconstructs Content Pillars, Tweet Formats, Writing Rhythm, and Hook Formulas.
- **Multi-Creator Synthesis:** Blends the best traits of 5-10 creators into original content tailored to your niche.

### ⏰ Spaced Content Drip Delivery (8:00 AM – 11:59 PM)
- Automatically delivers **1 fresh post card every 15 minutes** directly to your Telegram chat during active hours (08:00 – 23:59).
- Each card comes with a **`[🚀 Post to X Now]`** button that opens the pre-filled X composer directly in your phone's native X app in 1 tap, plus a **`[✅ Mark as Posted]`** button!
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
|   |  ApprovalService  |  | SchedulingService |  |    DNAService     |   |
|   +-------------------+  +-------------------+  +-------------------+   |
|   |  AutopilotService |  |       PublishingService                  |   |
|   +-------------------+  +------------------------------------------+   |
+--------------------|-------------------|--------------------|-----------+
                     |                   |                    |
     +---------------+                   |                    +---------------+
     |                                   |                                    |
+----v-----------------+      +----------v----------+      +------------------v---+
|  AI & TWEETDNA LAYER |      |  PUBLISHING LAYER   |      |   DATA & SCHEDULER   |
|                      |      |                     |      |                      |
| +------------------+ |      | +-----------------+ |      | +------------------+ |
| | TweetDNAAnalyzer | |      | | BasePublisher   | |      | | APScheduler      | |
| +------------------+ |      | +--------+--------+ |      | | (Hourly Drops)   | |
| | TweetDNAGenerator| |      |          |          |      | +------------------+ |
| +------------------+ |      |    +-----+----+     |      | | SQLite Store     | |
| | AIRouter (Groq/  | |      | +--v----+ +---v---+ |      | +------------------+ |
| | Gemini/Ollama)   | |      | |Manual | |X API  | |      | | SQLAlchemy Repos | |
| +------------------+ |      | |Handoff| |  v2   | |      | | (postpilot.db)   | |
+----------------------+      +---------+ +-------+ +      +----------------------+
```

---

## ⚡ 60-Second Quickstart

### 1. Installation

**Option A: Install directly via PyPI (Recommended)**
```bash
pip install postpilot
```

**Option B: Clone for local development**
```bash
git clone https://github.com/devFiend/X-PostPilot.git
cd X-PostPilot
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

---

## 🧬 TweetDNA Creator Intelligence

Reverse-engineer how your favorite creators write and synthesize their styles into your niche:

### Track a Creator (CLI or Telegram)
```bash
postpilot dna track @levelsio
postpilot dna track @swyx
```
In Telegram, simply send:
```text
/track @levelsio
```
PostPilot anonymously scrapes their recent public tweets, extracts their **Tone, Hook Patterns, and Writing Frameworks**, and adds them to your active creator intelligence pool!

### Generate Posts From Your Creator Pool
```bash
# Generate 4 on-demand posts across your tracked creators
postpilot dna ideas --count 4
```
In Telegram:
- `/ideas 2` — Returns 2 on-demand post cards.
- `/inspire @levelsio 2` — Drafts 2 posts specifically mimicking `@levelsio`'s voice.
- `/creators` — Lists all creators in your active intelligence pool.

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
5. Open your bot in Telegram and send `/track @levelsio` or `/ideas`.

---

## ☁️ Deploying to Render (24/7 Hosting)

PostPilot includes native Render support (`render.yaml` Blueprint) so your Telegram Bot and Hourly Drops run **24/7 in the cloud for free**:

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
| `postpilot dna track` | Track and analyze a creator's Content DNA | `postpilot dna track @levelsio` |
| `postpilot dna list` | List all tracked creators in intelligence pool | `postpilot dna list` |
| `postpilot dna ideas` | Generate posts synthesized from creator pool | `postpilot dna ideas --count 4` |
| `postpilot generate` | Generate multiple post options with AI | `postpilot generate -t "Clean Architecture" -c 3` |
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

PostPilot includes a complete test suite covering AI parsing, TweetDNA extraction, database repositories, state machine invariants, scheduler recovery, and security firewalls:

```bash
# Run full test suite
python -m pytest

# Run with verbose output
python -m pytest -v
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <b>Built with ❤️ by <a href="https://github.com/devFiend">DevFiend</a></b><br/>
  <i>Give this repository a ⭐ if it helps your content workflow!</i>
</div>
