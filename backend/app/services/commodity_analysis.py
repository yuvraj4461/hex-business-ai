from sqlalchemy.orm import Session

from app.models.commodity_forecast import (
    CommodityForecast,
)


def compare_commodity_forecasts(
    db: Session,
    commodity_name: str,
) -> dict:

    records = (
        db.query(
            CommodityForecast
        )
        .filter(
            CommodityForecast
            .commodity_name
            == commodity_name
        )
        .order_by(
            CommodityForecast
            .forecast_year
            .asc()
        )
        .all()
    )

    if len(records) < 2:
        return {
            "status":
                "INSUFFICIENT_DATA"
        }

    previous = records[-2]
    latest = records[-1]

    previous_value = float(
        previous.value
    )

    latest_value = float(
        latest.value
    )

    difference = (
        latest_value
        - previous_value
    )

    percentage_change = (
        difference
        / previous_value
        * 100
        if previous_value != 0
        else 0
    )

    if percentage_change > 0:
        direction = "INCREASED"

    elif percentage_change < 0:
        direction = "DECREASED"

    else:
        direction = "UNCHANGED"

    return {
        "status": "OK",
        "commodity":
            commodity_name,
        "unit":
            latest.unit,
        "previous_year":
            previous.forecast_year,
        "latest_year":
            latest.forecast_year,
        "previous_value":
            previous_value,
        "latest_value":
            latest_value,
        "difference":
            difference,
        "percentage_change":
            percentage_change,
        "direction":
            direction,
    }