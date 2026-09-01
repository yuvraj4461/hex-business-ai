"""Conversational analytics — turn a plain-language question about the
organization's own data into a validated query spec, run it safely, and
narrate the result. Powers the "Ask Your Data" page.

Nothing here ever emits raw SQL from the model: the LLM only produces a
small JSON spec (metric + one dimension + filters) which is validated
against ``semantic.py`` and executed with parameterised SQLAlchemy,
always scoped to a single ``organization_id``.
"""

from app.analytics.service import answer_data_question

__all__ = ["answer_data_question"]
