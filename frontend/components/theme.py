"""
theme.py
Single source of truth for the dashboard's look: one restrained palette,
one CSS block, one section header, one Plotly template. Every page imports
from here so the styling cannot drift between pages.

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

_CSS = f"""
<style>
.hero-title {{
  font-size: 2.4rem; font-weight: 800; line-height: 1.1;
  color: {TEXT}; margin-bottom: 0.2rem;
}}
.hero-sub {{ font-size: 1.05rem; color: {MUTED}; margin-bottom: 1rem; }}
.section-title {{
  font-size: 1.25rem; font-weight: 700; color: {TEXT};
  border-left: 4px solid {PRIMARY}; padding-left: 0.6rem; margin: 1.4rem 0 0.6rem;
}}
.card {{
  background: {SURFACE}; border: 1px solid #26314B;
  border-radius: 12px; padding: 0.9rem 1rem; margin-bottom: 0.8rem;
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
</style>
"""


def inject_css():
    """Inject the shared stylesheet once per page run."""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str):
    """Solid title + muted subtitle, identical on every page."""
    inject_css()
    st.markdown(f'<div class="hero-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-sub">{subtitle}</div>', unsafe_allow_html=True)


def section(title: str):
    """Accent-bar section header — the visual rhythm of every page."""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def style_fig(fig: go.Figure, height: int = 380) -> go.Figure:
    """One Plotly look everywhere: dark template, shared colorway."""
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        colorway=SERIES,
        height=height,
        margin=dict(t=40, b=40, l=40, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
    )
    return fig


def about(endpoint: str, body: str):
    """Standard 'what this page does + which endpoint serves it' block."""
    st.markdown(f"Endpoint: `{endpoint}`")
    st.markdown(body)
