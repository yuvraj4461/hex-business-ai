"""Run one sync for one connection: fetch -> land raw -> normalize -> upsert."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.normalizers import SYNC_ORDER, get_normalizer
from app.models.audit_log import AuditLog
from app.models.connection import Connection
from app.models.raw_record import RawRecord as RawRecordModel
from app.sources.base import RawRecord as RawRecordDTO
from app.sources.registry import get_adapter

logger = logging.getLogger(__name__)


def _parse_since(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _land_raw(
    db: Session,
    connection_id: int,
    dto: RawRecordDTO,
) -> RawRecordModel:
    row = db.execute(
        select(RawRecordModel).where(
            RawRecordModel.connection_id == connection_id,
            RawRecordModel.entity_type == dto.entity_type,
            RawRecordModel.external_id == dto.external_id,
        )
    ).scalar_one_or_none()

    if row is None:
        row = RawRecordModel(
            connection_id=connection_id,
            entity_type=dto.entity_type,
            external_id=dto.external_id,
            payload=dto.payload,
            content_hash=dto.hash,
        )
        db.add(row)
        db.flush()
        return row

    if row.content_hash != dto.hash:
        row.payload = dto.payload
        row.content_hash = dto.hash
        row.normalized_at = None  # force re-normalization

    return row


def run_sync(
    db: Session,
    connection: Connection,
    entities: list[str] | None = None,
) -> dict:
    """Synchronise a connection. Commits its own work; never raises."""

    adapter = get_adapter(connection)
    available = {c.entity_type for c in adapter.capabilities()}
    targets = [
        e
        for e in SYNC_ORDER
        if e in available and (entities is None or e in entities)
    ]

    mapping_cfg = (connection.config or {}).get("mapping", {})
    started = datetime.utcnow()
    stats: dict[str, dict] = {}
    errors: list[str] = []

    for entity in targets:
        normalizer = get_normalizer(entity, mapping_cfg.get(entity))
        since = _parse_since((connection.cursor or {}).get(entity))
        fetched = inserted = updated = skipped = failed = 0

        try:
            for dto in adapter.fetch(entity, since=since):
                fetched += 1
                try:
                    # One savepoint per record: a bad row is isolated.
                    with db.begin_nested():
                        raw_row = _land_raw(db, connection.id, dto)

                        if raw_row.normalized_at is not None:
                            skipped += 1
                            continue

                        mapped = normalizer.map(
                            db,
                            dto,
                            connection.organization_id,
                            connection.id,
                        )
                        if mapped is None:
                            skipped += 1
                        else:
                            outcome = normalizer.upsert(
                                db,
                                mapped,
                                connection.organization_id,
                                connection.id,
                                dto.external_id,
                            )
                            inserted += outcome == "inserted"
                            updated += outcome == "updated"

                        raw_row.normalized_at = datetime.utcnow()
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    logger.exception(
                        "Normalize failed: connection=%s entity=%s ext=%s",
                        connection.id,
                        entity,
                        dto.external_id,
                    )
                    errors.append(f"{entity}:{dto.external_id}: {exc}")

            # advance cursor for incremental sources
            cursor = dict(connection.cursor or {})
            cursor[entity] = started.isoformat()
            connection.cursor = cursor

        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Fetch failed: connection=%s entity=%s",
                connection.id,
                entity,
            )
            errors.append(f"{entity}: {exc}")

        stats[entity] = {
            "fetched": fetched,
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
        }

    # Keep derived shipments in step with any PO changes this sync brought in.
    if "purchase_order" in stats:
        try:
            from app.services.shipment_projection import project_shipments

            stats["shipment_projection"] = project_shipments(
                db, connection.organization_id
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Shipment projection failed post-sync")
            errors.append(f"shipment_projection: {exc}")

    connection.last_sync_at = datetime.utcnow()
    connection.last_error = "; ".join(errors)[:2000] or None
    connection.status = "ERROR" if errors and not stats else "ACTIVE"

    db.add(
        AuditLog(
            organization_id=connection.organization_id,
            action="connection.sync",
            entity_type="connection",
            entity_id=connection.id,
            description=f"Synced {connection.display_name}",
            data={"stats": stats, "errors": errors[:20]},
        )
    )
    db.commit()

    total_written = sum(
        s.get("inserted", 0) + s.get("updated", 0)
        for s in stats.values()
    )
    return {
        "connection_id": connection.id,
        "duration_ms": int(
            (datetime.utcnow() - started).total_seconds() * 1000
        ),
        "entities": stats,
        "rows_written": total_written,
        "errors": errors,
        "status": connection.status,
    }
