# 02 — Scope & Requirements

**Status:** Draft v0.2 (2025‑08‑20)
**Owner:** YC Matcher Team
**Related:** [01‑product‑brief.md], [03‑architecture.md], [10‑ui‑reference.md]

---

## 1) Purpose

Define exactly **what the product must do** and the **acceptance criteria** to prove it.
Target outcome: a **hands‑off matcher** that, given *your profile*, *your match criteria*, and a *message template*, **autonomously** browses YC Cofounder Matching, evaluates profiles, and **sends messages** when appropriate.

Primary automation engine: **OpenAI Computer Use (CUA) via Responses API (computer_use tool) with local Playwright execution**. Agents SDK may be used as a wrapper, but you must run the browser and execute actions locally.
Fallback engine: **Playwright (Chromium)**, used only if CUA is unavailable.

---

## 2) In‑scope vs Out‑of‑scope

### In‑scope

* **Three inputs** (user‑provided):
  1. **Your Profile** (free text / markdown)
  2. **Match Criteria** (goals, must‑have/should‑have, disqualifiers)
  3. **Message Template** (with placeholders, e.g., `{first_name}`, `{why_match}`)

* **Autonomous browsing** of YC listing pages and profiles (CUA-first).
* **Profile understanding** from on‑screen text/screenshot, robust to layout changes.
* **Decision engine** with three modes:
  * **Advisor** (LLM‑only recommendation; HIL approval to send)
  * **Rubric** (deterministic rule scoring)
  * **Hybrid** (combine Advisor + Rubric via α)
* **Auto‑send** when decision ≥ threshold and quotas permit.
* **Safety**: STOP flag, pacing, daily/weekly quotas, dedupe, audit log.
* **UI**: Streamlit control panel for inputs, run control, live log.
* **Observability**: `events.jsonl` (append‑only), `seen.sqlite`, `quota.sqlite`.

### Out‑of‑scope

* Account creation or password storage.
* Solving CAPTCHAs or bypassing anti‑bot systems.
* Mass scraping/export of YC data; only transient per‑profile processing.
* Multi‑tenant SaaS/hosting. (Local desktop/server use only.)

---

## 3) User stories

* **U1 — Configure once**: As a user, I paste *my profile*, *criteria*, *template*.
* **U2 — One‑click run**: I click **Run** and the system handles discovery → decision → messaging.
* **U3 — HIL Advisory**: In **Advisor** mode, I see the recommendation and can **Approve & Send**.
* **U4 — Shadow/Dry‑run**: I can run evaluation **without sending**.
* **U5 — Safety**: I can hit **STOP** to immediately pause all actions.
* **U6 — Audit**: I can review exactly **what happened and why** in `events.jsonl`.

---

## 4) Functional requirements (FR)

> Each requirement has an ID for traceability into tests.

**Discovery & Navigation**

* **FR‑01**: The system must open the YC cofounder matching listing page (configurable `YC_MATCH_URL`) via **CUA**.
* **FR‑02**: The system must iterate candidate tiles, open each profile, and return to the listing to continue (robust to pagination/infinite scroll).
* **FR‑03**: The system must detect session/login state and **pause** with a UI prompt if login is required (no credentials stored).

**Perception & Extraction**

* **FR‑04**: The system must extract profile text reliably via CUA (screenshot → text) and/or DOM when fallback is Playwright.
* **FR‑05**: The system must normalize a minimal **Profile schema**:
  * `name`, `headline`, `bio`, `skills[]`, `interests[]`, `location?`, `stage?`, `availability?`, `links?`, `raw_text`.

**Decision**

* **FR‑06**: **Advisor** mode: produce a recommendation with rationale and a score ∈ [0,1].
* **FR‑07**: **Rubric** mode: deterministic rule scoring (must‑have → hard fail; should‑have → weighted score).
* **FR‑08**: **Hybrid** mode: final_score = `α * advisor_score + (1‑α) * rubric_score`. `α` configurable (`ALPHA`).
* **FR‑09**: Apply **threshold** (`THRESHOLD`) to determine auto‑send eligibility.
* **FR‑10**: Enforce **dedupe** (`seen.sqlite`) by hashing a stable profile identifier (e.g., profile URL + name).

