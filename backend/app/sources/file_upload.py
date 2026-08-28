"""File-upload adapter — CSV / Excel.

Universal, no auth: any business can export a spreadsheet from any system
and drop it in. One connection can hold one file per entity type. The
uploaded file is stored under ``backend/data/uploads/{connection_id}/`` and
its location + options are recorded in ``connection.config["uploads"]``.
"""

from __future__ import annotations

import math
import os
from datetime import datetime
from pathlib import Path
from typing import Iterator

import pandas as pd

from app.sources.base import (
    Capability,
    EntityType,
    RawRecord,
    SourceAdapter,
    content_hash,
)

UPLOAD_ROOT = Path(
    os.getenv("HEX_UPLOAD_DIR", "data/uploads")
)


def connection_dir(connection_id: int) -> Path:
    path = UPLOAD_ROOT / str(connection_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=str)
    return pd.read_csv(path, dtype=str)


class FileUploadAdapter(SourceAdapter):
    source_type = "file_upload"

    def _uploads(self) -> dict:
        return self.config.get("uploads", {})

    def test_connection(self) -> tuple[bool, str]:
        uploads = self._uploads()
        if not uploads:
            return False, "No files uploaded yet."

        missing = [
            e for e, u in uploads.items() if not Path(u["path"]).exists()
        ]
        if missing:
            return False, f"Uploaded file missing on disk for: {missing}"

        return True, f"{len(uploads)} file(s) ready: {list(uploads)}"

    def capabilities(self) -> list[Capability]:
        return [
            Capability(entity_type=e, incremental=False)
            for e in self._uploads()
        ]

    def fetch(
        self,
        entity_type: str,
        since: datetime | None = None,
    ) -> Iterator[RawRecord]:
        upload = self._uploads().get(entity_type)
        if not upload:
            return

        frame = _read_frame(Path(upload["path"]))
        id_column = upload.get("id_column")

        for position, row in enumerate(frame.to_dict(orient="records")):
            payload = {
                k: (None if _is_nan(v) else v) for k, v in row.items()
            }

            if id_column and payload.get(id_column) not in (None, ""):
                external_id = str(payload[id_column])
            else:
                external_id = content_hash(payload)[:16]

            yield RawRecord(
                entity_type=entity_type,
                external_id=external_id,
                payload=payload,
            )


def _is_nan(value: object) -> bool:
    return isinstance(value, float) and math.isnan(value)


# Entity types a file upload is allowed to target.
SUPPORTED_ENTITIES = (
    EntityType.SUPPLIER,
    EntityType.PRODUCT,
    EntityType.PURCHASE_ORDER,
    EntityType.PURCHASE_ORDER_LINE,
    EntityType.SALES_ORDER,
    EntityType.TRANSACTION,
    EntityType.EXPENSE,
    EntityType.INVENTORY,
    EntityType.BOM,
    EntityType.SHIPMENT,
)
