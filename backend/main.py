"""
Minimal FastAPI app for the Venture Agent prototype.

Endpoints:
  GET  /
  GET  /business
  POST /business
  GET  /ventures
  POST /ventures
  GET  /ventures/{venture_id}
  POST /ventures/{venture_id}/evaluate
  POST /chat
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

import database
from models import Business, Venture, ChatRequest, ChatResponse, EvaluateResponse
import backend.orchestrator as agent_module

app = FastAPI(title="Venture Agent Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    database.init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "venture-agent-backend"}


# --- Business ---

@app.get("/business")
def list_business(business_id: int = 1):
    business = database.get_business(business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@app.post("/business")
def create_business(business: Business):
    created = database.create_business(business.model_dump(exclude={"id"}))
    return created


# --- Ventures ---

@app.get("/ventures")
def list_ventures(business_id: int = 1):
    return database.get_ventures(business_id)


@app.post("/ventures")
def create_venture(venture: Venture):
    created = database.create_venture(venture.model_dump(exclude={"id"}))
    return created


@app.get("/ventures/{venture_id}")
def get_venture(venture_id: int):
    venture = database.get_venture(venture_id)
    if not venture:
        raise HTTPException(status_code=404, detail="Venture not found")
    return venture


@app.post("/ventures/{venture_id}/evaluate", response_model=EvaluateResponse)
def evaluate_venture(venture_id: int):
    venture = database.get_venture(venture_id)
    if not venture:
        raise HTTPException(status_code=404, detail="Venture not found")

    recommendation = agent_module.evaluate_venture(
        business_id=venture["business_id"], venture_id=venture_id
    )
    database.update_venture_recommendation(venture_id, recommendation)

    return EvaluateResponse(venture_id=venture_id, recommendation=recommendation)


# --- People / Finance (support endpoints for the frontend pages) ---

@app.get("/employees")
def list_employees(business_id: int = 1):
    return database.get_employees(business_id)


@app.get("/finance")
def get_finance(business_id: int = 1):
    finance = database.get_finance(business_id)
    if not finance:
        raise HTTPException(status_code=404, detail="Finance info not found")
    return finance


# --- Chat ---

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply = agent_module.chat(request.business_id, request.message)
    return ChatResponse(reply=reply)
