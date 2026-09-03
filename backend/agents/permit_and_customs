import json
import requests
from typing import List, Literal, Optional

from pydantic import BaseModel, Field
from strands import Agent, tool
from strands.tools import web_search

from backend.agent_wrapper import TrackedBedrockModel

# ============================================================
# 1. SCHEMAS (Pydantic == the "structured outputs" contract)
# ============================================================

class NAICSClassification(BaseModel):
    """Classification step grounding searches in the US NAICS code system."""
    naics_code: Optional[str] = Field(None, description="Best-matching NAICS code (e.g. '812910').")
    naics_title: Optional[str] = Field(None, description="Official NAICS title.")
    confidence: Literal["high", "medium", "low"] = Field("medium")

class VentureDetails(BaseModel):
    """Output of Agent 1 (Planner). Extracted from raw user text."""
    business_type: str = Field(..., description="Normalized business type / industry.")
    location_city: str = Field(..., description="City extracted from the input.")
    location_state: str = Field(..., description="US State extracted from the input.")
    naics: Optional[NAICSClassification] = None
    estimated_categories: List[str] = Field(
        ...,
        description="Brainstormed categories of regulations likely required across Federal, State, County, and Municipal levels."
    )

class RegulationItem(BaseModel):
    """A single permit/license/regulation line item."""
    name: str = Field(..., description="Name of the permit, license, or regulation.")
    jurisdiction: Literal["Federal", "State", "County", "Municipal"] = Field(
        ..., description="Level of US government issuing the permit."
    )
    issuing_authority: str = Field(
        ..., description="Specific government body / department (e.g., 'Texas Comptroller', 'IRS')."
    )
    cost_type: Literal["one_time", "yearly", "both", "unknown"] = Field(...)
    
    # --- NUMERIC COST PARSING ---
    fixed_cost: Optional[float] = Field(
        None, description="One-time upfront fee as a float (e.g. 200.0). Null if unknown or not applicable."
    )
    recurring_cost: Optional[float] = Field(
        None, description="Recurring annual renewal fee as a float (e.g. 150.0). Null if unknown or not applicable."
    )
    
    reason: str = Field(..., description="Why this permit applies to the venture.")
    source_url: Optional[str] = Field(
        None, description="Source URL or API used to confirm the requirement."
    )

class RegulationPlan(BaseModel):
    """Intermediate output from the Researcher agent."""
    items: List[RegulationItem]

class FinalRegulationEstimates(BaseModel):
    """Final, verified structured output of the whole pipeline."""
    business_type: str
    location_city: str
    location_state: str
    naics: Optional[NAICSClassification] = None
    regulations: List[RegulationItem]
    
    # --- CALCULATED NUMERIC TOTALS ---
    total_fixed_cost: float = Field(
        0.0, description="Estimated sum of all known one-time fixed upfront fees."
    )
    total_recurring_cost_yearly: float = Field(
        0.0, description="Estimated sum of all known ongoing recurring annual renewal fees."
    )
    
    verification_summary: str = Field(
        ..., description="Summary of the audit process, flagging any unverified costs or requirements."
    )

# ============================================================
# 2. API TOOLS (Priority APIs -> Fallback to web_search)
# ============================================================

@tool
def search_ecfr(query: str) -> str:
    """Search the Electronic Code of Federal Regulations (eCFR) API for federal regulations."""
    try:
        url = "https://www.ecfr.gov/api/search/v1/results"
        params = {"query": query, "per_page": 3}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200 and response.json().get("results"):
            return json.dumps([r.get("hierarchy_headings") for r in response.json().get("results")])
    except Exception as e:
        return f"eCFR API failed ({str(e)}). Please use the web_search tool."
    return "No results found in eCFR. Please use the web_search tool."

@tool
def search_regulations_gov(query: str) -> str:
    """Search Regulations.gov API for proposed and finalized federal rules."""
    try:
        url = "https://api.regulations.gov/v4/documents"
        params = {"filter[searchTerm]": query, "page[size]": 3, "api_key": "DEMO_KEY"}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200 and response.json().get("data"):
            return json.dumps([d.get("attributes", {}).get("title") for d in response.json().get("data")])
    except Exception as e:
        return f"Regulations.gov API failed ({str(e)}). Please use the web_search tool."
    return "No results found in Regulations.gov. Please use the web_search tool."

