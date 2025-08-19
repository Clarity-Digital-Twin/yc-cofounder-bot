from __future__ import annotations

import streamlit as st

from .decision import decide_and_draft
from .templates import load_default_template


def main() -> None:
    st.set_page_config(page_title="YC Matcher (HIL Paste Mode)", layout="wide")
    st.title("YC Co‑Founder Matcher — Paste & Evaluate")

    with st.sidebar:
        st.header("Session Settings")
        default_template = load_default_template()
        criteria = st.text_area("Ideal match criteria", height=160, placeholder="e.g., Python, FastAPI, React, healthcare", key="criteria")
        template = st.text_area("Message template", value=default_template, height=300, key="template")
        quota = st.number_input("Quota (messages this session)", min_value=1, max_value=50, value=5, step=1, key="quota")

    st.subheader("Paste Candidate Profile")
    profile_text = st.text_area("Profile text", height=400, key="profile")

    col1, col2 = st.columns([1, 1])
    with col1:
        go = st.button("Evaluate", type="primary")
    with col2:
        st.caption("This mode does not auto-send. Semi‑auto sending comes next.")

    if go:
        if not profile_text.strip():
            st.warning("Paste a profile first.")
            return
        result = decide_and_draft(criteria=criteria, profile_text=profile_text, template=template)
        st.markdown(f"**Decision:** {result.decision}")
        st.markdown(f"**Rationale:** {result.rationale}")
        if result.message:
            st.markdown("**Draft message:**")
            st.code(result.message)


if __name__ == "__main__":
    main()
