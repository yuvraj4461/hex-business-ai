from datetime import date, datetime
from decimal import Decimal


def make_json_safe(
    value,
):

    if isinstance(
        value,
        (
            datetime,
            date,
        ),
    ):
        return value.isoformat()

    if isinstance(
        value,
        Decimal,
    ):
        return float(value)

    if isinstance(
        value,
        dict,
    ):
        return {
            key: make_json_safe(
                item
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            make_json_safe(item)
            for item in value
        ]

    return value