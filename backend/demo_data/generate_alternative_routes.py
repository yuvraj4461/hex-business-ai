from app.database.connection import SessionLocal
from app.models import (
    Organization,
    Product,
    Supplier,
    SupplyRoute,
)


def create_alternative_routes():
    db = SessionLocal()

    try:

        organizations = (
            db.query(Organization)
            .order_by(Organization.id)
            .all()
        )

        total_created = 0

        for organization in organizations:

            suppliers = (
                db.query(Supplier)
                .filter(
                    Supplier.organization_id
                    == organization.id
                )
                .limit(1)
                .all()
            )

            products = (
                db.query(Product)
                .filter(
                    Product.organization_id
                    == organization.id
                )
                .limit(1)
                .all()
            )

            if not suppliers or not products:
                continue

            supplier = suppliers[0]
            product = products[0]

            routes = [
                {
                    "name": "Cape of Good Hope",
                    "corridor": "CAPE_OF_GOOD_HOPE",
                    "distance": 10500,
                    "days": 28,
                    "cost": 340000,
                    "risk": "LOW",
                },
                {
                    "name": "Air Freight",
                    "corridor": "AIR",
                    "distance": 0,
                    "days": 3,
                    "cost": 1200000,
                    "risk": "LOW",
                },
            ]

            for item in routes:

                existing = (
                    db.query(SupplyRoute)
                    .filter(
                        SupplyRoute.organization_id
                        == organization.id,
                        SupplyRoute.corridor
                        == item["corridor"],
                        SupplyRoute.product_id
                        == product.id,
                    )
                    .first()
                )

                if existing:
                    continue

                route = SupplyRoute(
                    organization_id=organization.id,
                    supplier_id=supplier.id,
                    product_id=product.id,
                    route_name=item["name"],
                    origin_country="China",
                    origin_port="Shanghai",
                    destination_country="India",
                    destination_port="Mundra",
                    transport_mode=(
                        "AIR"
                        if item["corridor"] == "AIR"
                        else "SEA"
                    ),
                    corridor=item["corridor"],
                    distance_km=item["distance"],
                    transit_days=item["days"],
                    freight_cost=item["cost"],
                    risk_level=item["risk"],
                    status="ACTIVE",
                )

                db.add(route)
                total_created += 1

            db.commit()

        print(
            f"Created {total_created} alternative routes."
        )

    finally:
        db.close()


if __name__ == "__main__":
    create_alternative_routes()