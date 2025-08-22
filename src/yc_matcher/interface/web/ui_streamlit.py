from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from yc_matcher import config
from yc_matcher.application.autonomous_flow import AutonomousFlow
from yc_matcher.application.use_cases import ProcessCandidate
from yc_matcher.config import load_settings
from yc_matcher.domain.entities import Criteria, Profile
from yc_matcher.infrastructure.sqlite_quota import SQLiteDailyWeeklyQuota
from yc_matcher.infrastructure.sqlite_repo import SQLiteSeenRepo
from yc_matcher.infrastructure.stop_flag import FileStopFlag
from yc_matcher.infrastructure.storage import read_count
from yc_matcher.infrastructure.template_loader import load_default_template
from yc_matcher.interface.di import build_services

# Load environment variables from .env file
load_dotenv()


def render_three_input_mode() -> None:
    """Render autonomous 3-input mode UI following Clean Code principles.

    SOLID: Single Responsibility - Only handles UI rendering
    DRY: Reuses existing services and components
    """
    st.set_page_config(page_title="YC Matcher (Autonomous Mode)", layout="wide")
    st.title("🚀 YC Co-Founder Matcher - Autonomous Mode")

    # Initialize session state for HIL and screenshots
    if "hil_pending" not in st.session_state:
        st.session_state["hil_pending"] = None
    if "last_screenshot" not in st.session_state:
        st.session_state["last_screenshot"] = None

    # Three main inputs (Strategy Pattern - different input strategies)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📝 Your Profile")
        your_profile = st.text_area(
            "Describe yourself",
            height=200,
            placeholder="Technical co-founder\n5 years Python/FastAPI\nNYC based\nB2B SaaS experience",
            key="your_profile",
        )

    with col2:
        st.subheader("🎯 Match Criteria")
        criteria_text = st.text_area(
            "What you're looking for",
            height=200,
            placeholder="Business background\nB2B sales experience\nHealthcare knowledge\nSF or remote",
            key="match_criteria_auto",
        )

    with col3:
        st.subheader("💬 Message Template")
        template_text = st.text_area(
            "Outreach template", height=200, value=load_default_template(), key="msg_template_auto"
        )

    # Configuration section
    st.markdown("---")
    col_conf1, col_conf2, col_conf3 = st.columns(3)

    with col_conf1:
        # Auto-send control
        auto_send = st.toggle(
            "Auto-send on match",
            value=config.get_auto_send_default(),
            key="auto_send",
            help="When ON: Automatically sends messages to matches. When OFF: Shows matches for review first.",
        )
        if auto_send:
            st.info("🚀 Messages will be sent automatically")
        else:
            st.info("👀 Matches will be shown for review")

        # Mode is always AI now
        mode = "ai"  # For backwards compatibility

    with col_conf2:
        # Quota and limits
        max_profiles = st.number_input(
            "Max profiles to process",
            min_value=1,
            max_value=100,
            value=config.get_auto_browse_limit(),
            step=1,
            key="auto_quota",
        )

    with col_conf3:
        # Safety controls
        st.subheader("🛡️ Safety Mode")
        shadow_mode = st.toggle(
            "Test Mode (Evaluate Only)",
            value=config.is_shadow_mode(),
            key="shadow_auto",
            help="When ON: Evaluates profiles but NEVER sends messages. When OFF: Will actually send real messages to matches.",
        )
        if shadow_mode:
            st.success("✅ **SAFE MODE**: Will evaluate but NOT send any messages")
            st.caption("Perfect for testing. No messages will be sent.")
        else:
            st.error("⚠️ **LIVE MODE**: Will ACTUALLY SEND real messages!")
            st.caption("Real messages will be sent to matches. Use with caution.")

    # Debug info expander
    with st.expander("🔍 Debug Info", expanded=False):
        # Determine engine type
        cua_enabled = config.is_cua_enabled()
        playwright_enabled = config.is_playwright_enabled()

        if cua_enabled:
            engine = "**CUA planner + Playwright executor**"
            st.success(f"Engine: {engine}")
            st.caption("OpenAI CUA plans actions, Playwright executes them")
        elif playwright_enabled:
            engine = "**Playwright-only**"
            st.info(f"Engine: {engine}")
            st.caption("Direct browser automation without AI planning")
        else:
            engine = "**None (dry run)**"
            st.warning(f"Engine: {engine}")

        # Show key environment settings
        st.code(f"""
Environment Settings:
• PLAYWRIGHT_HEADLESS: {config.is_headless()}
• PLAYWRIGHT_BROWSERS_PATH: {os.getenv("PLAYWRIGHT_BROWSERS_PATH", "not set")}
• CUA_MODEL: {config.get_cua_model() or "not set"}
• CUA_MAX_TURNS: {config.get_cua_max_turns()}
• PACE_MIN_SECONDS: {config.get_pace_seconds()}
• Auto-Send: {auto_send}
• Shadow Mode: {shadow_mode}
        """)

    # Advanced settings in expander (Clean Code: hide complexity)
    with st.expander("⚙️ Advanced Settings"):
        # Using AI-only decision mode
        st.info("🤖 Using AI-only decision mode")
        decision_model = config.get_decision_model()
        st.caption(f"Model: **{decision_model}**")

        # Set dummy values for backwards compatibility
        threshold = 0.7  # Not used but kept for function signature
        alpha = 0.5  # Not used but kept for function signature  # noqa: F841

        enable_cua = st.toggle(
            "Use OpenAI Computer Use",
            value=config.is_cua_enabled(),
            help="Use AI to browse (vs Playwright fallback)",
            key="enable_cua_auto",
        )

    # STOP control (Safety First principle)
    stop_flag = FileStopFlag(Path(".runs/stop.flag"))

    col_stop1, col_stop2 = st.columns([1, 4])
    with col_stop1:
        if st.button("🛑 STOP", type="secondary", use_container_width=True):
            stop_flag.set()
            st.rerun()
    with col_stop2:
        if stop_flag.is_stopped():
            st.error("⛔ STOP flag is SET - browsing will halt immediately")
            if st.button("Clear STOP flag"):
                stop_flag.clear()
                st.rerun()

    # HIL Safety Check Panel (Strategy Pattern for different approval strategies)
    if st.session_state.get("hil_pending"):
        with st.warning("⚠️ Safety Check Required"):
            st.markdown("**Action requiring approval:**")
            safety_check = st.session_state["hil_pending"]
            st.code(safety_check.get("message", "Unknown action"))

            col_approve, col_reject = st.columns(2)
            with col_approve:
                if st.button("✅ Approve", type="primary"):
                    st.session_state["hil_response"] = True
                    st.session_state["hil_pending"] = None
                    st.rerun()
            with col_reject:
                if st.button("❌ Reject", type="secondary"):
                    st.session_state["hil_response"] = False
                    st.session_state["hil_pending"] = None
                    st.rerun()

    # Screenshot Panel (shows last action screenshot)
    if st.session_state.get("last_screenshot"):
        with st.expander("📸 Last Screenshot", expanded=False):
            screenshot_b64 = st.session_state["last_screenshot"]
            st.image(f"data:image/png;base64,{screenshot_b64}", use_column_width=True)

    # Status Panel - Show current system state
    with st.expander("🔍 System Status", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            # Login status
            email, password = config.get_yc_credentials()
            has_credentials = bool(email and password)
            browser = st.session_state.get("browser_instance")
            is_logged_in = False
            if browser and hasattr(browser, "is_logged_in"):
                try:
                    is_logged_in = browser.is_logged_in()
                except Exception:
                    pass

            if is_logged_in:
                st.success("✅ **Logged In**")
            elif has_credentials:
                st.info("🔑 **Credentials Available** (will auto-login)")
            else:
                st.warning("⚠️ **Manual Login Required**")

        with col2:
            # Model info
            decision_model = config.get_decision_model()
            st.info(f"🤖 **Model**: {decision_model}")

            # Engine type
            engine = "CUA + Playwright" if enable_cua else "Playwright Only"
            st.info(f"⚙️ **Engine**: {engine}")

        with col3:
            # Headless mode
            headless = config.is_headless()
            mode_str = "Headless" if headless else "Headful (visible)"
            st.info(f"👁️ **Browser**: {mode_str}")

            # Decision mode
            st.info(f"📊 **Decision**: {mode.capitalize()}")

    # Last Events Panel
    if os.path.exists(".runs/events.jsonl"):
        with st.expander("📝 Recent Events", expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("🔄 Refresh", key="refresh_events"):
                    st.rerun()
            with col3:
                if st.button("🗑️ Clear", key="clear_events"):
                    # Clear the events file
                    with open(".runs/events.jsonl", "w") as f:
                        f.write("")
                    st.rerun()
            
            try:
                import json
                from datetime import datetime, timedelta

                # Read last 20 events (more context)
                events_path = Path(".runs/events.jsonl")
                content = events_path.read_text().strip()
                recent_events = []  # Initialize here to avoid undefined variable
                
                if not content:
                    st.info("No recent events")
                else:
                    lines = content.split("\n")
                    
                    # Get only recent events (last hour)
                    cutoff_time = datetime.now() - timedelta(hours=1)
                    
                    for line in lines[-20:]:
                        if line.strip():
                            try:
                                event = json.loads(line)
                                # Try to parse timestamp (handle both 'timestamp' and 'ts' fields)
                                timestamp_str = event.get("timestamp", "")
                                ts_unix = event.get("ts", None)
                                
                                if timestamp_str:
                                    try:
                                        event_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                                        # Only include recent events
                                        if event_time.replace(tzinfo=None) > cutoff_time:
                                            recent_events.append(event)
                                    except:
                                        # If can't parse time, include it anyway (for backwards compat)
                                        recent_events.append(event)
                                elif ts_unix:
                                    # Handle Unix timestamp format
                                    try:
                                        event_time = datetime.fromtimestamp(ts_unix)
                                        if event_time > cutoff_time:
                                            # Convert ts to readable timestamp for display
                                            event["timestamp"] = event_time.strftime("%Y-%m-%d %H:%M:%S")
                                            recent_events.append(event)
                                    except:
                                        recent_events.append(event)
                                else:
                                    # No timestamp at all, include it
                                    recent_events.append(event)
                            except Exception:
                                pass

                # Display in reverse order (newest first)
                if not recent_events:
                    st.info("No events in the last hour. Events are cleared after 1 hour.")
                    
                for event in reversed(recent_events):
                    event_type = event.get("event", "unknown")
                    timestamp = event.get("timestamp", "")

                    # Color-code by event type with more detail
                    if event_type == "sent":
                        st.success(f"✅ {timestamp} - {event_type}")
                    elif event_type in ["error", "stopped", "login_failed", "evaluation_error", "profile_processing_error", "openai_error"]:
                        error_msg = event.get("error", "Unknown error")
                        st.error(f"❌ {timestamp} - {event_type}: {error_msg[:100]}")
                    elif event_type == "decision":
                        decision = event.get("data", {}).get("decision", "")
                        if decision == "YES":
                            st.info(f"👍 {timestamp} - decision: YES")
                        elif decision == "ERROR":
                            st.error(f"⚠️ {timestamp} - decision: ERROR")
                        else:
                            st.warning(f"👎 {timestamp} - decision: NO")
                    else:
                        st.text(f"• {timestamp} - {event_type}")
            except Exception as e:
                st.error(f"Could not read events: {e}")

    # Main action button
    st.markdown("---")
    if st.button("🚀 Start Autonomous Browsing", type="primary", use_container_width=True):
        if not your_profile or not criteria_text:
            st.error("Please fill in Your Profile and Match Criteria")
            return

        # Store configuration in session state
        st.session_state["auto_config"] = {
            "your_profile": your_profile,
            "criteria": criteria_text,
            "template": template_text,
            "mode": mode,
            "max_profiles": max_profiles,
            "shadow": shadow_mode,
            # Pass required parameters to build_services
            "threshold": None,
            "alpha": None,
            "auto_send": auto_send,
            "enable_cua": enable_cua,
        }

        # Launch autonomous flow with HIL callback
        st.info("🔄 Starting autonomous browsing...")

        # Create HIL callback for safety checks
        async def hil_approve_callback(safety_check: Any) -> bool:
            """HIL approval callback that integrates with Streamlit UI."""
            # Store pending check in session state
            st.session_state["hil_pending"] = {
                "id": getattr(safety_check, "id", ""),
                "code": getattr(safety_check, "code", ""),
                "message": getattr(safety_check, "message", ""),
            }

            # Wait for user response (non-blocking async pattern)
            import asyncio
            import time

            timeout = 60  # 60 second timeout
            start = time.time()

            while time.time() - start < timeout:
                if "hil_response" in st.session_state:
                    response = st.session_state.pop("hil_response")
                    return bool(response)
                await asyncio.sleep(0.5)  # Non-blocking async sleep

            # Timeout - default to reject for safety
            return False

        with st.spinner("🔄 Starting autonomous browsing..."):
            try:
                # Build services (browser singleton ensures we reuse any existing browser)
                eval_use, send_use, logger = build_services(
                    criteria_text=criteria_text,
                    template_text=template_text,
                    prompt_ver="v1",
                    rubric_ver="v1",
                    enable_cua=enable_cua,  # Pass UI toggle value
                )

                browser = send_use.browser

                # Store browser in session state for potential reuse
                st.session_state["browser_instance"] = browser

                # Wire callbacks to browser if CUA enabled
                if enable_cua:
                    if hasattr(browser, "hil_approve_callback"):
                        browser.hil_approve_callback = hil_approve_callback
                    if hasattr(browser, "screenshot_callback"):
                        # Screenshot callback to update UI
                        def screenshot_callback(screenshot_b64: str) -> None:
                            st.session_state["last_screenshot"] = screenshot_b64

                        browser.screenshot_callback = screenshot_callback

                # Create dependencies for autonomous flow
                seen_repo = SQLiteSeenRepo(db_path=Path(".runs/seen.sqlite"))
                quota = SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))
                stop_flag = FileStopFlag(Path(".runs/stop.flag"))

                # Create autonomous flow orchestrator
                flow = AutonomousFlow(
                    browser=send_use.browser,
                    evaluate=eval_use,
                    send=send_use,
                    seen=seen_repo,
                    logger=logger,
                    stop=stop_flag,
                    quota=quota,
                )

                # Execute autonomous flow
                results = flow.run(
                    your_profile=your_profile,
                    criteria=criteria_text,
                    template=template_text,
                    mode=mode,
                    limit=max_profiles,
                    shadow_mode=shadow_mode,
                    threshold=threshold,
                    alpha=0.5,
                )

                # Display results
                st.success("✅ Autonomous browsing complete!")

                # Count errors
                error_count = sum(1 for r in results.get("results", []) if r.get("decision") == "ERROR")
                
                col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
                with col_metrics1:
                    st.metric("Evaluated", results.get("total_evaluated", 0))
                with col_metrics2:
                    st.metric("Sent", results.get("total_sent", 0))
                with col_metrics3:
                    st.metric("Skipped", results.get("total_skipped", 0))
                with col_metrics4:
                    st.metric("⚠️ Errors", error_count)
                
                # Show errors prominently if any occurred
                if error_count > 0:
                    st.error(f"⚠️ {error_count} profiles failed to evaluate!")
                    with st.expander("🔴 Error Details", expanded=True):
                        for r in results.get("results", []):
                            if r.get("decision") == "ERROR":
                                st.error(f"Profile {r.get('profile_num')}: {r.get('rationale', 'Unknown error')}")
                                if "error" in r:
                                    st.code(r["error"])

                # Show detailed results in expander
                with st.expander("📊 All Results", expanded=False):
                    # Show results in a more readable format
                    for r in results.get("results", []):
                        decision = r.get("decision", "?")
                        profile = r.get("profile_num", "?")
                        
                        if decision == "YES":
                            st.success(f"Profile {profile}: ✅ {decision} - {r.get('rationale', '')}")
                        elif decision == "NO":
                            st.info(f"Profile {profile}: ❌ {decision} - {r.get('rationale', '')}")
                        elif decision == "ERROR":
                            st.error(f"Profile {profile}: ⚠️ ERROR - {r.get('rationale', '')}")

            except Exception as e:
                import traceback

                st.error(f"Failed to start: {e}")
                with st.expander("Error Details", expanded=True):
                    st.code(traceback.format_exc())


