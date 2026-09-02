"""Live web research for the Copilot — Google (SerpApi) + Wikipedia.

The Copilot grounds its answers in outside facts (prices, tariffs, events,
definitions) and then lets the specialist agents interpret them. This
module does the fetching; ``app/ai/agent_synthesis.py`` does the reasoning.

Degrades gracefully:
  - no SerpApi key  -> Wikipedia-only
  - any network error -> empty results, never raises
"""

from __future__ import annotations

import logging
import os
import re

import requests

logger = logging.getLogger(__name__)

# The question names something that genuinely lives outside the company's
# own database.
_EXPLICIT_EXTERNAL = re.compile(
    r"\b(price|prices|pricing|tariff|tariffs|inflation|interest rate|"
    r"exchange rate|\bfx\b|currency|commodit\w*|stock market|the market|"
    r"competitor\w*|industry|sector|news|headline\w*|geopolit\w*|\bwar\b|"
    r"sanction\w*|regulat\w*|\btax(es|ation)?\b|\bgdp\b|export\w*|import\w*|"
    r"worldwide|global economy|red sea|suez|panama canal|strait of|"
    r"shipping (route|lane|disruption)|freight rate|benchmark)\b",
    re.I,
)
# "My revenue", "how are WE doing", "the company" — an internal question.
_INTERNAL = re.compile(
    r"\b(my|our|we|us|the business|the company|the org\w*|this (quarter|month|"
    r"year|week))\b",
    re.I,
)
# Generic "what is X / define X / explain X" — worth a Wikipedia lookup,
# but only when it isn't really about the company.
_DEFINITIONAL = re.compile(
    r"\b(what (is|are|does)|who is|define|definition of|explain|meaning of|"
    r"how (do|does) .+ work)\b",
    re.I,
)


def looks_outward(query: str) -> bool:
    q = query or ""
    if _EXPLICIT_EXTERNAL.search(q):
        return True
    if _INTERNAL.search(q):
        return False
    return bool(_DEFINITIONAL.search(q))

SERPAPI_URL = "https://serpapi.com/search.json"
WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"

_TIMEOUT = 15


def _serp_key() -> str | None:
    # Same accessor as the World Watch web-search collector.
    key = os.getenv("SERPAPI_KEY") or os.getenv("TAVILY_API_KEY")
    if key and key.startswith("tvly-"):
        return None  # a Tavily key won't work against SerpApi
    return key


def _google(query: str, max_results: int) -> list[dict]:
    key = _serp_key()
    if not key:
        return []
    try:
        resp = requests.get(
            SERPAPI_URL,
            params={"engine": "google", "q": query, "num": max_results, "api_key": key},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise RuntimeError(data["error"])
        out = []
        for r in (data.get("organic_results") or [])[:max_results]:
            out.append(
                {
                    "title": r.get("title"),
                    "url": r.get("link"),
                    "snippet": r.get("snippet"),
                    "source": r.get("source")
                    or (r.get("displayed_link") or "").split("/")[0],
                }
            )
        # answer box / knowledge graph, if present, as a lead result
        box = data.get("answer_box") or {}
        ans = box.get("answer") or box.get("snippet")
        if ans:
            out.insert(
                0,
                {
                    "title": box.get("title") or "Featured answer",
                    "url": box.get("link"),
                    "snippet": ans,
                    "source": "Google",
                },
            )
        return [r for r in out if r.get("title")]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google research failed for %r: %s", query, exc)
        return []


def _wikipedia(query: str) -> dict | None:
    try:
        resp = requests.get(
            WIKI_SEARCH,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 1,
            },
            headers={"User-Agent": "HEX-Business-AI/1.0 (research)"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        hits = resp.json().get("query", {}).get("search", [])
        if not hits:
            return None
        title = hits[0]["title"]

        s = requests.get(
            WIKI_SUMMARY + requests.utils.quote(title.replace(" ", "_")),
            headers={"User-Agent": "HEX-Business-AI/1.0 (research)"},
            timeout=_TIMEOUT,
        )
        s.raise_for_status()
        body = s.json()
        return {
            "title": body.get("title") or title,
            "summary": (body.get("extract") or "").strip(),
            "url": (body.get("content_urls") or {})
            .get("desktop", {})
            .get("page")
            or f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Wikipedia research failed for %r: %s", query, exc)
        return None


def research(query: str, max_results: int = 5) -> dict:
    """Return {provider, results, wikipedia} for a natural-language query.

    Wikipedia is only consulted for definitional / entity questions —
    otherwise its search returns a loosely-matched article that pollutes
    the answer.
    """

    query = (query or "").strip()
    if not query:
        return {"provider": "none", "results": [], "wikipedia": None}

    results = _google(query, max_results)
    wiki = _wikipedia(query) if _DEFINITIONAL.search(query) else None

    provider = "serpapi+wikipedia" if results and wiki else (
        "serpapi" if results else "wikipedia" if wiki else "none"
    )

    return {"provider": provider, "results": results, "wikipedia": wiki}


def sources_from(research_result: dict) -> list[dict]:
    """Flatten a research() result into a deduped [{title, url}] list."""

    seen: set[str] = set()
    out: list[dict] = []
    for r in research_result.get("results", []):
        url = r.get("url")
        if url and url not in seen:
            seen.add(url)
            out.append({"title": r.get("title") or url, "url": url})
    wiki = research_result.get("wikipedia")
    if wiki and wiki.get("url") and wiki["url"] not in seen:
        out.append({"title": f"Wikipedia — {wiki['title']}", "url": wiki["url"]})
    return out
