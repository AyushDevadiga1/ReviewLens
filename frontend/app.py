"""
app.py
ReviewLens Streamlit dashboard.
Run: streamlit run frontend/app.py

Three pages:
  1. Single Product — analyze one URL
  2. Compare Products — side-by-side comparison
  3. Sentiment Trends — aspect drift over time
"""

import streamlit as st

st.set_page_config(
    page_title="ReviewLens",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Sidebar navigation ────────────────────────────────────────────────
st.sidebar.title("ReviewLens")
st.sidebar.caption("AI-powered e-commerce review analysis")

page = st.sidebar.radio(
    "Navigate",
    ["Single Product", "Compare Products", "Sentiment Trends"]
)

# TODO: import and call the appropriate page renderer
# if page == "Single Product":
#     from pages.single import render_single_page
#     render_single_page()
# elif page == "Compare Products":
#     from pages.compare import render_compare_page
#     render_compare_page()
# elif page == "Sentiment Trends":
#     from pages.trends import render_trends_page
#     render_trends_page()