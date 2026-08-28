"""Source adapter contract.

An adapter knows how to talk to one kind of external system and hand HEX
back plain records. It does not know anything about HEX's canonical
schema — mapping is the job of `app/ingestion/normalizers/`.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator


class EntityType:
    """Canonical entity names an adapter may emit."""

    SUPPLIER = "supplier"
    PRODUCT = "product"
    PURCHASE_ORDER = "purchase_order"
    PURCHASE_ORDER_LINE = "purchase_order_line"
    SALES_ORDER = "sales_order"
    TRANSACTION = "transaction"
    EXPENSE = "expense"
    INVENTORY = "inventory"
    BOM = "bom"
    SHIPMENT = "shipment"

    ALL = (
        SUPPLIER,
        PRODUCT,
        PURCHASE_ORDER,
        PURCHASE_ORDER_LINE,
        SALES_ORDER,
        TRANSACTION,
        EXPENSE,
        INVENTORY,
        BOM,
        SHIPMENT,
    )


def content_hash(payload: dict) -> str:
    """Stable hash of a payload so re-syncs can skip unchanged rows."""

    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class RawRecord:
    entity_type: str
    external_id: str
    payload: dict
    hash: str = field(default="")

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = content_hash(self.payload)


@dataclass
class Capability:
    entity_type: str
    incremental: bool = False  # supports `since` filtering


class SourceAdapter(ABC):
    """One adapter instance is bound to one Connection row."""

    source_type: str = ""

    def __init__(self, connection, credentials: dict) -> None:
        self.connection = connection
        self.config: dict = connection.config or {}
        self.credentials = credentials or {}

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Return (ok, message). Must not raise."""

    @abstractmethod
    def capabilities(self) -> list[Capability]:
        """Which entities this configured connection can produce."""

    @abstractmethod
    def fetch(
        self,
        entity_type: str,
        since: datetime | None = None,
    ) -> Iterator[RawRecord]:
        """Yield records for one entity, newer than `since` when supported."""