**Messaging**

* **FR‑11**: Compose a **personalized message** from template, supporting placeholders:
  * `{first_name}`, `{why_match}`, `{my_context}`, `{their_highlight}`, `{cta}`
* **FR‑12**: **Send** only if:
  * not seen, not stopped, under quota, decision ≥ threshold, and **shadow mode** is off.
* **FR‑13**: **Verify send** by observing post‑send DOM/visual confirmation. On failure, retry ≤1 with backoff.

**Safety & Controls**

* **FR‑14**: **STOP** switch halts new actions within ≤ 2 seconds.
* **FR‑15**: Pacing: min delay **D** between sends; daily/weekly **quota** (`quota.sqlite`).
* **FR‑16**: **Shadow mode**: run full pipeline but never click "Send".
* **FR‑17**: **Playwright fallback**: if CUA init or action fails and `ENABLE_PLAYWRIGHT_FALLBACK=1`, use Playwright selectors to complete the step or mark as retriable failure.

**Observability**

* **FR‑18**: Log every step to `events.jsonl` (newline JSON) with:
  * `ts`, `run_id`, `event`, `provider`, `model`, `decision_mode`, `scores`, `threshold`, `action`, `ok`, `retry`, `cost_est`, `lat_ms`, and minimal redacted context.
* **FR‑19**: Emit `sent` event: `{"event":"sent","ok":true,"mode":"auto","verified":true,...}` on success.
* **FR‑20**: Persist `seen` and `quota` to SQLite; support re‑runs without duplications.

---

## 5) Non‑functional requirements (NFR)

* **NFR‑01 Performance**: ≥ 20 profiles/hour on a typical laptop with CUA; ≥ 60/hour with Playwright fallback on stable pages.
* **NFR‑02 Robustness**: Handle minor DOM/visual changes without code changes (CUA vision).
* **NFR‑03 Reliability**: ≤ 3% false positive sends (non‑fit accidentally messaged) on canary.
* **NFR‑04 Safety**: STOP and quotas always take precedence over sends.
* **NFR‑05 Privacy**: No persistent storage of full raw screenshots; keep minimal derived text needed for decision. No third‑party telemetry.
* **NFR‑06 Locality**: No writes to `$HOME`; all caches under repo (Makefile enforces).
* **NFR‑07 Observability**: 100% of actions/events traceable via `events.jsonl`.

---

## 6) Configuration (env)

```env
# Engines
ENABLE_CUA=1                         # Use OpenAI Computer Use (primary)
ENABLE_PLAYWRIGHT_FALLBACK=1         # Use Playwright if CUA fails
ENABLE_PLAYWRIGHT=0                  # (Optional) force Playwright

# OpenAI
OPENAI_API_KEY=sk-...
CUA_MODEL=<your-computer-use-model>  # from Models endpoint
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1200

# Decision
DECISION_MODE=hybrid                 # advisor|rubric|hybrid
OPENAI_DECISION_MODEL=<your-best-llm>  # for Advisor/Hybrid reasoning
THRESHOLD=0.72
ALPHA=0.50                           # weight for Advisor in Hybrid

# Run-time
YC_MATCH_URL=https://www.startupschool.org/cofounder-matching
PACE_MIN_SECONDS=45
DAILY_QUOTA=25
WEEKLY_QUOTA=120
SHADOW_MODE=0                        # 1 = never send
```

---

## 7) UI requirements (summary)

* Three inputs: **Your Profile**, **Match Criteria**, **Message Template** (markdown editors).
* Controls: **Run/Stop**, **Decision Mode**, **Threshold**, **Shadow Mode**.
* Status: CUA connectivity, fallback status, quota counters, last action.
* Live log view (tail of `events.jsonl`) and **Download logs**.

---

## 8) Data & storage

