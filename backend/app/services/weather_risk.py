def detect_weather_risk(
    weather_data: dict,
) -> list[dict]:

    hourly = weather_data.get(
        "hourly",
        {},
    )

    times = hourly.get(
        "time",
        [],
    )

    precipitation = hourly.get(
        "precipitation",
        [],
    )

    wind = hourly.get(
        "wind_speed_10m",
        [],
    )

    weather_codes = hourly.get(
        "weather_code",
        [],
    )

    risks = []

    for index in range(
        min(
            len(times),
            len(precipitation),
            len(wind),
            len(weather_codes),
        )
    ):

        rain = precipitation[index]
        wind_speed = wind[index]
        code = weather_codes[index]

        if (
            rain is not None
            and rain >= 30
        ):
            risks.append(
                {
                    "type": "HEAVY_PRECIPITATION",
                    "severity": "HIGH",
                    "time": times[index],
                    "value": rain,
                }
            )

        if (
            wind_speed is not None
            and wind_speed >= 60
        ):
            risks.append(
                {
                    "type": "HIGH_WIND",
                    "severity": "HIGH",
                    "time": times[index],
                    "value": wind_speed,
                }
            )

        # Weather codes 95-99 correspond to
        # thunderstorm / severe thunderstorm
        # categories in the WMO-based scheme.
        if code in [95, 96, 99]:
            risks.append(
                {
                    "type": "THUNDERSTORM",
                    "severity": "HIGH",
                    "time": times[index],
                    "weather_code": code,
                }
            )

    return risks