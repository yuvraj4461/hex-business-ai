from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order


def sales_agent(
    state: dict,
    db: Session,
) -> dict:

    organization_id = state["organization_id"]

    total_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.organization_id
            == organization_id,
        )
        .scalar()
    )

    completed_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.organization_id
            == organization_id,
            Order.status == "COMPLETED",
        )
        .scalar()
    )

    cancelled_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.organization_id
            == organization_id,
            Order.status == "CANCELLED",
        )
        .scalar()
    )

    findings = list(
        state.get("findings", [])
    )

    findings.append(
        {
            "agent": "Sales Agent",
            "type": "sales_analysis",
            "data": {
                "total_orders":
                    int(total_orders or 0),
                "completed_orders":
                    int(completed_orders or 0),
                "cancelled_orders":
                    int(cancelled_orders or 0),
            },
        }
    )

    return {
        **state,
        "findings": findings,
    }