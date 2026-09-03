import json

from strands import Agent

from backend.agent_wrapper import TrackedBedrockModel
from backend.agents.regulations_agent.schemas import (
    RegulationItem,
    RegulationPlan,
    FinalRegulationFindings,
)
from strands.tools import web_search

regulations = [
    RegulationItem(
        name="business_registration",
        level="state",
        reason="Registering the business entity is generally required to legally operate.",
    ),
    RegulationItem(
        name="ein_tax_registration",
        level="federal",
        reason="A federal tax ID is typically required for hiring, banking, and tax filing.",
    ),
    RegulationItem(
        name="general_business_license",
        level="local",
        reason="Most local jurisdictions require a general license to operate a business.",
    ),
    RegulationItem(
        name="zoning_land_use_permit",
        level="local",
        reason="Confirms the premises/location is zoned for this type of business activity.",
    ),
    RegulationItem(
        name="industry_specific_license",
        level="state",
        reason="Certain industries require state-specific licenses, permits, or certifications to operate legally.",
    ),
]


# ============================================================
# 3. BEDROCK MODEL (UNCHANGED)
# ============================================================

model = TrackedBedrockModel(
    model_id="amazon.nova-2-lite-v1:0",
    agent_name="Regulation_Agent",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    temperature=0.1,
)


# ============================================================
# 4. WORKFLOW AGENTS
# ============================================================

# Step A: Add relevant missing regulations to the baseline
discovery_agent = Agent(
    model=model,
    system_prompt="""
You analyze a business venture and expand the initial list of regulations.
Start with the provided baseline regulation items and add all other permits,
licenses, certificates, or registrations that might be relevant, required,
or standard for this specific venture, at the federal, state, and local level.
Do not filter or remove any items in this step.
""",
)

# Step B: Filter out non-essential/irrelevant regulations
filtering_agent = Agent(
    model=model,
    system_prompt="""
You refine a regulation list for a business venture.
Review the candidate regulation items:
- Remove items that are clearly unnecessary, trivial, or duplicate for this venture.
- Adjust level (federal, state, local) if needed.
Return only the cleaned, finalized regulation plan.
""",
)

# Step C: Research and validate regulations. Handles BOTH a first-time full
# validation pass and a feedback-driven amendment pass — the behavior is
# selected by what the prompt gives it (see regulations_agent() below), not
# by having two separate agents/system-prompts with duplicated citation rules.
validation_agent = Agent(
    model=model,
    tools=[web_search],
    system_prompt="""
Research and validate US regulatory requirements for a business venture using web search.

SOURCE POLICY:
- Official federal, state, county, and municipal government sources are the source of truth;
  prefer the authority that issues or enforces the requirement.
- Secondary sources may help discover requirements but cannot be final evidence.
- If official evidence is unavailable or insufficient, mark the finding "uncertain".
- Never invent requirements, authorities, fees, penalties, citations, quotes, or applicability.

You will receive either:
(a) a regulation plan for first-time validation, or
(b) previous findings plus a problems summary.

For (b):
- Re-research ONLY items implicated by the feedback.
- Preserve unaffected items exactly, including reason, evidence, and citations.
- Add requirements identified as missing.
- Return the COMPLETE updated findings, including unchanged items.

For (a):
- Freshly research every item in the regulation plan.

For EVERY finding provide:
- issuing_authority: responsible government body.
- requirement_type: license, permit, certificate, registration, or other.
- status:
  "confirmed" = directly verified by an official source;
  "likely_required" = strongly indicated by official sources but exact applicability is unclear;
  "uncertain" = insufficient, unavailable, or conflicting evidence.
- reason: why it applies to this venture.
- evidence: what was found and how it was validated.
- citations: sources actually retrieved via web search, each with its URL and a short
  verbatim quote (≤1 sentence) directly supporting the finding.

Retrieve and inspect the underlying source; search-result snippets alone are not sufficient.

If the state, county, or locality is unspecified, do not assume one. Mark the jurisdiction
as uncertain and explain why.

Clearly distinguish confirmed, likely, and unresolved requirements.
""",
)


# ============================================================
# 5. RUN WORKFLOW
# ============================================================

def regulations_agent(
    venture_description: str,
    problems_summary: str | None = None,
    previous_findings: FinalRegulationFindings | dict | None = None,
) -> FinalRegulationFindings:

    has_feedback = bool(problems_summary) and bool(previous_findings)

    # ------------------------------------------------------------
    # AMEND PATH: reuse previous work, only re-research flagged items
    # ------------------------------------------------------------
    if has_feedback:

        if isinstance(previous_findings, FinalRegulationFindings):
            previous_plan = previous_findings
        else:
            previous_plan = FinalRegulationFindings.model_validate(previous_findings)

        prompt_amend = f"""
VENTURE:
{venture_description}

PROBLEMS SUMMARY (feedback on the previous plan):
{problems_summary}

PREVIOUS REGULATION FINDINGS:
{json.dumps(previous_plan.model_dump(), indent=2)}

Update only the items implicated by the problems summary. Return the
complete, updated set of findings including unchanged items.
"""
        amended_findings = validation_agent(
            prompt_amend,
            structured_output_model=FinalRegulationFindings,
        ).structured_output

        return amended_findings

    # ------------------------------------------------------------
    # FULL PATH: first run, no feedback given
    # ------------------------------------------------------------

    # 1. DISCOVERY STEP
    prompt_discover = f"""
    VENTURE:
    {venture_description}

    Identify all potentially relevant permits, licenses, certificates,
    registrations, or other regulatory requirements for this venture
    at the federal, state, and local level.

    Return a comprehensive candidate regulation plan.
"""
    expanded_plan = discovery_agent(
        prompt_discover,
        structured_output_model=RegulationPlan,
    ).structured_output

    # 2. FILTERING STEP
    prompt_filter = f"""
VENTURE:
{venture_description}

EXPANDED CANDIDATE REGULATIONS:
{json.dumps([r.model_dump() for r in expanded_plan.regulations], indent=2)}

Filter out unnecessary or redundant items and return the finalized list of essential regulations.
"""
    filtered_plan = filtering_agent(
        prompt_filter,
        structured_output_model=RegulationPlan,
    ).structured_output

    # 3. WEB SEARCH & VALIDATION STEP
    prompt_validate = f"""
VENTURE:
{venture_description}

FINAL REGULATION PLAN TO VALIDATE:
{json.dumps([r.model_dump() for r in filtered_plan.regulations], indent=2)}

Use web search to confirm and validate these specific regulatory items and
produce final findings.
"""
    final_findings = validation_agent(
        prompt_validate,
        structured_output_model=FinalRegulationFindings,
    ).structured_output

    return final_findings
