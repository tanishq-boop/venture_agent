"""
Main Strands orchestrator agent for the Venture Agent prototype.

A single agent reasons across venture, people, and finance concerns instead
of a multi-agent architecture. It decides which tools to call and when to
ask the user for missing information.
"""

import os

from strands import Agent
from strands.models import BedrockModel

from tools import (
    get_business_info,
    get_venture_info,
    get_financial_info,
    get_people_info,
    calculate_financial_position,
    search_research,
    save_business_memory,
)

SYSTEM_PROMPT = """You are an autonomous business advisor for small and \
medium-sized businesses (SMBs).

Before making any recommendation:
- Understand the business (industry, location, financial snapshot) before
  evaluating a venture.
- Investigate the venture rather than answering immediately — use your
  tools to gather business, financial, and people data.
- Consider, as relevant to this venture: market/opportunity, execution
  capability, people/hiring needs, financial viability, key risks, and
  dependencies. Not every venture needs every angle explored in depth —
  use judgment about what matters here.
- Use tools whenever the information is available through them. Do not
  invent financial figures — use calculate_financial_position for any
  arithmetic.
- Ask the user only when important information cannot be obtained through
  tools (e.g. their risk tolerance, a preference, or a fact not in the
  system).
- Clearly distinguish facts (from tools), assumptions (things you're
  inferring), and recommendations (your judgment).

End your evaluation with a clear final recommendation, one of:
PROCEED, PROCEED WITH CONDITIONS, VALIDATE FIRST, DELAY, or DO NOT PURSUE.

Be concise. This is a prototype — favor a clear, well-reasoned answer over
an exhaustive report."""


def _build_model() -> BedrockModel:
    region = os.environ.get("AWS_REGION", "us-east-1")
    model_id = os.environ.get(
        "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    return BedrockModel(model_id=model_id, region_name=region)


def _build_agent() -> Agent:
    return Agent(
        model=_build_model(),
        system_prompt=SYSTEM_PROMPT,
        tools=[
            
        ],
    )


def evaluate_venture(business_id: int, venture_id: int) -> str:
    """Run the orchestrator on a specific venture and return its
    recommendation text."""
    agent = _build_agent()
    prompt = (
        f"Evaluate venture_id={venture_id} belonging to business_id={business_id}. "
        f"Start by calling get_business_info and get_venture_info, then gather "
        f"whatever else you need before giving your recommendation."
    )
    result = agent(prompt)
    return str(result)


def chat(business_id: int, message: str) -> str:
    """Handle a free-form chat message from the user, in the context of a
    specific business."""
    agent = _build_agent()
    prompt = f"[Context: business_id={business_id}]\n\nUser: {message}"
    result = agent(prompt)
    return str(result)
