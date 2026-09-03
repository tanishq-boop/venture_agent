import json
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# 1. STRUCTURED MODELS
# ============================================================

class CostItem(BaseModel):
    name: str = Field(description="Cost category name")
    cost_type: Literal["one_time", "continuous", "both"] = Field(
        description="When the cost occurs"
    )
    reason: str = Field(description="Why this cost is relevant")


class CostPlan(BaseModel):
    costs: list[CostItem]


class Citation(BaseModel):
    source: str = Field(description="URL the figure/evidence came from")
    quote: str = Field(description="Short verbatim excerpt supporting the estimate")


class CostEstimate(BaseModel):
    name: str
    cost_type: Literal["one_time", "continuous", "both"]
    estimated_one_time_cost: float | None = None
    estimated_monthly_cost: float | None = None
    currency: str
    reason: str = Field(description="Why this cost applies to this venture")
    evidence: str = Field(description="What was found / how the number was derived")
    citations: list[Citation] = Field(
        description="Sources backing this estimate, each with a short supporting quote"
    )


class FinalCostEstimates(BaseModel):
    estimates: list[CostEstimate]