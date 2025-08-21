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

### 2. The REAL Browser Problem

```mermaid
sequenceDiagram
    participant AF as AutonomousFlow
    participant CUA as OpenAICUABrowser
    participant ASYNC as Async Methods
    participant PW as Playwright
    
    Note over AF,CUA: PROBLEM: Sync/Async Mismatch!
    
    AF->>CUA: browser.open(url) [SYNC]
    CUA->>CUA: asyncio.run(_open_async)
    CUA->>ASYNC: _open_async(url)
    ASYNC->>ASYNC: _ensure_browser()
    
    Note over ASYNC,PW: CRASHES HERE!
    ASYNC->>PW: playwright.chromium.launch()
    PW--xAF: Error: Executable doesn't exist<br/>/home/jj/.cache/ms-playwright
    
    Note over PW: Looking in WRONG path!<br/>Should use .ms-playwright
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

### 5. Why It's Failing - The Real Issue

```mermaid
graph TB
    subgraph "Current State"
        ENV[PLAYWRIGHT_BROWSERS_PATH=.ms-playwright<br/>Set in environment]
        CUA[OpenAICUABrowser]
        PW[Playwright]
    end
    
    subgraph "The Problem"
        INIT[_ensure_browser called]
        LAUNCH[playwright.chromium.launch<br/>headless=False]
        FAIL[Looks for browser in<br/>/home/jj/.cache/ms-playwright]
    end
    
    subgraph "Why?"
        R1[Environment variable not passed<br/>to async context]
        R2[Playwright ignores env var<br/>after initialization]
        R3[Need to set BEFORE<br/>async_playwright().start()]
    end
    
    ENV -.NOT USED.-> CUA
    CUA --> INIT
    INIT --> LAUNCH
    LAUNCH --> FAIL
    
    FAIL --> R1
    FAIL --> R2
    FAIL --> R3
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