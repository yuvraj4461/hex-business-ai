from sqlalchemy.orm import Session

from app.models.agriculture_signal import (
    AgricultureSignal,
)
from app.models.commodity_forecast import (
    CommodityForecast,
)


CROP_COMMODITY_MAP = {
    "Wheat": "WHEAT_U.S._HRW",
    "Rice": "RICE_THAILAND_5%",
    "Sugar": "SUGAR_WORLD",
}


def calculate_agriculture_commodity_risk(
    db: Session,
) -> list[dict]:

    signals = (
        db.query(
            AgricultureSignal
        )
        .all()
    )

    results = []

    for signal in signals:

        commodity_symbol = (
            CROP_COMMODITY_MAP.get(
                signal.crop
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
                == 2026,
            )
            .first()
        )

        if not forecast:
            continue

        risk_score = float(
            signal.signal_value
        )

        results.append(
            {
                "region": signal.region,
                "crop": signal.crop,
                "agriculture_signal":
                    signal.signal_type,
                "agriculture_value":
                    risk_score,
                "severity":
                    signal.severity,
                "commodity":
                    forecast.commodity_name,
                "commodity_symbol":
                    forecast.commodity_symbol,
                "forecast_2026":
                    float(
                        forecast.value
                    ),
                "unit":
                    forecast.unit,
            }
        )

    return results