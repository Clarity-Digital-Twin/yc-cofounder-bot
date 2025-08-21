# YC Co-Founder Matcher - Architecture Diagrams

## The ACTUAL Data Flow (From Code Analysis)

### 1. Entry Point Flow

```mermaid
graph TD
    User[User] -->|Fills 3 inputs| UI[Streamlit UI<br/>ui_streamlit.py]
    UI -->|Creates services via DI| DI[build_services<br/>di.py]
    
    DI -->|Decision Mode?| DM{Decision Mode}
    DM -->|advisor| ADV[OpenAIDecision]
    DM -->|rubric| RUB[RubricOnlyAdapter]  
    DM -->|hybrid| HYB[GatedDecision<br/>+OpenAIDecision]
    
    DI -->|Browser Type?| BT{ENABLE_CUA?}
    BT -->|Yes| CUA[OpenAICUABrowser]
    BT -->|No + ENABLE_PLAYWRIGHT| PW[PlaywrightBrowser]
    BT -->|Neither| NULL[_NullBrowser]
    
    UI -->|Creates| AF[AutonomousFlow]
    AF -->|Uses| CUA
    AF -->|Uses| ADV
```

### 2. Browser Init & Async/Sync Edges

```mermaid
sequenceDiagram
    participant AF as AutonomousFlow
    participant CUA as OpenAICUABrowser
    participant ASYNC as Async Methods
    participant PW as Playwright
    
    Note over AF,CUA: Sync/async boundary is sensitive
    
    AF->>CUA: open(url) [sync]
    CUA->>CUA: asyncio.run(_open_async)
    CUA->>ASYNC: _open_async(url)
    ASYNC->>ASYNC: _ensure_browser()
    ASYNC->>PW: async_playwright().start(); chromium.launch()
    Note over CUA,PW: PLAYWRIGHT_BROWSERS_PATH set before start (current code)
    
    alt Called from an active loop
        CUA--xAF: asyncio.run raises "loop already running"
    else Normal sync context
        PW-->>CUA: Page ready
    end
```

### 3. What's Actually Happening in AutonomousFlow

```mermaid
flowchart TD
    Start[Start] --> Open[browser.open<br/>YC_MATCH_URL]
    Open --> Loop{For i in range<br/>limit}
    
    Loop -->|Check| Stop{STOP flag?}
    Stop -->|Yes| End[Return results]
    Stop -->|No| Click[browser.click_view_profile]
    
    Click -->|Success| Read[browser.read_profile_text]
    Click -->|Fail| NoMore[No more profiles]
    NoMore --> End
    
    Read -->|Empty| Skip1[browser.skip]
    Read -->|Has text| Hash[hash_profile_text]
    
    Hash --> Seen{Already seen?}
    Seen -->|Yes| Skip2[browser.skip]
    Seen -->|No| Mark[seen.mark_seen]
    
    Mark --> Eval[evaluate profile]
    Eval --> Decision{Should send?}
    
    Decision -->|Yes| Fill[browser.fill_message]
    Fill --> Send[browser.send]
    Send --> Verify[browser.verify_sent]
    
    Decision -->|No| Skip3[browser.skip]
    
    Skip1 --> Loop
    Skip2 --> Loop
    Skip3 --> Loop
    Verify --> Loop
```

### 4. The Actual Class Dependencies

```mermaid
classDiagram
    class AutonomousFlow {
        -browser: BrowserPort
        -evaluate: EvaluateProfile
        -send: SendMessage
        -seen: SQLiteSeenRepo
        -logger: LoggerWithStamps
        -stop: FileStopFlag
        -quota: SQLiteDailyWeeklyQuota
        +run(profile, criteria, template, mode, limit)
    }
    
    class OpenAICUABrowser {
        -client: OpenAI
        -playwright: Playwright [NULL!]
        -browser: Browser [NULL!]
        -page: Page [NULL!]
        +open(url) SYNC
        +_open_async(url) ASYNC
        +_ensure_browser() ASYNC
        Problem: Browser path not set!
    }
    
    class EvaluateProfile {
        -decision: DecisionPort
        -message: MessageRenderer
        +__call__(profile, criteria)
    }
    
    class GatedDecision {
        -decision: OpenAIDecision
        -gate_scorer: RubricScorer
        -threshold: float
        -alpha: float
        +__call__(profile, criteria)
    }
    
    AutonomousFlow --> OpenAICUABrowser
    AutonomousFlow --> EvaluateProfile
    EvaluateProfile --> GatedDecision
    GatedDecision --> OpenAIDecision
```

