from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from ...application.use_cases import ProcessCandidate
from ...config import load_settings
from ...domain.entities import Criteria, Profile
from ...infrastructure.sqlite_repo import SQLiteSeenRepo
from ...infrastructure.storage import read_count
from ...infrastructure.template_loader import load_default_template
from ..di import build_services


def main() -> None:
    st.set_page_config(page_title="YC Matcher (Semi‑Auto: Paste Eval)", layout="wide")
    st.title("YC Co‑Founder Matcher — Paste & Evaluate (Gated)")

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
                            criteria_text=criteria_text, template_text=template_text, prompt_ver="v1", rubric_ver="v1"
                        )
                        pc = ProcessCandidate(
                            evaluate=eval_use2,
                            send=send_use2,
                            browser=send_use2.browser,
                            seen=seen,
                            logger=logger2,
                        )
                        pc(url=settings.yc_match_url, criteria=Criteria(text=criteria_text), limit=int(quota), auto_send=True)
                        st.success("Sent (check logs for details).")
                    except Exception as e:
                        st.error(f"Send failed: {e}")


if __name__ == "__main__":
    main()