* `events.jsonl` — append‑only audit (newline JSON).
* `.runs/seen.sqlite` — dedupe by stable key.
* `.runs/quota.sqlite` — daily/weekly counters.
* **No** user secrets or YC credentials stored.

---

## 9) Safety, compliance, and rate limits

* Respect site ToS. Keep human‑like pacing (`PACE_MIN_SECONDS`) and quotas.
* **STOP** halts new actions immediately; running actions complete or fail fast.
* Dry‑run mode prevents sends entirely.
* Only per‑profile ephemeral processing; do not export/republish data.

---

## 10) Acceptance criteria (AC)

* **AC‑01**: With valid inputs and login, a single **Run** processes ≥ 10 profiles, logs each to `events.jsonl`, and sends ≥ 1 message if eligible.
* **AC‑02**: Setting `SHADOW_MODE=1` results in **no** sends while still producing decisions and logs.
* **AC‑03**: With `DAILY_QUOTA=1`, the second eligible profile **does not** send and logs a `quota_exceeded` event.
* **AC‑04**: Pressing **STOP** during processing halts new profile actions within ≤ 2 seconds.
* **AC‑05**: If CUA initialization fails, Playwright fallback takes over when `ENABLE_PLAYWRIGHT_FALLBACK=1`.
* **AC‑06**: `events.jsonl` includes a `sent` event with `ok=true` and `verified=true` for each successful send.
* **AC‑07**: Re‑running the same listing does **not** send to previously seen profiles.

---

## 11) Test plan (traceability)

| REQ         | Test ID         | Description                                      |
| ----------- | --------------- | ------------------------------------------------ |
| FR‑01/02    | INT‑NAV‑CUA‑01  | CUA opens listing, iterates profiles, returns.   |
| FR‑04/05    | INT‑EXTRACT‑01  | Extracts expected fields from a sample profile.  |
| FR‑06/07/08 | UNIT‑DEC‑01     | Advisor/Rubric/Hybrid scores; edge cases.        |
| FR‑09       | UNIT‑THRESH‑01  | Threshold gates auto‑send correctly.             |
| FR‑11/12    | INT‑MSG‑01      | Template renders placeholders; conditional send. |
| FR‑13       | INT‑VERIFY‑01   | Post‑send verification and retry ≤1.             |
| FR‑14       | INT‑STOP‑01     | STOP halts within ≤ 2 seconds.                   |
| FR‑15       | INT‑QUOTA‑01    | Quota prevents sends after limits reached.       |
| FR‑16       | INT‑SHADOW‑01   | Shadow mode produces decisions but no sends.     |
| FR‑17       | INT‑FALLBACK‑01 | Forced CUA failure triggers Playwright path.     |
| FR‑18/19/20 | UNIT‑LOG‑01     | Schema fields present; `sent` event format.      |
| NFR‑06      | INT‑LOCAL‑01    | No `$HOME` writes; repo‑scoped caches only.      |

---

## 12) Open questions / decisions

* **Model selection**: Which CUA model is enabled on our account today? (See `MODEL_SELECTION.md`.)
* **Element targeting**: Which YC send button texts/labels need explicit fallbacks in Playwright?
* **Ethics/ToS**: Confirm final rate limits and daily caps consistent with YC guidelines.
* **Login strategy**: HIL manual login only (baseline) vs. future SSO session persistence.

---

## 13) Glossary

* **CUA**: Computer Use (OpenAI Responses API computer_use tool; Playwright executes actions).
* **HIL**: Human‑in‑the‑loop.
* **Advisor**: LLM‑only recommendation mode.
* **Rubric**: Deterministic, rule‑based scoring.
* **Hybrid**: Advisor + Rubric weighted by `ALPHA`.

---

**Definition of Done for this document**

* All FR/NFR/AC are testable and mapped to IDs.
* Inputs/outputs and controls reflect the **3‑input** product vision.
* CUA‑first, Playwright fallback is explicit and configurable.
* Safety (STOP, quotas, shadow) and observability are complete and verifiable.
