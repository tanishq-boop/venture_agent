import json
import os
import sys
from pathlib import Path
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    from .schemas import RegulationItem, RegulationPlan, RegulationReport
except ImportError:
    from schemas import RegulationItem, RegulationPlan, RegulationReport

from strands import Agent
from strands.models import BedrockModel
from tools import cached_web_search


# ============================================================
# 1. NEW DATA SCHEMAS
# ============================================================
class BusinessClassification(BaseModel):
    naics_code: str = Field(description="The exact 6-digit NAICS code for this business type")
    industry_title: str = Field(description="Official NAICS industry title")
    state_abbr: str = Field(description="2-letter US state abbreviation (e.g., TX, CA)")
    city: str = Field(description="The primary municipality name")


# ============================================================
# 2. EXPANDED COMPREHENSIVE BASELINE CATALOG
# ============================================================
baseline_regulations = [
    RegulationItem(
        name="federal_ein_registration",
        governing_body="Internal Revenue Service (IRS)",
        strictness="very_strict",
        punishment_for_violation="Inability to open business bank accounts, hire employees, or file taxes.",
        maintenance_difficulty="low",
        ongoing_obligations=["File annual federal business tax returns"],
        estimated_fees="$0"
    ),
    RegulationItem(
        name="general_business_operating_license",
        governing_body="City/County Finance or Revenue Department",
        strictness="strict",
        punishment_for_violation="Fines, late fees, and cease-and-desist orders.",
        maintenance_difficulty="low",
        ongoing_obligations=["Annual gross receipts reporting and renewal"],
        estimated_fees="$50 - $500/year"
    ),
    RegulationItem(
        name="state_sales_tax_seller_permit",
        governing_body="State Department of Revenue",
        strictness="very_strict",
        punishment_for_violation="Tax liens, asset seizure, and revocation of authority to transact business.",
        maintenance_difficulty="moderate",
        ongoing_obligations=["Monthly or quarterly state sales tax remittance"],
        estimated_fees="$0 - $50 one-time"
    ),
    RegulationItem(
        name="certificate_of_occupancy_and_zoning",
        governing_body="City Building & Development Services",
        strictness="very_strict",
        punishment_for_violation="Immediate stop-work order or red-tag padlocking.",
        maintenance_difficulty="low",
        ongoing_obligations=["Maintain approved floor plan and occupancy limits"],
        estimated_fees="$200 - $800 one-time"
    ),
    RegulationItem(
        name="fire_department_operational_permit",
        governing_body="Local Fire Marshal",
        strictness="strict",
        punishment_for_violation="Forced closure until life-safety hazards are mitigated.",
        maintenance_difficulty="moderate",
        ongoing_obligations=["Annual fire extinguisher and suppression system inspections"],
        estimated_fees="$100 - $300/year renewal"
    ),
    RegulationItem(
        name="local_health_department_permit",
        governing_body="City / County Public Health Department",
        strictness="very_strict",
        punishment_for_violation="Mandatory closure notices and daily escalating fines.",
        maintenance_difficulty="high",
        ongoing_obligations=["Unannounced random inspections", "Mandatory Certified Food Manager on shift"],
        estimated_fees="$250 - $600/year renewal"
    ),
    RegulationItem(
        name="environmental_and_wastewater_permit",
        governing_body="State EPA / Local Water Utility",
        strictness="strict",
        punishment_for_violation="Severe daily fines for illegal discharge (e.g., FOG - Fats, Oils, Grease).",
        maintenance_difficulty="high",
        ongoing_obligations=["Quarterly grease trap pumping manifests submitted to city"],
        estimated_fees="$200 - $500/year"
    ),
]


# ============================================================
# 3. BEDROCK MODEL CONFIGURATION
# ============================================================
bedrock_model = BedrockModel(
    model_id="amazon.nova-pro-v1:0", # Upgraded to Pro for better tool reasoning
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    temperature=0.1, 
)


# ============================================================
# 4. TOOL-ENABLED MULTI-AGENT WORKFLOW
# ============================================================

