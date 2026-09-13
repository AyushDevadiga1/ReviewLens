"""
single.py
Single product analysis page.
Enter one URL, see the full aspect breakdown for that product.

Shows:
  - Radar chart of aspect sentiment scores
  - Fake review percentage (filtered before ABSA)
  - Top genuine positive and negative reviews per aspect
"""

import streamlit as st
import plotly.graph_objects as go
import requests
from typing import Optional


def render_single_page():
    """
    Main single product page renderer.

    TODO:
      1. st.title("Single Product Analysis")
      2. st.text_input() for the product URL
      3. Optional "review_text" mode for quick testing without scraping
      4. "Analyze" button → POST to /analyze
      5. On response:
         a. Call render_radar_chart() with the aspect scores
         b. Show fake review stats (scraped / fake / genuine / percentage)
         c. Show a table of aspect scores with sentiment emoji
         d. Show top positive and negative reviews per aspect
      6. Handle API errors gracefully (st.error)
    """
    pass


def render_radar_chart(aspects: list):
    """
    Render a Plotly radar chart of aspect sentiment scores.

    Args:
        aspects: list of dicts from AnalyzeResponse.aspects

    TODO:
      1. Create go.Figure()
      2. Add one go.Scatterpolar trace:
         r = [a["mean_score"] for a in aspects]
         theta = [a["display_name"] for a in aspects]
         fill = 'toself'
      3. Update layout: polar with range 0-10, showlegend=False
      4. st.plotly_chart(fig, use_container_width=True)
    """
    pass