@tool
def search_local_codes(city: str, state: str, query: str) -> str:
    """Search the universal Socrata Discovery API for state and municipal open data codes."""
    try:
        # Fixed: Now uses the universal US catalog instead of hardcoded NY state
        url = "https://api.us.socrata.com/api/catalog/v1" 
        params = {"q": f"{city} {state} {query} permit", "limit": 2}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200 and response.json().get("results"):
            return json.dumps([d.get("resource", {}).get("name") for d in response.json().get("results")])
    except Exception as e:
        return f"Socrata API failed ({str(e)}). Please use the web_search tool."
    return f"No local API datasets found for {city}, {state}. Please use the web_search tool."

@tool
def search_trade_tariffs(product_description: str) -> str:
    """Search Trade.gov and USITC HTS APIs for import/export tariffs and customs duties."""
    try:
        url = f"https://hts.usitc.gov/api/search?query={product_description}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text[:500] 
    except Exception as e:
        return f"USITC API failed ({str(e)}). Please use the web_search tool."
    return "No tariff data found in USITC. Please use the web_search tool."

@tool
def search_opencorporates(company_type: str, state: str) -> str:
    """Search OpenCorporates API for business entity registration requirements."""
    return "OpenCorporates API requires authentication. Please use the web_search tool to find Secretary of State entity formation rules."

compliance_tools = [
    search_ecfr,
    search_regulations_gov,
    search_local_codes,
    search_trade_tariffs,
    search_opencorporates,
    web_search
]

# ============================================================
# 3. BEDROCK MODEL & AGENTS
# ============================================================

model = TrackedBedrockModel(
    model_id="amazon.nova-lite-v1:0", 
    region_name="us-east-1",
    temperature=0.1,
)

naics_agent = Agent(
    model=model,
    system_prompt="""
You classify a US business description into the closest official NAICS code.
If no confident match exists, return null fields with confidence 'low'.
"""
)

planner_agent = Agent(
    model=model,
    system_prompt="""
You are a US compliance planning assistant.
Extract the business_type, location_city, and location_state.
Brainstorm a broad list of estimated_categories of regulations likely required.
CRITICAL: Do not use generic terms. Think strictly across four US tiers:
1. Federal (e.g., EIN, FDA, EPA, Trade)
2. State (e.g., LLC Registration, Sales Tax Permit, State Licensing Boards)
3. County (e.g., Health Department, Environmental Health)
4. Municipal/City (e.g., General Business License, Zoning, Fire Safety)
Return the structured VentureDetails object.
"""
)

researcher_agent = Agent(
    model=model,
    tools=compliance_tools,
    system_prompt="""
You are a US regulatory research assistant.
For EACH category in the VentureDetails:
1. Prioritize using the specific API tools (eCFR, Socrata, Trade, etc.).
2. If those tools return no results, fallback to using the `web_search` tool.
3. Find the actual permit name, jurisdiction, issuing authority, and estimated cost.
Drop categories that do not apply, and add any missing permits discovered.
For each item, determine if the cost is a one-time fixed_cost, a recurring_cost, or both.
Ensure all costs are raw floats (e.g., 200.0, not "$200"). If unknown, leave as null.
Return the structured RegulationPlan object.
"""
)

verifier_agent = Agent(
    model=model,
    tools=compliance_tools,
    system_prompt="""
You are a Regulatory Verification Auditor.
You receive an unverified RegulationPlan. Your job is to verify its accuracy.
1. Use the search tools to fact-check the issuing authority and the cost.
2. If a cost seems hallucinated or cannot be confirmed, mark the cost as 'unknown' and nullify the float value.
3. Ensure there are no duplicate permits between County and City levels unless legally required.
4. Calculate total_fixed_cost (sum of all valid fixed_cost floats) and total_recurring_cost_yearly (sum of all valid recurring_cost floats).
Return the structured FinalRegulationEstimates object.
"""
)

