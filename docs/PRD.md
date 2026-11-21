# PostPilot — Product Requirements Document (PRD)

**Product Name:** PostPilot  
**Category:** AI-Powered Social Media Content Assistant  
**Version:** V1.0  
**Initial Platform:** X (Twitter)  
**Primary Language:** Python 3.11+  
**Interfaces:** Python CLI (`Typer` + `Rich`) and Telegram Bot (`python-telegram-bot`)  
**Core Constraint:** $0-First Development & Operation  

---

## 1. Executive Summary & Vision

PostPilot is a personal AI-powered social media copilot that helps individual creators, developers, founders, and personal brands plan, draft, refine, schedule, approve, and publish high-quality content on X. 

Unlike simple "auto-tweeters" or spam bots, PostPilot is a **content management engine and executive assistant**:
- Helps decide what to write through structured category prompts and creator profiles.
- Generates multiple distinct post angles without repeating thoughts.
- Maintains an approval-governed publishing queue.
- Operates under a strict **$0-first philosophy**: fully functional offline or using free AI tiers (Groq, Gemini Free Tier, local Ollama) without mandatory hosting or third-party paid subscriptions.
- Features **Dual-Mode Publishing**:
  1. **Manual Mode ($0 cost):** Delivers pre-formatted posts with copy buttons via Telegram or terminal clipboard output when scheduled, completely avoiding X API charges and browser bans.
  2. **Official X API Mode (Pay-per-use):** Direct programmatic publishing via X API v2 when configured with official developer credentials.

---

## 2. Problem Statement

Creators, solo founders, and technical professionals consistently run into five hurdles:
1. **Ideation Fatigue:** Staring at a blank editor trying to come up with daily insights or hooks.
2. **Draft Disorganization:** Notes and tweet ideas scattered across Apple Notes, Notion, Slack self-messages, and scratch files.
3. **Inconsistent Cadence:** Forgetting to post at optimal times due to high context-switching costs.
4. **Fear of Hallucinated / Embarrassing Automation:** Autonomous bots publishing unreviewed, repetitive, or low-quality AI outputs under their personal name.
5. **Platform Financial & Policy Walls:** X API v2 pricing ($0.015/basic post, $0.20/URL post) makes purely automated micro-posting expensive for hobbyists, while unofficial browser automation puts personal accounts at risk of permanent suspension.

---

## 3. Product Goals & Non-Goals

### 3.1 Primary Goals
- **Single Backend, Dual Interfaces:** One clean service layer powering both a feature-packed terminal CLI and an interactive Telegram bot.
- **Provider-Agnostic Content Generation:** Native support for Groq (fast Llama 3/Mixtral), Google Gemini (deep content planning), and Ollama (local/offline).
- **Strict Approval Engine:** Content is never published automatically unless explicit autopilot privileges are granted.
- **Persistent Local Queue & Scheduling:** SQLite-backed queue using APScheduler with automatic state recovery across system reboots and sleep cycles.
- **Zero-Cost Operation:** 100% usable end-to-end without spending a dime.
- **Strict Platform Compliance:** Zero browser scraping, zero private cookie hacking, zero ban risk.

### 3.2 Non-Goals (Explicitly Excluded from V1)
- Multi-platform publishing (LinkedIn, Threads, Bluesky, Mastodon scheduled for V2).
- Automated follow/unfollow, auto-liking, automated DM sending, or growth-hacking bot behaviors.
- Web-based SaaS dashboard or multi-tenant database.
- Browser automation / Selenium / Playwright hacks for X web UI.
- Unsolicited auto-replies or engagement farming.

---

## 4. User Personas

### Primary Persona: The Indie Developer / Builder (DevFiend)
- **Role:** Full-stack developer, founder, build-in-public creator.
- **Needs:** Quick capture of engineering lessons, bug postmortems, architecture tips, and release announcements without leaving the terminal or while messaging on Telegram.
- **Pain Point:** Cannot justify enterprise social media tools or unmetered X API costs; cannot risk personal account suspension from non-compliant web bots.

---

## 5. Core Feature Specifications

### 5.1 AI Content Generation Engine
- **Command:** `postpilot generate --topic "<topic>" --count <n> --category <cat> --provider <provider>`
- **Content Categories:**
  - Educational / Breakdown
  - Personal Experience & Lessons Learned
  - Contrarian Opinion / Developer Observation
  - Build-in-Public / Progress Update
  - Technical Tips & Snippets
  - Questions & Engagement Hooks
  - Short Stories & Narratives
- **Output Validation:**
  - Length check: Strict enforcement of the 280-character limit (standard X post).
  - Variety check: Distinct angles, hooks, and structures across generated candidates.
  - Profile injection: Uses creator tone, content pillars, and banned buzzwords.

