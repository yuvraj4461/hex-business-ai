"""Standing web-search queries for the World Watch pipeline.

Each entry drives one Tavily news search. `category` seeds the stored
event_type; `severity_hint` nudges scoring when the text is ambiguous.
"""

# Phrased to surface actual *incidents* (something happened) rather than
# market previews / "week ahead" commentary, which are not actionable
# supply-chain events.
STANDING_QUERIES: list[dict] = [
    {
        "query": "container freight rates spike surcharge shipping carriers this week",
        "category": "FREIGHT",
    },
    {
        "query": "government imposes new tariff import duty export ban trade restriction",
        "category": "TARIFF",
    },
    {
        "query": "commodity price spike shortage steel aluminum copper wheat crude oil",
        "category": "PRICE_SHOCK",
    },
    {
        "query": "port closed strike blockade vessels stranded shipping halted",
        "category": "LOGISTICS",
        "severity_hint": "HIGH",
    },
    {
        "query": "factory shutdown production halt supplier disruption manufacturing plant",
        "category": "LOGISTICS",
    },
    {
        "query": "currency crash devaluation inflation spike export controls country",
        "category": "INFLATION",
    },
    {
        "query": "Red Sea Suez Panama Taiwan Strait Hormuz shipping attack blocked rerouting",
        "category": "GEOPOLITICAL",
        "severity_hint": "HIGH",
    },
    {
        "query": "earthquake flood cyclone typhoon disrupts port factory logistics",
        "category": "NATURAL_DISASTER",
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
    "NATURAL_DISASTER": "NATURAL_DISASTER",
}
