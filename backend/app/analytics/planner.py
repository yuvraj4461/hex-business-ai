"""Turn a plain-language question into a validated :class:`QuerySpec`.

Tries Gemini first (strict JSON contract), then falls back to a
deterministic keyword parser so the feature keeps working when the model
is rate-limited or unset — the common shapes ("<metric> by <dimension>",
"top N …", "… in 2026") are all covered without the LLM.
"""

from __future__ import annotations

import json
import logging
import re

from app.ai import gemini
from app.analytics.semantic import (
    DIMENSIONS,
    METRICS,
    QuerySpec,
    SpecError,
    validate_spec,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# LLM path
# --------------------------------------------------------------------------

def _prompt(question: str, prior_spec: dict | None) -> str:
    metric_lines = "\n".join(
        f"  - {k}: {m.label} ({m.unit}); can group by: "
        f"{', '.join(m.allowed_dimensions) or '(total only)'}"
        for k, m in METRICS.items()
    )
    dim_lines = "\n".join(f"  - {k}: {d.label} ({d.kind})" for k, d in DIMENSIONS.items())

    prior = (
        f"\nThe user is refining this previous query, so start from it and "
        f"apply only the change they asked for:\n{json.dumps(prior_spec)}\n"
        if prior_spec else ""
    )

    return f"""You translate a business question into ONE JSON query spec for HEX.
Reply with ONLY a fenced ```json block, nothing else.

METRICS (use the key):
{metric_lines}

DIMENSIONS (use the key, pick at most ONE):
{dim_lines}

Spec shape:
{{
  "metric": "<metric key>",
  "dimension": "<dimension key or empty string for a single total>",
  "year": <4-digit year or null>,
  "last_n_months": <int or null>,
  "filters": {{ "<dimension key>": "<value>" }},
  "limit": <int or null, set for "top N">,
  "sort": "value_desc" | "value_asc" | "chrono"
}}

Rules:
- Only use keys listed above. The dimension must be allowed for the metric.
- "revenue by product / category / status" -> metric "product_revenue".
- Time words ("trend", "over time", "by month") -> a time dimension + sort "chrono".
- "top 5 X" -> limit 5, sort "value_desc". "worst / lowest" -> sort "value_asc".
- A year like 2026 -> "year": 2026. "last 6 months" -> "last_n_months": 6.
{prior}
QUESTION: {question}
"""


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _parse_llm(text: str) -> QuerySpec | None:
    if not text:
        return None
    match = _JSON_BLOCK.search(text)
    raw = match.group(1) if match else text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return QuerySpec.from_dict(data)


# --------------------------------------------------------------------------
# Deterministic fallback
# --------------------------------------------------------------------------

_METRIC_WORDS: list[tuple[str, str]] = []
for _key, _m in METRICS.items():
    _METRIC_WORDS.append((_key, _key.replace("_", " ")))
    for _syn in _m.synonyms:
        _METRIC_WORDS.append((_key, _syn))
# longest phrases first so "average order value" wins over "order"
_METRIC_WORDS.sort(key=lambda kv: len(kv[1]), reverse=True)

_DIM_WORDS: list[tuple[str, str]] = []
for _key, _d in DIMENSIONS.items():
    _DIM_WORDS.append((_key, _key.replace("_", " ")))
    for _syn in _d.synonyms:
        _DIM_WORDS.append((_key, _syn))
_DIM_WORDS.sort(key=lambda kv: len(kv[1]), reverse=True)

_STATUS_WORDS = {
    "completed": "COMPLETED", "complete": "COMPLETED",
    "pending": "PENDING", "cancelled": "CANCELLED", "canceled": "CANCELLED",
}


def _fallback_plan(
    question: str, prior_spec: dict | None
) -> tuple[QuerySpec, bool]:
    """Return (spec, confident). ``confident`` is True when the wording
    clearly names a metric and either a dimension or an explicit total —
    in that case we can skip the LLM entirely."""

    text = f" {question.lower()} "

    prior = QuerySpec.from_dict(prior_spec)

    metric = None
    for key, word in _METRIC_WORDS:
        if f" {word} " in text or text.strip().endswith(word):
            metric = key
            break
    metric_explicit = metric is not None
    if metric is None:
        metric = prior.metric if prior and prior.metric in METRICS else "revenue"

    # collect every dimension the wording hints at, then prefer one that is
    # actually valid for the metric we picked ("category" is ambiguous
    # between product_category and expense_category).
    dim_hits = [key for key, word in _DIM_WORDS if word in text]
    if re.search(r"\b(trend|over time|monthly|each month)\b", text):
        dim_hits.append("month")

    # "revenue by product/category/status" -> product_revenue
    if metric == "revenue" and any(
        d in ("product", "product_category", "order_status") for d in dim_hits
    ):
        metric = "product_revenue"

    allowed = set(METRICS[metric].allowed_dimensions)
    dimension = next((d for d in dim_hits if d in allowed), "")
    if not dimension and prior and prior.dimension in allowed and _is_refinement(text):
        dimension = prior.dimension

    spec = QuerySpec(metric=metric, dimension=dimension)

    year = re.search(r"\b(20\d{2})\b", text)
    if year:
        spec.year = int(year.group(1))
    months = re.search(r"last\s+(\d{1,2})\s+months?", text)
    if months:
        spec.last_n_months = int(months.group(1))

    topn = re.search(
        r"\b(?:top|bottom|worst|lowest|best|first|highest)\s+(\d{1,2})\b", text
    ) or re.search(
        r"\b(\d{1,2})\s+(?:products?|suppliers?|customers?|categories|items?)\b",
        text,
    )
    if topn:
        spec.limit = int(topn.group(1))
    if re.search(r"\b(worst|lowest|least|bottom|smallest|fewest)\b", text):
        spec.sort = "value_asc"

    for word, value in _STATUS_WORDS.items():
        if f" {word} " in text:
            spec.filters["order_status"] = value
            break

    refining = bool(prior and _is_refinement(text))

    # carry unchanged fields from the prior spec on a refinement
    if refining:
        spec.year = spec.year or prior.year
        spec.last_n_months = spec.last_n_months or prior.last_n_months
        if not spec.filters:
            spec.filters = dict(prior.filters)
        if metric == prior.metric and not spec.limit:
            spec.limit = prior.limit

    explicit_total = bool(
        re.search(r"\b(total|overall|how much|how many|sum of|count of)\b", text)
    )
    confident = (
        (metric_explicit or refining)
        and (bool(spec.dimension) or explicit_total or bool(spec.year))
    )
    return spec, confident


def _is_refinement(text: str) -> bool:
    return bool(
        re.search(
            r"\b(break|breakdown|split|instead|now|also|just|only|filter|"
            r"that|those|it|them|drill|group)\b",
            text,
        )
    )


# --------------------------------------------------------------------------
# Public
# --------------------------------------------------------------------------

def plan_query(question: str, prior_spec: dict | None = None) -> tuple[QuerySpec, bool]:
    """Return (validated spec, planner_degraded).

    Deterministic-first: when the wording clearly names a metric + dimension
    we skip the LLM entirely (fast, and works when Gemini is rate-limited).
    Only genuinely ambiguous questions pay the model round-trip.
    ``planner_degraded`` is True only when we wanted the LLM and it failed.
    """

    det_spec, confident = _fallback_plan(question, prior_spec)
    det_spec = _coerce(det_spec)

    if confident:
        validated = _validate_with_fallbacks(det_spec)
        if validated is not None:
            return validated, False

    if gemini.is_configured():
        try:
            text = gemini.generate_text(_prompt(question, prior_spec))
            spec = _parse_llm(text)
            if spec is not None:
                return validate_spec(_coerce(spec)), False
            logger.info("planner: LLM output did not parse, using deterministic")
        except SpecError as exc:
            logger.info("planner: LLM spec invalid (%s), using deterministic", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("planner: LLM unavailable (%s), using deterministic", exc)

    # Not confident and the LLM didn't (or couldn't) give us a valid spec —
    # this is a keyword guess, so flag it.
    validated = _validate_with_fallbacks(det_spec)
    return (validated or QuerySpec(metric="revenue")), True


def _validate_with_fallbacks(spec: QuerySpec) -> QuerySpec | None:
    for attempt in (spec, _drop_dimension(spec), QuerySpec(metric=spec.metric),
                    QuerySpec(metric="revenue")):
        try:
            return validate_spec(attempt)
        except SpecError:
            continue
    return None


def _drop_dimension(spec: QuerySpec) -> QuerySpec:
    return QuerySpec(
        metric=spec.metric, dimension="", year=spec.year,
        last_n_months=spec.last_n_months, filters={}, limit=None,
    )


def _coerce(spec: QuerySpec) -> QuerySpec:
    """Fix the one mismatch the model reliably makes."""
    if spec.metric == "revenue" and spec.dimension in (
        "product", "product_category", "order_status",
    ):
        spec.metric = "product_revenue"
    return spec
