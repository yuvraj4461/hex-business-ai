from app.services.fx import (
    get_fx_rate,
    get_multiple_rates,
)


usd_inr = get_fx_rate(
    "USD",
    "INR",
)

print(
    "USD/INR:",
    usd_inr,
)


multiple = get_multiple_rates(
    "USD",
    [
        "INR",
        "EUR",
        "GBP",
        "JPY",
    ],
)

print(
    "\nMultiple USD rates:"
)

for rate in multiple:
    print(rate)