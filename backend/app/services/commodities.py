from pathlib import Path
import re

import pymupdf
from sqlalchemy.orm import Session

from app.models.commodity_forecast import (
    CommodityForecast,
)


PDF_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "CMO-April-2026.pdf"
)


# Some installations may have a slightly
# different filename. We automatically search
# for a CMO PDF if this exact file is missing.
if not PDF_PATH.exists():

    data_dir = (
        Path(__file__).resolve().parents[2]
        / "data"
    )

    candidates = list(
        data_dir.glob("CMO*.pdf")
    )

    if not candidates:
        raise FileNotFoundError(
            f"No CMO PDF found in {data_dir}"
        )

    PDF_PATH = candidates[0]


COMMODITY_CATEGORIES = {
    "Coal, Australia": "ENERGY",
    "Crude oil, Brent": "ENERGY",
    "Natural gas, Europe": "ENERGY",
    "Natural gas, U.S.": "ENERGY",
    "Liquefied natural gas, Japan": "ENERGY",

    "Cocoa": "BEVERAGES",
    "Coffee, Arabica": "BEVERAGES",
    "Coffee, Robusta": "BEVERAGES",
    "Tea, average": "BEVERAGES",

    "Coconut oil": "FOOD",
    "Groundnut oil": "FOOD",
    "Palm oil": "FOOD",
    "Soybean meal": "FOOD",
    "Soybean oil": "FOOD",
    "Soybeans": "FOOD",

    "Barley": "AGRICULTURE",
    "Maize": "AGRICULTURE",
    "Rice, Thailand, 5%": "AGRICULTURE",
    "Wheat, U.S., HRW": "AGRICULTURE",

    "Bananas, U.S.": "FOOD",
    "Beef": "FOOD",
    "Chicken": "FOOD",
    "Oranges": "FOOD",
    "Shrimp": "FOOD",
    "Sugar, World": "FOOD",

    "Logs, Africa": "RAW_MATERIAL",
    "Logs, S.E. Asia": "RAW_MATERIAL",
    "Sawnwood, S.E. Asia": "RAW_MATERIAL",
    "Cotton": "RAW_MATERIAL",
    "Rubber, TSR20": "RAW_MATERIAL",
    "Tobacco": "RAW_MATERIAL",

    "DAP": "FERTILIZER",
    "Phosphate rock": "FERTILIZER",
    "Potassium chloride": "FERTILIZER",
    "TSP": "FERTILIZER",
    "Urea, E. Europe": "FERTILIZER",

    "Aluminum": "METAL",
    "Copper": "METAL",
    "Iron ore": "METAL",
    "Lead": "METAL",
    "Nickel": "METAL",
    "Tin": "METAL",
    "Zinc": "METAL",

    "Gold": "PRECIOUS_METAL",
    "Silver": "PRECIOUS_METAL",
    "Platinum": "PRECIOUS_METAL",
}

UNIT_PATTERN = (
    r"\$\s*/\s*"
    r"(?:bbl|mmbtu|kg|mt|cum|dmt|toz)"
)

ROW_PATTERN = re.compile(
    rf"^(.+?)\s+"
    rf"({UNIT_PATTERN})\s+"
    rf"(.+)$",
    re.IGNORECASE,
)


def extract_price_pages() -> str:

    document = pymupdf.open(
        PDF_PATH
    )

    # The commodity table is on PDF pages
    # 20 and 21 in this report.
    # PyMuPDF uses zero-based indexes.
    page_indexes = [19, 20]

    text_parts = []

    for index in page_indexes:

        if index >= len(document):
            continue

        text_parts.append(
            document[index].get_text()
        )

    document.close()

    return "\n".join(
        text_parts
    )


def parse_number(
    value: str,
) -> float | None:

    value = value.strip()

    if value in {
        "...",
        "…",
        "",
    }:
        return None

    value = value.replace(
        ",",
        "",
    )

    try:
        return float(value)
    except ValueError:
        return None

