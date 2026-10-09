"""
Overview.py — ReviewLens entrypoint and landing page.

Explains the project first, then shows live numbers: what it does,
live backend metrics, model benchmarks, the pipeline map, and where
to go next. Other pages live in pages/ as numbered scripts.
"""

import plotly.graph_objects as go
import streamlit as st

from components.api_client import api_health
from components.sidebar import render_sidebar
from components import theme

st.set_page_config(page_title="ReviewLens · Overview", layout="wide")

render_sidebar()

# Benchmarks from ml/fake_review/model/metadata.json (held-out 20%
# of Dataset-SA.csv, 15,001 TF-IDF + rating features). Hardcoded here
# because model artifacts are not shipped in the frontend image.
BENCHMARKS = {
    "accuracy": 0.8773,
    "f1_weighted": 0.8936,
    "features": 15001,
    "dataset": "Dataset-SA.csv",
}

_STAGES = [
    ("Ingest", "offline loaders"),
    ("Clean", "20-char floor"),
    ("Fake filter", "~5% flagged"),
    ("ABSA", "7 aspects"),
    ("Aggregate", "0–10 scores"),
    ("Serve", "API + you"),
]

theme.hero(
    "ReviewLens",
    "Aspect-based sentiment intelligence for e-commerce reviews — "
    "from raw datasets to side-by-side product verdicts.",
)

st.markdown(
    "Online ratings lie flat: a 4.2★ product can hide a terrible camera "
    "behind a great battery. ReviewLens mines **per-aspect sentiment** "
    "(battery, camera, display, …) from thousands of real reviews, "
    "filters likely-fake praise first, and lets you compare products "
    "aspect by aspect instead of star by star."
)

theme.section("Live backend")
try:
    health = api_health()
except RuntimeError as exc:
    st.error(f"Backend unreachable — start the API first. ({exc})")
    st.stop()
c1, c2, c3 = st.columns(3)
c1.metric("Products in DB", health.get("total_products_in_db", 0))
c2.metric("Reviews in DB", health.get("total_reviews_in_db", 0))
c3.metric("Backend", str(health.get("status", "?")).title())
st.caption(
    f"Fake detector: {health.get('fake_detector_version', '?')} · "
    f"ABSA: {health.get('absa_model_version', '?')}"
)

theme.section("Why you can trust these numbers (XAI)")
st.markdown(
    "Every verdict on this dashboard traces to visible inputs — "
    "nothing is a black box:"
)
c1, c2 = st.columns(2)
with c1:
    st.markdown(
        "**Fake filter** — TF-IDF + LogisticRegression sentiment "
        f"({BENCHMARKS['accuracy']:.1%} accuracy), plus two published "
        "length rules. Flagged reviews can be re-checked by hand: "
        "a 5-star review under 30 characters *is* the rule firing."
    )
with c2:
    st.markdown(
        "**ABSA** — zero-shot multilingual extraction; each aspect keeps "
        "its sentiment, confidence and mention count, so any score "
        "expands back into the mentions behind it."
    )
with st.expander("Reproducibility notes (for the sceptical)"):
    st.markdown(
        "- Training split uses `random_state=42`; metrics above are "
        "held-out, not training, numbers.\n"
        "- Loaders are idempotent: re-running never duplicates rows, "
        "so counts are stable run after run.\n"
        "- API pins every ML dependency (`torch`, `transformers`, "
        "`pyabsa`) — the numbers you see are version-locked.\n"
        "- Known limit, stated plainly: long, elaborate fakes pass the "
        "length heuristic. The filter catches incentivised one-liners, "
        "not novels."
    )

theme.section("Model benchmarks")
fig = theme.style_fig(go.Figure(), height=220)
fig.add_trace(go.Bar(
    x=[BENCHMARKS["accuracy"] * 100, BENCHMARKS["f1_weighted"] * 100],
    y=["Accuracy", "Weighted F1"],
    orientation="h",
    marker_color=[theme.PRIMARY, theme.ACCENT],
    text=[f"{BENCHMARKS['accuracy']:.1%}", f"{BENCHMARKS['f1_weighted']:.1%}"],
    textposition="inside",
))
fig.update_layout(xaxis=dict(range=[0, 100], title="Percent"))
st.plotly_chart(fig, use_container_width=True)
st.caption(
    f"Sentiment classifier on held-out 20% of {BENCHMARKS['dataset']} "
    f"({BENCHMARKS['features']:,} features). ABSA is zero-shot "
    "multilingual — no fine-tuning, aspects extracted out of the box."
)

theme.section("The pipeline")
blocks = '<div class="pipe">' + "".join(
    f"<div class='step'><b>{name}</b><span>{desc}</span></div>"
    + ("<div class='arrow'>→</div>" if i < len(_STAGES) - 1 else "")
    for i, (name, desc) in enumerate(_STAGES)
) + "</div>"
st.markdown(blocks, unsafe_allow_html=True)
with st.expander("What happens at each stage?"):
    st.markdown(
        "**Ingest** — Amazon JSON + Flipkart CSV stream into Postgres; "
        "re-runs never duplicate rows.\n\n"
        "**Clean** — whitespace normalised, sub-20-char reviews dropped.\n\n"
        "**Fake filter** — extremely positive short reviews flagged "
        "(5-star one-liners especially); the rest flow on.\n\n"
        "**ABSA** — aspect terms extracted and mapped to 7 canonical "
        "aspects with sentiment + confidence.\n\n"
        "**Aggregate** — mentions become 0–10 scores, winners and "
        "margins computed, weeks bucketed for trends.\n\n"
        "**Serve** — everything above is one API call away; "
        "this dashboard is a thin client over it."
    )

theme.section("Start here")
st.markdown(
    "1. **Single Product** — paste a review or pick a product, "
    "see its aspect breakdown.\n"
    "2. **Compare Products** — pick 2–3, get the side-by-side "
    "verdict with winners.\n"
    "3. **Sentiment Trends** — watch an aspect drift week by week.\n"
    "4. **Pipeline** — the long-form version of the diagram above."
)
