"""
radar_chart.py
Reusable Plotly radar chart component.
Called from pages/compare.py and pages/single.py.
"""

import plotly.graph_objects as go
import streamlit as st
from typing import List

from components import theme


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

    fig = theme.style_fig(go.Figure(), height=430)
    for product in product_data:
        scores = product.get("scores", {})
        ordered = [float(scores.get(axis, 0.0)) for axis in aspect_display_names]
        fig.add_trace(go.Scatterpolar(
            r=ordered + [ordered[0]],   # close the polygon
            theta=aspect_display_names + [aspect_display_names[0]],
            fill='toself',
            name=product.get("name", "product"),
            line=dict(width=2),
            opacity=0.85,
        ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 10], gridcolor="#26314B",
                            linecolor="#26314B", tickfont=dict(color=theme.MUTED, size=10)),
            angularaxis=dict(gridcolor="#26314B", linecolor="#26314B",
                             tickfont=dict(color=theme.TEXT, size=11)),
        ),
        showlegend=True,
        title=dict(text="Aspect Sentiment Comparison",
                   font=dict(color=theme.TEXT, size=15), x=0.02),
        legend=dict(orientation="h", yanchor="top", y=-0.04,
                    xanchor="center", x=0.5, font=dict(color=theme.TEXT, size=11)),
        margin=dict(t=55, b=95, l=75, r=75),
    )
    st.plotly_chart(fig, use_container_width=True)
