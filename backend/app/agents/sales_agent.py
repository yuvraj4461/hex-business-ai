"""Sales Agent.

Reads order history for the organisation and reports demand health:
volume, revenue, fulfilment rate and cancellation rate, plus a recent
vs. prior period trend. Emits recommendations when cancellation rate or
revenue trend cross attention thresholds.

Note: prior to this version the Sales Agent was defined but never wired
into the graph, so none of this executed.
"""

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order

# An order cancellation rate above this is treated as a demand-quality signal.
CANCELLATION_WARNING_RATE = 0.15

# Period-over-period revenue drop that warrants a recommendation.
REVENUE_DECLINE_THRESHOLD = -0.10

TREND_WINDOW_DAYS = 30


def _percent(part: float, whole: float) -> float:
    if not whole:
        return 0.0
    return round(part / whole, 4)


def sales_agent(
    state: dict,
    db: Session,
) -> dict:

    organization_id = state["organization_id"]

    base = db.query(Order).filter(
        Order.organization_id == organization_id
    )

    # -------------------------------------------------
    # Volume and revenue by status
    # -------------------------------------------------

    status_rows = (
        db.query(
            Order.status,
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), 0),
        )
        .filter(Order.organization_id == organization_id)
        .group_by(Order.status)
        .all()
    )

    by_status = {
        (status or "UNKNOWN").upper(): {
            "orders": int(count or 0),
            "value": float(value or 0),
        }
        for status, count, value in status_rows
    }

    total_orders = sum(
        row["orders"] for row in by_status.values()
    )

    total_value = sum(
        row["value"] for row in by_status.values()
    )

    completed = by_status.get("COMPLETED", {"orders": 0, "value": 0.0})
    cancelled = by_status.get("CANCELLED", {"orders": 0, "value": 0.0})
    pending = by_status.get("PENDING", {"orders": 0, "value": 0.0})

    cancellation_rate = _percent(
        cancelled["orders"], total_orders
    )

    fulfilment_rate = _percent(
        completed["orders"], total_orders
    )

    # -------------------------------------------------
    # Recent vs prior period revenue
    # -------------------------------------------------

    now = datetime.utcnow()

    recent_start = now - timedelta(days=TREND_WINDOW_DAYS)
    prior_start = now - timedelta(days=TREND_WINDOW_DAYS * 2)

    def revenue_between(start, end) -> float:
        value = (
            db.query(func.coalesce(func.sum(Order.total_amount), 0))
            .filter(
                Order.organization_id == organization_id,
                Order.status != "CANCELLED",
                Order.order_date >= start,
                Order.order_date < end,
            )
            .scalar()
        )
        return float(value or 0)

    recent_revenue = revenue_between(recent_start, now)
    prior_revenue = revenue_between(prior_start, recent_start)

    if prior_revenue:
        revenue_change = round(
            (recent_revenue - prior_revenue) / prior_revenue, 4
        )
    else:
        revenue_change = 0.0

    average_order_value = (
        round(total_value / total_orders, 2)
        if total_orders
        else 0.0
    )

    # -------------------------------------------------
    # Findings
    # -------------------------------------------------

    findings = list(state.get("findings") or [])
    recommendations = list(state.get("recommendations") or [])

    findings.append(
        {
            "agent": "Sales Agent",
            "type": "sales_analysis",
            "data": {
                "total_orders": total_orders,
                "total_order_value": round(total_value, 2),
                "average_order_value": average_order_value,
                "completed_orders": completed["orders"],
                "cancelled_orders": cancelled["orders"],
                "pending_orders": pending["orders"],
                "fulfilment_rate": fulfilment_rate,
                "cancellation_rate": cancellation_rate,
                "by_status": by_status,
            },
        }
    )

    findings.append(
        {
            "agent": "Sales Agent",
            "type": "revenue_trend",
            "data": {
                "window_days": TREND_WINDOW_DAYS,
                "recent_revenue": round(recent_revenue, 2),
                "prior_revenue": round(prior_revenue, 2),
                "change_ratio": revenue_change,
                "direction": (
                    "UP"
                    if revenue_change > 0.02
                    else "DOWN"
                    if revenue_change < -0.02
                    else "FLAT"
                ),
            },
        }
    )

    # -------------------------------------------------
    # Recommendations
    # -------------------------------------------------

    if total_orders == 0:
        findings.append(
            {
                "agent": "Sales Agent",
                "type": "no_order_history",
                "data": {
                    "note": (
                        "No orders recorded for this organisation, so demand "
                        "signals cannot be derived from sales history."
                    )
                },
            }
        )

    if cancellation_rate > CANCELLATION_WARNING_RATE:
        recommendations.append(
            {
                "agent": "Sales Agent",
                "type": "high_cancellation_rate",
                "severity": "MEDIUM",
                "reason": (
                    f"{cancellation_rate:.1%} of orders are cancelled, above the "
                    f"{CANCELLATION_WARNING_RATE:.0%} attention threshold. This "
                    "usually indicates fulfilment delays or supply shortfalls "
                    "rather than weak demand."
                ),
                "cancellation_rate": cancellation_rate,
                "cancelled_orders": cancelled["orders"],
                "value_at_risk": round(cancelled["value"], 2),
            }
        )

    if revenue_change < REVENUE_DECLINE_THRESHOLD and prior_revenue:
        recommendations.append(
            {
                "agent": "Sales Agent",
                "type": "revenue_decline",
                "severity": "HIGH",
                "reason": (
                    f"Revenue over the last {TREND_WINDOW_DAYS} days fell "
                    f"{abs(revenue_change):.1%} against the prior period. "
                    "Review demand forecasts and pipeline before committing "
                    "additional inventory spend."
                ),
                "recent_revenue": round(recent_revenue, 2),
                "prior_revenue": round(prior_revenue, 2),
                "change_ratio": revenue_change,
            }
        )

    if pending["orders"] and total_orders:
        pending_share = _percent(pending["orders"], total_orders)

        if pending_share > 0.4:
            recommendations.append(
                {
                    "agent": "Sales Agent",
                    "type": "pending_order_backlog",
                    "severity": "MEDIUM",
                    "reason": (
                        f"{pending_share:.1%} of orders are still pending, worth "
                        f"{pending['value']:,.2f}. A backlog this size is exposed "
                        "to any upstream supply disruption."
                    ),
                    "pending_orders": pending["orders"],
                    "pending_value": round(pending["value"], 2),
                }
            )

    return {
        **state,
        "findings": findings,
        "recommendations": recommendations,
    }