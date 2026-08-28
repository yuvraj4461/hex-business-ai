from sqlalchemy import select

from app.ingestion.normalizers.base import (
    Normalizer,
    find_product_id,
    find_supplier_id,
    to_date,
    to_float,
    to_str,
)
from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from app.sources.base import EntityType, RawRecord


class PurchaseOrderNormalizer(Normalizer):
    entity_type = EntityType.PURCHASE_ORDER
    model = PurchaseOrder

    def map(self, db, raw: RawRecord, organization_id: int, connection_id: int):
        p = raw.payload
        po_number = to_str(self.source_field(p, "po_number"))
        if not po_number:
            return None

        supplier_id = find_supplier_id(
            db,
            organization_id,
            name=to_str(self.source_field(p, "supplier")),
            external_id=to_str(self.source_field(p, "supplier_external_id")),
            connection_id=connection_id,
        )

        return {
            "po_number": po_number,
            "supplier_id": supplier_id,
            "status": to_str(self.source_field(p, "status")) or "OPEN",
            "currency": (
                to_str(self.source_field(p, "currency")) or "INR"
            ).upper()[:3],
            "total_amount": to_float(self.source_field(p, "total_amount"))
            or 0,
            "incoterm": to_str(self.source_field(p, "incoterm")),
            "order_date": to_date(self.source_field(p, "order_date")),
            "expected_date": to_date(self.source_field(p, "expected_date")),
        }


class PurchaseOrderLineNormalizer(Normalizer):
    entity_type = EntityType.PURCHASE_ORDER_LINE
    model = PurchaseOrderLine

    def map(self, db, raw: RawRecord, organization_id: int, connection_id: int):
        p = raw.payload
        po_number = to_str(self.source_field(p, "po_number"))
        if not po_number:
            return None

        po_id = db.execute(
            select(PurchaseOrder.id).where(
                PurchaseOrder.organization_id == organization_id,
                PurchaseOrder.po_number == po_number,
            )
        ).scalar_one_or_none()
        if po_id is None:
            # Parent PO not ingested yet — skip; a re-sync after the PO
            # file is uploaded will pick it up.
            return None

        product_id = find_product_id(
            db,
            organization_id,
            name=to_str(self.source_field(p, "product")),
            external_id=to_str(self.source_field(p, "product_external_id")),
            connection_id=connection_id,
        )

        return {
            "purchase_order_id": po_id,
            "product_id": product_id,
            "material_symbol": to_str(self.source_field(p, "material_symbol")),
            "description": to_str(self.source_field(p, "description")),
            "quantity": to_float(self.source_field(p, "quantity")) or 0,
            "unit_cost": to_float(self.source_field(p, "unit_cost")) or 0,
        }
