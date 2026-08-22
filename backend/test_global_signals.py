from pprint import pprint

from app.services.global_signals import (
    collect_global_signals,
)


signals = collect_global_signals(
    latitude=30.7333,
    longitude=76.7794,
)

pprint(signals)