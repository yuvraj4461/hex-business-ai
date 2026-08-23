from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.customer import Customer
from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.transaction import Transaction
from app.models.user import User

from app.security.dependencies import (
    require_permission,
)


router = APIRouter(
    prefix="/business",
    tags=["Business"],
)


# ---------------------------------------------------------
# BUSINESS OVERVIEW
# ---------------------------------------------------------

@router.get("/overview")
def business_overview(
    current_user: User = Depends(
        require_permission("view_analytics")
    ),
    db: Session = Depends(get_db),
):
    organization_id = (
        current_user.organization_id
    )


    # -----------------------------
    # Revenue
    # -----------------------------

    revenue_result = (
        db.query(
            func.coalesce(
                func.sum(
                    Transaction.amount
                ),
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


    # -----------------------------
    # Expenses
    # -----------------------------

    expense_result = (
        db.query(
            func.coalesce(
                func.sum(
                    Expense.amount
                ),
                0,
            )
        )
        .filter(
            Expense.organization_id
            == organization_id,
        )
        .scalar()
    )


    # -----------------------------
    # Orders
    # -----------------------------

    order_count = (
        db.query(
            func.count(
                Order.id
            )
        )
        .filter(
            Order.organization_id
            == organization_id,
        )
        .scalar()
    )


    # -----------------------------
    # Customers
    # -----------------------------

    customer_count = (
        db.query(
            func.count(
                Customer.id
            )
        )
        .filter(
            Customer.organization_id
            == organization_id,
        )
        .scalar()
    )


    # -----------------------------
    # Low stock
    # -----------------------------

    low_stock_count = (
        db.query(
            func.count(
                Inventory.id
            )
        )
        .filter(
            Inventory.organization_id
            == organization_id,

            Inventory.quantity
            <= Inventory.reorder_level,
        )
        .scalar()
    )


    revenue = float(
        revenue_result or 0
    )

    expenses = float(
        expense_result or 0
    )

    profit = (
        revenue - expenses
    )


    return {
        "organization_id":
            organization_id,

        "revenue":
            revenue,

        "expenses":
            expenses,

        "profit":
            profit,

        "orders":
            int(order_count or 0),

        "customers":
            int(customer_count or 0),

        "low_stock_products":
            int(low_stock_count or 0),

        "user": {
            "name":
                current_user.name,

            "role":
                current_user.role,
        },
    }


# ---------------------------------------------------------
# ADMIN OVERVIEW
# ---------------------------------------------------------

@router.get("/admin")
def admin_overview(
    current_user: User = Depends(
        require_permission("manage_users")
    ),
):
    return {
        "message":
            "Admin access granted",

        "user":
            current_user.name,

        "role":
            current_user.role,
    }


# ---------------------------------------------------------
# DETAILED DASHBOARD
# ---------------------------------------------------------

@router.get("/dashboard")
def dashboard(
    current_user: User = Depends(
        require_permission("view_analytics")
    ),
    db: Session = Depends(get_db),
):
    organization_id = (
        current_user.organization_id
    )


    revenue_result = (
        db.query(
            func.coalesce(
                func.sum(
                    Transaction.amount
                ),
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


    expense_result = (
        db.query(
            func.coalesce(
                func.sum(
                    Expense.amount
                ),
                0,
            )
        )
        .filter(
            Expense.organization_id
            == organization_id,
        )
        .scalar()
    )


    order_count = (
        db.query(
            func.count(
                Order.id
            )
        )
        .filter(
            Order.organization_id
            == organization_id,
        )
        .scalar()
    )


    customer_count = (
        db.query(
            func.count(
                Customer.id
            )
        )
        .filter(
            Customer.organization_id
            == organization_id,
        )
        .scalar()
    )


    low_stock_count = (
        db.query(
            func.count(
                Inventory.id
            )
        )
        .filter(
            Inventory.organization_id
            == organization_id,

            Inventory.quantity
            <= Inventory.reorder_level,
        )
        .scalar()
    )


    revenue = float(
        revenue_result or 0
    )

    expenses = float(
        expense_result or 0
    )

    profit = (
        revenue - expenses
    )


    return {
        "organization_id":
            organization_id,

        "user": {
            "name":
                current_user.name,

            "role":
                current_user.role,
        },

        "metrics": {
            "revenue":
                revenue,

            "expenses":
                expenses,

            "profit":
                profit,

            "orders":
                int(
                    order_count or 0
                ),

            "customers":
                int(
                    customer_count or 0
                ),

            "low_stock_products":
                int(
                    low_stock_count or 0
                ),
        },
    }