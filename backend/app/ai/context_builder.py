from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.global_event import GlobalEvent
from app.models.order import Order
from app.models.transaction import Transaction

from app.services.demand import (
    forecast_product_demand,
)

from app.services.agriculture import (
    get_agriculture_risks,
)

from app.services.commodity_analysis import (
    compare_commodity_forecasts,
)

from app.services.global_exposure import (
    build_global_exposure_summary,
)


def get_verified_business_metrics(
    db: Session,
    organization_id: int,
) -> dict:

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
            func.count(Order.id)
        )
        .filter(
            Order.organization_id
            == organization_id,
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

    orders = int(
        order_count or 0
    )


    return {
        "revenue": revenue,
        "expenses": expenses,
        "profit": profit,
        "orders": orders,
        "currency": "INR",
    }


def build_ai_context(
    db: Session,
    organization_id: int,
    event: GlobalEvent | None = None,
) -> dict:

    # -------------------------------------------------
    # VERIFIED INTERNAL BUSINESS DATA
    # -------------------------------------------------

    financial_metrics = (
        get_verified_business_metrics(
            db,
            organization_id,
        )
    )


    context = {

        "organization_id":
            organization_id,


        "business": {

            "verified_financial_metrics":
                financial_metrics,

            "demand_forecast":
                forecast_product_demand(
                    db,
                    organization_id,
                ),

        },


        "market": {
            "commodities": {},
        },


        "agriculture":
            get_agriculture_risks(
                db
            ),


        "global_event":
            None,


        "exposure":
            None,


        "verified_facts": {

            "revenue":
                financial_metrics[
                    "revenue"
                ],

            "expenses":
                financial_metrics[
                    "expenses"
                ],

            "profit":
                financial_metrics[
                    "profit"
                ],

            "orders":
                financial_metrics[
                    "orders"
                ],

            "currency":
                "INR",

        },
    }


    # -------------------------------------------------
    # COMMODITY INTELLIGENCE
    # -------------------------------------------------

    for commodity in [
        "Wheat, U.S., HRW",
        "Cotton",
        "Aluminum",
        "Copper",
    ]:

        context[
            "market"
        ][
            "commodities"
        ][commodity] = (
            compare_commodity_forecasts(
                db,
                commodity,
            )
        )


    # -------------------------------------------------
    # GLOBAL EVENT + EXPOSURE
    # -------------------------------------------------

    if event:

        context[
            "global_event"
        ] = {

            "id":
                event.id,

            "source":
                event.source,

            "type":
                event.event_type,

            "title":
                event.title,

            "severity":
                event.severity,

            "region":
                event.region,

            "detected_at":
                event.detected_at,

        }


        exposure = (
            build_global_exposure_summary(
                db,
                organization_id,
                event,
            )
        )


        context[
            "exposure"
        ] = exposure


        # -------------------------------------------------
        # EXPLICIT VERIFIED RISK FACTS
        # -------------------------------------------------

        context[
            "verified_facts"
        ][
            "global_event"
        ] = {

            "id":
                event.id,

            "title":
                event.title,

            "severity":
                event.severity,

            "region":
                event.region,

        }


        if isinstance(
            exposure,
            dict,
        ):

            financial = (
                exposure.get(
                    "financial"
                )
                or {}
            )


            business_risk = (
                exposure.get(
                    "business_risk"
                )
                or {}
            )


            context[
                "verified_facts"
            ][
                "business_risk"
            ] = {

                "score":
                    business_risk.get(
                        "score"
                    ),

                "level":
                    business_risk.get(
                        "level"
                    ),

            }


            context[
                "verified_facts"
            ][
                "revenue_at_risk"
            ] = float(
                financial.get(
                    "total_revenue_at_risk",
                    0,
                )
                or 0
            )


            context[
                "verified_facts"
            ][
                "cost_impact"
            ] = float(
                financial.get(
                    "total_cost_impact",
                    0,
                )
                or 0
            )


            context[
                "verified_facts"
            ][
                "affected_routes"
            ] = len(
                exposure.get(
                    "exposures",
                    [],
                )
                or []
            )


    return context