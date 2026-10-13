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
SURFACE2 = "#1E2A40"
PRIMARY = "#10B981"
ACCENT = "#10B981"
TEXT = "#E6EAF2"
MUTED = "#8B94A7"
SUCCESS = "#10B981"
WARN = "#F59E0B"
DANGER = "#E5484B"

# Harmonious emerald, teal, cyan, indigo spectrum
SERIES = ["#10B981", "#2DD4BF", "#38BDF8", "#818CF8", "#A78BFA"]

PLOTLY_TEMPLATE = "plotly_dark"
FONT = "Inter, -apple-system, 'Segoe UI', sans-serif"

_CSS = f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
/* ================================================================
   FORCE DARK THEME ON ALL PAGES — must override Streamlit defaults
   ================================================================ */
/* Main container */
[data-testid="stMain"],
[data-testid="stMain"] [data-testid="stVerticalBlock"],
.main,
.block-container {{
  background-color: {BG} !important;
  font-family: {FONT} !important;
}}

/* Header styling */
header[data-testid="stHeader"] {{
  background-color: transparent !important;
}}

/* Unified, seamless sidebar */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
[data-testid="stSidebarNav"] {{
  background-color: #0D1322 !important;
  border-right: 1px solid #1E2A40 !important;
}}

[data-testid="stSidebarNav"] {{
  padding-top: 0.5rem !important;
  padding-bottom: 0.5rem !important;
}}

[data-testid="stSidebarNav"] li a {{
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
  color: {TEXT} !important;
  font-weight: 500 !important;
}}

[data-testid="stSidebarNav"] li a:hover {{
  background-color: #1A243B !important;
  color: {PRIMARY} !important;
}}