def render_paste_mode() -> None:
    """Render the existing paste-based evaluation mode.

    This is the current main() function content, extracted for clarity.
    SOLID: Single Responsibility - Separate UI modes
    """
    st.set_page_config(page_title="YC Matcher (Paste & Evaluate)", layout="wide")
    st.title("YC Co-Founder Matcher — Paste & Evaluate (Gated)")

    with st.sidebar:
        st.header("Session Settings")
        default_template = load_default_template()
        criteria_text = st.text_area(
            "Ideal match criteria",
            height=160,
            placeholder="e.g., Python, FastAPI, React, healthcare",
            key="criteria",
        )
        template_text = st.text_area(
            "Message template", value=default_template, height=300, key="template"
        )
        quota = st.number_input(
            "Quota (messages this session)", min_value=1, max_value=50, value=5, step=1, key="quota"
        )
        _shadow = st.toggle("Shadow Mode (no sending)", value=True)
        st.caption("Shadow Mode on: evaluate only, do not send.")
        # STOP switch (.runs/stop.flag)
        stop_flag = FileStopFlag(Path(".runs/stop.flag"))
        stopped = st.toggle("STOP (abort run)", value=stop_flag.is_stopped())
        if stopped:
            stop_flag.set()
        else:
            stop_flag.clear()
        if config.is_calendar_quota_enabled():
            st.info("Calendar quota enabled (daily/weekly caps). Sends will be blocked at limit.")
        try:
            sent = read_count()
            st.metric("Remaining", max(0, int(quota) - sent))
        except Exception:
            pass

    st.subheader("Paste Candidate Profile")
    profile_text = st.text_area("Profile text", height=400, key="profile")

    col1, col2 = st.columns([1, 1])
    with col1:
        go = st.button("Evaluate", type="primary")
    with col2:
        st.caption("Evaluate with schema + rubric. Approve & Send uses Playwright if enabled.")

    if go:
        if not profile_text.strip():
            st.warning("Paste a profile first.")
            return

        eval_use, send_use, logger = build_services(
            criteria_text=criteria_text,
            template_text=template_text,
            prompt_ver="v1",
            rubric_ver="v1",
            enable_cua=False,  # Paste mode doesn't use CUA
        )
        data = eval_use(Profile(raw_text=profile_text), Criteria(text=criteria_text))

        st.markdown(f"**Decision:** {data.get('decision')}")
        st.markdown(f"**Rationale:** {data.get('rationale')}")
        draft = data.get("draft")
        if draft:
            st.markdown("**Draft message:**")
            st.code(draft)
        if data.get("decision") == "YES":
            colA, colB = st.columns([1, 3])
            with colA:
                do_send = st.button("Approve & Send (Playwright)")
            with colB:
                st.caption("Requires ENABLE_PLAYWRIGHT=1 and manual login in the opened browser.")
            if do_send:
                if not config.is_playwright_enabled():
                    st.error("Set ENABLE_PLAYWRIGHT=1 in your environment to enable sending.")
                else:
                    try:
                        settings = load_settings()
                        seen = SQLiteSeenRepo(db_path=Path(".runs/seen.sqlite"))
                        eval_use2, send_use2, logger2 = build_services(
                            criteria_text=criteria_text,
                            template_text=template_text,
                            prompt_ver="v1",
                            rubric_ver="v1",
                            enable_cua=False,  # Paste mode doesn't use CUA
                        )
                        browser = send_use2.browser
                        pc = ProcessCandidate(
                            evaluate=eval_use2,
                            send=send_use2,
                            browser=browser,
                            seen=seen,
                            logger=logger2,
                        )
                        url = getattr(settings, "yc_match_url", None) or "https://www.startupschool.org/cofounder-matching"
                        pc(
                            url=str(url),
                            criteria=Criteria(text=criteria_text),
                            limit=int(quota),
                            auto_send=True,
                        )
                        st.success("Sent (check logs for details).")
                    except Exception as e:
                        st.error(f"Send failed: {e}")


def main() -> None:
    """Main entry point with feature flag for UI mode selection.

    Strategy Pattern: Select UI strategy based on feature flag
    Open/Closed: Easy to add new UI modes without modifying existing
    """
    # Feature flag for UI mode (Open/Closed Principle)
    if config.use_three_input_ui():
        render_three_input_mode()
    else:
        render_paste_mode()


if __name__ == "__main__":
    main()
