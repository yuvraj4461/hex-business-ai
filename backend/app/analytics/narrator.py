"""Write a short prose answer over a query result.

Deterministic by default — the templated sentence is clear and, crucially,
instant. Set ``HEX_DATA_AI_NARRATION=true`` to have Gemini phrase it
instead (adds one model round-trip per question; falls back to the
deterministic text if the model is slow or unavailable).
"""

from __future__ import annotations

import logging
import os

from app.ai import gemini
from app.analytics.semantic import METRICS, QuerySpec, spec_label

logger = logging.getLogger(__name__)


def _ai_enabled() -> bool:
    return os.getenv("HEX_DATA_AI_NARRATION", "").lower() in ("1", "true", "yes")


def narrate(question: str, spec: QuerySpec, result: dict) -> tuple[str, bool]:
    """Return (answer, ai_written). The deterministic template is the normal
    path and is not treated as a degradation."""

    rows = result.get("rows", [])
    unit = result.get("chart", {}).get("unit", "")

    if _ai_enabled() and gemini.is_configured() and rows:
        money = unit == "INR"
        value_hint = (
            "Values are Indian Rupees — write them like ₹12,34,567 (Indian digit "
            "grouping), rounded, no decimals."
            if money
            else "Values are plain counts." if unit == "count"
            else "Values are in days."
        )
        prompt = f"""You are HEX. Answer the user's question in 2-3 plain sentences
using ONLY the numbers below. No preamble, no bullet lists, no markdown headings.
Mention the highest and lowest values and the overall shape. {value_hint}

QUESTION: {question}
WHAT WAS MEASURED: {spec_label(spec)}
DATA (label, value): {[(r["label"], round(r["value"])) for r in rows][:40]}
"""
        try:
            text = gemini.generate_text(prompt)
            if text and text.strip():
                return text.strip(), True
        except Exception as exc:  # noqa: BLE001
            logger.warning("narrator: Gemini unavailable (%s), using fallback", exc)

    return _fallback(question, spec, result), False


def _fmt(value: float, unit: str) -> str:
    if unit == "INR":
        return f"₹{value:,.0f}"
    if unit == "days":
        return f"{value:,.1f} days"
    return f"{value:,.0f}"


def _fallback(question: str, spec: QuerySpec, result: dict) -> str:
    metric = METRICS.get(spec.metric)
    label = metric.label if metric else spec.metric
    unit = result.get("chart", {}).get("unit", "")
    rows = result.get("rows", [])

    if not rows:
        return (
            f"No {label.lower()} data matched that question for your "
            f"organization yet."
        )

    if result.get("chart", {}).get("type") == "stat":
        return f"{label}: {_fmt(rows[0]['value'], unit)}."

    total = sum(r["value"] for r in rows)
    top = max(rows, key=lambda r: r["value"])
    bottom = min(rows, key=lambda r: r["value"])

    parts = [f"{spec_label(spec)} — {len(rows)} groups."]
    parts.append(
        f"Highest is {top['label']} at {_fmt(top['value'], unit)}; "
        f"lowest is {bottom['label']} at {_fmt(bottom['value'], unit)}."
    )
    if metric and metric.aggregate == "sum":
        parts.append(f"Total across all groups: {_fmt(total, unit)}.")
    return " ".join(parts)
