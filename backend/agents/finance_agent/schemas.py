import json
from typing import Literal

from pydantic import BaseModel, Field
from strands import Agent


# ============================================================
# 1. STRUCTURED MODELS (UNCHANGED)
# ============================================================

class CostItem(BaseModel):
    name: str = Field(description="Cost category name")
    cost_type: Literal["one_time", "continuous", "both"] = Field(
        description="When the cost occurs"
    )
    reason: str = Field(description="Why this cost is relevant")


class CostPlan(BaseModel):
    costs: list[CostItem]


class CostEstimate(BaseModel):
    name: str
    cost_type: Literal["one_time", "continuous", "both"]
    estimated_one_time_cost: float | None = None
    estimated_monthly_cost: float | None = None
    currency: str
    explanation: str
    sources: list[str]


class FinalCostEstimates(BaseModel):
    estimates: list[CostEstimate]


