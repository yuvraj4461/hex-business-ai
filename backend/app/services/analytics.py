from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.expense import Expense
from app.models.order import Order
from app.models.transaction import Transaction


def get_revenue(
    db: Session,
    organization_id: int,
) -> float:

    result = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.organization_id
            == organization_id,
            Transaction.transaction_type
            == "REVENUE",
        )
        .scalar()
    )

    return float(result or 0)


def get_expenses(
    db: Session,
    organization_id: int,
) -> float:

    result = (
        db.query(
            func.coalesce(
                func.sum(Expense.amount),
                0,
            )
        )
        .filter(
            Expense.organization_id
            == organization_id,
        )
        .scalar()
    )

    return float(result or 0)


def get_order_count(
    db: Session,
    organization_id: int,
) -> int:

    result = (
        db.query(func.count(Order.id))
        .filter(
            Order.organization_id
            == organization_id,
        )
        .scalar()
    )

    return int(result or 0)


def get_customer_count(
    db: Session,
    organization_id: int,
) -> int:

    result = (
        db.query(func.count(Customer.id))
        .filter(
            Customer.organization_id
            == organization_id,
        )
        .scalar()
    )

    return int(result or 0)

def get_revenue_analysis(
    db: Session,
    organization_id: int,
) -> dict:

    revenue = get_revenue(
        db,
        organization_id,
    )

    expenses = get_expenses(
        db,
        organization_id,
    )

    orders = get_order_count(
        db,
        organization_id,
    )

    customers = get_customer_count(
        db,
        organization_id,
    )

    profit = revenue - expenses

    average_order_value = (
        revenue / orders
        if orders > 0
        else 0
    )

    return {
        "revenue": revenue,
        "expenses": expenses,
        "profit": profit,
        "orders": orders,
        "customers": customers,
        "average_order_value": average_order_value,
    }