from datetime import datetime

from app.database.connection import SessionLocal
from app.models import (
    Organization,
    Customer,
    Product,
    Service,
    Supplier,
    Employee,
    Location,
    Order,
    OrderItem,
    Inventory,
    InventoryTransaction,
    Transaction,
    Expense,
    ProductMaterial,
    SupplyRoute,
)
from app.models.global_event import GlobalEvent

from demo_data.generate_demo_data import (
    create_customers,
    create_products,
    create_services,
    create_suppliers,
    create_employees,
    create_locations,
    create_orders,
    create_order_items,
    create_inventory,
    create_inventory_transactions,
    create_transactions,
    create_expenses,
)


MATERIALS = {
    "Food": [
        ("WHEAT", "Wheat", 0.25, "kg"),
        ("OIL", "Edible Oil", 0.05, "liter"),
    ],
}


GLOBAL_EVENTS = [
    {
        "source": "HEX_SIMULATION",
        "external_id": "RED_SEA_001",
        "event_type": "LOGISTICS",
        "title": "Simulated Red Sea shipping disruption",
        "description": (
            "A simulated disruption affecting "
            "shipping routes through the Red Sea."
        ),
        "country": None,
        "region": "Red Sea",
        "severity": "HIGH",
    },
    {
        "source": "HEX_SIMULATION",
        "external_id": "FRANCE_001",
        "event_type": "GENERAL",
        "title": "Ardennes, Auvergne, France",
        "description": (
            "Simulated external intelligence event."
        ),
        "country": "France",
        "region": "Ardennes, Auvergne, France",
        "severity": "INFO",
    },
    {
        "source": "HEX_SIMULATION",
        "external_id": "FRANCE_002",
        "event_type": "GENERAL",
        "title": "France",
        "description": (
            "Simulated external intelligence event."
        ),
        "country": "France",
        "region": "France",
        "severity": "INFO",
    },
    {
        "source": "HEX_SIMULATION",
        "external_id": "TURKEY_001",
        "event_type": "GENERAL",
        "title": "Gursu, Bursa, Turkey",
        "description": (
            "Simulated external intelligence event."
        ),
        "country": "Turkey",
        "region": "Gursu, Bursa, Turkey",
        "severity": "INFO",
    },
]


