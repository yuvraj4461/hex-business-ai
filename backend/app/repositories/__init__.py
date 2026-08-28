"""Data-access seam between analysis code and the canonical tables.

Phase 1 leaves this intentionally thin. As `app/agents/*` and
`app/services/*` are touched, their raw ``db.query(...)`` calls move here
so that "where the data comes from" (seeded vs. synced from a connection)
lives in one place and analysis stays identical either way.
"""
