"""
comparison_table.py
Reusable side-by-side aspect score table component.
Called from pages/compare.py.
"""

import pandas as pd
import streamlit as st
from typing import List


def _score_to_emoji(score: float) -> str:
    """Map a 0–10 score to a colour emoji for quick visual scanning."""
    if score >= 7.0:
        return "🟢"
    elif score >= 4.0:
        return "🟡"
    return "🔴"


def render_comparison_table(compare_response: dict):
    """
    Render a side-by-side aspect score table with a winner column.

    Args:
        compare_response: the JSON body from GET /compare, shaped as:
            {
              "products": [
                {"product_name": str, "aspects": [{"aspect": str, "display_name": str,
                                                    "mean_score": float, ...}]},
                ...
              ],
              "winners": [{"aspect": str, "display_name": str, "winner": str, ...}]
            }

    TODO:
      1. Build a dict: {aspect_key: {product_name: "score_emoji score"}}
         e.g. {"battery": {"OnePlus 12": "🟢 8.4", "Samsung S24": "🟡 6.1"}}
      2. Add a "Winner" column from compare_response["winners"]
      3. Create pd.DataFrame, rows=aspects, columns=product names + "Winner"
      4. st.dataframe(df, use_container_width=True)
      5. Below the table: st.caption() showing which product wins the most aspects
    """
    pass
