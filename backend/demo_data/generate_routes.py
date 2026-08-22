from app.database.connection import SessionLocal
from app.models import (
    Organization,
    Product,
    Supplier,
    SupplyRoute,
)


def create_routes():
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
                .limit(3)
                .all()
            )

            products = (
                db.query(Product)
                .filter(
                    Product.organization_id
                    == organization.id
                )
                .limit(3)
                .all()
            )

            if not suppliers or not products:
                continue

            for index, supplier in enumerate(suppliers):

                product = products[
                    index % len(products)
                ]

                existing = (
                    db.query(SupplyRoute)
                    .filter(
                        SupplyRoute.organization_id
                        == organization.id,
                        SupplyRoute.supplier_id
                        == supplier.id,
                        SupplyRoute.product_id
                        == product.id,
                        SupplyRoute.corridor
                        == "RED_SEA",
                    )
                    .first()
                )

                if existing:
                    continue

                route = SupplyRoute(
                    organization_id=organization.id,
                    supplier_id=supplier.id,
                    product_id=product.id,
                    route_name=(
                        f"{supplier.name} → "
                        f"{organization.name} "
                        f"via Red Sea"
                    ),
                    origin_country="China",
                    origin_port="Shanghai",
                    destination_country="India",
                    destination_port="Mundra",
                    transport_mode="SEA",
                    corridor="RED_SEA",
                    distance_km=7000,
                    transit_days=18,
                    freight_cost=250000,
                    risk_level="MEDIUM",
                    status="ACTIVE",
                )

                db.add(route)
                total_created += 1

            db.commit()

        print(
            f"Created {total_created} Red Sea routes."
        )

    finally:
        db.close()


if __name__ == "__main__":
    create_routes()