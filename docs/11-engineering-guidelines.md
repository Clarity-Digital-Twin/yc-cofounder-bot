Engineering Guidelines (DDD, Clean Code, TDD)

Principles
- DDD: Separate domain, application, infrastructure, and interface layers. Keep domain pure and independent.
- SOLID/DRY/Clean: Small, cohesive modules; explicit dependencies; no duplication.
- TDD: Write failing unit tests first for domain/application logic; iterate to green; refactor.
- GoF Patterns (when useful): Strategy (scoring), Adapter (Playwright/OpenAI), Repository (SQLite), Builder (message), Command (send/skip), Facade (decision service).

Layering
- Domain: entities/value objects (Criteria, Profile, Decision), domain services (ScoringService), pure and framework‑agnostic.
- Application: use cases/orchestrators (EvaluateProfile, SendMessage), ports (interfaces) that the infra implements.
- Infrastructure: adapters/clients (OpenAI client, Playwright computer, SQLite repo, JSONL logger) implementing application ports.
- Interface: Streamlit UI and CLI, wiring and DI container/factories.

Dependencies
- Domain → none
- Application → Domain
- Infrastructure → Application + Domain (implements ports)
- Interface → Application (invokes use cases)

Testing Strategy
- Unit (Domain/Application): TDD, fast, no I/O. Mock ports.
- Integration (Infra): verify adapters (OpenAI stub, Playwright test page, SQLite repo) against ports.
- E2E (Manual/HIL): runbook with Shadow Mode, logs, and acceptance criteria.

Coding Conventions
- Types: mypy strict; prefer `dataclass` for domain entities; Pydantic for schemas/DTOs.
- Errors: fail fast in domain; convert to user‑friendly messages in interface.
- Config: immutable settings object passed via DI; no global reads in domain.
- Logging: structured JSON events via logger port; no print statements in domain/application.
- Prompts: versioned; stored as assets; include prompt version in logs.

Ports (Interfaces)
- DecisionPort: `evaluate(profile: Profile, criteria: Criteria) -> DecisionDTO`
- ScoringPort: `score(profile: Profile, criteria: Criteria) -> Score`
- MessagePort: `render(decision: Decision) -> Draft`
- QuotaPort: `check_and_increment(limit: int) -> bool`
- SeenRepo: `is_seen(hash) -> bool`, `mark_seen(hash)`
- LoggerPort: `emit(Event)`
- BrowserPort: `open(url)`, `view_profile()`, `fill_message(text)`, `send()`, `skip()`

DI & Composition
- Provide factories in interface layer to assemble application services with infra implementations.
- Favor constructor injection; pass only ports needed by each use case.

Refactoring Policy
- Start implementing ports and use cases with the current module layout; migrate to layered packages as we grow.
- Keep public APIs stable; mark internal helpers as private (leading underscore) where applicable.