### 5. Common Failure Modes

```mermaid
graph TB
    subgraph "Potential Issues"
        M1[Async/sync mismatch<br/>asyncio.run within async]
        M2[Headless/display problems]
        M3[Playwright install path mismatch]
        M4[CUA call blocks event loop]
    end
    
    subgraph "Mitigations"
        F1[Keep Port sync; expose async adapter for tests]
        F2[Allow PLAYWRIGHT_HEADLESS=1 fallback]
        F3[Ensure PLAYWRIGHT_BROWSERS_PATH set before start]
        F4[Run OpenAI calls in thread executor]
    end
    
    M1 --> F1
    M2 --> F2
    M3 --> F3
    M4 --> F4
```

### 6. The Fix We Need

```mermaid
graph LR
    subgraph "Before _ensure_browser"
        SET[os.environ['PLAYWRIGHT_BROWSERS_PATH']<br/>= '.ms-playwright']
    end
    
    subgraph "Then"
        START[async_playwright().start()]
        LAUNCH[chromium.launch()]
    end
    
    SET --> START
    START --> LAUNCH
    LAUNCH --> SUCCESS[Browser opens!]
```

## The Truth

1. **It IS simple** in concept - browse, evaluate, send
2. **BUT** the implementation has issues:
   - Async/sync mismatch between layers
   - Browser path not being set correctly
   - Environment variables not propagating to async context

3. **The core loop works** but can't start because browser won't launch

4. **We lost our fixes** when we reset to avoid the API key issue

## 7. CUA + Playwright Detailed Interaction Flow

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant AF as AutonomousFlow
    participant CUA as OpenAICUABrowser
    participant Client as OpenAI Client
    participant PW as Playwright Page
    participant YC as YC Website
    
    Note over UI,YC: Full CUA Loop (Responses API Pattern)
    
    UI->>AF: run(profile, criteria, template)
    AF->>CUA: open(YC_MATCH_URL)
    
    rect rgb(240, 240, 240)
        Note over CUA,PW: Browser Initialization
        CUA->>CUA: _ensure_browser()
        CUA->>CUA: Set PLAYWRIGHT_BROWSERS_PATH
        CUA->>PW: chromium.launch()
        PW->>PW: new_page()
    end
    
    rect rgb(250, 250, 240)
        Note over CUA,YC: Navigation Loop
        CUA->>PW: goto(url)
        PW->>YC: GET /cofounder-matching
        YC-->>PW: HTML Response
        PW->>PW: screenshot()
        
        CUA->>Client: responses.create(screenshot)
        Client-->>CUA: Response with computer_call
        
        alt Has computer_call
            CUA->>PW: Execute action (click/type)
            PW->>YC: Perform action
            YC-->>PW: Updated page
            PW->>PW: screenshot()
            CUA->>Client: responses.create(computer_call_output)
        else Text response
            CUA-->>AF: Return extracted text
        end
    end
    
    AF->>AF: evaluate_profile()
    AF->>CUA: send_message() if threshold met
