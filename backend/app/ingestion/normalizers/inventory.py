from app.ingestion.normalizers.base import (
    Normalizer,
    find_product_id,
    to_int,
    to_str,
)
from app.models.inventory import Inventory
from app.sources.base import EntityType, RawRecord


class InventoryNormalizer(Normalizer):
    entity_type = EntityType.INVENTORY
    model = Inventory

    def map(self, db, raw: RawRecord, organization_id: int, connection_id: int):
        p = raw.payload

        product_id = find_product_id(
            db,
            organization_id,
            name=to_str(self.source_field(p, "product")),
            external_id=to_str(self.source_field(p, "product_external_id")),
            connection_id=connection_id,
        )
        if product_id is None:
            # Inventory.product_id is NOT NULL — skip rows we can't link.
            return None

        return {
            "product_id": product_id,
            "quantity": to_int(self.source_field(p, "quantity")) or 0,
            "reorder_level": to_int(self.source_field(p, "reorder_level"))
            or 0,
            "safety_stock": to_int(self.source_field(p, "safety_stock")) or 0,
        }
