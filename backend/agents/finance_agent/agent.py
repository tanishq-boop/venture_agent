import json

from strands import Agent

from backend.agent_wrapper import TrackedBedrockModel
from backend.agents.finance_agent.schemas import CostItem, CostPlan, FinalCostEstimates
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
# 4. WORKFLOW AGENTS
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

# Step C: Research and estimate costs. Handles BOTH a first-time full
# estimation pass and a feedback-driven amendment pass — the behavior is
# selected by what the prompt gives it (see finance_agent() below), not by
# having two separate agents/system-prompts with duplicated citation rules.
estimation_agent = Agent(
    model=model,
    tools=[web_search],
    system_prompt="""
You research and estimate costs for a business venture using web search.

You will either be given:
(a) a cost plan to estimate for the first time, or
(b) a previous full set of cost estimates plus a problems summary describing
    what is missing, wrong, or unsupported in that previous plan.

If given (b) — a previous set of estimates and a problems summary:
- Only re-investigate and update items that the problems summary actually
  implicates. Use web search to find better/updated pricing or evidence for
  those items only.
- Leave every other item exactly as it was: copy its reason, evidence, and
  citations through unchanged. Do not re-research or rewrite items the
  feedback did not raise concerns about.
- If the feedback implies a cost category is missing entirely, add it as a
  new item with its own reason, evidence, and citations.
- Your output must be the complete, updated cost plan covering all items
  (unchanged items included), not just the changed ones.

If given (a) — no previous estimates — treat every item in the provided cost
plan as needing fresh research.

For EVERY cost item you return, you must provide:
- reason: why this cost applies to this specific venture.
- evidence: what you found and how you derived the estimated amount(s) from it.
- citations: a list of sources used for this item. Each citation must include the
  source URL and a short (one sentence or less) verbatim quote from that source
  that directly supports the estimate. Do not fabricate quotes or sources —
  only cite pages you actually retrieved via web search.

Provide concrete estimated amounts (one-time or monthly) and currency alongside
the reason, evidence, and citations for each item.
""",
)


# ============================================================
# 5. RUN WORKFLOW
# ============================================================

def finance_agent(
    venture_description: str,
    problems_summary: str | None = None,
    previous_estimates: FinalCostEstimates | dict | None = None,
) -> FinalCostEstimates:

    has_feedback = bool(problems_summary) and bool(previous_estimates)

    # ------------------------------------------------------------
    # AMEND PATH: reuse previous work, only re-research flagged items
    # ------------------------------------------------------------
    if has_feedback:

        if isinstance(previous_estimates, FinalCostEstimates):
            previous_plan = previous_estimates
        else:
            previous_plan = FinalCostEstimates.model_validate(previous_estimates)

        prompt_amend = f"""
VENTURE:
{venture_description}

PROBLEMS SUMMARY (feedback on the previous plan):
{problems_summary}

PREVIOUS COST ESTIMATES:
{json.dumps(previous_plan.model_dump(), indent=2)}

Update only the items implicated by the problems summary. Return the
complete, updated cost plan including unchanged items.
"""
        amended_estimates = estimation_agent(
            prompt_amend,
            structured_output_model=FinalCostEstimates,
        ).structured_output

        return amended_estimates

    # ------------------------------------------------------------
    # FULL PATH: first run, no feedback given
    # ------------------------------------------------------------

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