from decimal import Decimal
from datetime import date, timedelta

import httpx


FRANKFURTER_URL = (
    "https://api.frankfurter.dev/v2"
)


def get_fx_rate(
    base: str,
    quote: str,
) -> dict:

    url = (
        f"{FRANKFURTER_URL}/rate/"
        f"{base.upper()}/"
        f"{quote.upper()}"
    )

    response = httpx.get(
        url,
        timeout=30.0,
    )

    response.raise_for_status()

    data = response.json()

    return {
        "date": data["date"],
        "base": data["base"],
        "quote": data["quote"],
        "rate": Decimal(
            str(data["rate"])
        ),
    }


def get_multiple_rates(
    base: str,
    quotes: list[str],
) -> list[dict]:

    url = (
        f"{FRANKFURTER_URL}/rates"
    )

    response = httpx.get(
        url,
        params={
            "base": base.upper(),
            "quotes": ",".join(
                quotes
            ),
        },
        timeout=30.0,
    )

    response.raise_for_status()

    return response.json()



def get_monthly_fx_history(
    base: str,
    quote: str,
    months: int = 12,
) -> list[dict]:

    end_date = date.today()

    start_date = end_date.replace(
        day=1
    )

    start_date = (
        start_date
        - timedelta(days=months * 31)
    )

    url = (
        f"{FRANKFURTER_URL}/rates"
    )

    response = httpx.get(
        url,
        params={
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "base": base.upper(),
            "quotes": quote.upper(),
            "group": "month",
        },
        timeout=30.0,
    )

    response.raise_for_status()

    return response.json()