def get_target_organization(db):
    organization = (
        db.query(Organization)
        .filter(
            Organization.name
            == "HEX Demo Business"
        )
        .first()
    )

    if organization:
        return organization

    organization = Organization(
        name="HEX Demo Business",
        industry="Food",
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    return organization


def business_data_exists(
    db,
    organization_id: int,
) -> bool:

    product_exists = (
        db.query(Product)
        .filter(
            Product.organization_id
            == organization_id
        )
        .first()
    )

    order_exists = (
        db.query(Order)
        .filter(
            Order.organization_id
            == organization_id
        )
        .first()
    )

    return (
        product_exists is not None
        or order_exists is not None
    )


def seed_business_data(
    db,
    organization,
):

    if business_data_exists(
        db,
        organization.id,
    ):
        print(
            "Business data already exists "
            "for HEX Demo Business."
        )
        return


    print(
        "Generating business data for "
        "HEX Demo Business..."
    )


    customers = create_customers(
        db,
        organization,
        count=30,
    )


    products = create_products(
        db,
        organization,
    )


    services = create_services(
        db,
        organization,
    )


    suppliers = create_suppliers(
        db,
        organization,
        count=5,
    )


    create_employees(
        db,
        organization,
        count=10,
    )


    locations = create_locations(
        db,
        organization,
    )


    orders = create_orders(
        db,
        organization,
        customers,
        locations,
        products,
        services,
        count=60,
    )


    create_order_items(
        db,
        organization,
        orders,
        products,
        services,
    )


    create_inventory(
        db,
        organization,
        products,
        locations,
    )


    create_inventory_transactions(
        db,
        organization,
        products,
        locations,
        count=100,
    )


    create_transactions(
        db,
        organization,
        orders,
    )


    create_expenses(
        db,
        organization,
        count=25,
    )


    db.commit()


    print(
        "Business data created successfully."
    )


def seed_materials(
    db,
    organization,
):

    products = (
        db.query(Product)
        .filter(
            Product.organization_id
            == organization.id
        )
        .all()
    )

    created = 0

    materials = MATERIALS.get(
        organization.industry,
        [],
    )


    for product in products:

        for (
            symbol,
            name,
            quantity,
            unit,
        ) in materials:

            existing = (
                db.query(ProductMaterial)
                .filter(
                    ProductMaterial.organization_id
                    == organization.id,

                    ProductMaterial.product_id
                    == product.id,

                    ProductMaterial.material_symbol
                    == symbol,
                )
                .first()
            )

            if existing:
                continue


            db.add(
                ProductMaterial(
                    organization_id=(
                        organization.id
                    ),
                    product_id=product.id,
                    material_symbol=symbol,
                    material_name=name,
                    quantity_per_unit=quantity,
                    unit=unit,
                )
            )

            created += 1


    db.commit()


    print(
        f"Created {created} "
        "product-material mappings."
    )


def seed_routes(
    db,
    organization,
):

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
        print(
            "Skipping routes: "
            "suppliers/products missing."
        )
        return


    created = 0


    for index, supplier in enumerate(
        suppliers
    ):

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
            organization_id=(
                organization.id
            ),
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
        created += 1


    db.commit()


    print(
        f"Created {created} Red Sea routes."
    )


def seed_alternative_routes(
    db,
    organization,
):

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
        return


    supplier = suppliers[0]
    product = products[0]


    routes = [
        {
            "name":
                "Cape of Good Hope",
            "corridor":
                "CAPE_OF_GOOD_HOPE",
            "distance":
                10500,
            "days":
                28,
            "cost":
                340000,
            "risk":
                "LOW",
        },
        {
            "name":
                "Air Freight",
            "corridor":
                "AIR",
            "distance":
                0,
            "days":
                3,
            "cost":
                1200000,
            "risk":
                "LOW",
        },
    ]


    created = 0


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


        db.add(
            SupplyRoute(
                organization_id=(
                    organization.id
                ),
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
        )

        created += 1


    db.commit()


    print(
        f"Created {created} "
        "alternative routes."
    )


def seed_global_events(db):

    created = 0


    for event_data in GLOBAL_EVENTS:

        existing = (
            db.query(GlobalEvent)
            .filter(
                GlobalEvent.external_id
                == event_data[
                    "external_id"
                ]
            )
            .first()
        )


        if existing:
            continue


        db.add(
            GlobalEvent(
                **event_data,
                detected_at=datetime.utcnow(),
            )
        )

        created += 1


    db.commit()


    print(
        f"Created {created} global events."
    )


def main():

    db = SessionLocal()


    try:

        print(
            "======================================"
        )

        print(
            "HEX PRODUCTION DATA SEED"
        )

        print(
            "======================================"
        )


        organization = (
            get_target_organization(db)
        )


        print(
            f"Target organization: "
            f"{organization.name}"
        )

        print(
            f"Organization ID: "
            f"{organization.id}"
        )

        print(
            f"Industry: "
            f"{organization.industry}"
        )


        seed_business_data(
            db,
            organization,
        )


        seed_materials(
            db,
            organization,
        )


        seed_routes(
            db,
            organization,
        )


        seed_alternative_routes(
            db,
            organization,
        )


        seed_global_events(db)


        print()
        print(
            "======================================"
        )

        print(
            "PRODUCTION SEED COMPLETE"
        )

        print(
            "======================================"
        )


    except Exception:

        db.rollback()
        raise


    finally:

        db.close()


if __name__ == "__main__":
    main()