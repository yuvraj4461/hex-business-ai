"""Merge.dev unified Accounting API adapter.

One integration that reaches QuickBooks, Xero, NetSuite, Sage Intacct,
MS Dynamics, etc. The app-level key is ``MERGE_API_KEY``; each linked
company contributes an ``account_token`` (obtained via Merge Link, see
``app/api/merge.py``) stored encrypted in the connection credentials.

The adapter does the Merge-specific mapping itself — it emits flat dicts
keyed to HEX canonical column names, so the normalizers in
``app/ingestion/normalizers`` run unchanged.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Iterator

import requests

from app.sources.base import (
    Capability,
    EntityType,
    RawRecord,
    SourceAdapter,
)

MERGE_API_KEY = os.getenv("MERGE_API_KEY")
MERGE_BASE = os.getenv(
    "MERGE_BASE_URL", "https://api.merge.dev/api/accounting/v1"
)

_ENTITY_PATH = {
    EntityType.SUPPLIER: "contacts",
    EntityType.PRODUCT: "items",
    EntityType.PURCHASE_ORDER: "purchase-orders",
    EntityType.PURCHASE_ORDER_LINE: "purchase-orders",
    EntityType.EXPENSE: "invoices",
}


def is_configured() -> bool:
    return bool(MERGE_API_KEY)


class MergeAdapter(SourceAdapter):
    source_type = "merge"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {MERGE_API_KEY}",
            "X-Account-Token": self.credentials.get("account_token", ""),
        }

    def _get(self, path: str, params: dict) -> dict:
        resp = requests.get(
            f"{MERGE_BASE}/{path}",
            headers=self._headers(),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _paginate(self, path: str, params: dict) -> Iterator[dict]:
        cursor = None
        while True:
            page = self._get(path, {**params, "cursor": cursor} if cursor else params)
            yield from page.get("results", [])
            cursor = page.get("next")
            if not cursor:
                break

    # --- SourceAdapter -------------------------------------------------

    def test_connection(self) -> tuple[bool, str]:
        if not is_configured():
            return False, "Merge is not configured (set MERGE_API_KEY)."
        if not self.credentials.get("account_token"):
            return False, "No Merge account linked yet."
        try:
            info = self._get("company-info", {"page_size": 1})
            n = len(info.get("results", []))
            return True, f"Connected to Merge ({n} company record)."
        except requests.RequestException as exc:
            return False, f"Merge request failed: {exc}"

    def capabilities(self) -> list[Capability]:
        if not is_configured() or not self.credentials.get("account_token"):
            return []
        return [
            Capability(entity_type=e, incremental=True)
            for e in _ENTITY_PATH
        ]

    def fetch(
        self,
        entity_type: str,
        since: datetime | None = None,
    ) -> Iterator[RawRecord]:
        if not is_configured():
            raise RuntimeError("Merge is not configured (set MERGE_API_KEY).")

        path = _ENTITY_PATH.get(entity_type)
        if not path:
            return

        params: dict = {"page_size": 100}
        if since:
            params["modified_after"] = since.isoformat()
        if entity_type == EntityType.SUPPLIER:
            params["is_supplier"] = "true"
        if entity_type in (
            EntityType.PURCHASE_ORDER,
            EntityType.PURCHASE_ORDER_LINE,
        ):
            params["expand"] = "line_items,vendor"
        if entity_type == EntityType.EXPENSE:
            params["type"] = "ACCOUNTS_PAYABLE"

        for obj in self._paginate(path, params):
            yield from _to_records(entity_type, obj)


def _addr_field(obj: dict, field: str) -> str | None:
    for addr in obj.get("addresses") or []:
        if addr.get(field):
            return addr[field]
    return None


def _to_records(entity_type: str, obj: dict) -> Iterator[RawRecord]:
    oid = str(obj.get("id"))

    if entity_type == EntityType.SUPPLIER:
        yield RawRecord(
            entity_type,
            oid,
            {
                "name": obj.get("name"),
                "contact_email": obj.get("email_address"),
                "country": _addr_field(obj, "country"),
                "city": _addr_field(obj, "city"),
                "status": obj.get("status") or "ACTIVE",
            },
        )

    elif entity_type == EntityType.PRODUCT:
        yield RawRecord(
            entity_type,
            oid,
            {
                "name": obj.get("name"),
                "unit_price": obj.get("unit_price")
                or obj.get("purchase_price"),
            },
        )

    elif entity_type == EntityType.PURCHASE_ORDER:
        vendor = obj.get("vendor")
        yield RawRecord(
            entity_type,
            oid,
            {
                "po_number": obj.get("number") or oid,
                "status": obj.get("status") or "OPEN",
                "order_date": obj.get("issue_date"),
                "expected_date": obj.get("delivery_date"),
                "total_amount": obj.get("total_amount"),
                "currency": obj.get("currency") or "USD",
                "supplier_external_id": (
                    vendor.get("id") if isinstance(vendor, dict) else vendor
                ),
            },
        )

    elif entity_type == EntityType.PURCHASE_ORDER_LINE:
        po_number = obj.get("number") or oid
        for i, line in enumerate(obj.get("line_items") or []):
            item = line.get("item")
            yield RawRecord(
                entity_type,
                f"{oid}:{line.get('id', i)}",
                {
                    "po_number": po_number,
                    "product_external_id": (
                        item.get("id") if isinstance(item, dict) else item
                    ),
                    "description": line.get("description"),
                    "quantity": line.get("quantity"),
                    "unit_cost": line.get("unit_price"),
                },
            )

    elif entity_type == EntityType.EXPENSE:
        yield RawRecord(
            entity_type,
            oid,
            {
                "category": "Accounts Payable",
                "amount": obj.get("total_amount"),
                "date": obj.get("issue_date"),
                "description": obj.get("memo") or obj.get("number"),
            },
        )
