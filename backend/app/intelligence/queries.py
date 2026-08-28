"""Standing web-search queries for the World Watch pipeline.

Each entry drives one Tavily news search. `category` seeds the stored
event_type; `severity_hint` nudges scoring when the text is ambiguous.
"""

STANDING_QUERIES: list[dict] = [
    {
        "query": "global container shipping freight rate changes this week",
        "category": "FREIGHT",
    },
    {
        "query": "new import export tariffs or trade restrictions announced this week",
        "category": "TARIFF",
    },
    {
        "query": "commodity price surge steel aluminum copper wheat crude oil this week",
        "category": "PRICE_SHOCK",
    },
    {
        "query": "major port strike closure or shipping lane disruption today",
        "category": "LOGISTICS",
        "severity_hint": "HIGH",
    },
    {
        "query": "central bank interest rate decision and inflation data this week",
        "category": "INFLATION",
    },
    {
        "query": "Red Sea Suez Panama Canal Taiwan Strait shipping disruption latest",
        "category": "GEOPOLITICAL",
        "severity_hint": "HIGH",
    },
]

# category -> canonical GlobalEvent.event_type
CATEGORY_EVENT_TYPE = {
    "FREIGHT": "LOGISTICS",
    "TARIFF": "TRADE",
    "PRICE_SHOCK": "PRICE_SHOCK",
    "LOGISTICS": "LOGISTICS",
    "INFLATION": "ECONOMIC",
    "GEOPOLITICAL": "GEOPOLITICAL",
}
