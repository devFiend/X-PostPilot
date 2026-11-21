# PostPilot — Testing & Verification Strategy

**Framework:** `pytest` + `pytest-asyncio` + `pytest-mock`  
**Philosophy:** Rigorous unit and integration testing without spending money on AI tokens or X API credits. All external calls are mocked in automated suites.

---

## 1. Test Suite Structure

```
tests/
├── conftest.py              # Shared fixtures (in-memory SQLite, test configs, mock AI responses)
├── test_ai.py               # Multi-provider routing, fallback, and length validation
├── test_content.py          # Draft CRUD, content profile injection, character count checks
├── test_queue.py            # Status state machine (DRAFT -> APPROVED -> SCHEDULED -> PUBLISHED)
├── test_scheduler.py        # APScheduler persistence, timezone handling, restart recovery
├── test_publishing.py       # Manual handoff, X API client, rate limits, credit failures
└── test_telegram.py         # Owner authentication gatekeeper, message routing, command handlers
```

---

## 2. Testing Scenarios & Invariants

### 2.1 AI Providers & Output Validation (`test_ai.py`)
- **Character Count Limit:** Validate that every generated post does not exceed 280 characters.
- **Provider Failover:** When Groq returns a 503 or 429 error, verify that `AIRouter` falls back to Gemini or Ollama if configured for auto-fallback.
- **Mocking Providers:** Use mock HTTP responses to test Groq, Gemini, and Ollama without requiring active API keys during CI/CD.

### 2.2 Content & Approval State Machine (`test_content.py` & `test_queue.py`)
- **Unapproved Posting Invariant:** Ensure the system **never** publishes or schedules a post whose status is `DRAFT` or `PENDING_APPROVAL`.
- **Duplicate Detection:** Ensure identical post text cannot be submitted twice within a 48-hour window.
- **State Transitions:**
  - Valid: `DRAFT` $\rightarrow$ `APPROVED` $\rightarrow$ `SCHEDULED` $\rightarrow$ `PUBLISHED`
  - Invalid: `DRAFT` $\rightarrow$ `PUBLISHED` (must raise `ApprovalRequiredError`)

### 2.3 Scheduler & Restart Recovery (`test_scheduler.py`)
- **Database Persistence:** Schedule a post, instantiate a new scheduler instance (simulating app restart), and verify the job is recovered from SQLite.
- **Missed Job Handling:** Create a post scheduled for 10 minutes in the past; verify the recovery routine flags it for user confirmation rather than silently firing stale tweets.
- **Timezone Accuracy:** Verify that a post scheduled at `18:30 Africa/Lagos` correctly computes the UTC execution timestamp.

### 2.4 Publishing Adapters (`test_publishing.py`)
- **Manual Publisher:**
  - Verify that `ManualPublisher` generates a valid URL-encoded Twitter Intent link.
  - Verify that the clipboard copy hook is called.
  - Verify that the post is marked as `PUBLISHED_MANUAL` and never calls external networks.
- **Official X API Publisher:**
  - Mock HTTP 201 response $\rightarrow$ verify `tweet_id` is parsed and stored.
  - Mock HTTP 403 (Insufficient Credits) $\rightarrow$ verify graceful fallback to Manual mode with a logged alert.
  - Mock HTTP 429 (Rate Limit) $\rightarrow$ verify retry metadata.

### 2.5 Telegram Security & Bot Commands (`test_telegram.py`)
- **Owner ID Authentication:**
  - Incoming update from `TELEGRAM_OWNER_ID` $\rightarrow$ Processed normally.
  - Incoming update from attacker / unauthorized ID $\rightarrow$ Blocked immediately, response not sent, incident logged.
- **Confirmation for Destructive Actions:** Ensure `/cancel` or draft deletion requires explicit inline confirmation.

---

## 3. Running Tests

```bash
# Run all unit tests
pytest

# Run with verbose output and coverage
pytest -v --cov=postpilot --cov-report=term-missing

# Run only AI provider tests
pytest tests/test_ai.py

# Run only scheduler and queue tests
pytest tests/test_scheduler.py tests/test_queue.py
```
