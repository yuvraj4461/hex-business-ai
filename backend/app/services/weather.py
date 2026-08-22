import httpx


OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
)


def fetch_weather(
    latitude: float,
    longitude: float,
) -> dict:

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "temperature_2m,"
            "precipitation,"
            "wind_speed_10m,"
            "weather_code"
        ),
        "forecast_days": 2,
        "timezone": "auto",
    }

    response = httpx.get(
        OPEN_METEO_URL,
        params=params,
        timeout=30.0,
    )

    response.raise_for_status()

    return response.json()