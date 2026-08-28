"""Registry of entity normalizers."""

from app.ingestion.normalizers.base import Normalizer
from app.ingestion.normalizers.finance import (
    ExpenseNormalizer,
    TransactionNormalizer,
)
from app.ingestion.normalizers.inventory import InventoryNormalizer
from app.ingestion.normalizers.product import ProductNormalizer
from app.ingestion.normalizers.purchase_order import (
    PurchaseOrderLineNormalizer,
    PurchaseOrderNormalizer,
)
from app.ingestion.normalizers.shipment import ShipmentNormalizer
from app.ingestion.normalizers.supplier import SupplierNormalizer

NORMALIZERS: dict[str, type[Normalizer]] = {
    n.entity_type: n
    for n in (
        SupplierNormalizer,
        ProductNormalizer,
        TransactionNormalizer,
        ExpenseNormalizer,
        InventoryNormalizer,
        PurchaseOrderNormalizer,
        PurchaseOrderLineNormalizer,
        ShipmentNormalizer,
    )
}

# Order matters: parents before children (FK resolution during sync).
SYNC_ORDER = [
    SupplierNormalizer.entity_type,
    ProductNormalizer.entity_type,
    PurchaseOrderNormalizer.entity_type,
    PurchaseOrderLineNormalizer.entity_type,
    ShipmentNormalizer.entity_type,
    InventoryNormalizer.entity_type,
    TransactionNormalizer.entity_type,
    ExpenseNormalizer.entity_type,
]


def get_normalizer(entity_type: str, mapping: dict | None = None) -> Normalizer:
    cls = NORMALIZERS[entity_type]
    return cls(mapping=mapping)
