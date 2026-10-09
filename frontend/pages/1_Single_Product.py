"""1 · Single product analysis: a DB product or one ad-hoc review."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from streamlit_searchbox import st_searchbox

from components.api_client import (
    api_get,
    api_post,
    api_delete,
    product_search_options,
    take_product_match,
)
from components.radar_chart import render_radar_chart
from components.sidebar import render_sidebar
from components import theme

st.set_page_config(page_title="ReviewLens · Single Product", layout="wide")

render_sidebar()
theme.hero("Single Product Analysis",
           "One product's aspect breakdown — or one review, on the spot.")
theme.about(
    "POST /analyze/",
    "Runs the full pipeline on a stored product (**product_name** + "
    "**platform**) or a single review (**review_text** + **rating**): "
    "fake filter first, ABSA on survivors, aggregation into 0–10 scores. "
    "Returns the filter counts plus per-aspect scores — everything below "
    "is a direct rendering of that response.",
)


def _render_fake_gauge(filt: dict):
    pct = float(filt.get("fake_percentage", 0.0))
    fig = theme.style_fig(go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        title={"text": "Fake reviews (%)"},
        number={"suffix": "%"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": theme.DANGER if pct > 10 else theme.SUCCESS},
            "steps": [
                {"range": [0, 5], "color": "#eafaf1"},
                {"range": [5, 15], "color": "#fef9e7"},
                {"range": [15, 100], "color": "#fdedec"},
            ],
        },
    )), height=260)
    st.plotly_chart(fig, use_container_width=True)


def _render_sentiment_dist(aspects: list):
    labels = [a["display_name"] for a in aspects]
    fig = theme.style_fig(go.Figure())
    for key, name, color in (("positive_pct", "Positive", theme.SUCCESS),
                             ("neutral_pct", "Neutral", theme.WARN),
                             ("negative_pct", "Negative", theme.DANGER)):
        fig.add_trace(go.Bar(
            name=name, x=labels,
            y=[a.get(key, 0.0) / 100.0 * a.get("review_count", 0)
               for a in aspects],
            marker_color=color,
        ))
    fig.update_layout(barmode="stack", title="Mention sentiment mix",
                      xaxis_title="Aspect", yaxis_title="Mentions")
    st.plotly_chart(fig, use_container_width=True)


def _render_fake_trace(text: str, rating: float, flagged: bool):
    """Show the checkable facts behind a fake/genuine verdict.

    The backend decides with the v2 binary classifier when deployed
    (model fake-probability, threshold 0.5); the length rules below are
    the legacy v1 heuristic, shown here as a hand cross-check.
    """
    length = len(text.strip())
    with st.expander("Why this verdict?"):
        st.markdown(
            f"- Text length: **{length}** chars, rating **{rating}★**\n"
            f"- Legacy cross-check — 5★ one-liner (< 30 chars): "
            f"**{'FIRED' if rating >= 5.0 and length < 30 else '—'}**\n"
            f"- Legacy cross-check — short-gushing (< 50 chars): "
            f"**{'FIRED' if length < 50 else '—'}**\n"
            f"- Verdict: **{'FAKE' if flagged else 'GENUINE'}**\n"
            "- Short + gushing usually means incentivised; long and "
            "specific usually means genuine — re-check by hand."
        )


def _render_result(body: dict):
    filt = body.get("review_filter", {})
    st.session_state["last_analysis"] = body  # Pipeline page reads this

    theme.section("Review filter")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        _render_fake_gauge(filt)
    with col_b:
        st.metric(
            "Genuine reviews",
            f"{filt.get('genuine_count', 0)} / {filt.get('total_reviews', 0)}",
            delta=f"-{filt.get('fake_count', 0)} fake",
            delta_color="inverse",
        )
        st.caption("Flagged reviews are filtered before "
                   "ABSA — see the Pipeline page for how.")

    aspects = body.get("aspects", [])
    if not aspects:
        st.info("No aspects extracted — the ABSA model may be unavailable, "
                "or the review carries no recognisable aspect.")
        return

    theme.section("Aspect scores")
    render_radar_chart(
        [{"name": body.get("product_name", "review"),
          "scores": {a["display_name"]: a["mean_score"] for a in aspects}}],
        [a["display_name"] for a in aspects],
    )
    _render_sentiment_dist(aspects)
    st.dataframe(
        pd.DataFrame([{
            "Aspect": a["display_name"],
            "Score": round(a["mean_score"], 1),
            "Label": a["sentiment_label"],
            "Mentions": a["review_count"],
        } for a in aspects]),
        use_container_width=True,
    )


def _render_job_panel():
    """Manual polling loop for the submitted background job.

    Deliberately click-to-refresh instead of auto-polling: Streamlit has
    no non-blocking sleep here, and a blocking loop would make Cancel
    unclickable — the exact trap this panel exists to avoid.
    """
    job_id = st.session_state.get("job_id")
    if not job_id:
        return

    col1, col2 = st.columns(2)
    if col1.button("Check status"):
        try:
            st.session_state["job_state"] = api_get(f"/jobs/{job_id}")
        except RuntimeError as exc:
            st.error(str(exc))
            return
    if col2.button("Cancel job"):
        try:
            st.session_state["job_state"] = api_delete(f"/jobs/{job_id}")
            st.warning("Cancellation requested — the worker stops at the "
                       "next batch boundary.")
        except RuntimeError as exc:
            st.error(str(exc))
            return

    state = st.session_state.get("job_state")
    if not state:
        st.info("Job submitted — press Check status for progress.")
        return

    status = state.get("status", "?")
    total = state.get("progress_total", 0) or 0
    done = state.get("progress_done", 0) or 0
    if total > 0:
        st.progress(min(done / total, 1.0), text=f"{status} — {done}/{total} reviews")
    else:
        st.caption(f"Status: {status}…")

    if status == "done" and state.get("result"):
        st.toast("Analysis complete", icon="✅")
        _render_result(state["result"])
    elif status == "failed":
        st.error(f"Job failed: {state.get('error', 'unknown error')}")
    elif status == "cancelled":
        st.warning("Job cancelled — partial rows already stored stay stored "
                   "(dedup keeps a re-run clean).")


mode = st.radio("Input", ["Database product", "Single review text"],
                horizontal=True)

if mode == "Database product":
    pick = st_searchbox(
        lambda term: product_search_options(term, "single_product_options"),
        label="Type to search products…",
        placeholder="OnePlus, B0002, bullets…",
        key="single_product_search",
    )
    match = take_product_match(pick, "single_product_options")
    if st.button("Analyze", disabled=match is None):
        # Product runs take minutes: submit as a background job and poll.
        # Refresh-safe — the job survives; only this view re-attaches.
        try:
            job = api_post("/jobs/analyze", {
                "product_name": match["product_name"],
                "platform": match["platform"]})
        except RuntimeError as exc:
            st.error(str(exc))
        else:
            st.session_state["job_id"] = job["job_id"]
            st.session_state.pop("job_state", None)

    _render_job_panel()
else:
    text = st.text_area("Review text (min 20 characters)",
                        placeholder="Battery lasts two days, camera is fine…")
    rating = st.slider("Star rating", 1.0, 5.0, 4.0, 0.5)
    if st.button("Analyze", disabled=len(text.strip()) < 20):
        with st.spinner("Running fake detection + ABSA…"):
            try:
                body = api_post("/analyze/", {
                    "review_text": text.strip(), "rating": rating})
            except RuntimeError as exc:
                st.error(str(exc))
            else:
                st.toast("Analysis complete", icon="✅")
                if body.get("review_filter", {}).get("fake_count"):
                    st.warning("Flagged as a likely fake review — "
                               "no aspect analysis performed.")
                    _render_fake_trace(text.strip(), rating, True)
                else:
                    _render_fake_trace(text.strip(), rating, False)
                    _render_result(body)