# Step 1: Standardize the input
classification_agent = Agent(
    model=bedrock_model,
    system_prompt="""
You are a US Census and Business Classification Expert.
Analyze the proposed venture and location. Output the exact 6-digit NAICS code, 
the official industry title, the 2-letter state abbreviation, and the city.
""",
)

# Step 2: Autonomous Discovery & Pruning Agent (Equipped with Search Tool)
discovery_and_pruning_agent = Agent(
    model=bedrock_model,
    tools=[cached_web_search], # <-- The Agent can now execute searches autonomously
    system_prompt="""
You are an Autonomous Regulatory Compliance Agent. 
You will be provided with a venture description, NAICS code, location, and a broad BASELINE catalog of permits.
Your job is to use your `cached_web_search` tool to query official state (.gov) and municipal portals to build a custom regulatory plan.

PROCESS:
1. PRUNE: Evaluate each baseline permit against the specific business. Use your search tool to verify. If a baseline does NOT apply (e.g., health permits for a software company), REMOVE IT.
2. DISCOVER: Use your search tool to discover specialized state/local permits missing from the baseline (e.g., TABC liquor licenses, specialized occupational licenses, FDA registrations). ADD THEM.
3. OUTPUT: Return the final `RegulationPlan` containing only the strictly verified, applicable regulations.
""",
)

# Step 3: Synthesize findings
regulation_analyst_agent = Agent(
    model=bedrock_model,
    system_prompt="""
You are a Commercial Regulatory Legal Analyst.
Evaluate the finalized RegulationPlan:
1. Specify explicit punishments (fines, closures).
2. Rate ongoing maintenance difficulty (high/moderate/low).
3. Identify showstopper penalties and output a final chronological pre-opening checklist.
""",
)


# ============================================================
# 5. OPTIMIZED EXECUTION PIPELINE
# ============================================================

def evaluate_regulations(venture_description: str, location: str) -> RegulationReport:
    print("--> [1/3] Classifying business standard (NAICS)...")
    classification: BusinessClassification = classification_agent(
        f"VENTURE: {venture_description}\nLOCATION: {location}",
        structured_output_model=BusinessClassification,
    ).structured_output

    print(f"--> [2/3] Business Classified as NAICS {classification.naics_code}. Initiating Autonomous Search & Pruning...")
    discovery_prompt = f"""
VENTURE: {venture_description} (NAICS: {classification.naics_code})
LOCATION: {location}
COMPREHENSIVE BASELINE CATALOG: 
{json.dumps([r.model_dump() for r in baseline_regulations], indent=2)}

Use your web search tool to verify which baselines apply, drop the unnecessary ones, and discover any missing state/city specific permits.
"""
    # The agent will dynamically loop, calling cached_web_search as needed before returning the structured plan
    plan: RegulationPlan = discovery_and_pruning_agent(
        discovery_prompt,
        structured_output_model=RegulationPlan,
    ).structured_output

    print("--> [3/3] Analyzing compliance burden and generating final report...")
    report: RegulationReport = regulation_analyst_agent(
        json.dumps([r.model_dump() for r in plan.approved_regulations]),
        structured_output_model=RegulationReport,
    ).structured_output

    return report


if __name__ == "__main__":
    # Test with a highly regulated business
    test_venture = "1,200 sq ft retail bakery producing fresh bread and pastries"
    test_location = "Austin, Texas"

    report = evaluate_regulations(test_venture, test_location)
    
    print(f"\n--- COMPLIANCE BURDEN: {report.overall_compliance_burden.upper()} ---")
    print(f"Maintenance Difficulty: {report.maintenance_summary}")
    print("\nShowstopper Penalties:")
    for penalty in report.showstopper_penalties:
        print(f" - {penalty}")
    print("\nRegulated Items Found:")
    for reg in report.regulations:
        print(f" * {reg.name} ({reg.strictness.upper()} strictness | {reg.maintenance_difficulty.upper()} maintenance)")ng up the command line interface.
        
    