import json
import os
import requests
from typing import Literal
from pydantic import BaseModel, Field
from strands import Agent, tool
from backend.agent_wrapper import TrackedBedrockModel

# ============================================================
# 1. STRUCTURED OUTPUT SCHEMAS
# ============================================================

class Citation(BaseModel):
    source_name: str = Field(description="API, database, or official catalog name")
    url: str = Field(description="Endpoint URL or source query reference")
    quote: str = Field(description="Exact supporting rule excerpt or tariff code quote")

# YOUR EXACT CLASS:
class RegulationFinding(BaseModel):
    name: str
    level: Literal["federal", "state", "local"]
    requirement_type: Literal["license", "permit", "certificate", "registration", "other"]
    issuing_authority: str
    status: Literal["confirmed", "likely_required", "uncertain"]
    reason: str = Field(description="Why this requirement applies to this venture")
    evidence: str = Field(description="What was found / how the requirement was validated")
    citations: list[Citation] = Field(
        description="Sources backing this finding, each with a short supporting quote"
    )

class VentureComplianceReport(BaseModel):
    """Wrapper to split the findings into the two requested categories."""
    venture: str
    location: str
    
    # --- CATEGORY 1: ONE TIME ---
    one_time: list[RegulationFinding] = Field(
        description="All upfront permissions, initial registrations, and one-time customs duties/tariffs."
    )
    
    # --- CATEGORY 2: RECURRING ---
    recurring: list[RegulationFinding] = Field(
        description="All recurring permissions, annual renewals, and periodic certifications."
    )

# ============================================================
# 2. API TOOLS
# ============================================================

@tool
def search_ecfr(query: str) -> str:
    """Search the Electronic Code of Federal Regulations for federal rules."""
    try:
        url = "https://www.ecfr.gov/api/search/v1/results"
        res = requests.get(url, params={"query": query, "per_page": 3}, timeout=5)
        if res.status_code == 200 and res.json().get("results"):
            return json.dumps([r.get("hierarchy_headings") for r in res.json().get("results")])
        return "No eCFR results found."
    except Exception as e: return f"eCFR error: {e}"

@tool
def search_regulations_gov(query: str) -> str:
    """Search Regulations.gov for federal agency requirements and fees."""
    try:
        url = "https://api.regulations.gov/v4/documents"
        api_key = os.getenv("REGULATIONS_GOV_API_KEY", "DEMO_KEY")
        res = requests.get(url, params={"filter[searchTerm]": query, "page[size]": 3, "api_key": api_key}, timeout=5)
        if res.status_code == 200 and res.json().get("data"):
            return json.dumps([d.get("attributes", {}).get("title") for d in res.json().get("data")])
        return "No Regulations.gov results found."
    except Exception as e: return f"Regulations.gov error: {e}"

@tool
def search_local_codes(city: str, state: str, query: str) -> str:
    """Search Socrata Open Data for municipal licenses, permits, and inspection fees."""
    try:
        url = "https://api.us.socrata.com/api/catalog/v1"
        res = requests.get(url, params={"q": f"{city} {state} {query} permit fee", "limit": 7}, timeout=5)
        if res.status_code == 200 and res.json().get("results"):
            return json.dumps([d.get("resource", {}).get("name") for d in res.json().get("results")])
        return f"No local dataset found for {city}, {state}."
    except Exception as e: return f"Socrata error: {e}"

@tool
def search_trade_tariffs(product_description: str) -> str:
    """Search USITC HTS database for customs duty rates and import/export tariffs."""
    try:
        url = "https://hts.usitc.gov/api/search"
        res = requests.get(url, params={"query": product_description}, timeout=5)
        if res.status_code == 200: return res.text[:800]
        return "No tariff records found."
    except Exception as e: return f"USITC error: {e}"

compliance_tools = [
    search_ecfr, search_regulations_gov, search_local_codes, search_trade_tariffs
]

# ============================================================
# 3. AWS BEDROCK AGENT
# ============================================================

bedrock_model = TrackedBedrockModel(
    model_id="amazon.nova-pro-v1:0", 
    region_name="us-east-1",
    temperature=0.0, 
)

compliance_agent = Agent(
    model=bedrock_model,
    tools=compliance_tools,
    system_prompt="""
    You are a regulatory compliance and customs auditor.
    1. Search federal, local, and customs databases for the business type, imported products, and location.
    2. Sort EVERY finding strictly into the two provided lists: `one_time` or `recurring`. 
    3. CRITICAL: Because there is no specific field for cost in the schema, you MUST include the exact dollar fee, tariff rate, or duty percentage directly inside the `evidence` field for every item you find.
    """
)

# ============================================================
# 4. EXPORTABLE EXECUTION FUNCTION
# ============================================================

def get_compliance_requirements(venture_description: str, city: str, state: str) -> VentureComplianceReport:
    """Runs the agent and returns a native typed VentureComplianceReport object."""
    prompt = (
        f"Venture: {venture_description}\nLocation: {city}, {state}\n"
        "Identify all permissions, certifications, requirements, and customs duties. "
        "Split them strictly into one-time and recurring lists."
    )
    
    # The Strands framework forces the LLM to output exactly to your Pydantic schemas
    response = compliance_agent(
        prompt,
        structured_output_model=VentureComplianceReport
    )
    
    return response.structured_output


# ============================================================
# 5. TEST RUNNER (How you import/use it)
# ============================================================

if __name__ == "__main__":
    report = get_compliance_requirements(
        venture_description="Opening an arcade that imports claw machines from Japan and serves pre-packaged snacks",
        city="New York City",
        state="NY"
    )
    
    print(f"=== 1. ONE-TIME REQUIREMENTS & CUSTOMS ===")
    for item in report.one_time:
        print(f"• {item.name} ({item.level.upper()})")
        print(f"  Authority: {item.issuing_authority}")
        print(f"  Evidence (Includes Cost/Tariff): {item.evidence}\n")

    print(f"=== 2. RECURRING REQUIREMENTS ===")
    for item in report.recurring:
        print(f"• {item.name} ({item.level.upper()})")
        print(f"  Authority: {item.issuing_authority}")
        print(f"  Evidence (Includes Cost/Tariff): {item.evidence}\n")