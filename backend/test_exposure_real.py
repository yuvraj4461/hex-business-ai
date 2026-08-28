"""Smoke test: shipment-driven exposure.

    DATABASE_URL=postgresql://hex_admin:hex_password@localhost:5432/hex_business \
        python test_exposure_real.py

Exercises the geo matcher, shipment projection and exposure recompute for
org 10, cleaning up everything it creates.
"""

import sys
from datetime import datetime, timedelta

from app.database.connection import SessionLocal
from app.models.business_exposure import BusinessExposure
from app.models.global_event import GlobalEvent
from app.models.shipment import Shipment
from app.services import geo_exposure
from app.services.exposure_recompute import recompute_exposure

ORG_ID = 10


def _fake_event(region, country, severity="HIGH"):
    e = GlobalEvent(
        source="HEX_TEST",
        event_type="LOGISTICS",
        title=f"Test disruption in {region}",
        region=region,
        country=country,
        severity=severity,
        detected_at=datetime.utcnow(),
    )
    return e


def main() -> int:
    # 1. Geo matcher discriminates lanes.
    red_sea = _fake_event("Red Sea", None)
    ok, _ = geo_exposure.event_affects(
        red_sea, origin_country="India", destination_country="Netherlands"
    )
    assert ok, "India->NL should be hit by a Red Sea event"
    ok, _ = geo_exposure.event_affects(
        red_sea, origin_country="China", destination_country="India"
    )
    assert not ok, "China->India should NOT be hit by a Red Sea event"

    db = SessionLocal()
    event = _fake_event("Red Sea", None)
    db.add(event)
    db.flush()

    ship = Shipment(
        organization_id=ORG_ID,
        reference="TEST-SHIP-1",
        status="IN_TRANSIT",
        transport_mode="SEA",
        origin_country="India",
        destination_country="Germany",
        etd=datetime.utcnow(),
        eta=datetime.utcnow() + timedelta(days=20),
        value_amount=500000,
        currency="INR",
        is_derived=False,
    )
    db.add(ship)
    db.commit()

    try:
        written = recompute_exposure(db, ORG_ID, event)
        assert written >= 1, f"expected >=1 exposure, got {written}"

        rows = (
            db.query(BusinessExposure)
            .filter(BusinessExposure.global_event_id == event.id)
            .all()
        )
        shipment_rows = [r for r in rows if r.shipment_id == ship.id]
        assert shipment_rows, "no exposure row linked to the test shipment"
        assert float(shipment_rows[0].estimated_revenue_at_risk) == 500000.0

        # Zero-shipment fallback: a fresh event, delete shipment first.
        db.query(BusinessExposure).filter(
            BusinessExposure.global_event_id == event.id
        ).delete()
        db.delete(ship)
        db.commit()
        fallback = recompute_exposure(db, ORG_ID, event)
        # org 10 has seeded RED_SEA routes -> fallback should still produce rows
        assert fallback >= 1, "route-level fallback produced nothing"

        print("PASS: shipment-driven exposure smoke test")
        return 0
    finally:
        db.query(BusinessExposure).filter(
            BusinessExposure.global_event_id == event.id
        ).delete()
        db.query(Shipment).filter(
            Shipment.reference == "TEST-SHIP-1"
        ).delete()
        db.query(GlobalEvent).filter(
            GlobalEvent.source == "HEX_TEST"
        ).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    sys.exit(main())
