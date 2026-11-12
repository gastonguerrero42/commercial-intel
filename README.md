# Commercial Intelligence Multi-Agent System v2.1

Role: AI Engineer
Scope: CrewAI, Agents, Prompts, RAG, MCP, Guardrails, Human-in-the-Loop
Out of scope: Auth, Queues, Postgres Prod, Frontend, Infra

Flow: Query -> Input Guardrails -> FastAPI -> CrewAI Hierarchical Manager -> Ingestor (MCP) -> Analyst (RAG) -> Researcher (MCP Web) -> Writer_QA -> Output Guardrails -> DRAFT -> Human Approval -> FINAL

## Quickstart
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest -q

## API
POST /api/v1/ingest | POST /api/v1/analyze | GET /api/v1/reports/{id} | POST /api/v1/reports/{id}/approve | GET /health

## License
MIT
