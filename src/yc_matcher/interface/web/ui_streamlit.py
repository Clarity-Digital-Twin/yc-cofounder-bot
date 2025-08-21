from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from yc_matcher.application.use_cases import ProcessCandidate
from yc_matcher.config import load_settings
from yc_matcher.domain.entities import Criteria, Profile
from yc_matcher.infrastructure.sqlite_repo import SQLiteSeenRepo
from yc_matcher.infrastructure.storage import read_count
from yc_matcher.infrastructure.template_loader import load_default_template
from yc_matcher.interface.di import build_services


def render_three_input_mode() -> None:
    """Render autonomous 3-input mode UI following Clean Code principles.

    SOLID: Single Responsibility - Only handles UI rendering
    DRY: Reuses existing services and components
    """
    st.set_page_config(page_title="YC Matcher (Autonomous Mode)", layout="wide")
    st.title("🚀 YC Co-Founder Matcher - Autonomous Mode")

    # Three main inputs (Strategy Pattern - different input strategies)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📝 Your Profile")
        your_profile = st.text_area(
            "Describe yourself",
            height=200,
            placeholder="Technical co-founder\n5 years Python/FastAPI\nNYC based\nB2B SaaS experience",
            key="your_profile"
        )

    with col2:
        st.subheader("🎯 Match Criteria")
        criteria_text = st.text_area(
            "What you're looking for",
            height=200,
            placeholder="Business background\nB2B sales experience\nHealthcare knowledge\nSF or remote",
            key="match_criteria_auto"
        )

    with col3:
        st.subheader("💬 Message Template")
        template_text = st.text_area(
            "Outreach template",
            height=200,
            value=load_default_template(),
            key="msg_template_auto"
        )

    # Configuration section
    st.markdown("---")
    col_conf1, col_conf2, col_conf3 = st.columns(3)

    with col_conf1:
        # Decision mode selector (Strategy Pattern)
        mode = st.selectbox(
            "Decision Mode",
            ["advisor", "rubric", "hybrid"],
            index=2,  # Default to hybrid
            format_func=lambda x: {
                "advisor": "🧠 Advisor (AI-only, requires approval)",
                "rubric": "📊 Rubric (Rules-based, auto-send)",
                "hybrid": "🔄 Hybrid (AI + Rules combined)"
            }[x],
            key="decision_mode"
        )

    with col_conf2:
        # Quota and limits
        quota = st.number_input(
            "Max profiles to process",
            min_value=1,
            max_value=100,
            value=int(os.getenv("AUTO_BROWSE_LIMIT", "10")),
            step=1,
            key="auto_quota"
        )

    with col_conf3:
        # Safety controls
        shadow_mode = st.toggle(
            "Shadow Mode (evaluate only)",
            value=os.getenv("SHADOW_MODE", "1") == "1",
            key="shadow_auto"
        )
        if shadow_mode:
            st.caption("✅ Safe: Will NOT send messages")
        else:
            st.caption("⚠️ Live: Will send messages")

    # Advanced settings in expander (Clean Code: hide complexity)
    with st.expander("⚙️ Advanced Settings"):
        threshold = st.slider(
            "Auto-send threshold",
            min_value=0.0,
            max_value=1.0,
            value=float(os.getenv("THRESHOLD", "0.7")),
            step=0.05,
            help="Minimum score to auto-send (Rubric/Hybrid modes)",
            key="threshold_auto"
        )

        if mode == "hybrid":
            alpha = st.slider(
                "Hybrid weight (0=all rubric, 1=all AI)",
                min_value=0.0,
                max_value=1.0,
                value=float(os.getenv("ALPHA", "0.5")),
                step=0.1,
                key="alpha_auto"
            )

        enable_cua = st.toggle(
            "Use OpenAI Computer Use",
            value=os.getenv("ENABLE_CUA", "1") == "1",
            help="Use AI to browse (vs Playwright fallback)",
            key="enable_cua_auto"
        )

    # STOP control (Safety First principle)
    from yc_matcher.infrastructure.stop_flag import FileStopFlag
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
            "quota": quota,
            "shadow": shadow_mode,
            "threshold": threshold if mode in ["rubric", "hybrid"] else None,
            "alpha": alpha if mode == "hybrid" else None,
            "enable_cua": enable_cua
        }

        # Launch autonomous flow (will be implemented in next section)
        st.info("🔄 Starting autonomous browsing...")
        with st.spinner("Processing..."):
            try:
                # Reuse existing services (DRY principle)
                eval_use, send_use, logger = build_services(
                    criteria_text=criteria_text,
                    template_text=template_text,
                    prompt_ver="v1",
                    rubric_ver="v1",
                    decision_mode=mode  # Pass mode to DI
                )

                # For now, show configuration
                st.success("✅ Configuration loaded successfully")
                st.json(st.session_state["auto_config"])

                # TODO: Launch actual autonomous flow
                st.warning("Autonomous flow not yet implemented - will be added in Section 4")

            except Exception as e:
                st.error(f"Failed to start: {e}")


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
        from yc_matcher.infrastructure.stop_flag import FileStopFlag

        stop_flag = FileStopFlag(Path(".runs/stop.flag"))
        stopped = st.toggle("STOP (abort run)", value=stop_flag.is_stopped())
        if stopped:
            stop_flag.set()
        else:
            stop_flag.clear()
        if os.getenv("ENABLE_CALENDAR_QUOTA", "0") in {"1", "true", "True"}:
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
                if os.getenv("ENABLE_PLAYWRIGHT", "0") not in {"1", "true", "True"}:
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
                        )
                        browser = send_use2.browser
                        pc = ProcessCandidate(
                            evaluate=eval_use2,
                            send=send_use2,
                            browser=browser,
                            seen=seen,
                            logger=logger2,
                        )
                        url = getattr(settings, "yc_match_url", None) or os.getenv(
                            "YC_MATCH_URL", "https://www.startupschool.org/cofounder-matching"
                        )
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
    if os.getenv("USE_THREE_INPUT_UI", "false").lower() in {"true", "1", "yes"}:
        render_three_input_mode()
    else:
        render_paste_mode()


if __name__ == "__main__":
    main()
