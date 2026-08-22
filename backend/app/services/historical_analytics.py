from datetime import datetime

from sqlalchemy import func, literal_column
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.expense import Expense
from app.models.product import Product

def get_monthly_revenue(
    db: Session,
    organization_id: int,
) -> list[dict]:

    month_expression = func.date_trunc(
        literal_column("'month'"),
        Order.order_date,
    )

    results = (
        db.query(
            month_expression.label("month"),
            func.coalesce(
                func.sum(Order.total_amount),
                0,
            ).label("revenue"),
        )
        .filter(
            Order.organization_id == organization_id,
            Order.status == "COMPLETED",
        )
        .group_by(month_expression)
        .order_by(month_expression)
        .all()
    )

    return [
        {
            "month": month.strftime("%Y-%m"),
            "revenue": float(revenue),
        }
        for month, revenue in results
    ]

def get_monthly_orders(
    db: Session,
    organization_id: int,
) -> list[dict]:

    month_expression = func.date_trunc(
        literal_column("'month'"),
        Order.order_date,
    )

    results = (
        db.query(
            month_expression.label("month"),
            func.count(Order.id).label("orders"),
        )
        .filter(
            Order.organization_id == organization_id,
        )
        .group_by(month_expression)
        .order_by(month_expression)
        .all()
    )

    return [
        {
            "month": month.strftime("%Y-%m"),
            "orders": int(orders),
        }
        for month, orders in results
    ]

def get_monthly_expenses(
    db: Session,
    organization_id: int,
) -> list[dict]:

    month_expression = func.date_trunc(
        literal_column("'month'"),
        Expense.expense_date,
    )

    results = (
        db.query(
            month_expression.label("month"),
            func.coalesce(
                func.sum(Expense.amount),
                0,
            ).label("expenses"),
        )
        .filter(
            Expense.organization_id == organization_id,
        )
        .group_by(month_expression)
        .order_by(month_expression)
        .all()
    )

    return [
        {
            "month": month.strftime("%Y-%m"),
            "expenses": float(expenses),
        }
        for month, expenses in results
    ]

def get_historical_snapshot(
    db: Session,
    organization_id: int,
) -> dict:

    monthly_revenue = get_monthly_revenue(
        db,
        organization_id,
    )

    monthly_orders = get_monthly_orders(
        db,
        organization_id,
    )

    monthly_expenses = get_monthly_expenses(
        db,
        organization_id,
    )

    revenue_comparison = compare_latest_revenue(
        monthly_revenue,
    )

    category_comparison = []

    if revenue_comparison.get("status") == "OK":

        category_comparison = (
            get_category_revenue_comparison(
                db,
                organization_id,
                revenue_comparison[
                    "latest_month"
                ],
                revenue_comparison[
                    "previous_month"
                ],
            )
        )

    return {
        "monthly_revenue": monthly_revenue,
        "monthly_orders": monthly_orders,
        "monthly_expenses": monthly_expenses,
        "revenue_comparison": revenue_comparison,
        "category_comparison": category_comparison,
    }

def compare_latest_revenue(
    monthly_revenue: list[dict],
) -> dict:

    if len(monthly_revenue) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": (
                "At least two months of revenue "
                "data are required for comparison."
            ),
        }

    previous = monthly_revenue[-2]
    latest = monthly_revenue[-1]

    previous_revenue = previous["revenue"]
    latest_revenue = latest["revenue"]

    difference = (
        latest_revenue - previous_revenue
    )

    if previous_revenue != 0:
        percentage_change = (
            difference / previous_revenue
        ) * 100
    else:
        percentage_change = 0

    if percentage_change > 0:
        direction = "INCREASED"
    elif percentage_change < 0:
        direction = "DECREASED"
    else:
        direction = "UNCHANGED"

    return {
        "status": "OK",
        "previous_month": previous["month"],
        "latest_month": latest["month"],
        "previous_revenue": previous_revenue,
        "latest_revenue": latest_revenue,
        "difference": difference,
        "percentage_change": percentage_change,
        "direction": direction,
    }

def get_category_revenue_comparison(
    db: Session,
    organization_id: int,
    latest_month: str,
    previous_month: str,
) -> list[dict]:

    month_expression = func.date_trunc(
        literal_column("'month'"),
        Order.order_date,
    )

    rows = (
        db.query(
            Product.category.label("category"),
            month_expression.label("month"),
            func.coalesce(
                func.sum(OrderItem.line_total),
                0,
            ).label("revenue"),
        )
        .join(
            OrderItem,
            OrderItem.order_id == Order.id,
        )
        .join(
            Product,
            Product.id == OrderItem.product_id,
        )
        .filter(
            Order.organization_id == organization_id,
            Order.status == "COMPLETED",
            Product.organization_id == organization_id,
        )
        .group_by(
            Product.category,
            month_expression,
        )
        .order_by(
            Product.category,
            month_expression,
        )
        .all()
    )

    data = {}

    for category, month, revenue in rows:

        month_key = month.strftime("%Y-%m")

        if month_key not in {
            latest_month,
            previous_month,
        }:
            continue

        if category not in data:
            data[category] = {
                "category": category,
                "previous_revenue": 0.0,
                "latest_revenue": 0.0,
            }

        if month_key == previous_month:
            data[category]["previous_revenue"] = float(
                revenue
            )

        elif month_key == latest_month:
            data[category]["latest_revenue"] = float(
                revenue
            )

    results = []

    for category_data in data.values():

        previous = category_data[
            "previous_revenue"
        ]

        latest = category_data[
            "latest_revenue"
        ]

        difference = latest - previous

        percentage_change = (
            (difference / previous) * 100
            if previous != 0
            else 0
        )

        category_data["difference"] = difference

        category_data[
            "percentage_change"
        ] = percentage_change

        results.append(category_data)

    results.sort(
        key=lambda item: item["difference"]
    )

    return results