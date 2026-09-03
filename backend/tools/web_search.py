import json
import os

import requests
from strands import tool


# ============================================================
# Tavily
# ============================================================

def tavily_search(query: str) -> list[dict]:
    """Search the web using Tavily."""
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not configured.")

    response = requests.post(
        "https://api.tavily.com/search",
        headers={
            "Content-Type": "application/json",
        },
        json={
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
        },
        timeout=10,
    )

    response.raise_for_status()

    results = response.json().get("results", [])

    return [
        {
            "title": result.get("title"),
            "url": result.get("url"),
            "content": result.get("content"),
        }
        for result in results
    ]


# ============================================================
# Brave
# ============================================================

def brave_search(query: str) -> list[dict]:
    """Search the web using Brave."""
    api_key = os.getenv("BRAVE_API_KEY")

    if not api_key:
        raise RuntimeError("BRAVE_API_KEY is not configured.")

    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
        },
        params={
            "q": query,
            "count": 5,
        },
        timeout=10,
    )

    response.raise_for_status()

    results = (
        response.json()
        .get("web", {})
        .get("results", [])
    )

    return [
        {
            "title": result.get("title"),
            "url": result.get("url"),
            "content": result.get("description"),
        }
        for result in results
    ]


# ============================================================
# Web Search
# ============================================================

@tool
def cached_web_search(query: str) -> str:
    """
    Search the web using the provider configured by
    the SEARCH_PROVIDER environment variable.

    Supported providers:
        - tavily
        - brave
    """
    try:
        provider = os.getenv("SEARCH_PROVIDER", "tavily").lower()

        if provider == "tavily":
            results = tavily_search(query)

        elif provider == "brave":
            results = brave_search(query)

        else:
            return (
                f"Invalid SEARCH_PROVIDER: {provider}. "
                "Expected 'tavily' or 'brave'."
            )

        if not results:
            return f"No web results found for: {query}"

        return json.dumps(results)

    except Exception as e:
        return f"Web search failed: {e}"