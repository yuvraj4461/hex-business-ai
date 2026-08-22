def build_revenue_finding(
    historical_data: dict,
) -> dict:

    comparison = historical_data.get(
        "revenue_comparison",
        {},
    )

    if comparison.get("status") != "OK":
        return {
            "finding": "INSUFFICIENT_DATA",
            "message": comparison.get(
                "message",
                "Not enough historical data.",
            ),
        }

    category_data = historical_data.get(
        "category_comparison",
        [],
    )

    declining_categories = [
        item
        for item in category_data
        if item["difference"] < 0
    ]

    declining_categories.sort(
        key=lambda item: item["difference"]
    )

    return {
        "finding": "REVENUE_CHANGE",
        "direction": comparison["direction"],
        "previous_month": comparison[
            "previous_month"
        ],
        "latest_month": comparison[
            "latest_month"
        ],
        "percentage_change": comparison[
            "percentage_change"
        ],
        "revenue_difference": comparison[
            "difference"
        ],
        "top_declining_categories":
            declining_categories[:5],
    }