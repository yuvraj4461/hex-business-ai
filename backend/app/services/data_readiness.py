"""Per-domain view of how much of an org's operational data HEX holds.

Mirrors the agent-readiness idea on /agents: tells the user which analyses
can run and what to connect next.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.connection import Connection
from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.purchase_order import PurchaseOrder
from app.models.supplier import Supplier
from app.models.supply_route import SupplyRoute
from app.models.transaction import Transaction

# domain -> canonical models that feed it
DOMAINS: dict[str, list] = {
    "procurement": [Supplier, PurchaseOrder],
    "logistics": [SupplyRoute],
    "inventory": [Inventory],
    "demand": [Order],
    "finance": [Transaction, Expense],
}


def _model_stats(db: Session, model, organization_id: int) -> dict:
    total = db.execute(
        select(func.count(model.id)).where(
            model.organization_id == organization_id
        )
    ).scalar_one()

    synced = db.execute(
        select(func.count(model.id)).where(
            model.organization_id == organization_id,
            model.source_connection_id.is_not(None),
        )
    ).scalar_one()

    last_synced = db.execute(
        select(func.max(model.synced_at)).where(
            model.organization_id == organization_id
        )
    ).scalar_one_or_none()

    conn_ids = db.execute(
        select(model.source_connection_id)
        .where(
            model.organization_id == organization_id,
            model.source_connection_id.is_not(None),
        )
        .distinct()
    ).scalars().all()

    return {
        "total": total,
        "synced": synced,
        "last_synced": last_synced,
        "connection_ids": [c for c in conn_ids if c],
    }


def get_readiness(db: Session, organization_id: int) -> dict:
    conn_names = dict(
        db.execute(
            select(Connection.id, Connection.display_name).where(
                Connection.organization_id == organization_id
            )
        ).all()
    )

    domains = []
    ready_count = 0

    for domain, models in DOMAINS.items():
        total = synced = 0
        last_synced = None
        source_ids: set[int] = set()

        for model in models:
            s = _model_stats(db, model, organization_id)
            total += s["total"]
            synced += s["synced"]
            source_ids.update(s["connection_ids"])
            if s["last_synced"] and (
                last_synced is None or s["last_synced"] > last_synced
            ):
                last_synced = s["last_synced"]

        if total == 0:
            status = "MISSING"
            detail = "No data. Connect a source or upload a file."
        elif synced == 0:
            status = "PARTIAL"
            detail = f"{total} rows present, none from a live connection."
        else:
            status = "READY"
            detail = f"{total} rows ({synced} synced)."
            ready_count += 1

        domains.append(
            {
                "domain": domain,
                "status": status,
                "detail": detail,
                "row_count": total,
                "synced_row_count": synced,
                "last_synced_at": last_synced,
                "sources": [
                    conn_names.get(cid, f"connection {cid}")
                    for cid in sorted(source_ids)
                ],
            }
        )

    overall = (
        "READY"
        if ready_count == len(DOMAINS)
        else "PARTIAL"
        if ready_count
        else "MISSING"
    )

    return {
        "organization_id": organization_id,
        "overall": overall,
        "domains": domains,
    }
