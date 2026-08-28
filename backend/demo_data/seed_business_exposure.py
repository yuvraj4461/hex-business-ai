from app.database.connection import SessionLocal

from app.models import (
    Organization,
    SupplyRoute,
)

from app.models.global_event import GlobalEvent

from app.models.business_exposure import (
    BusinessExposure,
)


def seed_business_exposure():
    db = SessionLocal()

    try:
        organization = (
            db.query(Organization)
            .filter(
                Organization.name
                == "HEX Demo Business"
            )
            .first()
        )

        if not organization:
            print(
                "HEX Demo Business not found."
            )
            return

        event = (
            db.query(GlobalEvent)
            .filter(
                GlobalEvent.external_id
                == "RED_SEA_001"
            )
            .first()
        )

        if not event:
            print(
                "Red Sea event not found."
            )
            return

        routes = (
            db.query(SupplyRoute)
            .filter(
                SupplyRoute.organization_id
                == organization.id,

                SupplyRoute.corridor
                == "RED_SEA",

                SupplyRoute.status
                == "ACTIVE",
            )
            .all()
        )

        if not routes:
            print(
                "No active Red Sea routes found."
            )
            return

        created = 0
        skipped = 0

        for route in routes:

            existing = (
                db.query(BusinessExposure)
                .filter(
                    BusinessExposure.organization_id
                    == organization.id,

                    BusinessExposure.global_event_id
                    == event.id,

                    BusinessExposure.route_id
                    == route.id,
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            freight_cost = float(
                route.freight_cost
            )

            cost_impact = (
                freight_cost * 0.25
            )

            revenue_at_risk = (
                cost_impact * 2
            )

            exposure = BusinessExposure(
                organization_id=(
                    organization.id
                ),

                global_event_id=(
                    event.id
                ),

                route_id=(
                    route.id
                ),

                supplier_id=(
                    route.supplier_id
                ),

                product_id=(
                    route.product_id
                ),

                exposure_type=(
                    "ROUTE_DISRUPTION"
                ),

                severity="HIGH",

                estimated_delay_days=14,

                estimated_cost_impact=(
                    cost_impact
                ),

                estimated_revenue_at_risk=(
                    revenue_at_risk
                ),

                explanation=(
                    "Simulated Red Sea "
                    "shipping disruption "
                    "affects this active "
                    "supply route."
                ),
            )

            db.add(exposure)
            created += 1

        db.commit()

        print(
            f"Created {created} "
            "business exposure records."
        )

        print(
            f"Skipped {skipped} "
            "existing exposure records."
        )

        total_revenue_at_risk = (
            sum(
                float(
                    route.freight_cost
                )
                * 0.5
                for route in routes
                if route.corridor
                == "RED_SEA"
            )
        )

        print(
            "Expected Red Sea revenue "
            "at risk: "
            f"{total_revenue_at_risk:,.2f}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_business_exposure()