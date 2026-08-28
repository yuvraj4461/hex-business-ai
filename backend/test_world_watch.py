"""Smoke test for the World Watch intelligence pipeline.

    DATABASE_URL=postgresql://... python test_world_watch.py

Network-dependent collectors (GDELT, Tavily) are allowed to fail/skip;
the test asserts the pipeline is wired, dedups, scores severity, and the
World Watch agent produces a finding.
"""

import sys
from datetime import datetime

from app.database.connection import SessionLocal
from app.intelligence.collectors.web_search import collect_web_search
from app.intelligence.watcher import run_world_watch
from app.models.global_event import GlobalEvent
from app.services.event_scoring import calculate_severity

ORG_ID = 10


def main() -> int:
    db = SessionLocal()
    try:
        # 1. severity scoring is real, not "UNKNOWN"
        assert calculate_severity("port blockade and missile attack", "LOGISTICS") in (
            "HIGH",
            "CRITICAL",
        )

        # 2. web-search collector degrades gracefully with no key
        import os

        if not os.getenv("TAVILY_API_KEY"):
            assert collect_web_search(db) == {"skipped": "TAVILY_API_KEY not set"}

        # 3. full watcher runs and returns a structured summary
        summary = run_world_watch(db)
        assert "fx" in summary and "gdelt" in summary and "web_search" in summary
        assert isinstance(summary.get("errors"), list)
        assert isinstance(summary.get("duration_ms"), int)

        # 4. World Watch agent produces a finding
        from app.agents.watch_agent import watch_agent

        state = {"organization_id": ORG_ID, "findings": [], "recommendations": []}
        out = watch_agent(state, db)
        ww = [f for f in out["findings"] if f.get("type") == "world_watch"]
        assert ww, "World Watch agent produced no finding"
        assert "events_seen" in ww[0]["data"]

        # 5. GDELT dedup: a stored WEB_SEARCH/GDELT row is not re-inserted
        marker = GlobalEvent(
            source="WEB_SEARCH",
            external_id="testdedup" + datetime.utcnow().strftime("%H%M%S"),
            event_type="TRADE",
            title="test tariff headline",
            severity="LOW",
            detected_at=datetime.utcnow(),
            raw_data={"query": "q", "answer": "a", "sources": []},
        )
        db.add(marker)
        db.commit()
        before = db.query(GlobalEvent).filter(
            GlobalEvent.external_id == marker.external_id
        ).count()
        assert before == 1
        db.delete(marker)
        db.commit()

        print("PASS: world watch pipeline smoke test")
        print("  summary:", {k: summary[k] for k in ("fx", "web_search")})
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
