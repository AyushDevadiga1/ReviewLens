"""
sidebar.py
Shared sidebar rendered at the top of EVERY page script: branded header,
live backend status with a pulsing indicator, and the API-key override.
Multipage apps run only the selected script, so shared chrome must be
an explicit call, not app.py magic.
"""

import streamlit as st

from components.api_client import api_health
from components import theme


def render_sidebar():
    """Brand header, live status, key box. Call first in every page."""
    st.sidebar.markdown(
        '<div style="font-size:1.35rem;font-weight:800;letter-spacing:0.02em;">'
        f'<span style="color:{theme.PRIMARY}">◉</span> ReviewLens</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Aspect intelligence for e-commerce reviews")
    st.sidebar.divider()

    try:
        health = api_health()
        ok = health.get("status") == "healthy"
        theme.status_dot(
            "live" if ok else "warn",
            f"API {health.get('status', '?')} · "
            f"{health.get('total_products_in_db', 0)} products · "
            f"{health.get('total_reviews_in_db', 0)} reviews",
            container=st.sidebar,
        )
    except Exception as exc:
        theme.status_dot("alert", "API unreachable", container=st.sidebar)
        st.sidebar.caption(str(exc)[:120])

    # API key override - persist via query params so it survives refresh
    existing = st.query_params.get("api_key", "")
    key = st.sidebar.text_input(
        "X-API-Key (blank = use env)",
        value=existing,
        type="password",
        key="api_key_override",
        on_change=lambda: st.cache_data.clear(),
        help="Changing the key clears cached API responses.",
    )
    if key != existing:
        st.query_params["api_key"] = key
        st.cache_data.clear()

    # Show which key is active
    if key:
        st.sidebar.caption("Using override key")
    else:
        st.sidebar.caption("Using env key")