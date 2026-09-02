import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))
s
try:
    from .schemas import RegulationItem, RegulationPlan, RegulationReport
except ImportError:
    from schemas import RegulationItem, RegulationPlan, RegulationReport

from strands import Agent
from strands.models import BedrockModel
from tools import cached_web_search


# ============================================================
# 1. STARTER REGULATORY BASELINES (US LOCAL & STATE)
# ============================================================

baseline_regulations = [
    RegulationItem(
        name="certificate_of_occupancy_and_zoning",
        governing_body="City Building & Development Services",
        strictness="very_strict",
        punishment_for_violation="Immediate stop-work order or red-tag padlocking; prohibited from opening to the public.",
        maintenance_difficulty="low",
        ongoing_obligations=[
            "Maintain approved floor plan and occupancy limits",
            "Annual fire marshal life-safety inspection"
        ],
        estimated_fees="$200 - $800 one-time"
    ),
    RegulationItem(
        name="local_health_department_operating_permit",
        governing_body="City / County Public Health Department",
        strictness="very_strict",
        punishment_for_violation="Mandatory closure notices, public health grade downgrade, and daily escalating fines.",
        maintenance_difficulty="high",
        ongoing_obligations=[
            "Twice-daily refrigeration and hot-holding temperature logs",
            "Mandatory Certified Food Protection Manager on shift",
            "Unannounced random inspections"
        ],
        estimated_fees="$250 - $600/year renewal"
    ),
    RegulationItem(
        name="state_sales_tax_and_business_registration",
        governing_body="State Department of Revenue / Secretary of State",
        strictness="very_strict",
        punishment_for_violation="Tax liens, freeze on business bank accounts, and revocation of authority to transact business.",
        maintenance_difficulty="moderate",
        ongoing_obligations=[
            "Monthly or quarterly state sales tax remittance",
            "Annual franchise tax reporting"
        ],
        estimated_fees="$50 - $300 one-time state filing"
    ),
    RegulationItem(
        name="workplace_safety_and_labor_standards",
        governing_body="OSHA & State Workforce Commission",
        strictness="moderate",
        punishment_for_violation="OSHA citations starting at several thousand dollars per violation, back-wage claims, and workers' compensation penalties.",
        maintenance_difficulty="moderate",
        ongoing_obligations=[
            "Mandatory statutory labor law poster displays",
            "Workers' Compensation insurance coverage",
            "Safety Data Sheets (SDS) for all commercial cleaning chemicals"
        ],
        estimated_fees="Included in recurring workers' comp insurance premiums"
    ),
]


# ============================================================
# 2. BEDROCK MODEL CONFIGURATION
# ============================================================

bedrock_model = BedrockModel(
    model_id="amazon.nova-2-lite-v1:0",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    temperature=0.1,
)


# ============================================================
# 3. WORKFLOW AGENTS
# ============================================================

# Step 1: Review baseline, drop non-applicable, discover specific rules, write queries
regulation_planner_agent = Agent(
    model=bedrock_model,
    system_prompt="""
You are a US Regulatory Compliance & Municipal Licensing Specialist.
Analyze the business venture and target city/state:

1. Review the starter baseline regulations:
   - Keep baselines that strictly apply.
   - Remove baselines that do not apply (e.g., remove food health permits for software or dry retail).
2. Discover and add venture-specific rules (e.g., grease trap wastewater permits for bakeries/restaurants, liquor licensing, FDA facility registrations for wholesale packaged goods).
3. Formulate 2 to 3 targeted search queries targeting official municipal (austintexas.gov, county health) or state regulatory requirements, penalties, and renewal fee schedules.
""",
)

# Step 2: Synthesize findings into structured severity, punishment, and maintenance metrics
regulation_analyst_agent = Agent(
    model=bedrock_model,
    system_prompt="""
You are a Commercial Regulatory Legal Analyst.
Evaluate the gathered legal and municipal findings against the approved regulations:
1. Specify explicit punishments for non-compliance (fines, court citations, forced closure).
2. Rate the ongoing maintenance difficulty (high/moderate/low) based on the operational friction of logs, recurrent audits, and certifications.
3. Categorize the overall burden: 'heavy' (heavily regulated like food, alcohol, childcare), 'moderate', or 'light'.
4. Identify showstopper penalties and provide a chronological pre-opening checklist.
""",
)


# ============================================================
# 4. EXECUTION PIPELINE
# ============================================================

def evaluate_regulations(venture_description: str, location: str) -> RegulationReport:
    """Discovers rules, determines punishments and maintenance difficulty, and builds an action checklist."""

    # 1. Plan regulations to investigate & formulate queries
    plan_prompt = f"""
VENTURE:
{venture_description}

TARGET LOCATION:
{location}

STARTER BASELINE REGULATIONS:
{json.dumps([r.model_dump() for r in baseline_regulations], indent=2)}

Review the baselines, prune irrelevant items, add venture-specific local/state requirements, and generate 2-3 search queries.
"""
    plan: RegulationPlan = regulation_planner_agent(
        plan_prompt,
        structured_output_model=RegulationPlan,
    ).structured_output

    # 2. Execute cached web searches
    search_dossier = [
        {"query": q, "result": cached_web_search(q)}
        for q in plan.search_queries
    ]

    # 3. Analyze strictness, punishment, and operational maintenance
    analysis_prompt = f"""
VENTURE:
{venture_description}

TARGET LOCATION:
{location}

APPROVED REGULATIONS:
{json.dumps([r.model_dump() for r in plan.approved_regulations], indent=2)}

RESEARCH DATA:
{json.dumps(search_dossier, indent=2)}

Generate the complete RegulationReport detailing strictness, penalties, maintenance difficulty, and required steps.
"""
    report: RegulationReport = regulation_analyst_agent(
        analysis_prompt,
        structured_output_model=RegulationReport,
    ).structured_output

    return report


if __name__ == "__main__":
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
        print(f" * {reg.name} ({reg.strictness.upper()} strictness | {reg.maintenance_difficulty.upper()} maintenance)")
        print(f"   Punishment: {reg.punishment_for_violation}")
        print(f"   Ongoing Tasks: {reg.ongoing_obligations}")
        print(f"   Fees: {reg.estimated_fees}")