import os
import plotly.graph_objects as go
import streamlit as st

from components.api_client import api_health
from components.sidebar import render_sidebar
from components import theme

st.set_page_config(
    page_title="ReviewLens · Overview",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()
theme.inject_css()

# Benchmarks from ml/fake_review/model/v2/metadata.json
BENCHMARKS = {
    "accuracy":       0.8781,
    "f1_fake":        0.8807,
    "precision_fake": 0.8623,
    "recall_fake":    0.9000,
    "dataset": "Ott Deceptive Spam v1.4 (1,600 reviews)",
}

_STAGES = [
    ("Ingest",       "offline loaders"),
    ("Clean",        "20-char floor"),
    ("Fake filter",  "binary model"),
    ("ABSA",         "7 aspects"),
    ("Aggregate",    "0–10 scores"),
    ("Serve",        "API + you"),
]

# Professional SVGs for feature cards
SVG_FILTER = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
SVG_TARGET = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>'
SVG_COMPARE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="18" rx="1"/><rect x="14" y="3" width="7" height="18" rx="1"/></svg>'
SVG_TREND = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>'
SVG_CPU = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>'
SVG_API = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'

# ── HERO ────────────────────────────────────────────────────────────────────
hero_col1, hero_col2 = st.columns([1.1, 0.9], gap="large")

with hero_col1:
    theme.hero(
        "ReviewLens",
        "Aspect-based sentiment intelligence for e-commerce reviews — from raw datasets to side-by-side product verdicts.",
    )
    st.markdown(
        """
        <div style="font-size:1.02rem; line-height:1.7; color:#C4CDDC; margin-bottom:1.4rem;">
        Star ratings lie flat: a <b>4.2★</b> product often conceals critical hardware flaws behind high review volume.
        <b>ReviewLens</b> extracts sentiment across 7 granular aspects, eliminates deceptive promotional reviews first,
        and provides transparent, reproducible product comparison.
        </div>
        """,
        unsafe_allow_html=True,
    )
    act1, act2 = st.columns(2)
    with act1:
        st.page_link("pages/1_Single_Product.py", label="Single Product Analysis", use_container_width=True)
    with act2:
        st.page_link("pages/2_Compare_Products.py", label="Compare Products", use_container_width=True)

with hero_col2:
    arch_img = os.path.join(os.path.dirname(__file__), "assets", "reviewlens_architecture.jpg")
    if os.path.exists(arch_img):
        st.image(arch_img, use_column_width=True, caption="ReviewLens End-to-End System Architecture")

st.divider()

# ── LIVE BACKEND STATS ───────────────────────────────────────────────────────
theme.section("Live backend")

try:
    health = api_health()
except RuntimeError as exc:
    theme.status_dot("alert", "Backend unreachable")
    st.error(f"Start the API first. ({exc})")
    st.stop()

ok = health.get("status") == "healthy"
theme.status_dot(
    "live" if ok else "warn",
    f"Backend **{health.get('status', '?')}** · "
    f"fake detector `{health.get('fake_detector_version', '?')}` · "
    f"ABSA `{health.get('absa_model_version', '?')}`",
)

# Stat cards (HTML)
n_products = health.get("total_products_in_db", 0)
n_reviews  = health.get("total_reviews_in_db", 0)
acc_pct    = f"{BENCHMARKS['accuracy']:.1%}"
f1_pct     = f"{BENCHMARKS['f1_fake']:.1%}"

st.markdown(
    f"""
    <div class="stat-grid">
      <div class="stat-card">
        <span class="stat-value">{n_products}</span>
        <span class="stat-label">Products in Database</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{n_reviews:,}</span>
        <span class="stat-label">Stored Reviews</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{acc_pct}</span>
        <span class="stat-label">Classifier Accuracy</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{f1_pct}</span>
        <span class="stat-label">Fake F1 Score</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── FEATURE CARDS ────────────────────────────────────────────────────────────
theme.section("Core capabilities")

features = [
    (SVG_FILTER, "FILTER", "Deceptive Review Detection",
     "Binary TF-IDF + LogisticRegression model (88% F1) identifies and excludes likely-fake promotional reviews prior to sentiment scoring."),
    (SVG_TARGET, "ABSA", "Aspect-Based Sentiment",
     "PyABSA multilingual neural model extracts per-mention polarities across 7 canonical dimensions: battery, camera, display, build, value, delivery, performance."),
    (SVG_COMPARE, "BENCHMARK", "Side-by-Side Comparison",
     "Compare 2–3 products concurrently with normalized radar charts, grouped aspect bars, winner determinations, and margin calculations."),
    (SVG_TREND, "TIMELINE", "Sentiment Trends",
     "Track weekly sentiment drift per aspect. Mention volume bars provide statistical confidence context across sparse review periods."),
    (SVG_CPU, "ASYNC", "Background Processing",
     "Asynchronous worker handles large product workloads (50–200 reviews) with progress tracking and cancellation support."),
    (SVG_API, "SECURE", "Production REST API",
     "FastAPI backend with API-key authentication, per-key rate limiting (100 req/min), Prometheus metrics, and automated job tracking."),
]

cols = st.columns(3)
for i, (icon_svg, tag, title, desc) in enumerate(features):
    with cols[i % 3]:
        st.markdown(
            f"""<div class="feature-card">
              <div class="feature-header">
                <div class="feature-icon-svg">{icon_svg}</div>
                <span class="feature-tag">{tag}</span>
              </div>
              <span class="feature-title">{title}</span>
              <span class="feature-desc">{desc}</span>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("")

st.divider()

# ── XAI / TRUST ──────────────────────────────────────────────────────────────
theme.section("Methodology & explainability")

st.markdown(
    "Every evaluation metric traces directly to inspectable inputs — no black-box assumptions:"
)
c1, c2 = st.columns(2)
with c1:
    st.markdown(
        "**Fake Review Filter** — binary TF-IDF + LogisticRegression classifier "
        f"({BENCHMARKS['accuracy']:.1%} accuracy, {BENCHMARKS['recall_fake']:.0%} fake recall) "
        "calibrated at probability threshold 0.50. Ambiguous one-line reviews are surfaced with explicit confidence scores."
    )
with c2:
    st.markdown(
        "**Aspect-Based Sentiment (ABSA)** — zero-shot multilingual model; each aspect mention preserves its extracted polarity, confidence, and frequency count, enabling granular traceability."
    )

with st.expander("Reproducibility & validation specifications"):
    st.markdown(
        "- **Evaluation Split:** Stratified 80/20 train/test partition using fixed `random_state=42`.\n"
        "- **Idempotent Loaders:** Database loaders verify reviewer-text pairs prior to insertion to prevent duplicate records.\n"
        "- **Dependency Pinning:** Neural dependencies (`torch`, `transformers`, `pyabsa`) are version-locked for consistent inference.\n"
        "- **Domain Boundary:** Classifier trained on Ott Opinion Spam dataset; cross-domain transfer to consumer electronics operates at ~80–85% baseline accuracy."
    )

st.divider()

# ── MODEL BENCHMARKS ─────────────────────────────────────────────────────────
theme.section("Model benchmarks & evaluation")

# Top KPI row for benchmarks
b1, b2, b3, b4 = st.columns(4)
b1.metric("Classifier Accuracy", f"{BENCHMARKS['accuracy']:.1%}", help="Overall classification accuracy on held-out test split")
b2.metric("Fake F1 Score", f"{BENCHMARKS['f1_fake']:.1%}", help="Harmonic mean of precision and recall for deceptive reviews")
b3.metric("Detection Precision", f"{BENCHMARKS['precision_fake']:.1%}", help="Proportion of flagged reviews that were truly deceptive")
b4.metric("Deceptive Recall", f"{BENCHMARKS['recall_fake']:.1%}", help="Proportion of deceptive reviews successfully flagged")

col_bench, col_detail = st.columns([1.3, 1.0], gap="large")
with col_bench:
    metrics = [
        ("Classifier Accuracy", BENCHMARKS["accuracy"] * 100),
        ("Fake F1 Score",       BENCHMARKS["f1_fake"] * 100),
        ("Detection Precision", BENCHMARKS["precision_fake"] * 100),
        ("Deceptive Recall",    BENCHMARKS["recall_fake"] * 100),
    ]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[m[1] for m in metrics],
        y=[m[0] for m in metrics],
        orientation="h",
        marker=dict(
            color="#10B981",
            line=dict(color="#2DD4BF", width=1),
        ),
        text=[f"{m[1]:.1f}%" for m in metrics],
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(color="#FFFFFF", size=12, family="Inter"),
    ))
    fig.update_layout(
        template="plotly_dark",
        height=240,
        margin=dict(t=20, b=25, l=140, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme.TEXT, family="Inter, sans-serif"),
        xaxis=dict(range=[0, 105], title="Score (%)", gridcolor="#1E2A40", showgrid=True),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", showgrid=False),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_detail:
    st.markdown(
        f"""
        <div class="glass" style="height:240px; display:flex; flex-direction:column; justify-content:center;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
            <span style="color:{theme.MUTED};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;font-weight:600">Classification Checkpoint</span>
            <span class="badge badge-green">Production v2</span>
          </div>
          <div style="font-size:0.84rem; line-height:1.75; color:{theme.TEXT}">
            <b>Benchmark Dataset:</b> {BENCHMARKS['dataset']}<br>
            <b>Model Architecture:</b> TF-IDF N-grams (1,2) + Logistic Regression<br>
            <b>Decision Boundary:</b> Fake probability threshold &ge; 0.50<br>
            <b>Validation Split:</b> 20% Stratified Test Partition (`random_state=42`)<br>
            <b>Aspect Extractor:</b> Zero-Shot FAST-LCF-ATEPC Multilingual Neural Engine
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── PIPELINE DIAGRAM ─────────────────────────────────────────────────────────
theme.section("Pipeline execution stages")

blocks = '<div class="pipe">' + "".join(
    f"<div class='step'><b>{name}</b><span>{desc}</span></div>"
    + ("<div class='arrow'>→</div>" if i < len(_STAGES) - 1 else "")
    for i, (name, desc) in enumerate(_STAGES)
) + "</div>"
st.markdown(blocks, unsafe_allow_html=True)

st.divider()

# ── SYSTEM ARCHITECTURE MAP ──────────────────────────────────────────────────
theme.section("System architecture topology")

st.markdown(
    "<div class='pipe'>"
    "<div class='step'><b>Client Browser</b><span>Streamlit Client</span></div>"
    "<div class='arrow'>→</div>"
    "<div class='step'><b>Frontend UI</b><span>Streamlit :8501</span></div>"
    "<div class='arrow'>→</div>"
    "<div class='step'><b>Application API</b><span>FastAPI :8000</span></div>"
    "<div class='arrow'>→</div>"
    "<div class='step'><b>Relational Store</b><span>Postgres / SQLite</span></div>"
    "</div>",
    unsafe_allow_html=True,
)
st.caption(
    "Telemetry & Monitoring: Prometheus :9090 scrapes /metrics · Grafana :3000 · MLflow :5000 (experiment tracking)."
)

st.divider()

# ── START HERE CTA ───────────────────────────────────────────────────────────
theme.section("Navigation modules")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""<div class="glass" style="min-height:96px; display:flex; flex-direction:column; justify-content:center;">
          <div style="font-weight:700;margin-bottom:0.3rem">Single Product</div>
          <div style="font-size:0.82rem;color:{theme.MUTED};">Inspect aspect breakdown or score an individual review.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Single_Product.py", label="Open Single Analysis", use_container_width=True)

with c2:
    st.markdown(
        f"""<div class="glass" style="min-height:96px; display:flex; flex-direction:column; justify-content:center;">
          <div style="font-weight:700;margin-bottom:0.3rem">Compare Products</div>
          <div style="font-size:0.82rem;color:{theme.MUTED};">Side-by-side radar charts, aspect winners, and margins.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/2_Compare_Products.py", label="Open Comparison", use_container_width=True)

with c3:
    st.markdown(
        f"""<div class="glass" style="min-height:96px; display:flex; flex-direction:column; justify-content:center;">
          <div style="font-weight:700;margin-bottom:0.3rem">Sentiment Trends</div>
          <div style="font-size:0.82rem;color:{theme.MUTED};">Weekly score timeline with statistical volume bars.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/3_Sentiment_Trends.py", label="Open Trends", use_container_width=True)

with c4:
    st.markdown(
        f"""<div class="glass" style="min-height:96px; display:flex; flex-direction:column; justify-content:center;">
          <div style="font-weight:700;margin-bottom:0.3rem">Architecture Pipeline</div>
          <div style="font-size:0.82rem;color:{theme.MUTED};">Inspect pipeline stages, live metrics, and health.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/4_Pipeline.py", label="View Pipeline", use_container_width=True)

theme.footer()
