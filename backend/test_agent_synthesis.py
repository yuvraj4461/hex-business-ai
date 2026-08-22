from app.ai.agent_synthesis import (
    synthesize_agent_findings,
)


findings = [
    {
        "agent": "Finance Agent",
        "type": "financial_analysis",
        "data": {
            "revenue": 4500000,
            "expenses": 3200000,
            "profit": 1300000,
        },
    },
    {
        "agent": "Sales Agent",
        "type": "sales_analysis",
        "data": {
            "total_orders": 60,
            "completed_orders": 45,
            "cancelled_orders": 15,
        },
    },
    {
        "agent": "Operations Agent",
        "type": "operations_analysis",
        "data": {
            "low_stock_products": 3,
            "at_risk_suppliers": 1,
        },
    },
    {
        "agent": "Risk Agent",
        "type": "risk_analysis",
        "data": {
            "risk_flags": [
                {
                    "type": "LOW_STOCK",
                    "severity": "MEDIUM",
                },
                {
                    "type": "SUPPLIER_RISK",
                    "severity": "HIGH",
                },
            ],
        },
    },
]


answer = synthesize_agent_findings(
    question="What are the biggest risks in my business?",
    findings=findings,
    recommendations=[],
)


print(answer)