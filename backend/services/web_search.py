"""
Web search service for augmenting AI generation with up-to-date public information.

Uses Tavily Search API (purpose-built for AI agent workflows) as primary,
with DuckDuckGo as a free fallback that requires no API key.
"""

import httpx
from config import settings


class WebSearchService:
    """Retrieve web search results formatted for LLM prompt injection."""

    async def search(self, query: str, api_key: str = "", max_results: int = 5) -> list[dict]:
        """
        Search the web and return structured results.
        Uses Tavily if api_key provided, otherwise tries DuckDuckGo.
        """
        if api_key:
            return await self._search_tavily(query, api_key, max_results)
        # Fallback to free DuckDuckGo
        return await self._search_duckduckgo(query, max_results)

    async def _search_tavily(self, query: str, api_key: str, max_results: int) -> list[dict]:
        """Search using Tavily Search API (https://tavily.com)."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "max_results": max_results,
                        "search_depth": "advanced",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": r.get("content", ""),
                        }
                        for r in data.get("results", [])
                    ]
        except Exception:
            pass
        return []

    async def _search_duckduckgo(self, query: str, max_results: int) -> list[dict]:
        """Search using DuckDuckGo Instant Answer API (free, no key needed)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    # Add abstract if available
                    if data.get("AbstractText"):
                        results.append({
                            "title": data.get("AbstractSource", ""),
                            "url": data.get("AbstractURL", ""),
                            "content": data["AbstractText"],
                        })
                    # Add related topics
                    for topic in data.get("RelatedTopics", [])[:max_results - 1]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append({
                                "title": topic.get("FirstURL", ""),
                                "url": topic.get("FirstURL", ""),
                                "content": topic["Text"],
                            })
                    return results[:max_results]
        except Exception:
            pass
        return []

    async def search_relevant(self, query: str, api_key: str = "", n_results: int = 3) -> str:
        """
        Search and format results as prompt-ready text.
        Mirrors the vector_store.search_relevant() interface.
        """
        results = await self.search(query, api_key=api_key, max_results=n_results)
        if not results:
            return ""

        parts = []
        for i, r in enumerate(results):
            parts.append(f"[参考 {i + 1}]\n{r['title']}\n{r['content']}")
        return "\n\n---\n\n".join(parts)