# ============================================================
# 4. PIPELINE FUNCTIONS
# ============================================================

def classify_naics(venture_description: str) -> NAICSClassification:
    print("\n[NAICS] Classifying venture description...")
    try:
        return naics_agent(venture_description, structured_output_model=NAICSClassification).structured_output
    except Exception as e:
        print(f"[NAICS] Error: {e} - Skipping NAICS.")
        return NAICSClassification(confidence="low")

def extract_venture_details(venture_description: str, naics: Optional[NAICSClassification]) -> VentureDetails:
    prompt = f"DESCRIPTION:\n{venture_description}\nNAICS:\n{json.dumps(naics.model_dump() if naics else {})}"
    print("\n[PLANNER] Extracting venture details across US Tiers...")
    try:
        return planner_agent(prompt, structured_output_model=VentureDetails).structured_output
    except Exception as e:
        raise RuntimeError(f"Planner failed: {e}")

def research_regulations(venture_details: VentureDetails) -> RegulationPlan:
    prompt = f"VENTURE DETAILS:\n{json.dumps(venture_details.model_dump(), indent=2)}"
    print("\n[RESEARCHER] Querying APIs and web searching for active regulations...")
    try:
        return researcher_agent(prompt, structured_output_model=RegulationPlan).structured_output
    except Exception as e:
        raise RuntimeError(f"Researcher failed: {e}")

def verify_regulations(venture_details: VentureDetails, regulation_plan: RegulationPlan) -> FinalRegulationEstimates:
    prompt = f"VENTURE DETAILS:\n{json.dumps(venture_details.model_dump())}\n\nUNVERIFIED PLAN:\n{json.dumps(regulation_plan.model_dump())}"
    print("\n[VERIFIER] Auditing costs and calculating final totals...")
    try:
        return verifier_agent(prompt, structured_output_model=FinalRegulationEstimates).structured_output
    except Exception as e:
        raise RuntimeError(f"Verifier failed: {e}")

# ============================================================
# 5. RUN WORKFLOW
# ============================================================

def run_pipeline(venture_description: str) -> FinalRegulationEstimates:
    """Orchestrates the 4-hop strictly structured data chain."""
    naics = classify_naics(venture_description)
    venture_details = extract_venture_details(venture_description, naics)
    regulation_plan = research_regulations(venture_details)
    final_estimates = verify_regulations(venture_details, regulation_plan)
    return final_estimates

if __name__ == "__main__":
    description = "I want to open a small artisanal bakery and coffee shop in Austin, Texas."
    result = run_pipeline(description)

    print("\n================= FINAL VERIFIED REPORT =================")
    
    # --- 1. FIXED COSTS ---
    print("\n--- 1. FIXED (ONE-TIME) PERMITS & COSTS ---")
    for item in result.regulations:
        if item.cost_type in ["one_time", "both"]:
            # Format float cost to currency string if exists, else flag unknown
            cost = f"${item.fixed_cost:.2f}" if item.fixed_cost is not None else "Unknown/Unverified"
            print(f"  - [{item.jurisdiction.upper()}] {item.name}: {cost}")
            print(f"    Authority: {item.issuing_authority}")
            if item.source_url:
                print(f"    Source: {item.source_url}")
            print("")
            
    # --- 2. RECURRING COSTS ---
    print("--- 2. RECURRING PERMITS & COSTS ---")
    for item in result.regulations:
        if item.cost_type in ["yearly", "both"]:
            cost = f"${item.recurring_cost:.2f}/year" if item.recurring_cost is not None else "Unknown/Unverified"
            print(f"  - [{item.jurisdiction.upper()}] {item.name}: {cost}")
            print(f"    Authority: {item.issuing_authority}")
            if item.source_url:
                print(f"    Source: {item.source_url}")
            print("")

    # --- COST BREAKDOWN ---
    print("--- COST BREAKDOWN ---")
    print(f"Total Fixed (One-Time) Costs : ${result.total_fixed_cost:.2f}")
    print(f"Total Recurring (Annual) Cost: ${result.total_recurring_cost_yearly:.2f}/year")

    print("\n--- VERIFICATION SUMMARY ---")
    print(result.verification_summary)