def parse_commodity_rows(
    text: str,
) -> list[dict]:

    rows = []

    # The PDF table contains these commodity names.
    # We search for each one independently because
    # PDF extraction can split rows or insert newlines.
    commodities = {
        "Coal, Australia": ("$/mt", "ENERGY"),
        "Crude oil, Brent": ("$/bbl", "ENERGY"),
        "Natural gas, Europe": ("$/mmbtu", "ENERGY"),
        "Natural gas, U.S.": ("$/mmbtu", "ENERGY"),
        "Liquefied natural gas, Japan": (
            "$/mmbtu",
            "ENERGY",
        ),

        "Cocoa": ("$/kg", "BEVERAGES"),
        "Coffee, Arabica": ("$/kg", "BEVERAGES"),
        "Coffee, Robusta": ("$/kg", "BEVERAGES"),
        "Tea, average": ("$/kg", "BEVERAGES"),

        "Coconut oil": ("$/mt", "FOOD"),
        "Groundnut oil": ("$/mt", "FOOD"),
        "Palm oil": ("$/mt", "FOOD"),
        "Soybean meal": ("$/mt", "FOOD"),
        "Soybean oil": ("$/mt", "FOOD"),
        "Soybeans": ("$/mt", "FOOD"),

        "Barley": ("$/mt", "AGRICULTURE"),
        "Maize": ("$/mt", "AGRICULTURE"),
        "Rice, Thailand, 5%": (
            "$/mt",
            "AGRICULTURE",
        ),
        "Wheat, U.S., HRW": (
            "$/mt",
            "AGRICULTURE",
        ),

        "Bananas, U.S.": ("$/kg", "FOOD"),
        "Beef": ("$/kg", "FOOD"),
        "Chicken": ("$/kg", "FOOD"),
        "Oranges": ("$/kg", "FOOD"),
        "Shrimp": ("$/kg", "FOOD"),
        "Sugar, World": ("$/kg", "FOOD"),

        "Logs, Africa": ("$/cum", "RAW_MATERIAL"),
        "Logs, S.E. Asia": (
            "$/cum",
            "RAW_MATERIAL",
        ),
        "Sawnwood, S.E. Asia": (
            "$/cum",
            "RAW_MATERIAL",
        ),
        "Cotton": ("$/kg", "RAW_MATERIAL"),
        "Rubber, TSR20": (
            "$/kg",
            "RAW_MATERIAL",
        ),
        "Tobacco": ("$/mt", "RAW_MATERIAL"),

        "DAP": ("$/mt", "FERTILIZER"),
        "Phosphate rock": (
            "$/mt",
            "FERTILIZER",
        ),
        "Potassium chloride": (
            "$/mt",
            "FERTILIZER",
        ),
        "TSP": ("$/mt", "FERTILIZER"),
        "Urea, E. Europe": (
            "$/mt",
            "FERTILIZER",
        ),

        "Aluminum": ("$/mt", "METAL"),
        "Copper": ("$/mt", "METAL"),
        "Iron ore": ("$/dmt", "METAL"),
        "Lead": ("$/mt", "METAL"),
        "Nickel": ("$/mt", "METAL"),
        "Tin": ("$/mt", "METAL"),
        "Zinc": ("$/mt", "METAL"),

        "Gold": ("$/toz", "PRECIOUS_METAL"),
        "Silver": ("$/toz", "PRECIOUS_METAL"),
        "Platinum": (
            "$/toz",
            "PRECIOUS_METAL",
        ),
    }

    # Normalize PDF whitespace.
    normalized_text = text.replace(
        "\r",
        "\n",
    )

    # Collapse repeated spaces but preserve enough
    # information for regex matching.
    normalized_text = re.sub(
        r"[ \t]+",
        " ",
        normalized_text,
    )

    for commodity_name, (
        unit,
        category,
    ) in commodities.items():

        # Escape the commodity name because some
        # names contain punctuation.
        name_pattern = re.escape(
            commodity_name
        )

        unit_pattern = re.escape(
            unit
        ).replace(
            r"\$",
            r"\$\s*",
        ).replace(
            r"/",
            r"\s*/\s*",
        )

        # Capture four annual values:
        # 2024, 2025, 2026f, 2027f
        pattern = re.compile(
            rf"{name_pattern}"
            rf"\s+"
            rf"{unit_pattern}"
            rf"\s+"
            rf"("
            rf"(?:\d[\d,.]*|…|\.\.\.)"
            rf")"
            rf"\s+"
            rf"("
            rf"(?:\d[\d,.]*|…|\.\.\.)"
            rf")"
            rf"\s+"
            rf"("
            rf"(?:\d[\d,.]*|…|\.\.\.)"
            rf")"
            rf"\s+"
            rf"("
            rf"(?:\d[\d,.]*|…|\.\.\.)"
            rf")",
            re.IGNORECASE,
        )

        match = pattern.search(
            normalized_text
        )

        if not match:

            # Some PDF extraction may place the
            # unit on a separate line. Try a
            # looser fallback.
            loose_pattern = re.compile(
                rf"{name_pattern}"
                rf".{{0,80}}?"
                rf"("
                rf"(?:\d[\d,.]*|…|\.\.\.)"
                rf")\s+"
                rf"("
                rf"(?:\d[\d,.]*|…|\.\.\.)"
                rf")\s+"
                rf"("
                rf"(?:\d[\d,.]*|…|\.\.\.)"
                rf")\s+"
                rf"("
                rf"(?:\d[\d,.]*|…|\.\.\.)"
                rf")",
                re.IGNORECASE,
                re.DOTALL,
            )

            match = loose_pattern.search(
                normalized_text
            )

        if not match:
            print(
                f"Could not parse: "
                f"{commodity_name}"
            )
            continue

        values = []

        for value in match.groups():

            value = value.replace(
                ",",
                "",
            )

            if value in {
                "...",
                "…",
            }:
                values.append(None)
            else:
                try:
                    values.append(
                        float(value)
                    )
                except ValueError:
                    values.append(None)

        year_values = [
            (2024, values[0], False),
            (2025, values[1], False),
            (2026, values[2], True),
            (2027, values[3], True),
        ]

        symbol = (
            commodity_name
            .upper()
            .replace(
                " ",
                "_",
            )
            .replace(
                ",",
                "",
            )
        )

        for (
            year,
            value,
            is_forecast,
        ) in year_values:

            if value is None:
                continue

            rows.append(
                {
                    "commodity_symbol":
                        symbol,

                    "commodity_name":
                        commodity_name,

                    "category":
                        category,

                    "unit":
                        unit,

                    "forecast_year":
                        year,

                    "value":
                        value,

                    "source":
                        "WORLD_BANK",

                    "source_report_date":
                        "APRIL_2026",

                    "is_forecast":
                        is_forecast,
                }
            )

    return rows

def store_commodity_forecasts(
    db: Session,
    rows: list[dict],
) -> int:

    stored = 0

    for row in rows:

        existing = (
            db.query(
                CommodityForecast
            )
            .filter(
                CommodityForecast
                .commodity_symbol
                == row[
                    "commodity_symbol"
                ],

                CommodityForecast
                .forecast_year
                == row[
                    "forecast_year"
                ],

                CommodityForecast
                .source
                == row["source"],
            )
            .first()
        )

        if existing:
            continue

        forecast = CommodityForecast(
            commodity_symbol=row[
                "commodity_symbol"
            ],

            commodity_name=row[
                "commodity_name"
            ],

            category=row[
                "category"
            ],

            unit=row["unit"],

            forecast_year=row[
                "forecast_year"
            ],

            value=row["value"],

            source=row["source"],

            source_report_date=row[
                "source_report_date"
            ],

            is_forecast=row[
                "is_forecast"
            ],
        )

        db.add(forecast)

        stored += 1

    db.commit()

    return stored