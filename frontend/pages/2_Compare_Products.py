"""2 · Side-by-side product comparison with winners and margins."""

import streamlit as st
import plotly.graph_objects as go

from components.api_client import (
    api_post,
    cached_get,
    get_friendly_name,
    format_product_label,
)
from components.comparison_table import render_comparison_table
from components.radar_chart import render_radar_chart as shared_radar
from components.sidebar import render_sidebar
from components import theme

st.set_page_config(page_title="ReviewLens · Compare", layout="wide")

render_sidebar()
theme.hero("Compare Products",
           "Side-by-side aspect intelligence: compare 2–3 products to reveal the clear winner per dimension.")
theme.about(
    "POST /compare/",
    "Compares stored products across 7 canonical aspect dimensions. "
    "Select 2–3 analyzed products to generate instant radar charts, grouped score bars, "
    "and a comprehensive aspect scoreboard with statistical winning margins.",
)


def _render_grouped_bar(by_name: dict, ordered_names: list, axes: list):
    fig = theme.style_fig(go.Figure(), score_bands=True)
    for name in ordered_names:
        scores = {a["display_name"]: a["mean_score"]
                  for a in by_name.get(name, {}).get("aspects", [])}
        fig.add_trace(go.Bar(
            name=name, x=axes,
            y=[scores.get(axis, 0.0) for axis in axes],
        ))
    fig.update_layout(
        barmode="group",
        title="Comparative Aspect Quality Scores (0–10 Scale)",
        xaxis_title="Aspect Dimension",
        yaxis_title="Mean Score (0–10)",
        yaxis=dict(range=[0, 10.5]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)


def _clear_compare_cache():
    st.session_state["compare_result"] = None


def _render_result(body: dict):
    theme.section("Comparative Visualizations")
    elapsed = st.session_state.get("compare_elapsed")
    if elapsed:
        st.caption(f"Comparison computed in {elapsed:.2f} seconds")
    
    # Map raw product names to friendly names
    products = body.get("products", [])
    by_name = {get_friendly_name(p["product_name"]): p for p in products}
    ordered_names = [get_friendly_name(p["product_name"]) for p in products]
    
    axes = []
    for product in products:
        for a in product.get("aspects", []):
            if a["display_name"] not in axes:
                axes.append(a["display_name"])

    col_radar, col_bars = st.columns([1, 1])
    with col_radar:
        radar_data = [
            {"name": name,
             "scores": {a["display_name"]: a["mean_score"]
                        for a in by_name.get(name, {}).get("aspects", [])}}
            for name in ordered_names
        ]
        shared_radar(radar_data, axes)
    with col_bars:
        _render_grouped_bar(by_name, ordered_names, axes)

    theme.section("Aspect Scoreboard")
    render_comparison_table(body)

    theme.section("Category Verdict & Winning Margins")
    _counts: dict = {}
    for _w in body.get("winners", []):
        w_name = get_friendly_name(_w["winner"])
        _counts[w_name] = _counts.get(w_name, 0) + 1
    
    if _counts:
        _best = max(_counts, key=_counts.get)
        st.markdown(
            f"<div style='background:linear-gradient(135deg, rgba(16,185,129,0.15), rgba(5,150,105,0.05)); "
            f"border:1px solid #10B981; border-radius:12px; padding:1.2rem; margin-bottom:1rem;'>"
            f"<span style='font-size:0.85rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#10B981;'>OVERALL VERDICT</span><br>"
            f"<span style='font-size:1.35rem; font-weight:800; color:#E6EAF2;'><b>{_best}</b></span> "
            f"leads the comparison, winning <b>{_counts[_best]} of {len(body.get('winners', []))}</b> aspect dimensions.</div>",
            unsafe_allow_html=True,
        )

    w_cols = st.columns(min(len(body.get("winners", [])), 4) or 1)
    for idx, w in enumerate(body.get("winners", [])):
        with w_cols[idx % len(w_cols)]:
            win_name = get_friendly_name(w['winner'])
            st.metric(
                label=w['display_name'],
                value=f"{w['winning_score']:.1f}/10",
                delta=f"+{w['margin']:.1f} vs runner-up" if w['margin'] > 0 else "Sole mention",
                delta_color="normal"
            )
            st.caption(f"Winner: **{win_name}**")

    with st.expander("How are winners and margins computed?"):
        st.markdown(
            "Each review mention is scored on a **0–10 scale** based on its aspect sentiment confidence:\n"
            "- `Positive` sentiment: `7.0 + 3.0 × confidence`\n"
            "- `Neutral` sentiment: `5.0`\n"
            "- `Negative` sentiment: `3.0 - 3.0 × confidence`\n\n"
            "Mentions are aggregated per product. The highest mean score wins that aspect dimension. "
            "**Margin** is calculated as the winner's score minus the second-highest runner-up."
        )

    theme.footer()


try:
    catalog = cached_get("/products/")
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

if not catalog:
    st.info("No products found in the database.")
    st.stop()

# Sort catalog so analyzed products are listed first
sorted_catalog = sorted(
    catalog,
    key=lambda x: (x.get("aspect_count", 0) == 0, -x.get("review_count", 0))
)

labels = {}
analyzed_options = []
for p in sorted_catalog:
    lbl = format_product_label(p)
    labels[lbl] = (p["product_id"], p["product_name"], p.get("aspect_count", 0))
    if p.get("aspect_count", 0) > 0:
        analyzed_options.append(lbl)

# Pre-select top 2 analyzed products by default so the user is never stuck
default_picks = analyzed_options[:2] if len(analyzed_options) >= 2 else []

chosen = st.multiselect(
    "Select 2–3 products to compare:",
    list(labels.keys()),
    default=default_picks,
    max_selections=3,
    key="compare_pick",
    on_change=_clear_compare_cache,
    help="Select products tagged [Analyzed] for immediate comparison. Unanalyzed products must be processed on Single Product first.",
)

if len(chosen) < 2:
    st.info("Select at least two products to generate a side-by-side comparison.")
else:
    unanalyzed = [labels[c][1] for c in chosen if labels[c][2] == 0]
    if unanalyzed:
        friendly_unanalyzed = [get_friendly_name(u) for u in unanalyzed]
        st.warning(
            f"**{', '.join(friendly_unanalyzed)}** has not been analyzed yet. "
            "Please analyze it on the **Single Product** page first, or choose another product marked `[Analyzed]`."
        )

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        compare_clicked = st.button("Compare Products", type="primary", disabled=bool(unanalyzed), use_container_width=True)

    if compare_clicked or (st.session_state.get("compare_result") is None and not unanalyzed and len(chosen) >= 2):
        import time
        t0 = time.time()
        with st.spinner("Aggregating aspect scores and computing winning margins..."):
            try:
                body = api_post("/compare/", {
                    "product_ids": [labels[c][0] for c in chosen]
                })
                elapsed = time.time() - t0
                st.session_state["compare_result"] = body
                st.session_state["compare_elapsed"] = elapsed
            except RuntimeError as exc:
                st.error(str(exc))
                st.stop()

if st.session_state.get("compare_result"):
    _render_result(st.session_state["compare_result"])
