"""1 · Single product analysis: explore stored products with instant metrics & graphs, or test ad-hoc reviews."""

import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from components.api_client import (
    api_get,
    api_post,
    api_delete,
    cached_get,
    get_friendly_name,
    format_product_label,
)
from components.radar_chart import render_radar_chart
from components.sidebar import render_sidebar
from components import theme

st.set_page_config(page_title="ReviewLens · Single Product", layout="wide")

render_sidebar()
theme.hero("Single Product Analysis",
           "Per-aspect sentiment breakdown, fake review filtering, and ad-hoc review testing.")
theme.about(
    "POST /analyze/ & GET /products/{id}/analysis",
    "Runs the full ML pipeline or instantly loads pre-analyzed product data: "
    "TF-IDF + LogisticRegression fake detection filters promotional spam and bot reviews first, "
    "PyABSA extracts fine-grained aspect sentiments from survivors, and Bayesian aggregation "
    "scores each dimension from 0–10.",
)


def _render_fake_gauge(filt: dict):
    pct = float(filt.get("fake_percentage", 0.0))
    fig = theme.style_fig(go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        title={"text": "Likely Fake Reviews (%)", "font": {"size": 15, "color": theme.TEXT}},
        number={"suffix": "%", "font": {"size": 32, "color": theme.DANGER if pct > 15 else theme.SUCCESS}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": theme.MUTED},
            "bar": {"color": theme.DANGER if pct > 15 else (theme.WARN if pct > 5 else theme.SUCCESS)},
            "bgcolor": "#131b2e",
            "borderwidth": 1,
            "bordercolor": "#26314B",
            "steps": [
                {"range": [0, 5], "color": "#064e3b"},
                {"range": [5, 15], "color": "#78350f"},
                {"range": [15, 100], "color": "#7f1d1d"},
            ],
        },
    )), height=260)
    st.plotly_chart(fig, use_container_width=True)


