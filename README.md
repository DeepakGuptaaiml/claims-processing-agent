# Claims Processing Agent

LangGraph orchestration layer for enterprise claims AI: Medicare reportability, reserve forecasting, and policy Q&A — without modifying the existing ML repos.

**Interview narrative:** [docs/INTERVIEW_ARCHITECTURE.md](docs/INTERVIEW_ARCHITECTURE.md)  
**Azure deploy:** [docs/AZURE_CD_SETUP.md](docs/AZURE_CD_SETUP.md)

## Architecture

```
POST /agent/process  (port 8002)
        │
        ▼
   LangGraph workflow
   ├── MCP claim store (Oracle CLAIMS_AI_RO views)
   ├── Medicare API  POST /predict  (:8000)
   ├── Reserve API   POST /predict  (:8001)
   └── Policy RAG    POST /ask      (:8000)
```

## Quick start (local, 3 terminals)

```bash
# Terminal 1 — Medicare classifier
cd ../medicare_classifier && source .venv/bin/activate
uvicorn app.main:app --port 8000

# Terminal 2 — Reserve forecaster
cd ../claims-intelligence && source .venv/bin/activate
uvicorn app.main:app --port 8001

# Terminal 3 — Agent
cd claims-processing-agent && source .venv/bin/activate
pip install -r requirements.txt
python mcp_server/seed/seed_from_csv.py
uvicorn app.main:app --port 8002 --reload
```

### Process a claim

```bash
curl -X POST http://127.0.0.1:8002/agent/process \
  -H "Content-Type: application/json" \
  -d '{"claim_id": "1000000.639", "question": "Should this claim be reported to Medicare?"}'
```

## Deploy to Azure

**API bootstrap** (once):

```bash
chmod +x scripts/deploy-azure-api.sh scripts/deploy-azure-ui.sh
IMAGE=ghcr.io/deepakguptaaiml/claims-processing-agent:latest \
  ./scripts/deploy-azure-api.sh
```

**Examiner UI bootstrap** (once, after API is healthy):

```bash
IMAGE=ghcr.io/deepakguptaaiml/claims-processing-agent-streamlit:latest \
  ./scripts/deploy-azure-ui.sh
```

**Ongoing:** push to `main` → CI builds API + Streamlit images → CD updates both apps.

| App | Azure name | Port |
|-----|------------|------|
| Agent API | `claims-processing-agent-api` | 8002 |
| Examiner UI | `claims-processing-agent-ui` | 8501 |

Add GitHub secrets: `AZURE_CREDENTIALS` (reuse from other repos).

## Examiner UI (local)

```bash
pip install -r requirements-streamlit.txt
API_URL=http://127.0.0.1:8002 streamlit run streamlit_app.py
```

## Config

| Variable | Default | Description |
|----------|---------|-------------|
| `MEDICARE_API_URL` | `http://127.0.0.1:8000` | Medicare + RAG API |
| `RESERVE_API_URL` | `http://127.0.0.1:8001` | Reserve forecaster |
| `STORE_BACKEND` | `sqlite` | Claim store backend |
| `SQLITE_DB_PATH` | `mcp_server/data/claims_ai.db` | Claim store path |

## Tests

```bash
pytest -q
```
