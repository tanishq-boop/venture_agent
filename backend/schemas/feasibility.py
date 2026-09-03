# backend/agents/orchestrator/schemas.py

from typing import Literal
from pydantic import BaseModel


class FeasibilityAssessment(BaseModel):
    overall_feasibility: Literal[
        "highly_feasible",
        "feasible",
        "moderately_feasible",
        "low_feasibility",
        "not_feasible",
    ]
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    major_risks: list[str]
    assumptions: list[str]
    unresolved_questions: list[str]
    reasoning: str