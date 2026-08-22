from app.services.weather import fetch_weather
from app.services.weather_risk import (
    detect_weather_risk,
)


data = fetch_weather(
    30.7333,
    76.7794,
)

risks = detect_weather_risk(
    data,
)

print(
    "Weather risks detected:",
    len(risks),
)

for risk in risks[:10]:
    print(risk)