[data-testid="stSidebarNav"] li a[aria-current="page"] {{
  background-color: #162238 !important;
  color: {PRIMARY} !important;
  font-weight: 600 !important;
  border-left: 3px solid {PRIMARY} !important;
}}
/* Text colours */
html, body, p, span, div, li, label, h1, h2, h3, h4, h5, h6,
[class*="st-"], .stMarkdown, .stText, .element-container {{
  font-family: {FONT} !important;
  color: {TEXT};
}}
/* Streamlit metric */
[data-testid="stMetricValue"] {{ color: {TEXT} !important; font-weight: 700; }}
[data-testid="stMetricLabel"] {{ color: {MUTED} !important; font-size: 0.82rem; }}
[data-testid="stMetricDelta"] {{ font-size: 0.8rem !important; }}
/* Buttons */
.stButton > button {{
  background: linear-gradient(135deg, {PRIMARY}, #059669) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  transition: all 0.2s ease !important;
}}
.stButton > button:hover {{
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px {PRIMARY}44 !important;
}}
.stButton > button:disabled {{
  background: #1E2A40 !important;
  color: {MUTED} !important;
  transform: none !important;
}}
/* Containers with borders */
div[data-testid="stVerticalBlockBorderWrapper"] > div {{
  background: {SURFACE} !important;
  border-color: #26314B !important;
  border-radius: 14px !important;
}}
/* Expanders */
details {{
  background: {SURFACE} !important;
  border-radius: 10px !important;
  border: 1px solid #26314B !important;
  padding: 0.2rem;
}}
summary {{ color: {TEXT} !important; font-weight: 600 !important; padding: 0.4rem 0.6rem; }}
/* Select / multiselect */
[data-testid="stMultiSelect"] > div,
[data-testid="stSelectbox"] > div > div {{
  background: {SURFACE} !important;
  border-color: #26314B !important;
  color: {TEXT} !important;
  border-radius: 8px !important;
}}
/* Text inputs and textareas */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {{
  background: {SURFACE} !important;
  border-color: #26314B !important;
  color: {TEXT} !important;
  border-radius: 8px !important;
}}
/* Radio buttons */
[data-testid="stRadio"] > div {{ gap: 0.5rem !important; }}
/* Sliders */
[data-testid="stSlider"] [data-baseweb="slider"] {{ background: {SURFACE} !important; }}
/* Dataframe / table */
[data-testid="stDataFrame"] {{ border: 1px solid #26314B !important; border-radius: 10px !important; }}
/* Alert boxes */
[data-testid="stInfo"] {{
  background: {SURFACE2}CC !important;
  border: 1px solid #2563EB66 !important;
  border-radius: 10px !important;
  color: {TEXT} !important;
}}
[data-testid="stWarning"] {{
  background: {SURFACE2}CC !important;
  border: 1px solid {WARN}66 !important;
  border-radius: 10px !important;
  color: {TEXT} !important;
}}
[data-testid="stSuccess"] {{
  background: {SURFACE2}CC !important;
  border: 1px solid {SUCCESS}66 !important;
  border-radius: 10px !important;
  color: {TEXT} !important;
}}
[data-testid="stError"] {{
  background: {SURFACE2}CC !important;
  border: 1px solid {DANGER}66 !important;
  border-radius: 10px !important;
  color: {TEXT} !important;
}}
/* Spinner */
[data-testid="stSpinner"] p {{ color: {MUTED} !important; }}
/* Hide deploy button and menu */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
[data-testid="stToolbar"] {{ visibility: hidden; }}
button[data-testid="baseButton-header"] {{ display: none !important; }}
/* Caption / small text */
.stCaption, [data-testid="stCaption"] {{ color: {MUTED} !important; font-size: 0.79rem !important; }}
/* Page links (Overview and navigation cards) */
[data-testid="stPageLink-NavLink"] {{
  background: #162238 !important;
  border: 1px solid #26314B !important;
  border-radius: 8px !important;
  padding: 0.55rem 0.9rem !important;
  color: #E6EAF2 !important;
  font-weight: 600 !important;
  transition: all 0.2s ease !important;
  text-decoration: none !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
}}
[data-testid="stPageLink-NavLink"]:hover {{
  background: #1E2A40 !important;
  border-color: #10B981 !important;
  color: #10B981 !important;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.2) !important;
  transform: translateY(-1px) !important;
}}
[data-testid="stPageLink-NavLink"] p,
[data-testid="stPageLink-NavLink"] span {{
  color: inherit !important;
  font-weight: 600 !important;
}}
/* Progress bar */
[data-testid="stProgressBar"] > div {{ background: #10B98133 !important; border-radius: 4px !important; }}
[data-testid="stProgressBar"] > div > div {{ background: #10B981 !important; }}
/* Divider */
hr {{ border-color: #1E2A40 !important; }}

/* ================================================================
   HERO TYPOGRAPHY
   ================================================================ */
.hero-eyebrow {{
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.18em;
  text-transform: uppercase; color: {PRIMARY}; margin-bottom: 0.15rem;
  display: block;
}}
.hero-title {{
  font-size: 2.6rem; font-weight: 900; line-height: 1.08;
  margin-bottom: 0.25rem; display: block;
  background: linear-gradient(135deg, {TEXT} 0%, {PRIMARY} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.hero-sub {{
  font-size: 1.05rem; color: {MUTED}; margin-bottom: 1.2rem;
  max-width: 52rem; line-height: 1.6; display: block;
}}

/* ================================================================
   SECTION HEADERS
   ================================================================ */
.section-title {{
  font-size: 1.1rem; font-weight: 700; color: {TEXT} !important;
  border-left: 3px solid {PRIMARY}; padding-left: 0.65rem;
  margin: 1.8rem 0 0.9rem; letter-spacing: 0.01em; display: block;
}}

/* ================================================================
   FOOTER
   ================================================================ */
.page-foot {{
  margin-top: 2.5rem; padding-top: 0.9rem; border-top: 1px solid #1E2A40;
  font-size: 0.76rem; color: {MUTED};
}}

/* ================================================================
   PIPELINE DIAGRAM
   ================================================================ */
.pipe {{
  display: flex; align-items: stretch; gap: 0;
  margin: 1.2rem 0; flex-wrap: wrap;
}}
.step {{
  flex: 1; min-width: 90px;
  background: linear-gradient(160deg, {SURFACE}, {SURFACE2});
  border: 1px solid #26314B;
  border-radius: 12px; padding: 0.8rem 0.6rem; text-align: center;
  transition: border-color 0.2s, box-shadow 0.2s;
}}
.step:hover {{
  border-color: {PRIMARY}55;
  box-shadow: 0 0 18px {PRIMARY}22;
}}
.step b {{ display: block; font-size: 0.92rem; color: {TEXT} !important; margin-bottom: 0.15rem; }}
.step span {{ font-size: 0.73rem; color: {MUTED}; }}
.arrow {{ align-self: center; color: {PRIMARY}; font-size: 1.35rem; padding: 0 0.25rem; }}
a {{ color: {PRIMARY}; }}

/* ================================================================
   STATUS DOTS
   ================================================================ */
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
  display: inline-block; width: 9px; height: 9px; border-radius: 50%;
  margin-right: 0.45rem; vertical-align: baseline;
}}
.dot-live {{ background: {SUCCESS}; animation: rl-pulse 2s infinite; }}
.dot-alert {{ background: {DANGER}; animation: rl-blink 1s infinite; }}
.dot-warn {{ background: {WARN}; animation: rl-blink 1.6s infinite; }}
.dot-idle {{ background: {MUTED}; }}
@media (prefers-reduced-motion: reduce) {{
  .dot-live, .dot-alert, .dot-warn {{ animation: none; }}
}}

/* ================================================================
   GLASS CARD
   ================================================================ */
.glass {{
  background: linear-gradient(135deg, {SURFACE}EE, {SURFACE2}99);
  border: 1px solid #26314B; border-radius: 16px;
  padding: 1rem 1.2rem; margin-bottom: 0.9rem;
  box-shadow: 0 6px 24px rgba(0,0,0,0.4), 0 0 0 1px #ffffff08 inset;
}}
.glass-highlight {{
  background: linear-gradient(135deg, {PRIMARY}15, {PRIMARY}08);
  border: 1px solid {PRIMARY}33; border-radius: 16px;
  padding: 1rem 1.2rem; margin-bottom: 0.9rem;
  box-shadow: 0 6px 24px {PRIMARY}18;
}}

/* ================================================================
   STAT CARDS (for Overview)
   ================================================================ */
.stat-grid {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }}
.stat-card {{
  flex: 1; min-width: 140px;
  background: linear-gradient(160deg, {SURFACE}, {SURFACE2});
  border: 1px solid #26314B; border-radius: 16px;
  padding: 1.4rem 1rem; text-align: center;
  position: relative; overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}}
.stat-card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 30px rgba(0,0,0,0.5); }}
.stat-card::before {{
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, {PRIMARY}, #059669);
}}
.stat-value {{
  font-size: 2.4rem; font-weight: 900; line-height: 1; margin-bottom: 0.3rem;
  background: linear-gradient(135deg, {TEXT}, {PRIMARY});
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; display: block;
}}
.stat-label {{
  font-size: 0.75rem; color: {MUTED}; font-weight: 600;
  letter-spacing: 0.06em; text-transform: uppercase;
}}

/* ================================================================
   FEATURE CARDS (for Overview)
   ================================================================ */
.feature-card {{
  background: linear-gradient(160deg, {SURFACE}, {SURFACE2});
  border: 1px solid #26314B; border-radius: 14px;
  padding: 1.3rem 1.2rem; height: 100%;
  transition: border-color 0.25s, box-shadow 0.25s, transform 0.25s;
}}
.feature-card:hover {{
  border-color: {PRIMARY}44;
  box-shadow: 0 0 24px {PRIMARY}18;
  transform: translateY(-2px);
}}
.feature-header {{
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 0.8rem;
}}
.feature-icon-svg {{
  width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center;
  background: {SURFACE2}; border: 1px solid #26314B; border-radius: 8px; color: {PRIMARY};
}}
.feature-tag {{
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em;
  color: {PRIMARY}; background: {PRIMARY}15; border: 1px solid {PRIMARY}33;
  padding: 0.15rem 0.5rem; border-radius: 4px; text-transform: uppercase;
}}
.feature-title {{
  font-size: 0.95rem; font-weight: 700; color: {TEXT} !important;
  margin-bottom: 0.35rem; display: block;
}}
.feature-desc {{ font-size: 0.83rem; color: {MUTED}; line-height: 1.6; display: block; }}

/* ================================================================
   BADGES
   ================================================================ */
.badge {{
  display: inline-block; font-size: 0.68rem; font-weight: 700;
  padding: 0.15rem 0.55rem; border-radius: 20px; letter-spacing: 0.05em;
  text-transform: uppercase;
}}
.badge-green {{ background: {PRIMARY}22; color: {PRIMARY}; border: 1px solid {PRIMARY}44; }}
.badge-amber {{ background: {WARN}22; color: {WARN}; border: 1px solid {WARN}44; }}
.badge-red   {{ background: {DANGER}22; color: {DANGER}; border: 1px solid {DANGER}44; }}

/* ================================================================
   BENCHMARK BAR CHART CONTAINER
   ================================================================ */
.bench-wrap {{
  background: {SURFACE}; border: 1px solid #26314B;
  border-radius: 14px; padding: 1rem; margin-bottom: 1rem;
}}
</style>
"""


def inject_css():
    """Inject the shared stylesheet once per page run.
    Must filter blank lines so CommonMark does not terminate the <style> block prematurely.
    """
    clean_css = "\n".join(line for line in _CSS.splitlines() if line.strip())
    st.markdown(clean_css, unsafe_allow_html=True)


def hero(title: str, subtitle: str, eyebrow: str = "REVIEWLENS"):
    """Eyebrow + gradient title + muted subtitle, identical on every page."""
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
