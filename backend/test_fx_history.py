from pprint import pprint

from app.services.fx import (
    get_monthly_fx_history,
)


history = get_monthly_fx_history(
    "USD",
    "INR",
    months=12,
)

print(
    "Number of FX observations:",
    len(history),
)

pprint(history[:5])