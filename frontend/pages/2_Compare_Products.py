"""2 · Side-by-side product comparison with winners and margins."""

import streamlit as st
import plotly.graph_objects as go

from components.api_client import api_post, cached_get
from components.comparison_table import render_comparison_table
from components.radar_chart import render_radar_chart as shared_radar
from components.sidebar import render_sidebar
from components import theme

st.set_page_config(page_title="ReviewLens · Compare", layout="wide")

render_sidebar()
theme.hero("Compare Products",
           "Two or three products, one verdict per aspect.")
theme.about(
    "POST /compare/",
    "Takes 2–3 stored **product_ids** (IDs, not URLs — discover them via "
    "the dropdown, backed by GET /products). Requires analysed products: "
    "unanalysed ones return 404 telling you to run Single Product first. "
    "Each aspect's winner is the highest mean score; margin is winner "
    "minus runner-up.",
)


def _render_grouped_bar(by_name: dict, ordered_names: list, axes: list):
    fig = theme.style_fig(go.Figure())
    for name in ordered_names:
        scores = {a["display_name"]: a["mean_score"]
                  for a in by_name.get(name, {}).get("aspects", [])}
        fig.add_trace(go.Bar(
            name=name, x=axes,
            y=[scores.get(axis, 0.0) for axis in axes],
        ))
    fig.update_layout(barmode="group", title="Aspect scores by product",
                      xaxis_title="Aspect", yaxis_title="Mean score (0–10)",
                      yaxis=dict(range=[0, 10]))
    st.plotly_chart(fig, use_container_width=True)


try:
    catalog = cached_get("/products/")
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()
if not catalog:
    st.info("No products in the database yet — run the loaders first.")
    st.stop()

labels = {
    f"{p['product_name']} ({p['platform']}, {p['review_count']} reviews)":
    (p["product_id"], p["product_name"])
    for p in catalog
}
chosen = st.multiselect("Pick 2–3 products", list(labels.keys()),
                        max_selections=3)
if len(chosen) < 2:
    st.info("Select at least two products to compare.")
    st.stop()

if st.button("Compare"):
    with st.spinner("Aggregating aspect scores…"):
        try:
            body = api_post("/compare/", {
                "product_ids": [labels[c][0] for c in chosen]})
        except RuntimeError as exc:
            st.error(str(exc))
            st.stop()
    st.toast("Comparison ready", icon="✅")

    theme.section("Charts")
    by_name = {p["product_name"]: p for p in body.get("products", [])}
    ordered_names = [labels[c][1] for c in chosen]
    axes = []
    for name in ordered_names:
        for item in by_name.get(name, {}).get("aspects", []):
            if item["display_name"] not in axes:
                axes.append(item["display_name"])
    radar_data = [
        {"name": name,
         "scores": {a["display_name"]: a["mean_score"]
                    for a in by_name.get(name, {}).get("aspects", [])}}
        for name in ordered_names
    ]
    shared_radar(radar_data, axes)
    _render_grouped_bar(by_name, ordered_names, axes)

    theme.section("Scoreboard")
    render_comparison_table(body)

    theme.section("Winners")
    for w in body.get("winners", []):
        st.markdown(
            f"**{w['display_name']}** — {w['winner']} "
            f"({w['winning_score']:.1f}, margin +{w['margin']:.1f})"
        )
    with st.expander("How are winners computed?"):
        st.markdown(
            "Each aspect mention is scored 0–10 from its sentiment "
            "(`positive` ≈ 7 + 3·confidence, `negative` ≈ 3 − 3·confidence), "
            "averaged per product. The highest mean wins; **margin** is "
            "winner − runner-up (0.0 when only one product mentions "
            "the aspect)."
        )