### 5.2 Creator Content Profiles (`CreatorDNA`)
- Stored locally in SQLite and YAML/JSON.
- Configurable attributes:
  - Persona Name & Bio
  - Core Content Pillars (e.g., Software Engineering, AI tooling, Startups)
  - Tone & Voice (e.g., direct, candid, no corporate buzzwords)
  - Prohibited phrases (e.g., "In today's fast-paced world", "Game changer", "Dive deep")
  - Hook styles (curiosity gaps, counter-intuitive statements, bold claims).

### 5.3 Draft Management & Queue
- Status lifecycle:
  `DRAFT` $\rightarrow$ `PENDING_APPROVAL` $\rightarrow$ `APPROVED` $\rightarrow$ `SCHEDULED` $\rightarrow$ `PUBLISHING` $\rightarrow$ `PUBLISHED` (or `FAILED` / `CANCELLED`).
- Operations: list, view, edit text, approve, reject, delete, reschedule.
- Safety invariant: Unapproved drafts cannot be dispatched by the scheduler.

### 5.4 Scheduling & Local Background Engine
- Database-backed job queue powered by `APScheduler` and SQLite.
- Timezone-aware (defaults to user's localized timezone, e.g., `Africa/Lagos` or system local).
- Sleep & Reboot Recovery: On startup, PostPilot scans for missed or pending scheduled items and prompts for manual dispatch or automatic catch-up.

### 5.5 Dual-Mode Publishing Strategy ($0-First)
- **Method A: Manual Handoff ($0 Cost):**
  - Sends a push notification via Telegram with a "Copy Text" button and direct link to X compose intent (`https://twitter.com/intent/tweet?text=...`).
  - Terminal CLI prints formatted box with clipboard auto-copy.
  - Marks item as `HANDED_OFF` / `PUBLISHED_MANUAL`.
- **Method B: Official X API v2:**
  - Utilizes OAuth 1.0a / OAuth 2.0 user-context credentials.
  - Checks remaining balance or credit status before triggering POST `/2/tweets`.
  - Captures official Tweet ID and permalink.

### 5.6 Telegram Bot Interface
- Single-user authenticated bot (locked to `TELEGRAM_OWNER_ID`).
- Interactive conversation handlers for:
  - Drafting & generation with inline buttons (`[Approve]`, `[Edit]`, `[Regenerate]`, `[Schedule]`).
  - Queue inspection (`/queue`) and Draft browsing (`/drafts`).
  - Emergency Autopilot Pause (`/pause`, `/resume`).
- Direct copyable markdown code blocks for instant mobile posting to X.

### 5.7 Autopilot Mode
- **Level 1 (Assisted Autopilot):** Periodically drafts posts aligned with content pillars and delivers them to Telegram for one-tap approval.
- **Level 2 (Autonomous Autopilot - Explicit Opt-in):** Auto-schedules and publishes approved items or auto-generated items during pre-configured daily windows.
- Safety Guardrails: Max posts per day ceiling, mandatory rate limit cooldowns, and instant master switch kill switch (`postpilot autopilot disable` / `/pause`).

---

## 6. Project Phasing & Milestones

To guarantee steady progress and modular testing, PostPilot is structured into two core phases:

### Phase 1: Core Engine, Local Queue & $0 Manual Operations
- Base project setup, Typer CLI, SQLite schema, and configuration manager.
- Multi-provider AI generation (Groq, Gemini, Ollama) with response validation and character count enforcement.
- Local draft CRUD, status state machine, and approval lifecycle.
- APScheduler integration with SQLite persistence and reboot recovery.
- Manual Publishing Adapter: Terminal clipboard copy + X compose URL generator.

### Phase 2: Official Integrations, Telegram Bot & Autopilot
- Secure Telegram Bot with owner authentication, conversational flows, and inline keyboards.
- Telegram push notifications for scheduled post manual dispatch (one-tap copy).
- Official X API v2 publisher adapter with credential testing, rate limiting, and tweet ID tracking.
- Autopilot engine: schedule slots, pillar rotation, and emergency pause.
- End-to-end integration test suite, diagnostics (`doctor`), and release documentation.

---

## 7. Metrics & Definition of Done

1. **Zero Unexpected Costs:** Development and standard daily operations run completely on free tiers.
2. **Crash Resilience:** Killing the background worker process and restarting it leaves zero drafts lost and resumes all pending scheduled jobs cleanly.
3. **Zero Account Bans:** No non-compliant web scraping or reverse-engineered private API calls.
4. **Latency:** AI generation returns candidates within $<3$ seconds using Groq or $<7$ seconds using Gemini/Ollama.
