from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from yc_matcher import config
from yc_matcher.application.autonomous_flow import AutonomousFlow
from yc_matcher.infrastructure.control.stop_flag import FileStopFlag
from yc_matcher.infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota
from yc_matcher.infrastructure.persistence.sqlite_repo import SQLiteSeenRepo
from yc_matcher.infrastructure.utils.template_loader import load_default_template
from yc_matcher.interface.di import build_services

# Load environment variables from .env file
load_dotenv()


def render_three_input_mode() -> None:
    """Render the streamlined autonomous browsing UI."""
    st.set_page_config(page_title="YC Co-Founder Matcher", layout="wide", page_icon="🚀")

    # Header with clean title
    st.title("🚀 YC Co-Founder Matcher")
    st.markdown("Autonomous browser automation for finding your perfect co-founder")

    # Main input section - the three core inputs
    st.markdown("### Step 1: Define Your Search")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📝 Your Profile**")
        your_profile = st.text_area(
            "Describe yourself",
            height=200,
            placeholder="Technical co-founder\n5 years Python/FastAPI\nNYC based\nB2B SaaS experience",
            key="your_profile",
            label_visibility="collapsed",
        )

    with col2:
        st.markdown("**🎯 Match Criteria**")
        criteria_text = st.text_area(
            "What you're looking for",
            height=200,
            placeholder="Business background\nB2B sales experience\nHealthcare knowledge\nSF or remote",
            key="match_criteria",
            label_visibility="collapsed",
        )

    with col3:
        st.markdown("**💬 Message Template**")
        template_text = st.text_area(
            "Outreach template",
            height=200,
            value=load_default_template(),
            key="msg_template",
            label_visibility="collapsed",
        )

    # Settings section - only essential options
    st.markdown("### Step 2: Configure Settings")
    col_settings1, col_settings2, col_settings3 = st.columns(3)

    with col_settings1:
        max_profiles = st.number_input(
            "🔍 Max profiles to process",
            min_value=1,
            max_value=100,
            value=config.get_auto_browse_limit(),
            step=1,
            key="max_profiles",
        )

    with col_settings2:
        auto_send = st.toggle(
            "⚡ Auto-send messages",
            value=config.get_auto_send_default(),
            key="auto_send",
            help="ON: Auto-send to matches | OFF: Review matches first",
        )

    with col_settings3:
        shadow_mode = st.toggle(
            "🛡️ Test Mode",
            value=config.is_shadow_mode(),
            key="shadow_mode",
            help="ON: Evaluate only (safe) | OFF: Send real messages",
        )

    # Compact status bar
    with st.container():
        st.markdown("### System Status")
        status_cols = st.columns(4)

        # Check credentials
        email, password = config.get_yc_credentials()
        has_creds = bool(email and password)

        with status_cols[0]:
            if has_creds:
                st.success("✅ Credentials Ready")
            else:
                st.warning("⚠️ Add YC_EMAIL/PASSWORD to .env")

        with status_cols[1]:
            model = config.get_decision_model()
            st.info(f"🤖 {model}")

        with status_cols[2]:
            if shadow_mode:
                st.success("🛡️ Test Mode")
            else:
                st.warning("⚡ Live Mode")

        with status_cols[3]:
            if auto_send:
                st.info("⚡ Auto-Send ON")
            else:
                st.info("👀 Review Mode")

    # Validation check
    if not your_profile.strip() or not criteria_text.strip():
        st.info("ℹ️ Please fill in your profile and match criteria to continue")
        render_events_panel()
        return

    # Control section
    st.markdown("### Step 3: Start Browsing")

    # STOP flag management
    stop_flag = FileStopFlag(Path(".runs/stop.flag"))

    col_control1, col_control2 = st.columns([3, 1])

    with col_control1:
        # Main action button
        if st.button(
            "🚀 Start Autonomous Browsing",
            type="primary",
            use_container_width=True,
            disabled=stop_flag.is_stopped(),
        ):
            run_autonomous_browsing(
                your_profile=your_profile,
                criteria_text=criteria_text,
                template_text=template_text,
                max_profiles=max_profiles,
                shadow_mode=shadow_mode,
                auto_send=auto_send,
            )

    with col_control2:
        if stop_flag.is_stopped():
            if st.button("🔄 Clear STOP", type="secondary", use_container_width=True):
                stop_flag.clear()
                st.rerun()
        else:
            if st.button("🛑 STOP", type="secondary", use_container_width=True):
                stop_flag.set()
                st.rerun()

    if stop_flag.is_stopped():
        st.error("⛔ STOP flag is active - browsing halted")

    # Events panel
    render_events_panel()


