"""
radar_chart.py
Reusable Plotly radar chart component.
Called from pages/compare.py and pages/single.py.
"""

import plotly.graph_objects as go
import streamlit as st
from typing import List


def render_radar_chart(product_data: List[dict], aspect_display_names: List[str]):
    """
    Render a Plotly radar chart comparing one or more products across aspects.

    Args:
        product_data: list of dicts, each:
                      {"name": str, "scores": {aspect_key: float (0–10)}}
        aspect_display_names: ordered list of display labels for the radar axes
                              e.g. ["Battery Life", "Camera", "Display", ...]

    TODO:
      1. fig = go.Figure()
      2. For each product in product_data:
         scores_ordered = [product["scores"].get(a, 0) for a in aspect_keys]
         fig.add_trace(go.Scatterpolar(
             r=scores_ordered + [scores_ordered[0]],   # close the polygon
             theta=aspect_display_names + [aspect_display_names[0]],
             fill='toself',
             name=product["name"]
         ))
      3. fig.update_layout(
             polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
             showlegend=True,
             title="Aspect Sentiment Comparison"
         )
      4. st.plotly_chart(fig, use_container_width=True)
    """
    pass
