from sqlalchemy.orm import Session

from app.models.commodity_forecast import (
    CommodityForecast,
)

from app.models.product_material import (
    ProductMaterial,
)


COMMODITY_SYMBOL_MAP = {
    "WHEAT": "WHEAT_U.S._HRW",
    "OIL": "PALM_OIL",

    "COTTON": "COTTON",

    "COPPER": "COPPER",
    "ALUMINUM": "ALUMINUM",

    "RICE": "RICE_THAILAND_5%",
    "MAIZE": "MAIZE",

    "SOYBEAN_OIL": "SOYBEAN_OIL",
    "COCONUT_OIL": "COCONUT_OIL",

    "SUGAR": "SUGAR_WORLD",
}


def calculate_forecast_material_impact(
    db: Session,
    organization_id: int,
    forecast_year: int = 2026,
) -> list[dict]:

    mappings = (
        db.query(
            ProductMaterial
        )
        .filter(
            ProductMaterial.organization_id
            == organization_id
        )
        .all()
    )

    impacts = []

    for mapping in mappings:

        commodity_symbol = (
            COMMODITY_SYMBOL_MAP.get(
                mapping.material_symbol
            )
        )

        if not commodity_symbol:
            continue

        forecast = (
            db.query(
                CommodityForecast
            )
            .filter(
                CommodityForecast
                .commodity_symbol
                == commodity_symbol,

                CommodityForecast
                .forecast_year
                == forecast_year,
            )
            .first()
        )

        if not forecast:
            continue

        market_value = float(
            forecast.value
        )

        quantity = float(
            mapping.quantity_per_unit
        )

        estimated_material_cost = (
            quantity * market_value
        )

        impacts.append(
            {
                "product_id":
                    mapping.product_id,

                "material_symbol":
                    mapping.material_symbol,

                "material_name":
                    mapping.material_name,

                "commodity_symbol":
                    forecast.commodity_symbol,

                "commodity_name":
                    forecast.commodity_name,

                "forecast_year":
                    forecast_year,

                "market_value":
                    market_value,

                "unit":
                    forecast.unit,

                "quantity_per_unit":
                    quantity,

                "estimated_material_cost":
                    estimated_material_cost,

                "source":
                    forecast.source,
            }
        )

    return impacts