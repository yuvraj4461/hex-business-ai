"""Smoke test for the ingestion pipeline.

Run against the local database (matches the other test_*.py scripts):

    DATABASE_URL=postgresql://hex_admin:hex_password@localhost:5432/hex_business \
        python test_ingestion.py

Creates a throwaway file_upload connection in org 10, feeds it two
in-memory CSVs, syncs twice, asserts the canonical rows + idempotency,
then deletes everything it created.
"""

import csv
import io
import sys

from app.database.connection import SessionLocal
from app.ingestion.sync import run_sync
from app.models.connection import Connection
from app.models.expense import Expense
from app.models.supplier import Supplier
from app.sources.file_upload import connection_dir

ORG_ID = 10

SUPPLIERS_CSV = [
    {"code": "T-1", "name": "Test Supplier One", "country": "India",
     "lead_time_days": "18"},
    {"code": "T-2", "name": "Test Supplier Two", "country": "China",
     "lead_time_days": "40"},
]
EXPENSES_CSV = [
    {"ref": "TE-1", "category": "Freight", "amount": "12,500", "date": "2026-08-01"},
    {"ref": "TE-2", "category": "Duty", "amount": "3400", "date": "2026-08-02"},
]


def _write_csv(path, rows):
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    db = SessionLocal()
    conn = Connection(
        organization_id=ORG_ID,
        source_type="file_upload",
        display_name="__ingestion_smoke__",
        status="PENDING",
        config={},
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)

    try:
        folder = connection_dir(conn.id)
        _write_csv(folder / "supplier.csv", SUPPLIERS_CSV)
        _write_csv(folder / "expense.csv", EXPENSES_CSV)
        conn.config = {
            "uploads": {
                "supplier": {"path": str(folder / "supplier.csv"),
                             "id_column": "code"},
                "expense": {"path": str(folder / "expense.csv"),
                            "id_column": "ref"},
            }
        }
        db.commit()

        first = run_sync(db, conn)
        assert first["entities"]["supplier"]["inserted"] == 2, first
        assert first["entities"]["expense"]["inserted"] == 2, first

        suppliers = (
            db.query(Supplier)
            .filter(Supplier.source_connection_id == conn.id)
            .all()
        )
        assert {s.source_external_id for s in suppliers} == {"T-1", "T-2"}
        assert {s.country for s in suppliers} == {"India", "China"}
        assert any(s.lead_time_days == 40 for s in suppliers)

        expenses = (
            db.query(Expense)
            .filter(Expense.source_connection_id == conn.id)
            .all()
        )
        # "12,500" must be parsed as 12500.0
        assert any(abs(float(e.amount) - 12500.0) < 0.01 for e in expenses), (
            [float(e.amount) for e in expenses]
        )

        # Second sync = no changes -> everything skipped (idempotent).
        second = run_sync(db, conn)
        assert second["rows_written"] == 0, second
        assert second["entities"]["supplier"]["skipped"] == 2, second

        print("PASS: ingestion pipeline smoke test")
        return 0

    finally:
        for model in (Supplier, Expense):
            db.query(model).filter(
                model.source_connection_id == conn.id
            ).delete()
        db.query(Connection).filter(Connection.id == conn.id).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    sys.exit(main())
