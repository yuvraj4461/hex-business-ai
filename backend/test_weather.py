from app.services.weather import (
    fetch_weather,
)


# Chandigarh coordinates for development testing.
LATITUDE = 30.7333
LONGITUDE = 76.7794


data = fetch_weather(
    LATITUDE,
    LONGITUDE,
)


print(
    "Weather data received."
)

print(
    "Timezone:",
    data.get("timezone")
)

hourly = data.get(
    "hourly",
    {},
)

print(
    "Number of hourly records:",
    len(
        hourly.get(
            "time",
            [],
        )
    )
)

print(
    "First temperature:",
    hourly.get(
        "temperature_2m",
        [None],
    )[0],
)

print(
    "First precipitation:",
    hourly.get(
        "precipitation",
        [None],
    )[0],
)

print(
    "First wind speed:",
    hourly.get(
        "wind_speed_10m",
        [None],
    )[0],
)

print(
    "First weather code:",
    hourly.get(
        "weather_code",
        [None],
    )[0],
)