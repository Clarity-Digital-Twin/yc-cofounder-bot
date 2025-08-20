Model Selection and Upgrades

Overview
- This project uses two model roles:
  - Computer Use model: drives on-screen actions via OpenAI's Computer Use tool in the Agents SDK.
  - Decision model: performs reasoning for Advisor/Hybrid modes (text-only prompts), independent from Computer Use.

Defaults
- Computer Use: `CUA_MODEL=<your account's computer-use model>`
- Decision LLM: `DECISION_MODEL` must be set to the strongest model you have access to (account/tier dependent).

Guidelines
- Do not hardcode model names in code. Read them from env/config.
- Treat Computer Use and Decision models independently; you can upgrade one without the other.
- Favor determinism for Computer Use by lowering temperature (e.g., 0.2–0.4) and keeping prompts concise.

When a New Model Arrives (e.g., GPT‑5 with Computer Use)
1. Confirm availability in your account and that it explicitly supports Computer Use.
2. Update `.env`:
   - `CUA_MODEL=<new-computer-use-model>`
   - Optionally update `DECISION_MODEL=<new-reasoning-model>`
3. Run checks:
   - `make verify` (lint, types, tests)
   - Contract tests for `ComputerUsePort`
   - E2E smoke test on a small canary batch
4. Compare metrics (success rate, latency, cost). If regressions occur, revert env vars.

Acceptance Tests (must pass for any model change)
- Navigates to YC listing and opens a profile.
- Extracts visible profile text reliably.
- Fills and sends a message, then verifies confirmation.
- Respects STOP flag, quotas, and pacing.

Notes
- Model names and availability vary by tier and region. Always rely on official OpenAI documentation visible to your account for the canonical list of supported models and features.
- If the docs list multiple Computer Use models, prefer the one recommended for production (often labeled “latest” or “recommended”) unless you are explicitly testing a preview.

