"""The semantic layer: the small, fixed vocabulary of things the user is
allowed to ask for. The planner may only emit names that appear here, and
the executor builds every query from these definitions.

Kept deliberately narrow to what the seeded data actually supports
(see ``app/services/demo_seed.py``): time, product, product category,
supplier, supplier country, expense category, order status.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    unit: str  # "INR" | "count" | "days"
    # Dimensions this metric can be broken down by. "" is always allowed
    # (a single total).
    allowed_dimensions: tuple[str, ...]
    aggregate: str = "sum"  # sum | avg | count
    synonyms: tuple[str, ...] = field(default_factory=tuple)


_TIME = ("month", "quarter", "year")

METRICS: dict[str, Metric] = {
    "revenue": Metric(
        "revenue", "Revenue", "INR",
        allowed_dimensions=_TIME + ("product", "product_category", "order_status"),
        synonyms=("sales", "turnover", "income", "earnings"),
    ),
    "expenses": Metric(
        "expenses", "Expenses", "INR",
        allowed_dimensions=_TIME + ("expense_category",),
        synonyms=("cost", "costs", "spend", "spending", "outgoings"),
    ),
    "profit": Metric(
        "profit", "Profit", "INR",
        allowed_dimensions=_TIME,
        synonyms=("margin", "net income", "bottom line"),
    ),
    "order_count": Metric(
        "order_count", "Orders", "count",
        allowed_dimensions=_TIME + ("order_status", "customer"),
        aggregate="count",
        synonyms=("orders", "number of orders", "order volume", "deals"),
    ),
    "units_sold": Metric(
        "units_sold", "Units sold", "count",
        allowed_dimensions=_TIME + ("product", "product_category", "order_status"),
        synonyms=("units", "quantity sold", "volume", "pieces"),
    ),
    "avg_order_value": Metric(
        "avg_order_value", "Average order value", "INR",
        allowed_dimensions=_TIME + ("order_status", "customer"),
        aggregate="avg",
        synonyms=("aov", "average order", "average deal size", "basket size"),
    ),
    "product_revenue": Metric(
        "product_revenue", "Revenue", "INR",
        allowed_dimensions=("product", "product_category") + _TIME + ("order_status",),
        synonyms=("product sales", "revenue by product", "line revenue"),
    ),
    "inventory_on_hand": Metric(
        "inventory_on_hand", "Inventory on hand", "count",
        allowed_dimensions=("product", "product_category"),
        synonyms=("inventory", "stock", "stock on hand", "units in stock"),
    ),
    "supplier_lead_time": Metric(
        "supplier_lead_time", "Average lead time", "days",
        allowed_dimensions=("supplier", "supplier_country", "supplier_category"),
        aggregate="avg",
        synonyms=("lead time", "lead times", "supplier delay", "delivery time"),
    ),
}


# --------------------------------------------------------------------------
# Dimensions
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    kind: str  # "time" | "category"
    synonyms: tuple[str, ...] = field(default_factory=tuple)


DIMENSIONS: dict[str, Dimension] = {
    "month": Dimension("month", "Month", "time",
                       synonyms=("monthly", "by month", "over time", "trend")),
    "quarter": Dimension("quarter", "Quarter", "time",
                         synonyms=("quarterly", "by quarter")),
    "year": Dimension("year", "Year", "time",
                      synonyms=("yearly", "annual", "by year")),
    "product": Dimension("product", "Product", "category",
                         synonyms=("products", "by product", "per product", "item")),
    "product_category": Dimension("product_category", "Product category", "category",
                                  synonyms=("category", "categories", "product type",
                                            "by category")),
    "supplier": Dimension("supplier", "Supplier", "category",
                          synonyms=("suppliers", "vendor", "vendors", "by supplier")),
    "supplier_country": Dimension("supplier_country", "Supplier country", "category",
                                  synonyms=("country", "countries", "by country",
                                            "geography", "region")),
    "supplier_category": Dimension("supplier_category", "Supplier category", "category",
                                   synonyms=("supplier type",)),
    "expense_category": Dimension("expense_category", "Expense category", "category",
                                  synonyms=("expense type", "cost category",
                                            "spend category", "by category")),
    "order_status": Dimension("order_status", "Order status", "category",
                              synonyms=("status", "by status")),
    "customer": Dimension("customer", "Customer", "category",
                          synonyms=("customers", "client", "clients", "by customer")),
}

TIME_DIMENSIONS = {k for k, d in DIMENSIONS.items() if d.kind == "time"}


# --------------------------------------------------------------------------
# Query spec
# --------------------------------------------------------------------------

@dataclass
class QuerySpec:
    metric: str
    dimension: str = ""          # "" => a single total
    year: int | None = None
    last_n_months: int | None = None
    filters: dict[str, str] = field(default_factory=dict)  # dimension_key -> value
    limit: int | None = None
    sort: str = "value_desc"     # "value_desc" | "value_asc" | "chrono"

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "dimension": self.dimension,
            "year": self.year,
            "last_n_months": self.last_n_months,
            "filters": dict(self.filters),
            "limit": self.limit,
            "sort": self.sort,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "QuerySpec | None":
        if not data or not isinstance(data, dict):
            return None
        try:
            return cls(
                metric=str(data.get("metric") or ""),
                dimension=str(data.get("dimension") or ""),
                year=_as_int(data.get("year")),
                last_n_months=_as_int(data.get("last_n_months")),
                filters={
                    str(k): str(v)
                    for k, v in (data.get("filters") or {}).items()
                },
                limit=_as_int(data.get("limit")),
                sort=str(data.get("sort") or "value_desc"),
            )
        except Exception:  # noqa: BLE001
            return None


class SpecError(ValueError):
    """The spec references something outside the semantic layer."""


def validate_spec(spec: QuerySpec) -> QuerySpec:
    """Raise ``SpecError`` unless every field is in the vocabulary and the
    dimension is legal for the metric. Returns the (lightly normalised) spec."""

    metric = METRICS.get(spec.metric)
    if metric is None:
        raise SpecError(f"unknown metric {spec.metric!r}")

    dim = spec.dimension or ""
    if dim:
        if dim not in DIMENSIONS:
            raise SpecError(f"unknown dimension {dim!r}")
        if dim not in metric.allowed_dimensions:
            raise SpecError(
                f"metric {spec.metric!r} cannot be broken down by {dim!r}"
            )

    for fkey in spec.filters:
        if fkey not in DIMENSIONS:
            raise SpecError(f"unknown filter dimension {fkey!r}")

    if spec.limit is not None:
        spec.limit = max(1, min(int(spec.limit), 100))

    if dim and DIMENSIONS[dim].kind == "time":
        spec.sort = "chrono"
    elif spec.sort not in ("value_desc", "value_asc", "chrono"):
        spec.sort = "value_desc"

    if spec.last_n_months is not None:
        spec.last_n_months = max(1, min(int(spec.last_n_months), 60))

    return spec


def spec_label(spec: QuerySpec) -> str:
    """Human badge, e.g. ``Revenue · by month · 2026``."""

    metric = METRICS.get(spec.metric)
    parts = [metric.label if metric else spec.metric]

    if spec.dimension:
        d = DIMENSIONS.get(spec.dimension)
        parts.append(f"by {d.label.lower() if d else spec.dimension}")

    if spec.limit:
        parts.append(f"top {spec.limit}")
    if spec.year:
        parts.append(str(spec.year))
    elif spec.last_n_months:
        parts.append(f"last {spec.last_n_months} months")

    for k, v in spec.filters.items():
        parts.append(f"{v}")

    return " · ".join(parts)


def _as_int(value) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
