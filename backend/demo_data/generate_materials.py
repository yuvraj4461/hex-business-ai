from app.database.connection import SessionLocal
from app.models import (
    Organization,
    Product,
    ProductMaterial,
)


MATERIALS = {
    "Food": [
        (
            "WHEAT",
            "Wheat",
            0.25,
            "kg",
        ),
        (
            "OIL",
            "Edible Oil",
            0.05,
            "liter",
        ),
    ],

    "Clothing": [
        (
            "COTTON",
            "Cotton",
            0.6,
            "kg",
        ),
        (
            "POLYESTER",
            "Polyester",
            0.15,
            "kg",
        ),
    ],

    "Hardware": [
        (
            "COPPER",
            "Copper",
            0.08,
            "kg",
        ),
        (
            "ALUMINUM",
            "Aluminium",
            0.12,
            "kg",
        ),
    ],

    "Software": [
        (
            "CLOUD_COMPUTE",
            "Cloud Compute",
            1.0,
            "unit",
        ),
    ],
}


db = SessionLocal()

try:

    total = 0

    organizations = (
        db.query(Organization)
        .order_by(Organization.id)
        .all()
    )

    for organization in organizations:

        industry = (
            organization.industry
            or ""
        ).strip().lower()

        industry_map = {
            "food": "Food",
            "food business": "Food",

            "clothing": "Clothing",
            "clothing business": "Clothing",
            "fashion": "Clothing",

            "hardware": "Hardware",
            "hardware business": "Hardware",
            "electronics": "Hardware",

            "software": "Software",
            "software business": "Software",
            "saas": "Software",
        }

        industry_key = industry_map.get(
        industry
        )

        materials = MATERIALS.get(
            industry_key,
            [],
        )

        products = (
            db.query(Product)
            .filter(
                Product.organization_id
                == organization.id
            )
            .all()
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

                total += 1

    db.commit()

    print(
        f"Created {total} product-material mappings."
    )

finally:
    db.close()