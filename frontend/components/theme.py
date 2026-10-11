"""
theme.py
Single source of truth for the dashboard's look: Inter type scale, one
restrained palette, one CSS block, one section header, one Plotly template.
Every page imports from here so the styling cannot drift between pages.

Palette: near-black slate, ONE emerald accent. Red/amber appear only as
semantic data colors (bad/weak scores), never as decoration.
"""

import plotly.graph_objects as go
import streamlit as st

BG = "#0B0F19"
SURFACE = "#151D2E"
PRIMARY = "#10B981"
ACCENT = "#10B981"
TEXT = "#E6EAF2"
MUTED = "#8B94A7"
SUCCESS = "#10B981"
WARN = "#F59E0B"
DANGER = "#E5484B"

# Categorical series stay muted and consistent across every chart.
SERIES = ["#2DD4BF", "#818CF8", "#F59E0B", "#F472B6", "#94A3B8"]

PLOTLY_TEMPLATE = "plotly_dark"
FONT = "Inter, -apple-system, 'Segoe UI', sans-serif"

_CSS = f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
html, body, [class*="st-"] {{ font-family: {FONT}; }}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
.hero-eyebrow {{
  font-size: 0.75rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; color: {PRIMARY}; margin-bottom: 0.1rem;
}}
.hero-title {{
  font-size: 2.4rem; font-weight: 800; line-height: 1.1;
  color: {TEXT}; margin-bottom: 0.2rem;
}}
.hero-sub {{ font-size: 1.0rem; color: {MUTED}; margin-bottom: 1rem; max-width: 46rem; }}
.section-title {{
  font-size: 1.15rem; font-weight: 700; color: {TEXT};
  border-left: 4px solid {PRIMARY}; padding-left: 0.6rem; margin: 1.6rem 0 0.8rem;
}}
.page-foot {{
  margin-top: 2.2rem; padding-top: 0.8rem; border-top: 1px solid #26314B;
  font-size: 0.78rem; color: {MUTED};
}}
.pipe {{ display: flex; align-items: stretch; gap: 0; margin: 1rem 0; }}
.step {{
  flex: 1; background: {SURFACE}; border: 1px solid #26314B;
  border-radius: 12px; padding: 0.7rem 0.5rem; text-align: center;
}}
.step b {{ display: block; font-size: 0.95rem; }}
.step span {{ font-size: 0.75rem; color: {MUTED}; }}
.arrow {{ align-self: center; color: {PRIMARY}; font-size: 1.4rem; padding: 0 0.3rem; }}
a {{ color: {PRIMARY}; }}

/* Live status indicators: pulse = healthy/running, blink = alert.
   Disabled entirely for users who prefer reduced motion. */
@keyframes rl-pulse {{
  0% {{ box-shadow: 0 0 0 0 {PRIMARY}66; }}
  70% {{ box-shadow: 0 0 0 9px {PRIMARY}00; }}
  100% {{ box-shadow: 0 0 0 0 {PRIMARY}00; }}
}}
@keyframes rl-blink {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.25; }}
}}
.dot {{
  display: inline-block; width: 10px; height: 10px; border-radius: 50%;
  margin-right: 0.45rem; vertical-align: baseline;
}}
.dot-live {{ background: {SUCCESS}; animation: rl-pulse 2s infinite; }}
.dot-alert {{ background: {DANGER}; animation: rl-blink 1s infinite; }}
.dot-warn {{ background: {WARN}; animation: rl-blink 1.6s infinite; }}
.dot-idle {{ background: {MUTED}; }}
@media (prefers-reduced-motion: reduce) {{
  .dot-live, .dot-alert, .dot-warn {{ animation: none; }}
  .arrow {{ animation: none; }}
}}
.glass {{
  background: linear-gradient(135deg, {SURFACE}E6, {SURFACE}99);
  border: 1px solid #26314B; border-radius: 14px;
  padding: 0.9rem 1.1rem; margin-bottom: 0.8rem;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
}}
.arrow {{ animation: rl-pulse 2.4s infinite; border-radius: 50%; }}
</style>
"""


def inject_css():
    """Inject the shared stylesheet once per page run."""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, eyebrow: str = "REVIEWLENS"):
    """Eyebrow + solid title + muted subtitle, identical on every page."""
    inject_css()
    st.markdown(f'<div class="hero-eyebrow">{eyebrow}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="hero-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-sub">{subtitle}</div>', unsafe_allow_html=True)


def section(title: str):
    """Accent-bar section header — the visual rhythm of every page."""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def footer(left: str = "ReviewLens · aspect intelligence for e-commerce reviews",
           right: str = "FastAPI + Streamlit · data: Amazon & Flipkart datasets"):
    """Closing provenance line. Same position and style on every page."""
    st.markdown(f'<div class="page-foot">{left} &nbsp;·&nbsp; {right}</div>',
                unsafe_allow_html=True)


def style_fig(fig: go.Figure, height: int = 380,
              score_bands: bool = False) -> go.Figure:
    """One Plotly look everywhere: dark template, shared colorway, Inter.

    score_bands=True adds the dotted positive/negative cutoffs that give
    0–10 aspect scores their meaning. Only for score charts — never for
    percent gauges or benchmark bars.
    """
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        colorway=SERIES,
        height=height,
        margin=dict(t=40, b=40, l=40, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Inter, sans-serif"),
    )
    if score_bands:
        for value, name, color in ((7.0, "positive", SUCCESS),
                                   (4.0, "negative", DANGER)):
            fig.add_hline(y=value, line_dash="dot", line_color=color,
                          annotation_text=f"{name} {value}",
                          annotation_position="top right",
                          annotation_font_color=color)
    return fig


def status_dot(state: str, text: str, container=None):
    """Live status indicator. state: live | alert | warn | idle.

    Pulse means healthy/running, blink means needs attention.
    Pass container=st.sidebar to render inside the sidebar.
    """
    target = container if container is not None else st
    cls = {"live": "dot-live", "alert": "dot-alert",
           "warn": "dot-warn"}.get(state, "dot-idle")
    target.markdown(f'<span class="dot {cls}"></span>{text}',
                    unsafe_allow_html=True)


def about(endpoint: str, body: str):
    """Standard 'what this page does + which endpoint serves it' block."""
    st.markdown(f"Endpoint: `{endpoint}`")
    st.markdown(body)
