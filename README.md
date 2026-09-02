# Venture Agent Prototype

An autonomous business advisor for small and medium-sized businesses (SMBs).
A business defines **ventures** — objectives like opening a new location,
launching a product, or entering a new market — and a single orchestrator
agent evaluates whether the venture makes sense, gathering data via tools
and asking the user only when information is genuinely missing.

This is a **prototype**: one orchestrator agent, a handful of tools, SQLite
for storage, and a minimal frontend. It's built to be read end-to-end in a
few files, not to be production infrastructure.

## Architecture

```text
Frontend
   ↓
FastAPI
   ↓
Strands Orchestrator
   ↓
Tools
 ├── Business
 ├── Finance
 ├── People
 ├── Research
 └── Memory
   ↓
SQLite
```

There is one orchestrator agent (`backend/agent.py`) built with the
**Strands Agents SDK** running on **Amazon Bedrock**. It reasons across
venture viability, people/hiring, and finance itself — there is no
multi-agent split in this prototype. It calls tools (`backend/tools.py`)
to fetch business/venture/financial/people data, run deterministic
financial calculations, search for external research, and save notes to
memory.

## Repository structure

```text
venture-agent/
│
├── frontend/           # Minimal Next.js app (4 pages + chat)
│
├── backend/
│   ├── main.py          # FastAPI app and routes
│   ├── agent.py          # Strands orchestrator agent
│   ├── tools.py          # Tools the agent can call
│   ├── models.py         # Pydantic models
│   ├── database.py       # SQLite data access
│   └── requirements.txt
│
├── data/
│   └── seed.json         # Example SMB used to seed the database
│
├── .env.example
├── .gitignore
└── README.md
```

## 1. Create the virtual environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure AWS / Bedrock

Copy the example env file and fill in your values:

```bash
cp ../.env.example ../.env
```

Set, at minimum:

```env
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

Make sure your AWS credentials (e.g. via `aws configure`, environment
variables, or an IAM role) grant access to Bedrock in that region, and that
the chosen model is enabled for your account.

`SEARCH_API_KEY` is optional — leave it blank and `search_research` will
return a clearly-marked mock result so the rest of the workflow still runs.

## 4. Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The database is created and seeded automatically on first run (from
`data/seed.json`) at `backend/venture_agent.db`.

Visit `http://localhost:8000/` to confirm it's running, or
`http://localhost:8000/docs` for interactive API docs.

## 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000/`. Pages: `/business`, `/ventures`, `/people`,
`/finance`, each with a chat box to talk to the agent.

By default the frontend calls the backend at `http://localhost:8000`. To
change that, set `NEXT_PUBLIC_API_BASE` in `frontend/.env.local`.

## Example venture evaluation

The seed data includes business id `1` ("Example Bakery") with venture id
`1` ("Open a second bakery location", budget 600,000).

```bash
curl -X POST http://localhost:8000/ventures/1/evaluate
```

The orchestrator will:
1. Call `get_business_info(1)` and `get_venture_info(1)`.
2. Call `get_financial_info(1)` and `calculate_financial_position(...)` to
   check whether the business can afford the venture.
3. Call `get_people_info(1)` to check staffing.
4. Optionally call `search_research(...)` for market/competitor context.
5. Return a recommendation — one of `PROCEED`, `PROCEED WITH CONDITIONS`,
   `VALIDATE FIRST`, `DELAY`, or `DO NOT PURSUE` — with reasoning that
   separates facts, assumptions, and judgment.

You can also just chat with the agent directly:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"business_id": 1, "message": "Can we afford the second bakery location?"}'
```

## What this prototype intentionally does NOT do

Per its scope, this build skips: multi-agent architecture, vector
databases, Redis, message queues, Kubernetes, complex auth, and elaborate
repository/service layers. The code is meant to be simple enough to read
end-to-end, while structured cleanly enough to extend later (e.g. splitting
the orchestrator into Venture/Finance/People sub-agents, or replacing the
mock research tool with a real search integration).
