"""3 · Weekly sentiment drift per aspect, with mention volume."""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from streamlit_searchbox import st_searchbox

from components.api_client import (
    api_get,
    product_search_options,
    take_product_match,
    ASPECTS,
)
from components.sidebar import render_sidebar
from components import theme

st.set_page_config(page_title="ReviewLens · Trends", layout="wide")

render_sidebar()
theme.hero("Sentiment Trends",
           "Watch aspects drift week by week — volume bars keep thin "
           "weeks honest.")
theme.about(
    "GET /trends/?product_id=&aspect=&weeks=",
    "Mentions bucket by ISO week (review date when known, analysis time "
    "otherwise), scored 0–10 and averaged. Direction thresholds: "
    "±0.5 last-minus-first. Bars are mention counts — thin bars mean "
    "weak signal, whatever the line says.",
)


def render_trend_overlay(series: dict):
    """One line per aspect (left axis) + mention volume bars (right axis)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for aspect_key, body in series.items():
        points = body.get("trend", [])
        if not points:
            continue
        label = ASPECTS.get(aspect_key, {}).get("display_name", aspect_key)
        fig.add_trace(go.Scatter(
            x=[w["week"] for w in points],
            y=[w["mean_score"] for w in points],
            mode="lines+markers",
            name=f"{label} score",
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=[w["week"] for w in points],
            y=[w.get("review_count", 0) for w in points],
            name=f"{label} mentions",
            opacity=0.25,
        ), secondary_y=True)
    fig = theme.style_fig(fig)
    fig.update_layout(title="Weekly aspect sentiment + mention volume")
    fig.update_yaxes(title_text="Mean score (0–10)", range=[0, 10],
                     secondary_y=False)
    fig.update_yaxes(title_text="Mentions", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)


pick = st_searchbox(
    lambda term: product_search_options(term, "trend_product_options"),
    label="Type to search products…",
    placeholder="OnePlus, B0002, bullets…",
    key="trend_product_search",
)
match = take_product_match(pick, "trend_product_options")
if match is None:
    st.info("Search and pick a product to begin.")
    st.stop()
product_id = match["product_id"]
aspect_options = {ASPECTS[k].get("display_name", k): k for k in ASPECTS}
aspect_labels = st.multiselect(
    "Aspects (overlay up to 3)",
    list(aspect_options.keys()),
    default=["Battery Life"],
    max_selections=3,
)
aspect_keys = [aspect_options[label] for label in aspect_labels]
if not aspect_keys:
    st.info("Select at least one aspect.")
    st.stop()
weeks = st.slider("Weeks of history", 1, 52, 8)

if st.button("Show Trend"):
    with st.spinner("Computing weekly trend…"):
        series = {}
        for aspect_key in aspect_keys:
            try:
                body = api_get("/trends/", params={
                    "product_id": product_id,
                    "aspect": aspect_key,
                    "weeks": weeks,
                })
            except RuntimeError as exc:
                st.error(f"{ASPECTS[aspect_key].get('display_name', aspect_key)}: {exc}")
                continue
            series[aspect_key] = body
    if not series:
        st.stop()
    st.toast("Trend ready", icon="✅")

    theme.section("Chart")
    render_trend_overlay(series)

    theme.section("Direction")
    for aspect_key, body in series.items():
        direction = body.get("overall_direction", "stable")
        st.metric(
            f"{ASPECTS[aspect_key].get('display_name', aspect_key)} direction",
            direction,
        )
        if direction == "declining":
            st.warning("Sentiment for this aspect is declining "
                       "over the selected window.")

    with st.expander("How is the trend computed?"):
        st.markdown(
            "Mentions are bucketed by ISO week (review date when known, "
            "otherwise analysis time), scored 0–10 and averaged. "
            "**Improving** means last − first week > 0.5, **declining** "
            "the reverse, else **stable**. Thin bars = few mentions: "
            "treat those weeks as weak signal."
        )
