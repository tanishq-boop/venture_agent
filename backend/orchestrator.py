# backend/agents/orchestrator.py

from typing import Any

from backend.schemas.feasibility import FeasibilityAssessment
from strands import Agent, tool

from backend.agent_wrapper import TrackedBedrockModel
from backend.agents.finance_agent.agent import finance_agent


# ============================================================
# 1. MODEL
# ============================================================

model = TrackedBedrockModel(
    model_id="amazon.nova-2-lite-v1:0",
    region_name="us-east-1",
    temperature=0.1,
)


# ============================================================
# 2. DOMAIN AGENT STUBS
# ============================================================

@tool
def run_finance_agent(
    venture_description: str,
    problems_summary: str = "",
    previous_estimates: dict | None = None,
) -> dict[str, Any]:
    """
    Analyze the financial requirements and costs of a venture.

    On a first call, leave problems_summary and previous_estimates unset —
    this runs the full research pipeline from scratch.

    On a follow-up call (after reviewing a previous finance result), pass:
    - problems_summary: exactly what is missing, wrong, or unsupported in
      the previous result, and why it matters.
    - previous_estimates: the previous finance agent result dict, unmodified.

    Providing both lets the finance agent amend only the flagged items
    instead of redoing already-correct research.
    """

    result = finance_agent(
        venture_description,
        problems_summary=problems_summary or None,
        previous_estimates=previous_estimates,
    )

    return result.model_dump()

@tool
def run_regulations_agent(venture_description: str) -> dict[str, Any]:
    """
    Analyze regulations, licenses, permits, restrictions,
    and compliance requirements for a venture.

    TODO: Replace with the actual regulations agent.
    """

    return {
        "status": "stub",
        "venture": venture_description,
        "findings": [],
        "risks": [],
        "missing_information": [],
    }


@tool
def run_demand_agent(venture_description: str) -> dict[str, Any]:
    """
    Analyze market demand, target customers, competition,
    and market conditions.

    TODO: Replace with the actual demand agent.
    """

    return {
        "status": "stub",
        "venture": venture_description,
        "findings": [],
        "risks": [],
        "missing_information": [],
    }


# ============================================================
# 3. ORCHESTRATOR
# ============================================================

orchestrator = Agent(
    model=model,

    tools=[
        run_finance_agent,
        run_regulations_agent,
        run_demand_agent,
    ],

    system_prompt="""
You are the lead orchestrator for a US-based venture feasibility assessment.

IMPORTANT:
All venture assessments are assumed to be for the United States unless
the venture description explicitly specifies otherwise.

Think and reason within the US context across ALL domains:
- Finance: US pricing, wages, rents, operating costs, taxes, and market rates
- Regulations: US federal, state, and local laws, licenses, permits, and compliance
- Demand: US consumers, businesses, market size, competition, pricing, and demand

When the venture has a physical location, consider the relevant US state
and local jurisdiction. If a specific location is not provided, identify
important location-dependent factors and avoid inventing a jurisdiction.


ROLE:

Your job is to coordinate specialized agents, review their findings,
identify important gaps, request targeted follow-up research, and
synthesize the results into a final feasibility assessment.


AVAILABLE AGENTS:

1. FINANCE
   - Startup and recurring costs
   - Equipment, labour, inventory, premises
   - US market pricing and operating expenses
   - Financial estimates and assumptions

2. REGULATIONS
   - US federal, state, and local regulations
   - Licenses and permits
   - Compliance requirements
   - Legal restrictions and regulatory risks

3. DEMAND
   - US market demand
   - Target customers
   - Market size
   - Competition
   - Pricing and demand risks


ORCHESTRATION:

- Determine which specialists are relevant to the venture.
- Delegate domain-specific research to the appropriate specialist.
- Review returned findings before making the final assessment.
- Identify missing information, weak evidence, contradictions,
  unsupported assumptions, and important uncertainties.
- If missing information could materially affect feasibility, request
  targeted follow-up research from the relevant specialist.
- Feedback must specify what needs to be investigated and why.
- Multiple research cycles are allowed.
- Do not perform specialist research yourself when an appropriate
  specialist is available.
- Do not request additional research merely for completeness.
- Stop when the major feasibility factors have sufficient evidence and
  further research is unlikely to materially change the result.


EVIDENCE:

Keep conclusions grounded in specialist outputs.

Distinguish between:
- Research-supported findings
- Estimates
- Assumptions
- Unresolved risks

Do not invent missing information.

If information depends on a particular US state, city, or jurisdiction
and that information is unavailable, explicitly identify it as an
uncertainty rather than assuming a jurisdiction.


FINAL ASSESSMENT:

Synthesize the specialist findings into an overall US venture feasibility
assessment covering:

- Financial viability
- US market demand
- US regulatory feasibility
- Major risks
- Key assumptions
- Important dependencies
- Overall feasibility

Explain the reasoning behind the conclusion rather than simply
providing a score.
""",
)


# ============================================================
# 4. PUBLIC ENTRY POINT
# ============================================================

def venture_agent(
    venture_description: str,
) -> dict[str, Any]:

    prompt = f"""
      Assess the following venture in the United States.

      VENTURE:
      {venture_description}

      The assessment should use US market conditions, US pricing, and
      applicable US federal/state/local regulations.

      Coordinate the finance, regulations, and demand specialists.

      Use feedback-driven research where necessary.

      Do not stop after the first research pass if important unanswered
      questions could materially affect the feasibility assessment.

      At the end, provide a comprehensive feasibility assessment grounded
      in the specialist findings.
    """

    result = orchestrator(
      prompt,
      structured_output_model=FeasibilityAssessment,
    ).structured_output
    
    print(result)

    return result