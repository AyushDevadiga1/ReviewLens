"""
comparison_table.py
Reusable side-by-side aspect score table component.
Called from pages/compare.py.
"""

import pandas as pd
import streamlit as st
from typing import List


from components.api_client import get_friendly_name


def _score_to_label(score: float) -> str:
    """Map a 0–10 score to a formal text label for professional display."""
    if score >= 7.0:
        return "[HIGH]"
    elif score >= 4.0:
        return "[MED]"
    return "[LOW]"


def render_comparison_table(compare_response: dict):
    """
    Render a side-by-side aspect score table with a winner column.
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
            col_name = get_friendly_name(product["product_name"])
            scores = {a["aspect"]: a["mean_score"] for a in product.get("aspects", [])}
            score = scores.get(aspect_key)
            row[col_name] = (
                f"{_score_to_label(score)} {score:.1f} / 10" if score is not None else "—"
            )
        win_prod = winners.get(aspect_key, "—")
        row["Winner"] = get_friendly_name(win_prod) if win_prod != "—" else "—"
        rows[label] = row

    df = pd.DataFrame(rows).T
    st.dataframe(df, use_container_width=True)

    # Which product wins the most aspects?
    win_counts = {}
    for winner in winners.values():
        w_name = get_friendly_name(winner)
        win_counts[w_name] = win_counts.get(w_name, 0) + 1
    if win_counts:
        best = max(win_counts, key=win_counts.get)
        st.caption(
            f"**{best}** leads across {win_counts[best]} of {len(winners)} aspect dimensions. "
            f"Score legend: [HIGH] = 7.0–10.0 | [MED] = 4.0–6.9 | [LOW] = 0.0–3.9"
        )
