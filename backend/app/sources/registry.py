"""Maps `connection.source_type` -> adapter class, and builds instances."""

from __future__ import annotations

from app.security.crypto import decrypt_dict
from app.sources.base import SourceAdapter
from app.sources.file_upload import FileUploadAdapter
from app.sources.merge_adapter import MergeAdapter
from app.sources.sql_source import SqlSourceAdapter

ADAPTERS: dict[str, type[SourceAdapter]] = {
    FileUploadAdapter.source_type: FileUploadAdapter,
    SqlSourceAdapter.source_type: SqlSourceAdapter,
    MergeAdapter.source_type: MergeAdapter,
}


def is_supported(source_type: str) -> bool:
    return source_type in ADAPTERS


def get_adapter(connection) -> SourceAdapter:
    adapter_cls = ADAPTERS.get(connection.source_type)
    if adapter_cls is None:
        raise ValueError(
            f"No adapter registered for source_type={connection.source_type!r}"
        )

    credentials = decrypt_dict(connection.credentials_encrypted)
    return adapter_cls(connection, credentials)
