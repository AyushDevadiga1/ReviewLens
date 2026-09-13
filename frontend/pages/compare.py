"""
compare.py
Side-by-side product comparison page.
This is the most important page — the demo moment.

Shows:
  - Radar chart comparing all products on all aspects
  - Table with aspect scores per product
  - Winner column highlighting which product wins per aspect
  - Summary: "Product A wins on: Battery, Value. Product B wins on: Camera"
"""

import streamlit as st
import plotly.graph_objects as go
import requests
from typing import List


API_BASE = "http://localhost:8000"


def render_radar_chart(product_data: List[dict], aspects: List[str]):
    """
    Render a Plotly radar chart comparing products across aspects.

    Args:
        product_data: [{"name": str, "scores": {aspect: float}}]
        aspects: list of aspect names for radar axes

    TODO:
      1. Create go.Figure()
      2. For each product, add go.Scatterpolar trace:
         r = [scores[a] for a in aspects]
         theta = [display_name for a in aspects]
         fill = 'toself'
         name = product name
      3. Update layout: polar, showlegend=True
      4. st.plotly_chart(fig, use_container_width=True)
    """
    pass


def render_comparison_table(compare_response: dict):
    """
    Render side-by-side aspect score table with winner highlighting.

    TODO:
      1. Build pandas DataFrame:
         rows = aspects, columns = product names + "Winner"
      2. For each cell: show mean_score with sentiment emoji
         (≥7: 🟢, 4-7: 🟡, <4: 🔴)
      3. Winner column: show product name that won this aspect
      4. st.dataframe() with styling
    """
    pass


def render_compare_page():
    """
    Main comparison page renderer.

    TODO:
      1. st.title("Compare Products")
      2. st.text_input() for each of up to 3 product URLs
      3. "Compare" button
      4. On click:
         a. POST to /analyze for each URL (or GET /compare with all URLs)
         b. Call render_radar_chart()
         c. Call render_comparison_table()
         d. Show winner summary: "Product A wins on 3 of 7 aspects"
      5. Show fake review stats: "Filtered X fake reviews across all products"
    """
    pass