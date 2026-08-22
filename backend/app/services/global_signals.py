from app.services.fx import get_fx_rate
from app.services.global_events import (
    fetch_gdelt_events,
)
from app.services.weather import (
    fetch_weather,
)
from app.services.weather_risk import (
    detect_weather_risk,
)


def collect_global_signals(
    latitude: float,
    longitude: float,
) -> dict:

    gdelt_data = fetch_gdelt_events(
        timespan_minutes=60,
    )

    weather_data = fetch_weather(
        latitude,
        longitude,
    )

    weather_risks = detect_weather_risk(
        weather_data
    )

    fx = get_fx_rate(
        "USD",
        "INR",
    )

    return {
        "global_news": {
            "events_detected": len(
                gdelt_data.get(
                    "features",
                    [],
                )
            ),
        },

        "weather": {
            "risk_count": len(
                weather_risks
            ),
            "risks": weather_risks[:20],
        },

        "fx": {
            "USD_INR": {
                "date": fx["date"],
                "rate": str(
                    fx["rate"]
                ),
            }
        },
    }