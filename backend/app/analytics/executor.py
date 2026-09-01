"""Execute a validated :class:`QuerySpec` against the org's data.

Every query is built here from fixed SQLAlchemy expressions — the spec only
chooses *which* of them to assemble — and is always filtered by
``organization_id``. Results come back as ``{columns, rows, chart}`` ready
for the frontend.
"""

from __future__ import annotations

from datetime import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.semantic import (
    DIMENSIONS,
    METRICS,
    TIME_DIMENSIONS,
    QuerySpec,
)
from app.models.customer import Customer
from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.transaction import Transaction

_DEFAULT_CATEGORY_LIMIT = 12


# --------------------------------------------------------------------------
# Per-metric assembly
# --------------------------------------------------------------------------

def _time_bucket(col, dim: str):
    trunc = func.date_trunc(dim, col)
    if dim == "month":
        return func.to_char(trunc, "YYYY-MM")
    if dim == "quarter":
        return func.to_char(trunc, 'YYYY"-Q"Q')
    return func.to_char(trunc, "YYYY")  # year


def _metric_plan(db: Session, org_id: int, spec: QuerySpec):
    """Return (query, value_is_currency, chart_unit) for a non-profit metric.

    The query already selects ``label`` (unless no dimension) and ``value``,
    is grouped/ordered/limited, and scoped to the org.
    """

    metric = METRICS[spec.metric]
    dim = spec.dimension

    # ---- base per metric -------------------------------------------------
    if spec.metric == "revenue":
        base = db.query(Transaction).filter(
            Transaction.organization_id == org_id,
            Transaction.transaction_type == "REVENUE",
        )
        value = func.coalesce(func.sum(Transaction.amount), 0)
        date_col = Transaction.transaction_date
        dim_cols: dict = {}
        filterable: dict = {}

    elif spec.metric == "expenses":
        base = db.query(Expense).filter(
            Expense.organization_id == org_id,
        )
        value = func.coalesce(func.sum(Expense.amount), 0)
        date_col = Expense.expense_date
        dim_cols = {"expense_category": Expense.category}
        filterable = {"expense_category": Expense.category}

    elif spec.metric == "order_count":
        base = db.query(Order).filter(
            Order.organization_id == org_id,
            Order.status != "CANCELLED",
        )
        value = func.count(func.distinct(Order.id))
        date_col = Order.order_date
        dim_cols = {"order_status": Order.status}
        filterable = {"order_status": Order.status}
        if dim == "customer":
            base = base.join(Customer, Order.customer_id == Customer.id)
            dim_cols["customer"] = Customer.name

    elif spec.metric == "avg_order_value":
        base = db.query(Order).filter(
            Order.organization_id == org_id,
            Order.status != "CANCELLED",
        )
        value = func.coalesce(func.avg(Order.total_amount), 0)
        date_col = Order.order_date
        dim_cols = {"order_status": Order.status}
        filterable = {"order_status": Order.status}
        if dim == "customer":
            base = base.join(Customer, Order.customer_id == Customer.id)
            dim_cols["customer"] = Customer.name

    elif spec.metric in ("units_sold", "product_revenue"):
        base = (
            db.query(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .join(Product, OrderItem.product_id == Product.id)
            .filter(
                OrderItem.organization_id == org_id,
                Order.status != "CANCELLED",
            )
        )
        if spec.metric == "units_sold":
            value = func.coalesce(func.sum(OrderItem.quantity), 0)
        else:
            value = func.coalesce(func.sum(OrderItem.line_total), 0)
        date_col = Order.order_date
        dim_cols = {
            "product": Product.name,
            "product_category": Product.category,
            "order_status": Order.status,
        }
        filterable = {
            "product_category": Product.category,
            "order_status": Order.status,
        }

    elif spec.metric == "inventory_on_hand":
        base = (
            db.query(Inventory)
            .join(Product, Inventory.product_id == Product.id)
            .filter(Inventory.organization_id == org_id)
        )
        value = func.coalesce(func.sum(Inventory.quantity), 0)
        date_col = None
        dim_cols = {
            "product": Product.name,
            "product_category": Product.category,
        }
        filterable = {"product_category": Product.category}

    elif spec.metric == "supplier_lead_time":
        base = db.query(Supplier).filter(
            Supplier.organization_id == org_id,
            Supplier.lead_time_days.isnot(None),
        )
        value = func.coalesce(func.avg(Supplier.lead_time_days), 0)
        date_col = None
        dim_cols = {
            "supplier": Supplier.name,
            "supplier_country": Supplier.country,
            "supplier_category": Supplier.category,
        }
        filterable = {
            "supplier_country": Supplier.country,
            "supplier_category": Supplier.category,
        }

    else:  # pragma: no cover - guarded by validate_spec
        raise ValueError(f"no executor for metric {spec.metric!r}")

    # ---- time filters --------------------------------------------------
    if date_col is not None:
        if spec.year:
            base = base.filter(func.extract("year", date_col) == spec.year)
        elif spec.last_n_months:
            cutoff = datetime.utcnow() - relativedelta(months=spec.last_n_months)
            base = base.filter(date_col >= cutoff)

    # ---- equality filters (only those native to this metric) ----------
    for fkey, fval in spec.filters.items():
        col = filterable.get(fkey)
        if col is not None and fval:
            base = base.filter(func.lower(col) == str(fval).lower())

    is_currency = metric.unit == "INR"

    # ---- no dimension: a single total --------------------------------
    if not dim:
        return base.with_entities(value.label("value")), is_currency, metric.unit

    # ---- grouped ----------------------------------------------------------
    if dim in TIME_DIMENSIONS:
        label_expr = _time_bucket(date_col, dim)
    else:
        label_expr = dim_cols.get(dim)
        if label_expr is None:  # pragma: no cover - guarded by validate_spec
            raise ValueError(f"metric {spec.metric!r} has no dimension {dim!r}")

    q = base.with_entities(label_expr.label("label"), value.label("value"))
    q = q.group_by(label_expr)

    if spec.sort == "chrono":
        q = q.order_by(label_expr.asc())
    elif spec.sort == "value_asc":
        q = q.order_by(value.asc())
    else:
        q = q.order_by(value.desc())

    limit = spec.limit or (
        None if dim in TIME_DIMENSIONS else _DEFAULT_CATEGORY_LIMIT
    )
    if limit:
        q = q.limit(limit)

    return q, is_currency, metric.unit


# --------------------------------------------------------------------------
# Public entrypoint
# --------------------------------------------------------------------------

def run_spec(db: Session, organization_id: int, spec: QuerySpec) -> dict:
    metric = METRICS[spec.metric]
    dim = spec.dimension

    if spec.metric == "profit":
        return _run_profit(db, organization_id, spec)

    q, is_currency, unit = _metric_plan(db, organization_id, spec)
    rows_raw = q.all()

    if not dim:
        total = float(rows_raw[0].value) if rows_raw else 0.0
        return _result(
            columns=[("label", metric.label, "text"),
                     ("value", metric.label, "currency" if is_currency else "number")],
            rows=[{"label": metric.label, "value": round(total, 2)}],
            chart={"type": "stat", "x": "label", "y": "value", "unit": unit},
        )

    rows = [
        {"label": _clean_label(r.label), "value": round(float(r.value or 0), 2)}
        for r in rows_raw
        if r.label is not None
    ]
    chart_type = "line" if dim in TIME_DIMENSIONS else "bar"
    return _result(
        columns=[
            ("label", DIMENSIONS[dim].label, "text"),
            ("value", metric.label, "currency" if is_currency else "number"),
        ],
        rows=rows,
        chart={"type": chart_type, "x": "label", "y": "value", "unit": unit},
    )


def _run_profit(db: Session, org_id: int, spec: QuerySpec) -> dict:
    """profit = revenue - expenses, per time bucket or as a single total."""

    rev_spec = QuerySpec(metric="revenue", dimension=spec.dimension,
                         year=spec.year, last_n_months=spec.last_n_months,
                         sort=spec.sort)
    exp_spec = QuerySpec(metric="expenses", dimension=spec.dimension,
                         year=spec.year, last_n_months=spec.last_n_months,
                         sort=spec.sort)

    rev_q, _, _ = _metric_plan(db, org_id, rev_spec)
    exp_q, _, _ = _metric_plan(db, org_id, exp_spec)

    if not spec.dimension:
        rev = float(rev_q.all()[0].value or 0)
        exp = float(exp_q.all()[0].value or 0)
        return _result(
            columns=[("label", "Profit", "text"), ("value", "Profit", "currency")],
            rows=[{"label": "Profit", "value": round(rev - exp, 2)}],
            chart={"type": "stat", "x": "label", "y": "value", "unit": "INR"},
        )

    rev_by = {r.label: float(r.value or 0) for r in rev_q.all()}
    exp_by = {r.label: float(r.value or 0) for r in exp_q.all()}
    labels = sorted(set(rev_by) | set(exp_by))
    rows = [
        {"label": _clean_label(lbl),
         "value": round(rev_by.get(lbl, 0) - exp_by.get(lbl, 0), 2)}
        for lbl in labels
    ]
    return _result(
        columns=[("label", DIMENSIONS[spec.dimension].label, "text"),
                 ("value", "Profit", "currency")],
        rows=rows,
        chart={"type": "line", "x": "label", "y": "value", "unit": "INR"},
    )


def _result(*, columns, rows, chart) -> dict:
    return {
        "columns": [{"key": k, "label": lbl, "type": t} for k, lbl, t in columns],
        "rows": rows,
        "chart": chart,
        "row_count": len(rows),
    }


def _clean_label(value) -> str:
    if value is None:
        return "—"
    return str(value)
