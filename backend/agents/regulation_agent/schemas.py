import json
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# 1. STRUCTURED MODELS
# ============================================================

class RegulationItem(BaseModel):
    name: str = Field(description="Regulation, license, permit, or certificate category name")
    level: Literal["federal", "state", "local"] = Field(
        description="Jurisdiction level this requirement originates from"
    )
    reason: str = Field(description="Why this requirement is relevant")


class RegulationPlan(BaseModel):
    regulations: list[RegulationItem]


class Citation(BaseModel):
    source: str = Field(description="URL the requirement/evidence came from")
    quote: str = Field(description="Short verbatim excerpt supporting the finding")


class RegulationFinding(BaseModel):
    name: str
    level: Literal["federal", "state", "local"]
    requirement_type: Literal["license", "permit", "certificate", "registration", "other"]
    issuing_authority: str
    status: Literal["confirmed", "likely_required", "uncertain"]
    reason: str = Field(description="Why this requirement applies to this venture")
    evidence: str = Field(description="What was found / how the requirement was validated")
    citations: list[Citation] = Field(
        description="Sources backing this finding, each with a short supporting quote"
    )


class FinalRegulationFindings(BaseModel):
    findings: list[RegulationFinding]