```

## 8. Decision Flow Architecture (All 3 Modes)

```mermaid
flowchart TB
    subgraph "Input"
        Profile[Profile Text]
        Criteria[Match Criteria]
        Mode[Decision Mode]
    end
    
    subgraph "Decision Router"
        Router{Which Mode?}
    end
    
    subgraph "Advisor Mode"
        A1[OpenAIDecision]
        A2[LLM Analysis]
        A3[Extract Fields]
        A4[Generate Rationale]
        A5[HIL Approval Required]
    end
    
    subgraph "Rubric Mode"
        R1[RubricOnlyAdapter]
        R2[Calculate Skill Match]
        R3[Calculate Location Match]
        R4[Calculate Experience Match]
        R5[Weighted Score]
        R6[Auto-send if > threshold]
    end
    
    subgraph "Hybrid Mode"
        H1[GatedDecision]
        H2[Get LLM Confidence]
        H3[Get Rubric Score]
        H4[Alpha Weighting]
        H5[Combined Score]
        H6[Auto-send if > threshold]
    end
    
    Profile --> Router
    Criteria --> Router
    Mode --> Router
    
    Router -->|advisor| A1
    A1 --> A2 --> A3 --> A4 --> A5
    
    Router -->|rubric| R1
    R1 --> R2
    R1 --> R3
    R1 --> R4
    R2 --> R5
    R3 --> R5
    R4 --> R5
    R5 --> R6
    
    Router -->|hybrid| H1
    H1 --> H2
    H1 --> H3
    H2 --> H4
    H3 --> H4
    H4 --> H5
    H5 --> H6
```

## 9. Error Handling & Recovery Flows

```mermaid
stateDiagram-v2
    [*] --> BrowserInit
    
    BrowserInit --> BrowserReady: Success
    BrowserInit --> BrowserError: Fail
    
    BrowserError --> CheckPath: Path Issue?
    BrowserError --> CheckHeadless: Display Issue?
    
    CheckPath --> SetEnvVar: Fix Path
    SetEnvVar --> BrowserInit: Retry
    
    CheckHeadless --> FallbackHeadless: Set PLAYWRIGHT_HEADLESS=1
    FallbackHeadless --> BrowserInit: Retry
    
    BrowserReady --> Navigate
    Navigate --> ProfileLoop
    
    ProfileLoop --> CheckStop
    CheckStop --> StopRequested: stop.flag exists
    CheckStop --> ClickProfile: Continue
    
    StopRequested --> Cleanup
    
    ClickProfile --> ReadProfile: Success
    ClickProfile --> NoMoreProfiles: No button found
    ClickProfile --> CUATimeout: Timeout
    
    CUATimeout --> PlaywrightFallback: If enabled
    CUATimeout --> SkipProfile: If disabled
    
    PlaywrightFallback --> ReadProfile: Use selectors
    
    ReadProfile --> EvaluateProfile
    EvaluateProfile --> SendMessage: Above threshold
    EvaluateProfile --> SkipProfile: Below threshold
    
    SendMessage --> QuotaCheck
    QuotaCheck --> QuotaExceeded: Over limit
    QuotaCheck --> PerformSend: Within limit
    
    QuotaExceeded --> Cleanup
    PerformSend --> ProfileLoop
    SkipProfile --> ProfileLoop
    NoMoreProfiles --> Cleanup
    
    Cleanup --> [*]
```

## 10. Quota & Safety Mechanisms Flow

```mermaid
flowchart LR
    subgraph "Safety Checks"
        S1[Check STOP flag]
        S2[Check Daily Quota]
        S3[Check Weekly Quota]
        S4[Check Seen Database]
        S5[Check Shadow Mode]
        S6[Check Pace Timing]
    end
    
    subgraph "Decision Points"
        D1{STOP?}
        D2{Daily OK?}
        D3{Weekly OK?}
        D4{Already Seen?}
        D5{Shadow Mode?}
        D6{Too Fast?}
    end
    
    subgraph "Actions"
        A1[Abort - STOP requested]
        A2[Abort - Daily exceeded]
        A3[Abort - Weekly exceeded]
        A4[Skip - Already messaged]
        A5[Log only - Shadow mode]
        A6[Wait - Pace control]
        A7[Send Message]
    end
    
    S1 --> D1
    D1 -->|Yes| A1
    D1 -->|No| S2
    
    S2 --> D2
    D2 -->|No| A2
    D2 -->|Yes| S3
    
    S3 --> D3
    D3 -->|No| A3
    D3 -->|Yes| S4
    
    S4 --> D4
    D4 -->|Yes| A4
    D4 -->|No| S5
    
    S5 --> D5
    D5 -->|Yes| A5
    D5 -->|No| S6
    
    S6 --> D6
    D6 -->|Yes| A6
    A6 --> A7
    D6 -->|No| A7
