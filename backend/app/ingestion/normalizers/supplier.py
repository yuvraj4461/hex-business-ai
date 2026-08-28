from app.ingestion.normalizers.base import Normalizer, to_int, to_str
from app.models.supplier import Supplier
from app.sources.base import EntityType, RawRecord


class SupplierNormalizer(Normalizer):
    entity_type = EntityType.SUPPLIER
    model = Supplier

    def map(self, db, raw: RawRecord, organization_id: int, connection_id: int):
        p = raw.payload
        name = to_str(self.source_field(p, "name"))
        if not name:
            return None

        return {
            "name": name,
            "contact_email": to_str(self.source_field(p, "contact_email")),
            "category": to_str(self.source_field(p, "category")),
            "status": to_str(self.source_field(p, "status")) or "ACTIVE",
            "country": to_str(self.source_field(p, "country")),
            "city": to_str(self.source_field(p, "city")),
            "lead_time_days": to_int(self.source_field(p, "lead_time_days")),
        }
