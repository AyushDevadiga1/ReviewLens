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

/* Top decoration strip — default is a red→yellow bar; use the brand spectrum */
[data-testid="stDecoration"] {{
  background-image: linear-gradient(90deg, {PRIMARY} 0%, #2DD4BF 38%, #38BDF8 68%, #818CF8 100%) !important;
  height: 2px !important;
  opacity: 0.95;
}}

/* Rendering polish */
* {{ -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }}
::selection {{ background: {PRIMARY}3D; color: #FFFFFF; }}

/* Scrollbars — slim, on-brand */
* {{ scrollbar-width: thin; scrollbar-color: #2E3C59 transparent; }}
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
  background: #2E3C59; border-radius: 8px; border: 2px solid transparent;
  background-clip: padding-box;
}}
::-webkit-scrollbar-thumb:hover {{ background: #3E5178; background-clip: padding-box; }}
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{ background: #263247; background-clip: padding-box; }}

/* Headings — tighter, darker-weight scale */
[data-testid="stHeading"], h1, h2, h3, h4, h5 {{
  color: {TEXT}; letter-spacing: -0.015em; line-height: 1.26; font-weight: 700;
}}
h1 {{ font-size: 2.15rem !important; font-weight: 800 !important; }}
h2 {{ font-size: 1.5rem !important; }}
h3 {{ font-size: 1.2rem !important; }}
h4 {{ font-size: 1.02rem !important; }}

/* Markdown body rhythm */
[data-testid="stMarkdownContainer"] p {{ line-height: 1.65; color: {TEXT}; }}
[data-testid="stMarkdownContainer"] ul,
[data-testid="stMarkdownContainer"] ol {{ line-height: 1.6; padding-left: 1.2rem; margin: 0.25rem 0 0.6rem; }}
[data-testid="stMarkdownContainer"] li {{ margin: 0.2rem 0; color: {TEXT}; }}
[data-testid="stMarkdownContainer"] blockquote {{
  border-left: 3px solid {PRIMARY}66 !important;
  background: {SURFACE}80; border-radius: 0 10px 10px 0;
  padding: 0.45rem 0.8rem; margin: 0.4rem 0; color: {MUTED};
}}
[data-testid="stMarkdownContainer"] a {{
  color: {PRIMARY}; text-decoration: none; text-underline-offset: 3px;
  transition: color 0.15s ease;
}}
[data-testid="stMarkdownContainer"] a:hover {{ color: #34D399; text-decoration: underline; }}

/* Inline & block code */
:not(pre) > code {{
  background: {SURFACE2}; color: #5EEAD4; border: 1px solid #2A3752;
  border-radius: 5px; padding: 0.1em 0.4em; font-size: 0.86em;
}}
[data-testid="stCodeBlock"] {{
  background: #0D1322 !important; border: 1px solid #26314B;
  border-radius: 10px !important;
}}

/* Unified, seamless sidebar */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
[data-testid="stSidebarNav"] {{
  background-color: #0D1322 !important;
  border-right: 1px solid #1E2A40 !important;
}}
[data-testid="stSidebar"] {{
  box-shadow: 6px 0 24px rgba(0, 0, 0, 0.35) !important;
}}

[data-testid="stSidebarNav"] {{
  padding-top: 0.5rem !important;
  padding-bottom: 0.5rem !important;
}}
/* Streamlit reserves 6rem above the nav for chrome that is hidden here — reclaim it */
[data-testid="stSidebarNavItems"] {{
  padding-top: 1rem !important;
}}

[data-testid="stSidebarNav"] li {{ margin: 0 !important; }}

[data-testid="stSidebarNav"] li a {{
  border-radius: 9px !important;
  padding: 0.32rem 0.85rem !important;
  line-height: 1.4 !important;
  font-size: 0.92rem !important;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease !important;
  color: {TEXT} !important;
  font-weight: 500 !important;
}}

[data-testid="stSidebarNav"] li a:hover {{
  background-color: rgba(255, 255, 255, 0.045) !important;
  color: {PRIMARY} !important;
}}

[data-testid="stSidebarNav"] li a[aria-current="page"] {{
  background-image: linear-gradient(90deg, {PRIMARY}26, {PRIMARY}00) !important;
  background-color: transparent !important;
  color: {TEXT} !important;
  font-weight: 600 !important;
  box-shadow: inset 3px 0 0 {PRIMARY} !important;
}}
/* Text colours */
html, body, p, span, div, li, label, h1, h2, h3, h4, h5, h6,
[class*="st-"], .stMarkdown, .stText, .element-container {{
  font-family: {FONT} !important;
  color: {TEXT};
}}
/* Streamlit metric — tile treatment instead of floating text */
[data-testid="stMetric"] {{
  background: linear-gradient(160deg, {SURFACE}, rgba(30, 42, 64, 0.55));
  border: 1px solid #26314B !important;
  border-radius: 14px !important;
  padding: 0.85rem 1rem 0.9rem;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}}
[data-testid="stMetric"]:hover {{
  border-color: {PRIMARY}66 !important;
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
}}
[data-testid="stMetricValue"] {{ color: {TEXT} !important; font-weight: 800 !important; letter-spacing: -0.01em; }}
[data-testid="stMetricLabel"] {{
  color: {MUTED} !important; font-size: 0.72rem !important; font-weight: 600 !important;
  letter-spacing: 0.07em; text-transform: uppercase; margin-bottom: 0.15rem;
  white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
}}
[data-testid="stMetricLabel"] p {{
  white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
}}
[data-testid="stMetricDelta"] {{ font-size: 0.78rem !important; }}

/* Buttons — primary gets the emerald pill, secondary stays neutral */
.stButton > button,
[data-testid="stFormSubmitButton"] > button {{
  background: linear-gradient(135deg, {PRIMARY}, #059669) !important;
  color: #fff !important;
  border: 1px solid rgba(255, 255, 255, 0.10) !important;
  border-radius: 9px !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  min-height: 2.5rem; padding: 0.5rem 1rem;
  box-shadow: 0 2px 10px {PRIMARY}33, inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
  transition: transform 0.16s ease, box-shadow 0.16s ease, background 0.16s ease !important;
}}
.stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {{
  transform: translateY(-1px) !important;
  box-shadow: 0 8px 22px {PRIMARY}61 !important;
}}
.stButton > button:active,
[data-testid="stFormSubmitButton"] > button:active {{ transform: translateY(0) scale(0.985) !important; }}
.stButton > button:focus-visible,
[data-testid="stFormSubmitButton"] > button:focus-visible {{
  outline: 2px solid {PRIMARY} !important; outline-offset: 2px;
}}
.stButton > button[kind="secondary"],
[data-testid="stFormSubmitButton"] > button[kind="secondary"] {{
  background: linear-gradient(180deg, #1B2438, #161E30) !important;
  color: {TEXT} !important;
  border: 1px solid #2C3A57 !important;
  box-shadow: none !important;
}}
.stButton > button[kind="secondary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="secondary"]:hover {{
  background: linear-gradient(180deg, #1F2A42, #182136) !important;
  color: {PRIMARY} !important;
  border-color: {PRIMARY}80 !important;
  box-shadow: 0 6px 18px {PRIMARY}24 !important;
}}
.stButton > button:disabled,
[data-testid="stFormSubmitButton"] > button:disabled {{
  background: #1A2338 !important;
  color: {MUTED} !important;
  border-color: #232F49 !important;
  transform: none !important;
  box-shadow: none !important;
}}
/* Layout containers and columns: transparent background to avoid boxy light blue wrappers */
[data-testid="column"],
[data-testid="column"] > div,
[data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"] > div,
div[data-testid="stVerticalBlockBorderWrapper"] > div {{
  background: transparent !important;
  border-color: #26314B !important;
}}
/* Expanders */
details,
[data-testid="stExpanderDetails"] {{
  background: linear-gradient(180deg, {SURFACE}, #131B2C) !important;
  border-radius: 12px !important;
  border: 1px solid #26314B !important;
  padding: 0.2rem !important;
  transition: border-color 0.18s ease !important;
}}
details:hover,
[data-testid="stExpanderDetails"]:hover {{ border-color: #33456B !important; }}
summary {{ color: {TEXT} !important; font-weight: 600 !important; padding: 0.45rem 0.7rem; }}
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
/* Alert boxes — modern testids (stNotification) + legacy names */
[data-testid="stNotification"] {{
  margin: 0.15rem 0 !important;
  background: transparent !important;
  border: 0 !important;
}}
[data-testid^="stNotificationContent"] {{
  background: rgba(30, 42, 64, 0.72) !important;
  border: 1px solid #2A3752 !important;
  border-left: 3px solid {PRIMARY} !important;
  border-radius: 12px !important;
  padding: 0.7rem 0.95rem !important;
  color: {TEXT} !important;
}}
[data-testid="stNotification"]:has([data-testid="stNotificationContentError"]) [data-testid^="stNotificationContent"] {{ border-left-color: {DANGER} !important; }}
[data-testid="stNotification"]:has([data-testid="stNotificationContentWarning"]) [data-testid^="stNotificationContent"] {{ border-left-color: {WARN} !important; }}
[data-testid="stNotification"]:has([data-testid="stNotificationContentSuccess"]) [data-testid^="stNotificationContent"] {{ border-left-color: {SUCCESS} !important; }}
[data-testid="stNotification"]:has([data-testid="stNotificationContentInfo"]) [data-testid^="stNotificationContent"] {{ border-left-color: #38BDF8 !important; }}
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
/* Divider — soft fade instead of a hard rule */
hr {{
  border: 0 !important;
  height: 1px !important;
  background: linear-gradient(90deg, transparent, #2A3752 12%, #2A3752 88%, transparent) !important;
  margin: 1.5rem 0 !important;
}}

/* ================================================================
   FORMS, FIELDS & FOCUS
   ================================================================ */
[data-testid="stForm"] {{
  background: rgba(21, 29, 46, 0.55);
  border: 1px solid #26314B;
  border-radius: 14px;
  padding: 1rem 1.1rem 1.1rem;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] input:focus {{
  border-color: {PRIMARY} !important;
  box-shadow: 0 0 0 3px {PRIMARY}2E !important;
  caret-color: {PRIMARY} !important;
}}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {{ color: #6B7488 !important; opacity: 1; }}
[data-testid="stSelectbox"] > div > div {{
  transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}}
[data-testid="stSelectbox"] > div > div:hover {{ border-color: #3B4C74 !important; }}
[data-testid="stSelectbox"] > div > div:focus-within {{
  border-color: {PRIMARY}99 !important;
  box-shadow: 0 0 0 3px {PRIMARY}26 !important;
}}

/* Dropdown popovers (select, multiselect, date) */
[data-baseweb="popover"] {{
  background: {SURFACE} !important;
  border: 1px solid #2A3752 !important;
  border-radius: 12px !important;
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.55) !important;
  overflow: hidden;
}}
[data-baseweb="menu"] li {{
  color: {TEXT} !important; font-size: 0.88rem !important;
  padding: 0.5rem 0.8rem !important;
  transition: background 0.12s ease !important;
}}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] li[aria-selected="true"] {{ background: #1B2740 !important; }}

/* Radio & checkbox */
[data-testid="stRadio"] label {{
  border-radius: 8px; transition: background 0.15s ease;
  padding: 0.22rem 0.4rem;
}}
[data-testid="stRadio"] label:hover {{ background: rgba(26, 36, 59, 0.7); }}
[data-testid="stRadio"] label:has(input:checked) {{ background: {PRIMARY}1A; }}
input[type="checkbox"], input[type="radio"] {{ accent-color: {PRIMARY}; }}

/* ================================================================
   TABS
   ================================================================ */
[data-testid="stTabs"] [role="tablist"] {{
  border-bottom: 1px solid #26314B !important; gap: 0.35rem !important;
}}
[data-testid="stTabs"] [role="tab"] {{
  color: {MUTED} !important; font-weight: 600 !important; font-size: 0.9rem !important;
  padding: 0.55rem 0.9rem !important; border-radius: 9px 9px 0 0 !important;
  transition: color 0.18s ease, background 0.18s ease !important;
}}
[data-testid="stTabs"] [role="tab"]:hover {{ color: {TEXT} !important; background: rgba(26, 36, 59, 0.65) !important; }}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{ color: {PRIMARY} !important; }}

/* ================================================================
   TOOLTIPS, POPOVERS, TOASTS, EXCEPTIONS, TABLES
   ================================================================ */
[data-testid="stTooltipContent"] {{
  background: {SURFACE2} !important; border: 1px solid #2A3752 !important;
  border-radius: 10px !important; color: {TEXT} !important;
  font-size: 0.82rem !important; box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5) !important;
}}
[data-testid="stPopoverBody"] {{ background: {SURFACE} !important; border-color: #2A3752 !important; }}
[data-testid="stToast"] {{
  background: {SURFACE2} !important; border: 1px solid #2A3752 !important;
  border-left: 3px solid {PRIMARY} !important; border-radius: 10px !important;
  color: {TEXT} !important; box-shadow: 0 14px 34px rgba(0, 0, 0, 0.5) !important;
}}
[data-testid="stException"],
[data-testid="stErrorElementStack"] {{
  background: rgba(70, 22, 26, 0.45) !important;
  border: 1px solid {DANGER}55 !important;
  border-left: 3px solid {DANGER} !important;
  border-radius: 12px !important;
}}
[data-testid="stException"] *,
[data-testid="stException"] code {{ color: {TEXT} !important; }}
[data-testid="stTableStyledTable"] {{ border-color: #26314B !important; }}
[data-testid="stTableStyledTable"] thead tr th {{
  background: {SURFACE2} !important; color: {MUTED} !important;
  text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.74rem;
  border-color: #26314B !important;
}}
[data-testid="stTableStyledTable"] tbody tr {{ transition: background 0.12s ease !important; }}
[data-testid="stTableStyledTable"] tbody tr:hover {{ background: rgba(30, 42, 64, 0.55) !important; }}
[data-testid="stTableStyledTable"] tbody tr td {{ border-color: #22304A !important; }}

/* ================================================================
   MOTION
   ================================================================ */
@keyframes rl-fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
[data-testid="stAppViewContainer"] > div {{ animation: rl-fade 0.35s ease both; }}
@media (prefers-reduced-motion: reduce) {{
  .stButton > button:hover, .stat-card:hover, .feature-card:hover,
  [data-testid="stMetric"]:hover, .step:hover {{ transform: none !important; }}
  [data-testid="stAppViewContainer"] > div {{ animation: none !important; }}
}}

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
