from app.database.connection import SessionLocal
from app.models.commodity_forecast import CommodityForecast


FORECASTS = [
    {
        "commodity_symbol": "WHEAT_HRW",
        "commodity_name": "Wheat, U.S., HRW",
        "category": "GRAIN",
        "unit": "USD/MT",
        "records": [
            (2025, 285.0),
            (2026, 312.0),
        ],
    },
    {
        "commodity_symbol": "COTTON",
        "commodity_name": "Cotton",
        "category": "FIBER",
        "unit": "USD/MT",
        "records": [
            (2025, 1650.0),
            (2026, 1715.0),
        ],
    },
    {
        "commodity_symbol": "ALUMINUM",
        "commodity_name": "Aluminum",
        "category": "METAL",
        "unit": "USD/MT",
        "records": [
            (2025, 2380.0),
            (2026, 2510.0),
        ],
    },
    {
        "commodity_symbol": "COPPER",
        "commodity_name": "Copper",
        "category": "METAL",
        "unit": "USD/MT",
        "records": [
            (2025, 8950.0),
            (2026, 9340.0),
        ],
    },
]


def seed_commodity_forecasts():
    db = SessionLocal()

    try:
        created = 0
        skipped = 0

        for commodity in FORECASTS:

            for year, value in commodity["records"]:

                existing = (
                    db.query(CommodityForecast)
                    .filter(
                        CommodityForecast.commodity_name
                        == commodity["commodity_name"],

                        CommodityForecast.forecast_year
                        == year,
                    )
                    .first()
                )

                if existing:
                    skipped += 1
                    continue

                db.add(
                    CommodityForecast(
                        commodity_symbol=(
                            commodity[
                                "commodity_symbol"
                            ]
                        ),
                        commodity_name=(
                            commodity[
                                "commodity_name"
                            ]
                        ),
                        category=(
                            commodity[
                                "category"
                            ]
                        ),
                        unit=(
                            commodity[
                                "unit"
                            ]
                        ),
                        forecast_year=year,
                        value=value,
                        source="HEX_SIMULATION",
                        source_report_date="2026-08-23",
                        is_forecast=True,
                    )
                )

                created += 1

        db.commit()

        print(
            f"Created {created} commodity forecasts."
        )

        print(
            f"Skipped {skipped} existing forecasts."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_commodity_forecasts()