"""Verify the demo dataset in docs/demo-data/ ingests cleanly end-to-end.

    DATABASE_URL=postgresql://... python test_demo_data.py

Creates a throwaway file_upload connection, points it at the 8 demo CSVs,
syncs, and asserts the canonical rows + FK links (supplier -> PO -> shipment,
product -> inventory), then deletes everything it created.
"""

import os
import shutil
import sys

from app.database.connection import SessionLocal
from app.ingestion.sync import run_sync
from app.models.connection import Connection
from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from app.models.shipment import Shipment
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.transaction import Transaction
from app.models.business_exposure import BusinessExposure
from app.sources.file_upload import connection_dir

ORG_ID = 10
DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "docs", "demo-data"
)
ENTITIES = [
    "supplier", "product", "purchase_order", "purchase_order_line",
    "shipment", "inventory", "transaction", "expense",
]


def main() -> int:
    if not os.path.exists(os.path.join(DATA_DIR, "supplier.csv")):
        print("run docs/demo-data/generate.py first")
        return 1

    db = SessionLocal()
    conn = Connection(
        organization_id=ORG_ID, source_type="file_upload",
        display_name="__demo_data_smoke__", status="PENDING", config={},
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)

    try:
        folder = connection_dir(conn.id)
        uploads = {}
        for e in ENTITIES:
            shutil.copy(os.path.join(DATA_DIR, f"{e}.csv"), folder / f"{e}.csv")
            uploads[e] = {"path": str(folder / f"{e}.csv")}
        conn.config = {"uploads": uploads}
        db.commit()

        result = run_sync(db, conn)
        ent = result["entities"]
        assert ent["supplier"]["inserted"] == 6, ent
        assert ent["product"]["inserted"] == 8, ent
        assert ent["purchase_order"]["inserted"] == 5, ent
        assert ent["inventory"]["inserted"] == 8, ent
        assert ent["transaction"]["inserted"] >= 30, ent
        assert ent["expense"]["inserted"] >= 90, ent

        # FK links resolved by name
        pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.source_connection_id == conn.id
        ).all()
        assert all(p.supplier_id for p in pos), "PO -> supplier not linked"

        ships = db.query(Shipment).filter(
            Shipment.source_connection_id == conn.id
        ).all()
        assert ships and all(s.supplier_id and s.product_id for s in ships), \
            "shipment FKs not linked"
        assert any(s.purchase_order_id for s in ships), "shipment -> PO not linked"

        inv = db.query(Inventory).filter(
            Inventory.source_connection_id == conn.id
        ).all()
        assert all(i.product_id for i in inv), "inventory -> product not linked"
        low = [i for i in inv if i.quantity < i.reorder_level]
        assert len(low) >= 2, "expected some low-stock SKUs"

        rev = sum(
            float(t.amount) for t in db.query(Transaction).filter(
                Transaction.source_connection_id == conn.id
            )
        )
        assert rev > 10_000_000, rev

        # idempotent — every uploaded entity is skipped on a re-sync
        # (shipment_projection may still re-touch derived shipments)
        second = run_sync(db, conn)
        for e in ENTITIES:
            s = second["entities"][e]
            assert s["inserted"] == 0 and s["updated"] == 0, (e, s)

        print("PASS: demo data ingests and links cleanly")
        print(f"  6 suppliers, 8 products, 5 POs, {len(ships)} shipments, "
              f"{len(low)} low-stock SKUs, revenue INR {rev:,.0f}")
        return 0
    finally:
        # Shipment projection can create derived shipments (source_connection_id
        # is NULL) that reference the demo suppliers, so clean by FK too.
        sup_ids = [s.id for s in db.query(Supplier.id).filter(
            Supplier.source_connection_id == conn.id
        )]
        prod_ids = [p.id for p in db.query(Product.id).filter(
            Product.source_connection_id == conn.id
        )]
        ship_ids = [s.id for s in db.query(Shipment.id).filter(
            Shipment.supplier_id.in_(sup_ids or [-1])
        )]
        db.query(BusinessExposure).filter(
            BusinessExposure.shipment_id.in_(ship_ids or [-1])
        ).delete(synchronize_session=False)
        db.query(Shipment).filter(
            Shipment.supplier_id.in_(sup_ids or [-1])
        ).delete(synchronize_session=False)
        for m in (PurchaseOrderLine, PurchaseOrder, Inventory, Transaction,
                  Expense):
            db.query(m).filter(
                m.source_connection_id == conn.id
            ).delete(synchronize_session=False)
        db.query(Product).filter(
            Product.id.in_(prod_ids or [-1])
        ).delete(synchronize_session=False)
        db.query(Supplier).filter(
            Supplier.id.in_(sup_ids or [-1])
        ).delete(synchronize_session=False)
        db.query(Connection).filter(Connection.id == conn.id).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    sys.exit(main())