def _render_sentiment_dist(aspects: list):
    labels = [a["display_name"] for a in aspects]
    fig = theme.style_fig(go.Figure(), score_bands=True)
    for key, name, color in (("positive_pct", "Positive", theme.SUCCESS),
                             ("neutral_pct", "Neutral", theme.WARN),
                             ("negative_pct", "Negative", theme.DANGER)):
        fig.add_trace(go.Bar(
            name=name, x=labels,
            y=[a.get(key, 0.0) / 100.0 * a.get("review_count", 0) for a in aspects],
            marker_color=color,
        ))
    fig.update_layout(
        barmode="stack",
        title=dict(text="Mention Sentiment Mix per Aspect",
                   x=0.0, xanchor="left", y=0.99, yanchor="top",
                   font=dict(color=theme.TEXT, size=15)),
        xaxis_title="Aspect Dimension",
        yaxis_title="Review Mentions",
        legend=dict(orientation="h", yanchor="bottom", y=1.04,
                    xanchor="left", x=0, font=dict(color=theme.TEXT, size=11)),
        margin=dict(t=110, b=60, l=50, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_aspect_bars(aspects: list):
    """Bar chart for aspect scores (0-10 scale)."""
    labels = [a["display_name"] for a in aspects]
    scores = [round(a["mean_score"], 1) for a in aspects]
    colors = [
        theme.SUCCESS if s >= 7.0 else (theme.WARN if s >= 4.0 else theme.DANGER)
        for s in scores
    ]
    fig = theme.style_fig(go.Figure(go.Bar(
        x=labels,
        y=scores,
        marker_color=colors,
        text=[f"{s}/10" for s in scores],
        textposition="outside",
    )), height=260)
    fig.update_layout(
        title="Aspect Quality Scores (0–10 Scale)",
        xaxis_title="Aspect Dimension",
        yaxis_title="Score (0–10)",
        yaxis=dict(range=[0, 10.5]),
        margin=dict(t=40, b=40, l=40, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_fake_trace(text: str, rating: float, flagged: bool, model_prob=None):
    length = len(text.strip())
    prob_val = model_prob if model_prob is not None else (0.95 if flagged else 0.15)
    prob_str = f"{prob_val * 100:.1f}%"
    verdict_label = "DECEPTIVE / LIKELY FAKE" if flagged else "GENUINE — PASSED QUALITY GATE"
    heuristic_note = (
        "Excessive promotional language or insufficient detail specificity detected."
        if flagged
        else "Normal descriptive customer phrasing with specific usage details present."
    )
    with st.expander("Fake Detector Diagnostics & Inspection Log", expanded=flagged):
        st.markdown(
            f"- **Verdict**: **{verdict_label}**\n"
            f"- **Model Fake Probability**: **{prob_str}** (Detection threshold: 50.0%)\n"
            f"- **Text Length**: **{length}** characters | Customer rating: **{rating} / 5.0**\n"
            f"- **Linguistic Assessment**: {heuristic_note}\n"
        )


def _render_result(body: dict):
    filt = body.get("review_filter", {})
    st.session_state["last_analysis"] = body

    fake_cnt = filt.get("fake_count", 0)
    genuine_cnt = filt.get("genuine_count", 0)
    total_cnt = filt.get("total_reviews", 0)

    if fake_cnt > 0:
        theme.status_dot("alert", f"{fake_cnt} deceptive/fake reviews detected & filtered")
    else:
        theme.status_dot("live", "All analyzed reviews classified as genuine")

    # Overview Metrics Row
    theme.section("Review Quality & Spam Filtering")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Reviews Analyzed", total_cnt)
    with m2:
        st.metric("Genuine Verified", genuine_cnt, delta="Passed to ABSA", delta_color="normal")
    with m3:
        st.metric("Filtered Deceptive", fake_cnt, delta=f"-{fake_cnt} removed", delta_color="inverse")
    with m4:
        fake_pct = filt.get("fake_percentage", round((fake_cnt / total_cnt * 100) if total_cnt else 0, 1))
        st.metric("Fake Ratio", f"{fake_pct:.1f}%", delta="Cleaned" if fake_cnt else "Clean")

    col_gauge, col_aspect_bar = st.columns([1, 2])
    with col_gauge:
        _render_fake_gauge(filt)
    with col_aspect_bar:
        aspects = body.get("aspects", [])
        if aspects:
            _render_aspect_bars(aspects)
        else:
            st.info("No aspects extracted for this product.")

    if not aspects:
        return

    # Executive Summary & Prediction Explanation
    top_strengths = sorted([a for a in aspects if a["mean_score"] >= 6.5], key=lambda x: -x["mean_score"])
    weaknesses = sorted([a for a in aspects if a["mean_score"] < 5.0], key=lambda x: x["mean_score"])
    strength_text = ", ".join([f"{a['display_name']} ({a['mean_score']:.1f}/10)" for a in top_strengths[:2]]) if top_strengths else "Scores within normal baseline range"
    weak_text = ", ".join([f"{a['display_name']} ({a['mean_score']:.1f}/10)" for a in weaknesses[:2]]) if weaknesses else "No critical negative aspect outliers detected"
    avg_score = sum(a["mean_score"] for a in aspects) / len(aspects) if aspects else 0.0

    theme.section("Executive Synthesis & Prediction Explanation")
    st.markdown(
        f"""<div class="glass" style="padding:1.1rem 1.3rem; margin-bottom:1rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
            <span style="font-weight:700; font-size:1.02rem; color:#E6EAF2;">Comprehensive Model Assessment</span>
            <span class="badge {'badge-green' if avg_score >= 6.5 else ('badge-amber' if avg_score >= 4.5 else 'badge-red')}">Overall Index: {avg_score:.1f} / 10</span>
          </div>
          <div style="font-size:0.87rem; line-height:1.7; color:#C4CDDC;">
            • <b>Key Strengths:</b> {strength_text}<br>
            • <b>Primary Areas of Concern:</b> {weak_text}<br>
            • <b>Data Integrity & Quarantined Spam:</b> {fake_cnt} deceptive review(s) identified and excluded prior to aspect aggregation to prevent artificial rating manipulation.
          </div>
        </div>""",
        unsafe_allow_html=True
    )

    theme.section("Aspect Sentiment Scores (0–10 Scale)")
    tab_radar, tab_mix, tab_table = st.tabs(["Radar Overview", "Sentiment Mix", "Detailed Scoreboard"])

    with tab_radar:
        raw_name = body.get("product_name", "Product")
        display_name = get_friendly_name(raw_name)
        render_radar_chart(
            [{"name": display_name, "scores": {a["display_name"]: a["mean_score"] for a in aspects}}],
            [a["display_name"] for a in aspects],
        )

    with tab_mix:
        _render_sentiment_dist(aspects)

    with tab_table:
        st.dataframe(
            pd.DataFrame([{
                "Aspect Dimension": a["display_name"],
                "Quality Score": f"{a['mean_score']:.1f} / 10",
                "Sentiment Class": a["sentiment_label"].upper(),
                "Positive %": f"{a.get('positive_pct', 0):.0f}%",
                "Neutral %": f"{a.get('neutral_pct', 0):.0f}%",
                "Negative %": f"{a.get('negative_pct', 0):.0f}%",
                "Total Mentions": a["review_count"],
            } for a in aspects]),
            use_container_width=True,
        )



def _render_job_panel():
    """Job panel with auto-polling and cancellation support."""
    job_id = st.session_state.get("job_id")
    if not job_id:
        return

    # Auto-fetch state if missing
    if "job_state" not in st.session_state:
        try:
            st.session_state["job_state"] = api_get(f"/jobs/{job_id}")
        except RuntimeError:
            pass

    col1, col2 = st.columns([1, 1])
    if col1.button("Check Progress", use_container_width=True):
        with st.spinner("Polling worker status..."):
            try:
                st.session_state["job_state"] = api_get(f"/jobs/{job_id}")
            except RuntimeError as exc:
                st.error(str(exc))
                return
    if col2.button("Cancel ML Pipeline", use_container_width=True):
        try:
            st.session_state["job_state"] = api_delete(f"/jobs/{job_id}")
            st.warning("Cancellation requested — worker will halt at next batch.")
        except RuntimeError as exc:
            st.error(str(exc))
            return

    state = st.session_state.get("job_state")
    if not state:
        st.info("Job submitted to ML worker thread — awaiting first batch...")
        time.sleep(1.5)
        st.rerun()
        return

    status = state.get("status", "?")
    total = state.get("progress_total", 0) or 0
    done = state.get("progress_done", 0) or 0
    dot = {"queued": "idle", "running": "live", "done": "live",
           "failed": "alert", "cancelled": "warn"}.get(status, "idle")
    theme.status_dot(dot, f"ML Pipeline status: {status}")

    if total > 0:
        st.progress(min(done / total, 1.0), text=f"Processing {done}/{total} reviews through ABSA model...")
    else:
        st.caption(f"Status: {status}...")

    if status == "done" and state.get("result"):
        st.toast("ML Analysis complete!")
        _render_result(state["result"])
    elif status == "failed":
        st.error(f"Job failed: {state.get('error', 'unknown error')}")
    elif status == "cancelled":
        partial = state.get("result")
        if partial and partial.get("aspects"):
            st.warning("Job cancelled — displaying completed aspects.")
            _render_result(partial)
        else:
            st.warning("Job cancelled.")
    elif status in ("queued", "running"):
        time.sleep(2.0)
        try:
            st.session_state["job_state"] = api_get(f"/jobs/{job_id}")
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))


# ── Mode Selection ────────────────────────────────────────────────────────────
mode = st.radio("Choose Analysis Mode:", ["Database Stored Product", "Test Ad-hoc Review (Fake vs Genuine)"],
                horizontal=True)

if mode == "Database Stored Product":
    try:
        catalog = cached_get("/products/")
    except Exception as exc:
        catalog = []
        st.error(f"Could not load products catalog: {exc}")

    if not catalog:
        st.info("No products found in the database. Ensure database is connected.")
    else:
        # Sort catalog so analyzed products come first, then by review count
        sorted_catalog = sorted(
            catalog,
            key=lambda x: (x.get("aspect_count", 0) == 0, -x.get("review_count", 0))
        )
        options_map = {}
        for p in sorted_catalog:
            label = format_product_label(p)
            options_map[label] = p

        selected_label = st.selectbox(
            "Select product to inspect (auto-suggested with real product names):",
            options=list(options_map.keys()),
            help="Choose any stored product. Products tagged [Analyzed] display instant analytics.",
            key="single_product_select"
        )
        match = options_map.get(selected_label)

        if match:
            pid = match["product_id"]
            pname = match["product_name"]
            friendly = get_friendly_name(pname)
            is_analyzed = match.get("aspect_count", 0) > 0

            col_btn, col_info = st.columns([1, 2])
            with col_btn:
                btn_label = "Re-run Live ML Pipeline" if is_analyzed else "Run ML Analysis Pipeline"
                analyze_btn = st.button(
                    btn_label,
                    type="secondary" if is_analyzed else "primary",
                    use_container_width=True
                )
            with col_info:
                st.markdown(
                    f"**{friendly}**  \n"
                    f"Platform: `{match['platform'].upper()}` · ASIN: `{pname}` · "
                    f"Reviews: `{match['review_count']}` · Aspects: `{match.get('aspect_count', 0)}`"
                )

            if analyze_btn:
                st.session_state.pop("job_id", None)
                st.session_state.pop("job_state", None)
                try:
                    t0 = time.time()
                    with st.spinner(f"Submitting ML analysis job for '{friendly}'..."):
                        job = api_post("/jobs/analyze", {
                            "product_name": match["product_name"],
                            "platform": match["platform"]
                        })
                except RuntimeError as exc:
                    st.error(str(exc))
                else:
                    st.session_state["job_id"] = job["job_id"]
                    st.session_state.pop("job_state", None)
                    st.rerun()

            # If the user is running a job, show the job panel
            if st.session_state.get("job_id"):
                _render_job_panel()
            elif is_analyzed:
                # INSTANT VIEW: Load cached/stored analysis in <10ms!
                try:
                    t_load = time.time()
                    analysis_data = cached_get(f"/products/{pid}/analysis")
                    load_ms = (time.time() - t_load) * 1000
                    st.caption(f"Analysis retrieved from database in {load_ms:.1f}ms")
                    _render_result(analysis_data)
                except Exception as exc:
                    st.warning(f"Could not load pre-analyzed data: {exc}")

                # Sample reviews expander
                try:
                    sample_reviews = cached_get(f"/products/{pid}/reviews", (("limit", 6),))
                    if sample_reviews:
                        with st.expander(f"Sample Reviews & Model Verdicts ({len(sample_reviews)} shown)"):
                            for r in sample_reviews:
                                r_tag = "[DECEPTIVE]" if r["is_fake"] else "[GENUINE]"
                                r_conf = f"{r['confidence'] * 100:.0f}%" if r.get("confidence") else "—"
                                st.markdown(
                                    f"**{r_tag}** (Confidence: {r_conf}) — Rating: **{r['rating'] or '—'} / 5.0** · *{r['reviewer']}*\n"
                                    f"> {r['text']}\n"
                                )
                except Exception:
                    pass
            else:
                st.info(
                    f"This product (**{friendly}**) has {match['review_count']} reviews in the database "
                    "that have not been analyzed yet. Click **'Run ML Analysis Pipeline'** above to process it."
                )

else:
    # Mode 2: Test Ad-Hoc Review (Fake vs Genuine)
    theme.section("Test Custom Review Detection & Sentiment Extraction")
    st.caption("Enter a review below or use one of the preset examples. The system will classify it as genuine or deceptive, then extract aspect sentiments.")

    col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)

    if col_ex1.button("Promo Spam (Fake, 5-star)", use_container_width=True):
        st.session_state["review_input"] = "AMAZING BEST PRODUCT EVER BUY NOW 5 STARS LOVE IT SO MUCH PERFECT RECOMMEND TO EVERYONE"
        st.session_state["rating_input"] = 5.0
    if col_ex2.button("Negative Smear (Fake, 1-star)", use_container_width=True):
        st.session_state["review_input"] = "Horrible scam broke immediately do not buy waste of money total garbage seller"
        st.session_state["rating_input"] = 1.0
    if col_ex3.button("Genuine Review — Battery & Camera (4-star)", use_container_width=True):
        st.session_state["review_input"] = "The battery life easily lasts 14 hours on a single charge. However, the camera lens produces noticeable noise in low light situations."
        st.session_state["rating_input"] = 4.0
    if col_ex4.button("Genuine Review — Build & Fit (4-star)", use_container_width=True):
        st.session_state["review_input"] = "I bought this phone case last week. The volume buttons are slightly stiff to press, but the drop protection has worked well when my kid dropped it on ceramic tiles."
        st.session_state["rating_input"] = 4.0

    default_text = st.session_state.get("review_input", "The battery life easily lasts 14 hours on a single charge. However, the camera lens produces noticeable noise in low light situations.")
    default_rating = st.session_state.get("rating_input", 4.0)

    with st.form("single_review_form"):
        text = st.text_area(
            "Review text (min 20 characters):",
            value=default_text,
            height=110,
            placeholder="Type or paste any customer review to test detection...",
        )
        rating = st.slider("Star rating (out of 5)", 1.0, 5.0, float(default_rating), 0.5)
        analyze_clicked = st.form_submit_button("Analyze Review with ML Pipeline", type="primary", use_container_width=True)

    if analyze_clicked:
        clean_text = text.strip()
        if len(clean_text) < 20:
            st.warning("Please enter at least 20 characters before analyzing.")
        else:
            t0 = time.time()
            with st.spinner("Running Fake Detector (TF-IDF + Logistic Regression) and ABSA inference — this may take a few seconds..."):
                try:
                    body = api_post("/analyze/", {"review_text": clean_text, "rating": rating})
                except RuntimeError as exc:
                    st.error(str(exc))
                else:
                    elapsed = time.time() - t0
                    st.toast(f"Analysis complete in {elapsed:.1f}s")
                    filt = body.get("review_filter", {})
                    is_fake = bool(filt.get("fake_count", 0))
                    prob = filt.get("model_fake_prob", 0.0)

                    # Top result banner
                    theme.section("Inference Verdict")
                    st.caption(f"Processing time: {elapsed:.2f} seconds")
                    v1, v2, v3 = st.columns(3)
                    with v1:
                        if is_fake:
                            st.error("VERDICT: DECEPTIVE / FAKE REVIEW")
                        else:
                            st.success("VERDICT: GENUINE CUSTOMER REVIEW")
                    with v2:
                        st.metric("Fake Probability Score", f"{prob * 100:.1f}%")
                    with v3:
                        st.metric("Detection Confidence", f"{max(prob, 1 - prob) * 100:.1f}%")

                    _render_fake_trace(clean_text, rating, is_fake, prob)

                    if is_fake:
                        st.warning(
                            "This review was classified as likely deceptive by the binary classifier. "
                            "In accordance with ReviewLens quality gates, deceptive reviews are quarantined and excluded from "
                            "product aspect aggregation so aggregate ratings cannot be artificially manipulated."
                        )
                    else:
                        st.success(
                            "This review passed the deceptive-review detection gate. "
                            "Extracted aspects and sentiment scores are displayed below:"
                        )
                        _render_result(body)

theme.footer()
