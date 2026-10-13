"""3 · Weekly sentiment drift per aspect, with mention volume."""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from components.api_client import (
    api_get,
    cached_get,
    get_friendly_name,
    format_product_label,
    ASPECTS,
)
from components.sidebar import render_sidebar
from components import theme

st.set_page_config(page_title="ReviewLens · Trends", layout="wide")

render_sidebar()
theme.hero("Sentiment Trends",
           "Track weekly sentiment trajectory and drift per aspect dimension with mention volume verification.")
theme.about(
    "GET /trends/?product_id=&aspect=&weeks=",
    "Aggregates aspect mentions into ISO calendar weeks based on original review dates. "
    "Calculates 0–10 mean sentiment scores to identify improving, declining, or stable quality trends. "
    "Underlying mention volume bars help distinguish high-confidence signals from thin data weeks.",
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
            name=f"{label} score (0–10)",
            line=dict(width=3),
            marker=dict(size=8),
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=[w["week"] for w in points],
            y=[w.get("review_count", 0) for w in points],
            name=f"{label} volume",
            opacity=0.2,
        ), secondary_y=True)
    fig = theme.style_fig(fig, score_bands=True)
    fig.update_layout(
        title=dict(text="Weekly Aspect Sentiment Trajectory vs Review Volume",
                   x=0.0, xanchor="left", y=0.99, yanchor="top",
                   font=dict(color=theme.TEXT, size=15)),
        legend=dict(orientation="h", yanchor="bottom", y=1.04,
                    xanchor="left", x=0, font=dict(color=theme.TEXT, size=11)),
        margin=dict(t=115, b=55, l=55, r=25),
    )
    fig.update_yaxes(title_text="Mean Score (0–10)", range=[0, 10.5], secondary_y=False)
    fig.update_yaxes(title_text="Weekly Mentions", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)


try:
    catalog = cached_get("/products/")
except Exception:
    catalog = []

if not catalog:
    st.info("No products found in the database. Ensure database is connected.")
    st.stop()

# Sort so analyzed products are listed first, then by review count
sorted_catalog = sorted(
    catalog,
    key=lambda x: (x.get("aspect_count", 0) == 0, -x.get("review_count", 0))
)
options_map = {}
for p in sorted_catalog:
    label = format_product_label(p)
    options_map[label] = p

selected_label = st.selectbox(
    "Select product to analyze trends:",
    options=list(options_map.keys()),
    help="Select any stored product. Products tagged [Analyzed] have active sentiment timelines.",
    key="trend_product_select"
)
match = options_map.get(selected_label)
if match is None:
    st.info("Please select a product to begin.")
    st.stop()

product_id = match["product_id"]
friendly_title = get_friendly_name(match["product_name"])
is_analyzed = match.get("aspect_count", 0) > 0

if not is_analyzed:
    st.warning(
        f"**{friendly_title}** has not been analyzed yet. "
        "Please run **Single Product** analysis first to extract aspect sentiments before viewing trends."
    )

aspect_options = {ASPECTS[k].get("display_name", k): k for k in ASPECTS}
available_aspect_labels = list(aspect_options.keys())
valid_defaults = [lbl for lbl in ["Build Quality", "Battery Life"] if lbl in available_aspect_labels]
if not valid_defaults and available_aspect_labels:
    valid_defaults = [available_aspect_labels[0]]

aspect_labels = st.multiselect(
    "Aspect dimensions to track (overlay up to 3):",
    options=available_aspect_labels,
    default=valid_defaults,
    max_selections=3,
)
aspect_keys = [aspect_options[label] for label in aspect_labels]

col_slider, col_btn = st.columns([3, 1])
with col_slider:
    weeks = st.slider("Lookback window (weeks of history):", 4, 104, 52)
with col_btn:
    st.write("")
    st.write("")
    show_clicked = st.button("Compute Trend", type="primary", use_container_width=True, disabled=not is_analyzed)

if show_clicked or is_analyzed:
    if not aspect_keys:
        st.info("Select at least one aspect dimension above.")
        st.stop()

    import time
    t0 = time.time()
    with st.spinner("Computing weekly aspect sentiment trajectory..."):
        series = {}
        for aspect_key in aspect_keys:
            try:
                body = api_get("/trends/", params={
                    "product_id": product_id,
                    "aspect": aspect_key,
                    "weeks": weeks,
                })
                series[aspect_key] = body
            except RuntimeError:
                continue
    elapsed = time.time() - t0

    if not series:
        st.info(f"No weekly mention data found for selected aspects in {friendly_title}. Try selecting different aspects.")
        st.stop()

    theme.section(f"Sentiment Timeline — {friendly_title}")
    st.caption(f"Retrieved in {elapsed:.2f}s | {weeks}-week lookback window")
    render_trend_overlay(series)

    theme.section("Aspect Direction & Momentum")
    dir_cols = st.columns(len(series))
    for idx, (aspect_key, body) in enumerate(series.items()):
        with dir_cols[idx]:
            direction = body.get("overall_direction", "stable").upper()
            disp_name = ASPECTS.get(aspect_key, {}).get("display_name", aspect_key)
            pts = body.get("trend", [])
            latest_score = pts[-1]["mean_score"] if pts else 0.0

            # Formal direction indicator: arrow symbols + text
            direction_symbol = {"IMPROVING": "+", "DECLINING": "-", "STABLE": "="}.get(direction, "?")
            delta_label = f"{direction_symbol} {direction.capitalize()}"
            st.metric(
                label=disp_name,
                value=f"{latest_score:.1f}/10",
                delta=delta_label,
                delta_color="normal" if direction == "IMPROVING" else ("inverse" if direction == "DECLINING" else "off")
            )
            st.caption(f"{len(pts)} active weekly data points")

theme.footer()
