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
    """

    products = compare_response.get("products", [])
    winners = {w["aspect"]: w["winner"] for w in compare_response.get("winners", [])}
    if not products:
        st.info("No products to compare.")
        return

    # Union of aspect keys across products, labelled by display name.
    aspect_labels = {}
    for product in products:
        for item in product.get("aspects", []):
            aspect_labels[item["aspect"]] = item.get("display_name", item["aspect"])

    rows = {}
    for aspect_key, label in aspect_labels.items():
        row = {}
        for product in products:
            scores = {a["aspect"]: a["mean_score"] for a in product.get("aspects", [])}
            score = scores.get(aspect_key)
            row[product["product_name"]] = (
                f"{_score_to_emoji(score)} {score:.1f}" if score is not None else "—"
            )
        row["Winner"] = winners.get(aspect_key, "—")
        rows[label] = row

    df = pd.DataFrame(rows).T
    st.dataframe(df, use_container_width=True)

    # Which product wins the most aspects?
    win_counts = {}
    for winner in winners.values():
        win_counts[winner] = win_counts.get(winner, 0) + 1
    if win_counts:
        best = max(win_counts, key=win_counts.get)
        st.caption(
            f"{best} wins {win_counts[best]} of {len(winners)} aspects. "
            f"Margins are in the API response (`winning_score` − runner-up)."
        )
