"""Run the formula library against an organization's real ERP data and
return a battery of financial metrics — each with the value, the formula
used and the inputs, so the number is auditable and the LLM never has to
compute anything.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.executor import run_spec
from app.analytics.semantic import QuerySpec
from app.finance import formulas as F
from app.models.customer import Customer
from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.product import Product

# Expense categories treated as fixed overhead for break-even.
_FIXED_CATEGORIES = {
    "rent", "utilities", "salaries", "payroll", "insurance", "software",
    "subscriptions", "warehousing", "lease", "office",
}
# Categories that count as customer-acquisition spend.
_ACQUISITION_CATEGORIES = {"marketing", "sales", "advertising", "ads", "promotion"}


def _metric(label, value, unit, formula, inputs, note=None) -> dict:
    if value is None or (isinstance(value, float) and value != value):
        return {
            "label": label, "value": None, "unit": unit,
            "formula": formula, "inputs": inputs,
            "note": note or "not computable from available data",
        }
    if value == float("inf"):
        value = None
        note = note or "no burn — runway is effectively unlimited"
    return {
        "label": label,
        "value": round(value, 2) if isinstance(value, (int, float)) else value,
        "unit": unit, "formula": formula, "inputs": inputs, "note": note,
    }


def _try(label, unit, formula, fn, inputs):
    try:
        return _metric(label, fn(), unit, formula, inputs)
    except F.FinanceError as exc:
        return _metric(label, None, unit, formula, inputs, note=str(exc))
    except Exception as exc:  # noqa: BLE001
        return _metric(label, None, unit, formula, inputs, note=f"error: {exc}")


def company_finance(db: Session, organization_id: int) -> dict:
    org = organization_id
    now = datetime.utcnow()

    # ---- pull real data ------------------------------------------------
    rev_rows = run_spec(
        db, org, QuerySpec(metric="revenue", dimension="month")
    )["rows"]
    exp_rows = run_spec(
        db, org, QuerySpec(metric="expenses", dimension="month")
    )["rows"]
    rev_by_month = {r["label"]: r["value"] for r in rev_rows}
    exp_by_month = {r["label"]: r["value"] for r in exp_rows}
    months = sorted(set(rev_by_month) | set(exp_by_month))
    revenue_series = [rev_by_month.get(m, 0.0) for m in months]
    expense_series = [exp_by_month.get(m, 0.0) for m in months]
    net_series = [r - e for r, e in zip(revenue_series, expense_series)]

    revenue = sum(revenue_series)
    expenses = sum(expense_series)
    profit = revenue - expenses

    orders = run_spec(db, org, QuerySpec(metric="order_count"))["rows"]
    order_count = orders[0]["value"] if orders else 0
    aov = run_spec(db, org, QuerySpec(metric="avg_order_value"))["rows"]
    avg_order_value = aov[0]["value"] if aov else 0

    # customers
    per_customer = (
        db.query(
            Order.customer_id,
            func.count(Order.id).label("orders"),
            func.min(Order.order_date).label("first_order"),
        )
        .filter(Order.organization_id == org, Order.status != "CANCELLED",
                Order.customer_id.isnot(None))
        .group_by(Order.customer_id)
        .all()
    )
    active_customers = len(per_customer)
    orders_per_customer = (
        sum(c.orders for c in per_customer) / active_customers
        if active_customers else 0
    )
    cutoff = now - timedelta(days=90)
    new_customers_90d = sum(
        1 for c in per_customer if c.first_order and c.first_order >= cutoff
    )

    # expense split
    exp_by_cat = dict(
        db.query(func.lower(Expense.category), func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.organization_id == org)
        .group_by(func.lower(Expense.category))
        .all()
    )
    fixed_costs = sum(v for k, v in exp_by_cat.items() if k in _FIXED_CATEGORIES)
    acquisition_spend = sum(
        v for k, v in exp_by_cat.items() if k in _ACQUISITION_CATEGORIES
    )
    months_n = max(len(months), 1)
    monthly_fixed = fixed_costs / months_n

    inventory_value = float(
        db.query(func.coalesce(func.sum(Inventory.quantity * Product.unit_price), 0))
        .join(Product, Inventory.product_id == Product.id)
        .filter(Inventory.organization_id == org)
        .scalar()
        or 0
    )

    # cash proxy: cumulative net cash flow (we have no balance sheet)
    cash_proxy = 0.0
    running = 0.0
    for n in net_series:
        running += n
        cash_proxy = running
    burning_months = [-n for n in net_series if n < 0]
    avg_monthly_burn = (sum(burning_months) / len(burning_months)
                        if burning_months else 0.0)

    op_margin_pct = (profit / revenue * 100) if revenue else 0.0
    monthly_margin_per_customer = (
        (avg_order_value * orders_per_customer / 12) * (op_margin_pct / 100)
        if active_customers else 0.0
    )

    returns = F.returns_series(revenue_series) if len(revenue_series) > 1 else []

    # ---- battery -----------------------------------------------------
    profitability = [
        _metric("Operating margin", op_margin_pct, "percent",
                "operating_income / revenue x 100",
                {"operating_income": round(profit, 2), "revenue": round(revenue, 2)}),
        _try("Expense ratio", "percent", "expenses / revenue x 100",
             lambda: expenses / F._nonzero(revenue, "revenue") * 100,
             {"expenses": round(expenses, 2), "revenue": round(revenue, 2)}),
        _try("Return on spend (ROI)", "percent", "(revenue - expenses) / expenses x 100",
             lambda: F.roi(revenue, expenses),
             {"gain": round(revenue, 2), "cost": round(expenses, 2)}),
        _metric("Profit", profit, "currency", "revenue - expenses",
                {"revenue": round(revenue, 2), "expenses": round(expenses, 2)}),
    ]

    growth = []
    if len(revenue_series) >= 2:
        growth.append(_try(
            "Revenue MoM growth", "percent", "(current - previous) / |previous| x 100",
            lambda: F.growth_rate(revenue_series[-2], revenue_series[-1]),
            {"previous": round(revenue_series[-2], 2),
             "current": round(revenue_series[-1], 2)}))
        growth.append(_try(
            "Average monthly growth", "percent",
            "geometric mean of period growth",
            lambda: F.average_growth(revenue_series),
            {"months": len(revenue_series)}))
        growth.append(_try(
            "Next-month revenue forecast", "currency",
            "least-squares linear trend, 1 period ahead",
            lambda: F.linear_forecast(revenue_series, 1),
            {"series_len": len(revenue_series)}))
    if len(revenue_series) >= 13:
        growth.append(_try(
            "Revenue YoY growth", "percent", "(current - 12 months ago) / prior x 100",
            lambda: F.growth_rate(revenue_series[-13], revenue_series[-1]),
            {"previous": round(revenue_series[-13], 2),
             "current": round(revenue_series[-1], 2)}))
    if len(revenue_series) >= 2 and revenue_series[0] > 0:
        yrs = len(revenue_series) / 12
        growth.append(_try(
            "Revenue CAGR (annualised)", "percent",
            "(ending / beginning)^(1/years) - 1",
            lambda: F.cagr(revenue_series[0], revenue_series[-1], yrs),
            {"beginning": round(revenue_series[0], 2),
             "ending": round(revenue_series[-1], 2), "years": round(yrs, 2)}))

    cash = [
        _metric("Cash position (proxy)", cash_proxy, "currency",
                "cumulative (revenue - expenses) — no balance sheet available",
                {"months": months_n},
                note="proxy: HEX has no asset/liability data"),
        _metric("Average monthly burn", avg_monthly_burn, "currency",
                "mean of months with negative net cash flow",
                {"burning_months": len(burning_months)}),
        _try("Runway", "months", "cash position / monthly burn",
             lambda: F.runway_months(cash_proxy, avg_monthly_burn),
             {"cash": round(cash_proxy, 2), "burn": round(avg_monthly_burn, 2)}),
        _try("Free cash flow (period)", "currency", "sum of monthly net cash flow",
             lambda: sum(net_series), {"months": months_n}),
    ]

    risk = []
    if len(revenue_series) >= 2:
        risk.append(_try(
            "Revenue volatility (CoV)", "percent", "stdev(revenue) / mean(revenue) x 100",
            lambda: F.coefficient_of_variation(revenue_series),
            {"months": len(revenue_series)}))
        risk.append(_try(
            "Revenue std deviation", "currency", "sample standard deviation",
            lambda: F.standard_deviation(revenue_series),
            {"months": len(revenue_series)}))
        risk.append(_try(
            "Max revenue drawdown", "percent", "largest peak-to-trough decline",
            lambda: F.max_drawdown(revenue_series), {"months": len(revenue_series)}))
    if len(returns) >= 2:
        risk.append(_try(
            "Revenue return Sharpe", "ratio",
            "(mean monthly return - 0) / stdev(returns)",
            lambda: F.sharpe_ratio(returns, 0.0), {"observations": len(returns)}))

    unit_econ = []
    if new_customers_90d and acquisition_spend:
        cac_val = acquisition_spend / new_customers_90d
        unit_econ.append(_metric(
            "Customer acquisition cost", cac_val, "currency",
            "acquisition spend / new customers (90d)",
            {"spend": round(acquisition_spend, 2), "new_customers": new_customers_90d}))
        ltv_val = avg_order_value * orders_per_customer * (op_margin_pct / 100)
        unit_econ.append(_metric(
            "Customer lifetime value", ltv_val, "currency",
            "AOV x orders per customer x operating margin",
            {"aov": round(avg_order_value, 2),
             "orders_per_customer": round(orders_per_customer, 2),
             "margin_pct": round(op_margin_pct, 2)}))
        unit_econ.append(_try(
            "LTV : CAC", "ratio", "lifetime value / acquisition cost",
            lambda: F.ltv_cac_ratio(ltv_val, cac_val),
            {"ltv": round(ltv_val, 2), "cac": round(cac_val, 2)}))
        if monthly_margin_per_customer > 0:
            unit_econ.append(_try(
                "CAC payback", "months", "CAC / monthly margin per customer",
                lambda: F.cac_payback_months(cac_val, monthly_margin_per_customer),
                {"cac": round(cac_val, 2),
                 "monthly_margin": round(monthly_margin_per_customer, 2)}))
    else:
        unit_econ.append(_metric(
            "Customer acquisition cost", None, "currency",
            "acquisition spend / new customers",
            {}, note="no expense category tagged marketing/sales/advertising"))

    break_even = []
    cmr = op_margin_pct  # contribution margin ratio proxy
    monthly_revenue = revenue / months_n if months_n else 0.0
    be_rev = _try(
        "Break-even revenue (monthly)", "currency",
        "monthly fixed costs / contribution margin ratio",
        lambda: F.break_even_revenue(monthly_fixed, cmr),
        {"monthly_fixed": round(monthly_fixed, 2), "cm_ratio_pct": round(cmr, 2)})
    break_even.append(be_rev)
    if be_rev["value"] is not None:
        break_even.append(_metric(
            "Current monthly revenue vs break-even",
            monthly_revenue - be_rev["value"], "currency",
            "average monthly revenue - break-even revenue",
            {"monthly_revenue": round(monthly_revenue, 2),
             "break_even": be_rev["value"]},
            note="positive = above break-even"))

    return {
        "organization_id": org,
        "as_of": now.isoformat(),
        "headline": {
            "revenue": round(revenue, 2),
            "expenses": round(expenses, 2),
            "profit": round(profit, 2),
            "operating_margin_pct": round(op_margin_pct, 2),
            "months_of_data": months_n,
            "active_customers": active_customers,
        },
        "sections": {
            "profitability": profitability,
            "growth": growth,
            "cash": cash,
            "risk": risk,
            "unit_economics": unit_econ,
            "break_even": break_even,
        },
        "series": {
            "revenue_by_month": [
                {"label": m, "value": round(v, 2)}
                for m, v in zip(months, revenue_series)
            ],
            "net_cashflow_by_month": [
                {"label": m, "value": round(v, 2)}
                for m, v in zip(months, net_series)
            ],
        },
    }


def flatten_for_agent(battery: dict) -> dict:
    """Compact {label: value unit} view for the agent finding / LLM prompt."""
    out = dict(battery.get("headline", {}))
    for rows in battery.get("sections", {}).values():
        for m in rows:
            if m.get("value") is not None:
                out[m["label"]] = f'{m["value"]} {m["unit"]}'
    return out
