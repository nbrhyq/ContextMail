from __future__ import annotations

from typing import List
from urllib.parse import urlparse

import httpx

from app.config import Settings, get_settings
from app.models.domain import Evidence, EvidenceSourceType
from app.tools.interfaces import WebSearchTool
from app.tools.mock_tools import MockWebSearch


class BraveWebSearch:
    """Thin Brave Search API adapter. Query planning stays in ResearchAgent."""

    def __init__(self, api_key: str, max_results: int = 5, timeout: float = 20) -> None:
        if not api_key:
            raise ValueError("CONTEXTMAIL_BRAVE_SEARCH_API_KEY is required in live search mode")
        self.api_key = api_key
        self.max_results = max_results
        self.timeout = timeout

    async def search(self, query: str, *, preferred_domains: List[str] | None = None) -> List[Evidence]:
        scoped_query = query
        if preferred_domains:
            scoped_query = f"{query} ({' OR '.join(f'site:{domain}' for domain in preferred_domains)})"
        headers = {"Accept": "application/json", "X-Subscription-Token": self.api_key}
        params = {"q": scoped_query, "count": self.max_results, "safesearch": "moderate"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search", headers=headers, params=params
            )
            response.raise_for_status()
        results = response.json().get("web", {}).get("results", [])
        evidence: List[Evidence] = []
        for item in results:
            url = item.get("url", "")
            title = item.get("title", "Untitled search result")
            description = item.get("description", "").strip()
            if not url or not description:
                continue
            domain = urlparse(url).netloc.lower().removeprefix("www.")
            preferred = bool(preferred_domains and any(domain == d or domain.endswith(f".{d}") for d in preferred_domains))
            authoritative_suffixes = (".edu", ".edu.au", ".ac.uk", ".gov", ".gov.au")
            authoritative = preferred or domain.endswith(authoritative_suffixes)
            evidence.append(Evidence(
                claim=title,
                content=description,
                source_name=domain or title,
                source_url=url,
                source_type=EvidenceSourceType.WEB,
                relevance="Official/preferred source match" if authoritative else "Relevant web result; requires verification",
                verified=url.startswith("https://") and authoritative,
                metadata={"provider": "brave", "query": query, "preferred_source": preferred, "authoritative_domain": authoritative},
            ))
        return evidence


def create_search_tool(settings: Settings | None = None) -> WebSearchTool:
    configured = settings or get_settings()
    if configured.search_provider.lower() == "brave":
        return BraveWebSearch(configured.brave_search_api_key, configured.search_max_results)
    return MockWebSearch()
