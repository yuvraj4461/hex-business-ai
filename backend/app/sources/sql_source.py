"""SQL adapter — read directly from a customer database.

For on-prem / legacy ERPs that have a database but no usable API. The
customer provides **read-only replica** credentials and one SELECT per
entity. Each query may reference a ``:since`` bind param for incremental
sync and should expose an ``external_id`` column (falls back to a row hash).

Security: HEX only ever issues the customer's SELECTs. Document that the
DB user must be read-only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.sources.base import (
    Capability,
    RawRecord,
    SourceAdapter,
    content_hash,
)

_EPOCH = datetime(1970, 1, 1)

# driver key -> SQLAlchemy dialect+driver
_DRIVERS = {
    "postgresql": "postgresql+psycopg2",
    "postgres": "postgresql+psycopg2",
    "mysql": "mysql+pymysql",
    "mariadb": "mysql+pymysql",
    "mssql": "mssql+pyodbc",
}


class SqlSourceAdapter(SourceAdapter):
    source_type = "sql"

    def _engine(self) -> Engine:
        c = self.credentials
        driver = _DRIVERS.get(
            (self.config.get("driver") or "postgresql").lower(),
            "postgresql+psycopg2",
        )
        url = (
            f"{driver}://{c['user']}:{c['password']}"
            f"@{c['host']}:{c.get('port', 5432)}/{c['database']}"
        )
        return create_engine(url, pool_pre_ping=True, pool_recycle=1800)

    def _queries(self) -> dict:
        return self.config.get("queries", {})

    def test_connection(self) -> tuple[bool, str]:
        try:
            engine = self._engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except KeyError as exc:
            return False, f"Missing credential field: {exc}"
        except Exception as exc:  # noqa: BLE001
            return False, f"Connection failed: {exc}"

        queries = self._queries()
        if not queries:
            return True, "Connected. No entity queries configured yet."
        return True, f"Connected. Queries for: {list(queries)}"

    def capabilities(self) -> list[Capability]:
        return [
            Capability(
                entity_type=entity,
                incremental=":since" in query,
            )
            for entity, query in self._queries().items()
        ]

    def fetch(
        self,
        entity_type: str,
        since: datetime | None = None,
    ) -> Iterator[RawRecord]:
        query = self._queries().get(entity_type)
        if not query:
            return

        params = {}
        if ":since" in query:
            params["since"] = since or _EPOCH

        engine = self._engine()
        with engine.connect() as conn:
            result = conn.execution_options(stream_results=True).execute(
                text(query), params
            )
            for row in result.mappings():
                payload = {k: _jsonable(v) for k, v in dict(row).items()}
                external_id = (
                    str(payload["external_id"])
                    if payload.get("external_id") not in (None, "")
                    else content_hash(payload)[:16]
                )
                yield RawRecord(
                    entity_type=entity_type,
                    external_id=external_id,
                    payload=payload,
                )


def _jsonable(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", "replace")
    try:
        import decimal

        if isinstance(value, decimal.Decimal):
            return float(value)
    except ImportError:  # pragma: no cover
        pass
    return value
