from typing import Literal
from pydantic import BaseModel, Field


class DemandFactor(BaseModel):
    name: str = Field(description="Factor name (e.g., target_demographics, foot_traffic, night_economy)")
    category: str = Field(description="Category (e.g., demographics, neighborhood, competition, demand)")
    reason: str = Field(description="Operational justification for why this factor matters to this venture")


class DemandPlan(BaseModel):
    approved_factors: list[DemandFactor] = Field(
        description="Final evaluated list (baselines kept + custom additions - pruned irrelevant items)"
    )
    search_queries: list[str] = Field(
        description="2 to 3 targeted, location-specific US search queries",
        max_length=3,
    )


class LocationReport(BaseModel):
    target_location: str
    viability_score: int = Field(ge=0, le=100, description="0 to 100 viability score")
    verdict: Literal["prime_location", "viable", "high_risk", "unfavorable"]
    demographic_fit: str = Field(description="Income level, density, and customer persona alignment")
    competition_summary: str = Field(description="Incumbent density, saturation, and competitor posture")
    key_advantages: list[str] = Field(description="Key local demand drivers or tailwinds")
    key_risks: list[str] = Field(description="Headwinds, oversaturation, or operational friction")