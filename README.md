# Claims Processing Agent

LangGraph orchestration layer for enterprise claims AI: Medicare reportability, reserve forecasting, and policy Q&A — without modifying the existing ML repos.

## Architecture

```
POST /agent/process  (port 8002)
        │
        ▼
   LangGraph workflow
   ├── MCP claim store (SQLite dev → Oracle prod)
   ├── Medicare API  POST /predict  (:8000)
   ├── Reserve API   POST /predict  (:8001)
   └── Policy RAG    POST /ask      (:8000)
```

**Interview story:** One Oracle instance, multiple OLTP schemas, single `CLAIMS_AI_RO` read-only view layer exposed via MCP tools. Dev uses SQLite tables mirroring those views, seeded from `claims_data.csv`.

## Quick start (3 terminals)

```bash
# Terminal 1 — Medicare classifier
cd ../medicare_classifier && uvicorn app.main:app --port 8000

# Terminal 2 — Reserve forecaster
cd ../claims-intelligence && uvicorn app.main:app --port 8001

# Terminal 3 — Agent
cd claims-processing-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python mcp_server/seed/seed_from_csv.py
uvicorn app.main:app --port 8002 --reload
```

### Process a claim

```bash
curl -X POST http://127.0.0.1:8002/agent/process \
  -H "Content-Type: application/json" \
  -d '{"claim_id": "1000000.639", "question": "Should this claim be reported to Medicare?"}'
```

## MCP server (optional)

Expose claim-history tools over stdio for Claude Desktop / Cursor MCP clients:

```bash
python mcp_server/server.py
```

Tools: `get_claim_summary`, `get_payment_summary`, `get_reserve_context`, `get_claimant_context`

## Config

| Variable | Default | Description |
|----------|---------|-------------|
| `MEDICARE_API_URL` | `http://127.0.0.1:8000` | Medicare + RAG API |
| `RESERVE_API_URL` | `http://127.0.0.1:8001` | Reserve forecaster |
| `STORE_BACKEND` | `sqlite` | `sqlite` or `oracle` |
| `SQLITE_DB_PATH` | `mcp_server/data/claims_ai.db` | Dev DB |
| `CLAIMS_CSV_PATH` | `../medicare_classifier/data/claims_data.csv` | Seed source |

## Tests

```bash
pytest -q
```

## Prod swap

Set `STORE_BACKEND=oracle` and `ORACLE_DSN` / `ORACLE_USER` / `ORACLE_PASSWORD`. Only `OracleClaimStore` changes — LangGraph workflow and MCP tool names stay the same.
