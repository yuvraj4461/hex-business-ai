from sqlalchemy import select

from app.ingestion.normalizers.base import (
    Normalizer,
    find_product_id,
    find_supplier_id,
    to_date,
    to_float,
    to_str,
)
from app.models.purchase_order import PurchaseOrder
from app.models.shipment import Shipment
from app.models.supply_route import SupplyRoute
from app.sources.base import EntityType, RawRecord

_STATUS_MAP = {
    "PLANNED": "PLANNED",
    "BOOKED": "PLANNED",
    "IN TRANSIT": "IN_TRANSIT",
    "IN_TRANSIT": "IN_TRANSIT",
    "SHIPPED": "IN_TRANSIT",
    "ON WATER": "IN_TRANSIT",
    "DELAYED": "DELAYED",
    "ARRIVED": "ARRIVED",
    "DELIVERED": "ARRIVED",
    "CANCELLED": "CANCELLED",
    "CANCELED": "CANCELLED",
}


def _resolve_route(db, organization_id, supplier_id, product_id):
    q = select(SupplyRoute.id).where(
        SupplyRoute.organization_id == organization_id,
        SupplyRoute.status == "ACTIVE",
    )
    if supplier_id and product_id:
        r = db.execute(
            q.where(
                SupplyRoute.supplier_id == supplier_id,
                SupplyRoute.product_id == product_id,
            )
        ).scalar_one_or_none()
        if r:
            return r
    if supplier_id:
        r = db.execute(
            q.where(SupplyRoute.supplier_id == supplier_id)
        ).scalar_one_or_none()
        if r:
            return r
    if product_id:
        return db.execute(
            q.where(SupplyRoute.product_id == product_id)
        ).scalar_one_or_none()
    return None


class ShipmentNormalizer(Normalizer):
    entity_type = EntityType.SHIPMENT
    model = Shipment

    def map(self, db, raw: RawRecord, organization_id: int, connection_id: int):
        p = raw.payload
        reference = to_str(self.source_field(p, "reference")) or raw.external_id

        supplier_id = find_supplier_id(
            db,
            organization_id,
            name=to_str(self.source_field(p, "supplier")),
            external_id=to_str(self.source_field(p, "supplier_external_id")),
            connection_id=connection_id,
        )
        product_id = find_product_id(
            db,
            organization_id,
            name=to_str(self.source_field(p, "product")),
            external_id=to_str(self.source_field(p, "product_external_id")),
            connection_id=connection_id,
        )

        po_number = to_str(self.source_field(p, "po_number"))
        po_id = None
        if po_number:
            po_id = db.execute(
                select(PurchaseOrder.id).where(
                    PurchaseOrder.organization_id == organization_id,
                    PurchaseOrder.po_number == po_number,
                )
            ).scalar_one_or_none()

        route_id = _resolve_route(
            db, organization_id, supplier_id, product_id
        )

        raw_status = (to_str(self.source_field(p, "status")) or "").upper()
        status = _STATUS_MAP.get(raw_status, "PLANNED")

        return {
            "reference": reference,
            "purchase_order_id": po_id,
            "supplier_id": supplier_id,
            "product_id": product_id,
            "route_id": route_id,
            "origin_country": to_str(self.source_field(p, "origin_country")),
            "origin_port": to_str(self.source_field(p, "origin_port")),
            "destination_country": to_str(
                self.source_field(p, "destination_country")
            ),
            "destination_port": to_str(
                self.source_field(p, "destination_port")
            ),
            "carrier": to_str(self.source_field(p, "carrier")),
            "transport_mode": (
                to_str(self.source_field(p, "transport_mode")) or "SEA"
            ).upper(),
            "status": status,
            "etd": to_date(self.source_field(p, "etd")),
            "eta": to_date(self.source_field(p, "eta")),
            "ata": to_date(self.source_field(p, "ata")),
            "value_amount": to_float(self.source_field(p, "value_amount"))
            or 0,
            "currency": (
                to_str(self.source_field(p, "currency")) or "INR"
            ).upper()[:3],
            "is_derived": False,
        }