def run_autonomous_browsing(
    your_profile: str,
    criteria_text: str,
    template_text: str,
    max_profiles: int,
    shadow_mode: bool,
    auto_send: bool,
) -> None:
    """Execute the autonomous browsing flow."""
    with st.spinner("🔄 Starting autonomous browsing..."):
        try:
            # Build services
            eval_use, send_use, logger = build_services(
                criteria_text=criteria_text,
                template_text=template_text,
                prompt_ver="v1",
                rubric_ver="v1",
                enable_cua=False,
            )

            # Create dependencies
            seen_repo = SQLiteSeenRepo(db_path=Path(".runs/seen.sqlite"))
            quota = SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))
            stop_flag = FileStopFlag(Path(".runs/stop.flag"))

            # Create and run flow
            flow = AutonomousFlow(
                browser=send_use.browser,
                evaluate=eval_use,
                send=send_use,
                seen=seen_repo,
                logger=logger,
                stop=stop_flag,
                quota=quota,
            )

            # Execute with fixed parameters
            results = flow.run(
                your_profile=your_profile,
                criteria=criteria_text,
                template=template_text,
                mode="ai",  # Always AI mode
                limit=max_profiles,
                shadow_mode=shadow_mode,
                threshold=0.7,  # Fixed threshold
                alpha=0.5,  # Fixed alpha (not used in AI mode)
            )

            # Display results
            display_results(results)

        except Exception as e:
            st.error(f"❌ Failed: {str(e)}")
            with st.expander("Error Details"):
                import traceback
                st.code(traceback.format_exc())


def display_results(results: dict[str, Any]) -> None:
    """Display browsing results in a clean format."""
    st.success("✅ Browsing Complete!")

    # Calculate metrics
    error_count = sum(1 for r in results.get("results", []) if r.get("decision") == "ERROR")

    # Display metrics
    metrics = st.columns(4)
    with metrics[0]:
        st.metric("📊 Evaluated", results.get("total_evaluated", 0))
    with metrics[1]:
        st.metric("✉️ Sent", results.get("total_sent", 0))
    with metrics[2]:
        st.metric("⏭️ Skipped", results.get("total_skipped", 0))
    with metrics[3]:
        st.metric("⚠️ Errors", error_count)

    # Show errors if any
    if error_count > 0:
        with st.expander(f"⚠️ {error_count} Errors Occurred", expanded=True):
            for r in results.get("results", []):
                if r.get("decision") == "ERROR":
                    st.error(f"Profile {r.get('profile_num')}: {r.get('rationale', 'Unknown error')}")

    # Show all results in collapsible
    with st.expander("📊 Detailed Results"):
        for r in results.get("results", []):
            decision = r.get("decision", "?")
            profile = r.get("profile_num", "?")
            rationale = r.get("rationale", "")

            if decision == "YES":
                st.success(f"✅ Profile {profile}: Matched - {rationale}")
            elif decision == "NO":
                st.info(f"❌ Profile {profile}: No match - {rationale}")
            elif decision == "ERROR":
                st.error(f"⚠️ Profile {profile}: Error - {rationale}")


def render_events_panel() -> None:
    """Render recent events in a clean, collapsible panel."""
    if not os.path.exists(".runs/events.jsonl"):
        return

    with st.expander("📝 Recent Events"):
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Refresh", key="refresh_events", use_container_width=True):
                st.rerun()

        try:
            import json
            from pathlib import Path

            # Read recent events
            events_path = Path(".runs/events.jsonl")
            content = events_path.read_text().strip()

            if not content:
                st.info("No recent events")
                return

            # Parse last 10 events
            lines = content.split("\n")
            recent_events = []

            for line in lines[-10:]:
                if line.strip():
                    try:
                        event = json.loads(line)
                        recent_events.append(event)
                    except Exception:
                        pass

            # Display events (newest first)
            for event in reversed(recent_events):
                event_type = event.get("event", "unknown")
                timestamp = event.get("timestamp", "")

                # Simple color coding
                if event_type == "sent":
                    st.success(f"✅ {timestamp} - Message sent")
                elif event_type in ["error", "stopped"]:
                    st.error(f"❌ {timestamp} - {event_type}")
                elif event_type == "decision":
                    decision = event.get("data", {}).get("decision", "")
                    if decision == "YES":
                        st.info(f"👍 {timestamp} - Match found")
                    else:
                        st.caption(f"• {timestamp} - No match")
                else:
                    st.caption(f"• {timestamp} - {event_type}")

        except Exception as e:
            st.error(f"Could not read events: {e}")


def main() -> None:
    """Main entry point."""
    render_three_input_mode()


if __name__ == "__main__":
    main()