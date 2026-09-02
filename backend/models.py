"""
Simple Pydantic models for the Venture Agent prototype.

Kept intentionally minimal: this is a prototype, not a production schema.
"""

from typing import Optional
from pydantic import BaseModel


class Business(BaseModel):
    id: Optional[int] = None
    name: str
    industry: str
    location: str
    revenue: float = 0
    expenses: float = 0
    profit: float = 0
    cash: float = 0
    assets: float = 0


class Venture(BaseModel):
    id: Optional[int] = None
    business_id: int
    objective: str
    budget: float
    status: str = "proposed"


class Employee(BaseModel):
    id: Optional[int] = None
    business_id: int
    name: str
    role: str
    salary: float


class Finance(BaseModel):
    business_id: int
    revenue: float = 0
    expenses: float = 0
    profit: float = 0
    cash: float = 0
    debt: float = 0


class Memory(BaseModel):
    id: Optional[int] = None
    business_id: int
    content: str


# --- Request/response helpers used by main.py ---

class ChatRequest(BaseModel):
    business_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str


class EvaluateResponse(BaseModel):
    venture_id: int
    recommendation: str
