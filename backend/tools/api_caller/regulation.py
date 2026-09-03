import json
import os

import requests
from strands import tool

# ============================================================
# NAICS / US Census
# ============================================================

@tool
def get_naics_data(naics_code: str) -> str:
    """
    Query the US Census Economic Census API for a specific
    2022 NAICS industry code.

    Returns the official NAICS code, title, and selected
    economic census data for the US.
    """
    try:
        url = "https://api.census.gov/data/2022/ecnbasic"

        response = requests.get(
            url,
            params={
                "get": "NAICS2022,NAICS2022_LABEL,NAME,ESTAB,EMP,RCPTOT",
                "for": "us:*",
                "NAICS2022": naics_code,
                "key": os.getenv("CENSUS_API_KEY"),
            },
            timeout=5,
        )

        response.raise_for_status()

        rows = response.json()

        if len(rows) <= 1:
            return f"No Census data found for NAICS code: {naics_code}"

        headers = rows[0]

        results = [
            dict(zip(headers, row))
            for row in rows[1:]
        ]

        return json.dumps(results)

    except Exception as e:
        return f"Census NAICS API failed: {e}"


# ============================================================
# eCFR
# ============================================================

@tool
def search_ecfr(query: str) -> str:
    """
    Search the Electronic Code of Federal Regulations (eCFR)
    for federal regulatory requirements.
    """
    try:
        url = "https://www.ecfr.gov/api/search/v1/results"

        response = requests.get(
            url,
            params={
                "query": query,
                "per_page": 3,
            },
            timeout=5,
        )

        response.raise_for_status()

        results = response.json().get("results", [])

        if results:
            return json.dumps([
                r.get("hierarchy_headings")
                for r in results
            ])

        return "No results found in eCFR."

    except Exception as e:
        return f"eCFR API failed: {e}"


# ============================================================
# Regulations.gov
# ============================================================

@tool
def search_regulations_gov(query: str) -> str:
    """
    Search Regulations.gov for proposed and finalized
    federal regulatory documents.
    """
    try:
        url = "https://api.regulations.gov/v4/documents"

        api_key = os.getenv("REGULATIONS_GOV_API_KEY")

        if not api_key:
            return "Regulations.gov API key is not configured."

        response = requests.get(
            url,
            params={
                "filter[searchTerm]": query,
                "page[size]": 3,
                "api_key": api_key,
            },
            timeout=5,
        )

        response.raise_for_status()

        data = response.json().get("data", [])

        if data:
            return json.dumps([
                d.get("attributes", {}).get("title")
                for d in data
            ])

        return "No results found in Regulations.gov."

    except Exception as e:
        return f"Regulations.gov API failed: {e}"


# ============================================================
# Local / Municipal Data Discovery
# ============================================================

@tool
def search_local_codes(
    city: str,
    state: str,
    query: str,
) -> str:
    """
    Search the US Socrata catalog for state and municipal
    datasets related to regulatory requirements.
    """
    try:
        url = "https://api.us.socrata.com/api/catalog/v1"

        response = requests.get(
            url,
            params={
                "q": f"{city} {state} {query}",
                "limit": 7,
            },
            timeout=5,
        )

        response.raise_for_status()

        results = response.json().get("results", [])

        if results:
            return json.dumps([
                d.get("resource", {}).get("name")
                for d in results
            ])

        return (
            f"No local API datasets found for "
            f"{city}, {state}."
        )

    except Exception as e:
        return f"Socrata API failed: {e}"


# ============================================================
# USITC / Trade
# ============================================================

@tool
def search_trade_tariffs(
    product_description: str,
) -> str:
    """
    Search USITC HTS data for import/export tariffs
    and customs duties.
    """
    try:
        url = "https://hts.usitc.gov/api/search"

        response = requests.get(
            url,
            params={
                "query": product_description,
            },
            timeout=5,
        )

        response.raise_for_status()

        return response.text[:500]

    except Exception as e:
        return f"USITC API failed: {e}"


# ============================================================
# Export tool collection
# ============================================================

regulation_api_tools = [
    search_ecfr,
    search_regulations_gov,
    search_local_codes,
    search_trade_tariffs,
]