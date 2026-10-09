"""4 · The long-form pipeline walk: six stages, live numbers, knobs."""

import streamlit as st

from components.api_client import api_health
from components.sidebar import render_sidebar
from components import theme

st.set_page_config(page_title="ReviewLens · Pipeline", layout="wide")

render_sidebar()
theme.hero("The Pipeline",
           "Six stages from raw datasets to the verdicts on the other "
           "pages — with the live numbers to prove each one runs.")

try:
    health = api_health()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

c1, c2 = st.columns(2)
c1.metric("Reviews in database", health.get("total_reviews_in_db", 0))
c2.metric("Products in database", health.get("total_products_in_db", 0))

last = st.session_state.get("last_analysis")
if last:
    filt = last.get("review_filter", {})
    st.success(
        f"Last analysis ({last.get('product_name', '?')}): "
        f"{filt.get('genuine_count', 0)}/{filt.get('total_reviews', 0)} "
        f"genuine, {len(last.get('aspects', []))} aspects scored."
    )
else:
    st.info("Run an analysis on the Single Product page — "
            "its numbers will appear here.")

_STAGES = [
    ("1 · Ingest (offline loaders)",
     "Amazon JSON and Flipkart CSV rows stream into Postgres. Loads are "
     "**idempotent**: each product snapshots its stored `(reviewer, text)` "
     "pairs first, so re-runs and source duplicates never multiply rows. "
     "Products dedupe on `(name, platform)`."),
    ("2 · Clean (20-character floor)",
     "Whitespace normalised, sub-20-char reviews dropped. Everything "
     "downstream — including the fake heuristic thresholds — is calibrated "
     "**above** this floor, or the filter could never fire."),
    ("3 · Fake filter (binary model, ~88% F1)",
     "A TF-IDF + LogisticRegression classifier trained on 1,600 "
     "labelled fake/genuine reviews decides per review (fake-probability "
     "> 0.5). A legacy length heuristic survives only as fallback when "
     "v2 artifacts are absent. Fake rows store per review (deduped); "
     "genuine text flows to ABSA."),
    ("4 · ABSA (PyABSA multilingual)",
     "Surviving reviews go through aspect-term extraction: terms map to "
     "7 canonical aspects with sentiment + confidence. Empty results "
     "degrade to empty aspects, never 500s; re-analysis never duplicates "
     "rows (`review, aspect, sentiment` dedup)."),
    ("5 · Aggregate (0–10 scores)",
     "Mentions map to scores (`positive` ≈ 7 + 3·confidence, `negative` "
     "≈ 3 − 3·confidence), averaged per aspect with splits. Winners take "
     "the highest mean; margin = winner − runner-up. Trends bucket by ISO "
     "week; ±0.5 decides improving/declining/stable."),
    ("6 · Serve (this dashboard)",
     "FastAPI behind API-key auth (100 req/min per key, `/health` open). "
     "Every number on the other pages comes from these endpoints — "
     "nothing here is mocked."),
]

for title, body in _STAGES:
    theme.section(title)
    st.markdown(body)