```

## 11. Event Logging & Persistence Flow

```mermaid
sequenceDiagram
    participant Flow as AutonomousFlow
    participant Logger as LoggerWithStamps
    participant Events as events.jsonl
    participant Seen as seen.sqlite
    participant Quota as quota.sqlite
    
    Note over Flow,Quota: Every action emits events
    
    Flow->>Logger: log_event("started")
    Logger->>Events: {"event": "started", "timestamp": "..."}
    
    Flow->>Flow: Read profile
    Flow->>Logger: log_event("profile_read")
    Logger->>Events: {"event": "profile_read", "text": "..."}
    
    Flow->>Seen: check_seen(profile_hash)
    Seen-->>Flow: False (not seen)
    
    Flow->>Flow: Evaluate profile
    Flow->>Logger: log_event("decision")
    Logger->>Events: {"event": "decision", "mode": "hybrid", "score": 0.85}
    
    Flow->>Quota: check_quota()
    Quota-->>Flow: {daily: 5/25, weekly: 30/120}
    
    Flow->>Flow: Send message
    Flow->>Logger: log_event("sent")
    Logger->>Events: {"event": "sent", "profile_id": "..."}
    
    Flow->>Seen: mark_seen(profile_hash)
    Seen->>Seen: INSERT INTO seen_profiles
    
    Flow->>Quota: increment()
    Quota->>Quota: UPDATE quotas SET daily = daily + 1
```

## 12. BUGS & ISSUES IDENTIFIED (Validated Against Code)

### Critical Bugs Found:

1. **Async/Sync Interface Mismatch**
   - Ports are synchronous; several tests expect async methods
   - Risk: `asyncio.run()` fails when invoked inside an existing event loop
   - Action: Keep sync `BrowserPort` for app; provide an async test adapter or add `awaitable` wrappers guarded by "if loop running"

2. **Playwright Headless/Install Variance**
   - Launch can fail on CI/headless displays or missing install path
   - Current code sets `PLAYWRIGHT_BROWSERS_PATH` before start (good)
   - Action: Document `python -m playwright install chromium`; allow `PLAYWRIGHT_HEADLESS=1` fallback in docs/UI

3. **CUA Calls Block Event Loop**
   - `responses.create(...)` is sync but used inside `async` code
   - Risk: blocks the loop under real I/O; tests mock this
   - Action: run blocking calls in a thread via `asyncio.to_thread` or `loop.run_in_executor`

4. **Limited Error Recovery in Flow**
   - Flow catches exceptions and skips, but no retries/backoff
   - Action: Add small bounded retries for read/skip, and restart browser on fatal errors

5. **Quota Atomicity (File Counter)**
   - `FileQuota` JSON counter is not atomic across processes
   - Action: Prefer SQLite quota (already implemented) or add file lock

6. **Profile Text Cache Semantics**
   - Cache retains last text to avoid empty return; not a leak but can mislead
   - Action: Clear cache on navigation/skip to avoid stale reuse

7. **HIL Callback Robustness**
   - Code assumes async callback; a sync callback would error
   - Action: accept both sync/async callbacks (inspect and wrap accordingly)

8. **STOP Check Granularity**
   - Checked at loop head; SendMessage path doesn’t re-check
   - Action: Re-check stop before send, and in long operations

9. **Pacing Blocks UI Thread**
   - `time.sleep` in `SendMessage` blocks for `PACE_MIN_SECONDS`
   - Action: Move pacing outside or make non-blocking when called from UI
