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
                      {"name": str, "scores": {display_name: float (0–10)}}
        aspect_display_names: ordered list of display labels for the radar axes
                              e.g. ["Battery Life", "Camera", "Display", ...]
    """
    if not product_data or not aspect_display_names:
        st.info("No aspect data to chart yet — analyze a product first.")
        return

    fig = go.Figure()
    for product in product_data:
        scores = product.get("scores", {})
        ordered = [float(scores.get(axis, 0.0)) for axis in aspect_display_names]
        fig.add_trace(go.Scatterpolar(
            r=ordered + [ordered[0]],   # close the polygon
            theta=aspect_display_names + [aspect_display_names[0]],
            fill='toself',
            name=product.get("name", "product"),
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=True,
        title="Aspect Sentiment Comparison",
    )
    st.plotly_chart(fig, use_container_width=True)
