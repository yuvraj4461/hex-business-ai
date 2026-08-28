from app.ingestion.normalizers.base import Normalizer, to_float, to_str
from app.models.product import Product
from app.sources.base import EntityType, RawRecord


class ProductNormalizer(Normalizer):
    entity_type = EntityType.PRODUCT
    model = Product

    def map(self, db, raw: RawRecord, organization_id: int, connection_id: int):
        p = raw.payload
        name = to_str(self.source_field(p, "name"))
        if not name:
            return None

        return {
            "name": name,
            "category": to_str(self.source_field(p, "category")),
            "unit_price": to_float(self.source_field(p, "unit_price")) or 0,
        }
