"""
trends.py
Sentiment drift timeline page.
Pick a product, aspect, and date range — see weekly sentiment trend.

Shows:
  - Line chart of mean aspect score per week
  - Overall direction badge: improving / declining / stable
"""

import streamlit as st
import plotly.graph_objects as go
import requests
from typing import Optional


def render_trends_page():
    """
    Main sentiment trends page renderer.

    TODO:
      1. st.title("Sentiment Trends")
      2. Selectors:
         a. Product (from /compare or a product list endpoint)
         b. Aspect (from GET /aspects or a fixed dropdown)
         c. Number of weeks (slider, 1-52)
      3. "Show Trend" button → GET /trends?product_id=..&aspect=..&weeks=..
      4. On response:
         a. Call render_trend_line() with the weekly data
         b. Show overall_direction badge with st.metric
         c. Alert if direction is "declining"
      5. Handle API errors gracefully (st.error)
    """
    pass


def render_trend_line(weekly_data: list):
    """
    Render a Plotly line chart of weekly mean scores.

    Args:
        weekly_data: list of dicts [{"week": str, "mean_score": float, "count": int}]

    TODO:
      1. Create go.Figure()
      2. Add go.Scatter trace: x=week labels, y=mean_score, mode='lines+markers'
      3. Update layout: title, axis labels, range 0-10
      4. st.plotly_chart(fig, use_container_width=True)
    """
    pass