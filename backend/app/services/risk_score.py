def calculate_business_risk_score(
    exposure_summary: dict,
) -> dict:

    financial = (
        exposure_summary[
            "financial"
        ]
    )

    exposure_count = len(
        exposure_summary[
            "exposures"
        ]
    )

    revenue_at_risk = float(
        financial[
            "total_revenue_at_risk"
        ]
    )

    score = 0

    # Exposure quantity
    if exposure_count >= 10:
        score += 30

    elif exposure_count >= 5:
        score += 20

    elif exposure_count >= 1:
        score += 10

    # Revenue risk
    if revenue_at_risk >= 1000000:
        score += 40

    elif revenue_at_risk >= 500000:
        score += 30

    elif revenue_at_risk >= 100000:
        score += 20

    elif revenue_at_risk > 0:
        score += 10

    # High-severity routes
    high_risk_count = sum(
        1
        for item
        in exposure_summary[
            "exposures"
        ]
        if item["severity"]
        == "HIGH"
    )

    if high_risk_count >= 5:
        score += 30

    elif high_risk_count >= 2:
        score += 20

    elif high_risk_count == 1:
        score += 10

    score = min(
        score,
        100,
    )

    if score >= 75:
        level = "CRITICAL"

    elif score >= 50:
        level = "HIGH"

    elif score >= 25:
        level = "MEDIUM"

    else:
        level = "LOW"

    return {
        "score": score,
        "level": level,
        "exposure_count":
            exposure_count,
        "high_risk_count":
            high_risk_count,
        "revenue_at_risk":
            revenue_at_risk,
    }