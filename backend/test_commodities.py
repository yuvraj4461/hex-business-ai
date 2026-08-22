from pprint import pprint

from app.database.connection import SessionLocal

from app.services.commodities import (
    extract_price_pages,
    parse_commodity_rows,
    store_commodity_forecasts,
)


db = SessionLocal()

try:

    print(
        "Extracting World Bank commodity table..."
    )

    text = extract_price_pages()

    print(
        "Extracted characters:",
        len(text),
    )

    print(
        "\nFirst 3000 extracted characters:"
    )

    print(
        text[:3000]
    )

    rows = parse_commodity_rows(
        text
    )

    print(
        "\nParsed commodity records:",
        len(rows),
    )

    print(
        "\nFirst 10 records:"
    )

    pprint(
        rows[:10]
    )

    stored = store_commodity_forecasts(
        db,
        rows,
    )

    print(
        "\nNew records stored:",
        stored,
    )

finally:

    db.close()