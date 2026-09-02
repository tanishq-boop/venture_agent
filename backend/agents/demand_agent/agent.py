import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    from .schemas import DemandFactor, DemandPlan, LocationReport
except ImportError:
    from schemas import DemandFactor, DemandPlan, LocationReport

from strands import Agent
from tools import cached_web_search
from tracked_bedrock import TrackedBedrockModel


# ============================================================
# 1. STARTER BASELINE FACTORS
# ============================================================

baseline_demand_factors = [
    DemandFactor(
        name="population_and_demographics",
        category="demographics",
        reason="Validate population density, age distribution, and median household income.",
    ),
    DemandFactor(
        name="neighborhood_and_foot_traffic",
        category="neighborhood",
        reason="Evaluate daytime pedestrian traffic, office clusters, and commercial activity.",
    ),
    DemandFactor(
        name="competitor_saturation",
        category="competition",
        reason="Assess incumbent density, direct competitors, and submarket saturation.",
    ),
    DemandFactor(
        name="consumer_demand_and_gaps",
        category="demand",
        reason="Identify local appetite, underserved niches, and customer demand trends.",
    ),
]


# ============================================================
# 2. EXECUTION PIPELINE (AGENTS MOVED INSIDE TO GET VENTURE NAME)
# ============================================================

def evaluate_location_demand(venture_description: str, location: str) -> LocationReport:
    """Evaluates location viability starting from baseline factors."""
    
    # Initialize tracked models with the specific venture_description
    planner_model = TrackedBedrockModel(
        agent_name="demand_planner_agent",
        venture_name=venture_description, 
        model_id="amazon.nova-2-lite-v1:0",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        temperature=0.1,
    )

    demand_planner_agent = Agent(
        model=planner_model,
        system_prompt="""
You are a US Commercial Location & Demand Strategist.
Your goal is to prepare a targeted location research plan:

1. Start from the provided baseline demand factors:
   - Keep baseline factors if they are genuinely relevant to the venture.
   - Remove any baseline factor that is non-essential (e.g., foot traffic for a ghost kitchen or B2B shop).
2. Discover and add venture-specific demand factors ONLY if they materially affect feasibility (e.g., nightlife density for a late-night dessert bar, school density for a daycare).
3. Generate 2 to 3 targeted, location-specific search queries (referencing the US city/neighborhood) to fetch US Census demographic metrics, competitor maps, or local retail foot traffic.
"""
    )

    analyst_model = TrackedBedrockModel(
        agent_name="demand_analyst_agent",
        venture_name=venture_description, 
        model_id="amazon.nova-2-lite-v1:0",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        temperature=0.1,
    )

    demand_analyst_agent = Agent(
        model=analyst_model,
        system_prompt="""
You are a Commercial Real Estate & Market Demand Analyst.
Review the retrieved market data against the approved demand factors:
1. Assess demographic fit (median income vs expected pricing).
2. Assess competition: determine whether existing players signal market health or saturation.
3. Score viability from 0 to 100 and deliver a definitive verdict ('prime_location', 'viable', 'high_risk', 'unfavorable').
4. List concrete local advantages and key risks.
"""
    )


    # 1. Refine factors & generate queries in one pass
    plan_prompt = f"""
VENTURE:
{venture_description}

TARGET LOCATION:
{location}

STARTER BASELINE FACTORS:
{json.dumps([f.model_dump() for f in baseline_demand_factors], indent=2)}

Review the baseline factors, prune any that are not relevant, add necessary venture-specific factors, and output 2-3 search queries.
"""
    plan: DemandPlan = demand_planner_agent(
        plan_prompt,
        structured_output_model=DemandPlan,
    ).structured_output

    # 2. Execute cached web searches
    search_dossier = [
        {"query": q, "result": cached_web_search(q)}
        for q in plan.search_queries
    ]

    # 3. Produce structured LocationReport
    analysis_prompt = f"""
VENTURE:
{venture_description}

TARGET LOCATION:
{location}

FACTORS INVESTIGATED:
{json.dumps([f.model_dump() for f in plan.approved_factors], indent=2)}

WEB RESEARCH FINDINGS:
{json.dumps(search_dossier, indent=2)}

Generate the complete LocationReport.
"""
    report: LocationReport = demand_analyst_agent(
        analysis_prompt,
        structured_output_model=LocationReport,
    ).structured_output

    return report


if __name__ == "__main__":
    test_venture = "1,200 sq ft artisanal bakery and cafe"
    test_location = "South Congress, Austin, TX"

    result = evaluate_location_demand(test_venture, test_location)
    print(f"\n--- VERDICT: {result.verdict.upper()} ({result.viability_score}/100) ---")
    print(f"Demographic Fit: {result.demographic_fit}")
    print(f"Competition: {result.competition_summary}")
    print(f"Advantages: {result.key_advantages}")
    print(f"Risks: {result.key_risks}")