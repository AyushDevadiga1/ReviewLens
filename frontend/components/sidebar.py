"""
sidebar.py
Shared sidebar rendered at the top of EVERY page script: backend status
plus the API-key override. Multipage apps run only the selected script,
so shared chrome must be an explicit call, not app.py magic.
"""

import streamlit as st

from components.api_client import api_health


def render_sidebar():
    """Backend status dot + key box. Call first in every page script."""
    st.sidebar.title("ReviewLens")
    st.sidebar.caption("AI-powered e-commerce review analysis")

    try:
        health = api_health()
        st.sidebar.success(
            f"● API {health.get('status', 'unknown')} — "
            f"{health.get('total_products_in_db', 0)} products, "
            f"{health.get('total_reviews_in_db', 0)} reviews"
        )
    except Exception as exc:
        st.sidebar.error(f"● API unreachable: {exc}")

    st.sidebar.text_input(
        "X-API-Key (blank = use env)",
        value=st.session_state.get("api_key_override", ""),
        type="password",
        key="api_key_override",
        on_change=lambda: st.cache_data.clear(),
        help="Changing the key clears cached API responses.",
    )
