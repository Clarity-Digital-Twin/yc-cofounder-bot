UI Reference (YC Co‑Founder Matching)

Assets
- Link: WEBSITE_LINK.MD (Startup School cofounder-matching URL)
- Login screenshot: initial_log_in.png
- Profile view screenshot: view_profile_clicked.png
- Current example profile: CURRENT_COFOUNDER_PROFILE.MD
- Outreach template (default): MATCH_MESSAGE_TEMPLATE.MD

Observed Flow
- Landing/login: authenticate at Startup School cofounder-matching.
- Candidate list: each row exposes a “View profile” action.
- Profile page:
  - Main content: candidate bio, skills, background, interests.
  - Right panel: message box with “Send” and “Skip” controls.

HIL Paste Mode (MVP)
- Operator pastes the profile text (from the center pane) into the app.
- App returns Yes/No + rationale + draft using MATCH_MESSAGE_TEMPLATE.MD.
- Operator can copy message or click “Send via browser” (semi‑auto).

Semi‑Auto Mode (Next)
- Headful browser navigates list → clicks “View profile”.
- Reads profile, composes draft, focuses message box (right panel).
- Calls quota_guard; on approval, clicks “Send” or “Skip”.

Notes for Automation
- Prefer visible text (buttons labeled “View profile”, “Send”, “Skip”) for robust actions.
- Keep viewport ~1280×800 to match screenshots and stabilize layout.
- Insert short waits after navigation, opening profiles, and sending messages.
