from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem


def get_product_demand(
    db: Session,
    organization_id: int,
) -> list[dict]:

    results = (
        db.query(
            OrderItem.product_id,
            func.sum(
                OrderItem.quantity
            ).label(
                "quantity"
            ),
        )
        .join(
            Order,
            Order.id
            == OrderItem.order_id,
        )
        .filter(
            Order.organization_id
            == organization_id,

            Order.status
            == "COMPLETED",

            OrderItem.product_id
            .isnot(None),
        )
        .group_by(
            OrderItem.product_id,
        )
        .order_by(
            func.sum(
                OrderItem.quantity
            ).desc()
        )
        .all()
    )

    return [
        {
            "product_id":
                product_id,

            "quantity_sold":
                int(
                    quantity or 0
                ),
        }
        for product_id, quantity
        in results
    ]


def forecast_product_demand(
    db: Session,
    organization_id: int,
) -> list[dict]:

    historical = get_product_demand(
        db,
        organization_id,
    )

    forecasts = []

    for item in historical:

        baseline = float(
            item["quantity_sold"]
        )

        # Initial baseline model.
        # We will replace this with a
        # proper time-series model later.
        growth_rate = 0.10

        forecast = (
            baseline
            * (1 + growth_rate)
        )

        forecasts.append(
            {
                "product_id":
                    item["product_id"],

                "baseline_quantity":
                    baseline,

                "growth_rate":
                    growth_rate,

                "forecast_quantity":
                    forecast,

                "confidence":
                    60.0,

                "method":
                    "BASELINE_GROWTH",
            }
        )

    return forecasts