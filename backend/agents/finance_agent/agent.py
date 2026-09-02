
import json

from strands import Agent

from backend.agent_wrapper import TrackedBedrockModel
from backend.agents.finance_agent.schemas import CostItem, CostPlan, FinalCostEstimates
from strands.models import BedrockModel
from strands.tools import web_search


costs = [
    CostItem(
        name="rent",
        cost_type="continuous",
        reason="Cost of premises required to operate the venture."
    ),
    CostItem(
        name="electricity",
        cost_type="continuous",
        reason="Electricity required for operating the venture."
    ),
    CostItem(
        name="labour",
        cost_type="continuous",
        reason="Employees or other labour required to operate the venture."
    ),
    CostItem(
        name="inventory",
        cost_type="continuous",
        reason="Goods, materials, or supplies that must be purchased or replenished."
    ),
    CostItem(
        name="equipment",
        cost_type="one_time",
        reason="Machinery, tools, hardware, or initial setup items required for operations."
    ),
]


# ============================================================
# 3. BEDROCK MODEL (UNCHANGED)
# ============================================================

model = TrackedBedrockModel(
    model_id="amazon.nova-2-lite-v1:0",
    region_name="us-east-1",
    temperature=0.1,
)


# ============================================================
# 4. WORKFLOW AGENTS (SEPARATED)
# ============================================================

# Step A: Add relevant missing costs to the baseline
addition_agent = Agent(
    model=model,
    system_prompt="""
You analyze a business venture and expand the initial cost list.
Start with the provided baseline cost items and add all other categories 
that might be relevant, required, or standard for this specific venture.
Do not filter or remove any items in this step.
""",
)

# Step B: Filter out non-essential/irrelevant costs
filtering_agent = Agent(
    model=model,
    system_prompt="""
You refine a cost list for a business venture.
Review the candidate cost items:
- Remove items that are clearly unnecessary, trivial, or duplicate for this venture.
- Adjust cost_type (one_time, continuous, both) if needed.
Return only the cleaned, finalized cost plan.
""",
)

# Step C: Use web search to estimate values for the finalized list
estimation_agent = Agent(
    model=model,
    tools=[web_search],
    system_prompt="""
You estimate costs for a business venture.
Use the web search tool to find realistic current pricing, market standard rates, or average expenses for each item in the provided cost plan.
Provide concrete estimated amounts (one-time or monthly), currency, explanation, and sources used.
""",
)


# ============================================================
# 5. RUN WORKFLOW
# ============================================================

def create_cost_plan(venture_description: str) -> FinalCostEstimates:

    # 1. ADDITION STEP
    prompt_add = f"""
        VENTURE:
        {venture_description}

        INITIAL BASELINE COSTS:
        {json.dumps([c.model_dump() for c in costs], indent=2)}

        Add all possible additional cost categories required for this venture to the baseline list.
    """
    expanded_plan = addition_agent(
        prompt_add,
        structured_output_model=CostPlan,
    ).structured_output

    # 2. FILTERING STEP
    prompt_filter = f"""
VENTURE:
{venture_description}

EXPANDED CANDIDATE COSTS:
{json.dumps([c.model_dump() for c in expanded_plan.costs], indent=2)}

Filter out unnecessary or redundant items and return the finalized list of essential costs.
"""
    filtered_plan = filtering_agent(
        prompt_filter,
        structured_output_model=CostPlan,
    ).structured_output

    # 3. WEB SEARCH & ESTIMATION STEP
    prompt_estimate = f"""
VENTURE:
{venture_description}

FINAL COST PLAN TO ESTIMATE:
{json.dumps([c.model_dump() for c in filtered_plan.costs], indent=2)}

Use web search to research pricing for these specific cost items and produce final cost estimates.
"""
    final_estimates = estimation_agent(
        prompt_estimate,
        structured_output_model=FinalCostEstimates,
    ).structured_output

    return final_estimates