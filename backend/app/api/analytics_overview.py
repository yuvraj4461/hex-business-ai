"""GET /analytics/overview — a multi-section performance dashboard.

Covers the business-analysis areas the seeded/ingested data actually
supports: financial, sales, customer, product and operational/supply-chain.
Grouped and trend figures reuse the Ask-Your-Data query engine
(``app.analytics.executor``); cohort and status metrics that the engine
can't express are computed with direct, org-scoped SQLAlchemy here.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.executor import run_spec
from app.analytics.semantic import QuerySpec
from app.database.connection import get_db
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.shipment import Shipment
from app.models.supplier import Supplier
from app.models.user import User
from app.security.dependencies import require_permission

router = APIRouter(prefix="/analytics", tags=["Analytics"])

_CLOSED_PO = ("CLOSED", "CANCELLED", "RECEIVED", "COMPLETE", "COMPLETED")


def _rows(db: Session, org_id: int, **spec_kwargs) -> list[dict]:
    return run_spec(db, org_id, QuerySpec(**spec_kwargs))["rows"]


def _total(db: Session, org_id: int, metric: str) -> float:
    rows = _rows(db, org_id, metric=metric)
    return float(rows[0]["value"]) if rows else 0.0


def _kpi(label, value, unit="number", delta=None, delta_tone=None) -> dict:
    return {
        "label": label,
        "value": round(value, 2) if isinstance(value, (int, float)) else value,
        "unit": unit,
        "delta": delta,
        "delta_tone": delta_tone,
    }


@router.get("/overview")
def analytics_overview(
    current_user: User = Depends(require_permission("view_analytics")),
    db: Session = Depends(get_db),
):
    org = current_user.organization_id
    now = datetime.utcnow()

    # ---------------------------------------------------------------
    # Financial
    # ---------------------------------------------------------------
    revenue = _total(db, org, "revenue")
    expenses = _total(db, org, "expenses")
    profit = revenue - expenses
    margin = (profit / revenue * 100) if revenue else 0.0
    expense_ratio = (expenses / revenue * 100) if revenue else 0.0

    rev_by_month = {r["label"]: r["value"]
                    for r in _rows(db, org, metric="revenue", dimension="month")}
    exp_by_month = {r["label"]: r["value"]
                    for r in _rows(db, org, metric="expenses", dimension="month")}
    months = sorted(set(rev_by_month) | set(exp_by_month))
    pnl_trend = [
        {
            "label": m,
            "revenue": round(rev_by_month.get(m, 0), 2),
            "expenses": round(exp_by_month.get(m, 0), 2),
            "profit": round(rev_by_month.get(m, 0) - exp_by_month.get(m, 0), 2),
        }
        for m in months
    ]
    avg_monthly_rev = (revenue / len(months)) if months else 0.0

    financial = {
        "kpis": [
            _kpi("Revenue", revenue, "INR"),
            _kpi("Expenses", expenses, "INR"),
            _kpi("Profit", profit, "INR",
                 delta=f"{margin:.1f}% net margin",
                 delta_tone="stable" if margin >= 0 else "critical"),
            _kpi("Expense ratio", round(expense_ratio, 1), "percent"),
            _kpi("Avg monthly revenue", avg_monthly_rev, "INR"),
        ],
        "pnl_trend": pnl_trend,
        "expense_breakdown": _rows(
            db, org, metric="expenses", dimension="expense_category"
        ),
    }

    # ---------------------------------------------------------------
    # Sales
    # ---------------------------------------------------------------
    status_counts = dict(
        db.query(Order.status, func.count(Order.id))
        .filter(Order.organization_id == org)
        .group_by(Order.status)
        .all()
    )
    total_orders_all = sum(status_counts.values())
    completed = status_counts.get("COMPLETED", 0)
    cancelled = status_counts.get("CANCELLED", 0)
    completion_rate = (completed / total_orders_all * 100) if total_orders_all else 0.0
    cancellation_rate = (cancelled / total_orders_all * 100) if total_orders_all else 0.0

    orders = _total(db, org, "order_count")
    aov = _total(db, org, "avg_order_value")
    units = _total(db, org, "units_sold")

    sales = {
        "kpis": [
            _kpi("Orders (net of cancelled)", orders, "count"),
            _kpi("Average order value", aov, "INR"),
            _kpi("Units sold", units, "count"),
            _kpi("Completion rate", round(completion_rate, 1), "percent",
                 delta_tone="stable" if completion_rate >= 70 else "elevated"),
            _kpi("Cancellation rate", round(cancellation_rate, 1), "percent",
                 delta_tone="critical" if cancellation_rate >= 15 else "stable"),
        ],
        "sales_trend": _rows(db, org, metric="revenue", dimension="month"),
        "by_category": _rows(
            db, org, metric="product_revenue", dimension="product_category"
        ),
        "top_products": _rows(
            db, org, metric="product_revenue", dimension="product", limit=8
        ),
        "order_status": [
            {"label": s.title(), "value": c} for s, c in status_counts.items()
        ],
    }

    # ---------------------------------------------------------------
    # Customers
    # ---------------------------------------------------------------
    per_customer = (
        db.query(
            Order.customer_id.label("cid"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total_amount), 0).label("spend"),
            func.min(Order.order_date).label("first_order"),
        )
        .filter(Order.organization_id == org, Order.status != "CANCELLED",
                Order.customer_id.isnot(None))
        .group_by(Order.customer_id)
        .all()
    )
    total_customers = db.query(func.count(Customer.id)).filter(
        Customer.organization_id == org
    ).scalar() or 0
    active = len(per_customer)
    repeat = sum(1 for c in per_customer if c.orders > 1)
    repeat_rate = (repeat / active * 100) if active else 0.0
    cutoff = now - timedelta(days=90)
    new_recent = sum(1 for c in per_customer if c.first_order and c.first_order >= cutoff)
    returning = active - new_recent
    avg_rev_per_customer = (
        sum(float(c.spend) for c in per_customer) / active if active else 0.0
    )

    id_to_name = dict(
        db.query(Customer.id, Customer.name)
        .filter(Customer.organization_id == org)
        .all()
    )
    top_customers = sorted(
        per_customer, key=lambda c: float(c.spend), reverse=True
    )[:8]

    customers = {
        "kpis": [
            _kpi("Total customers", total_customers, "count"),
            _kpi("Active customers", active, "count"),
            _kpi("Repeat rate", round(repeat_rate, 1), "percent",
                 delta_tone="stable" if repeat_rate >= 30 else "elevated"),
            _kpi("Avg revenue / customer", avg_rev_per_customer, "INR"),
            _kpi("New (last 90 days)", new_recent, "count"),
        ],
        "new_vs_returning": [
            {"label": "New (90d)", "value": new_recent},
            {"label": "Returning", "value": max(returning, 0)},
        ],
        "top_customers": [
            {"label": id_to_name.get(c.cid, f"Customer {c.cid}"),
             "value": round(float(c.spend), 2)}
            for c in top_customers
        ],
    }

    # ---------------------------------------------------------------
    # Products
    # ---------------------------------------------------------------
    total_products = db.query(func.count(Product.id)).filter(
        Product.organization_id == org
    ).scalar() or 0
    avg_price = db.query(func.coalesce(func.avg(Product.unit_price), 0)).filter(
        Product.organization_id == org
    ).scalar() or 0
    revenue_by_product = _rows(
        db, org, metric="product_revenue", dimension="product", limit=10
    )
    best_seller = revenue_by_product[0]["label"] if revenue_by_product else "—"

    products = {
        "kpis": [
            _kpi("Products", total_products, "count"),
            _kpi("Best seller", best_seller, "text"),
            _kpi("Avg unit price", float(avg_price), "INR"),
        ],
        "revenue_by_product": revenue_by_product,
        "units_by_category": _rows(
            db, org, metric="units_sold", dimension="product_category"
        ),
    }

    # ---------------------------------------------------------------
    # Operations / supply chain
    # ---------------------------------------------------------------
    inv_units = _total(db, org, "inventory_on_hand")
    inv_value = (
        db.query(
            func.coalesce(
                func.sum(Inventory.quantity * Product.unit_price), 0
            )
        )
        .join(Product, Inventory.product_id == Product.id)
        .filter(Inventory.organization_id == org)
        .scalar()
        or 0
    )
    low_stock = (
        db.query(func.count(Inventory.id))
        .filter(
            Inventory.organization_id == org,
            Inventory.quantity < Inventory.reorder_level,
        )
        .scalar()
        or 0
    )
    supplier_count = db.query(func.count(Supplier.id)).filter(
        Supplier.organization_id == org
    ).scalar() or 0
    avg_lead = _total(db, org, "supplier_lead_time")
    open_pos = (
        db.query(func.count(PurchaseOrder.id))
        .filter(
            PurchaseOrder.organization_id == org,
            func.upper(PurchaseOrder.status).notin_(_CLOSED_PO),
        )
        .scalar()
        or 0
    )
    in_transit = (
        db.query(func.count(Shipment.id))
        .filter(
            Shipment.organization_id == org,
            Shipment.status == "IN_TRANSIT",
        )
        .scalar()
        or 0
    )
    inv_by_cat = (
        db.query(
            func.coalesce(Product.category, "Uncategorised"),
            func.coalesce(func.sum(Inventory.quantity), 0),
        )
        .join(Product, Inventory.product_id == Product.id)
        .filter(Inventory.organization_id == org)
        .group_by(Product.category)
        .all()
    )

    operations = {
        "kpis": [
            _kpi("Inventory on hand", inv_units, "count"),
            _kpi("Inventory value", float(inv_value), "INR"),
            _kpi("Low-stock SKUs", low_stock, "count",
                 delta_tone="elevated" if low_stock else "stable"),
            _kpi("Suppliers", supplier_count, "count"),
            _kpi("Avg supplier lead time", round(avg_lead, 1), "days"),
            _kpi("Open purchase orders", open_pos, "count"),
            _kpi("Shipments in transit", in_transit, "count"),
        ],
        "inventory_by_category": [
            {"label": name, "value": int(qty)} for name, qty in inv_by_cat
        ],
        "lead_time_by_supplier": _rows(
            db, org, metric="supplier_lead_time", dimension="supplier", limit=10
        ),
    }

    return {
        "organization_id": org,
        "generated_at": now.isoformat(),
        "financial": financial,
        "sales": sales,
        "customers": customers,
        "products": products,
        "operations": operations,
    }
