# Claims Processing Agent — Interview Architecture

Enterprise narrative for LangGraph + MCP + Oracle + RAG. Use this doc to rehearse demos and system-design answers.

---

## Elevator pitch (30 seconds)

> We built a **LangGraph claims processing agent** that takes a claim ID, pulls read-only context from **Oracle `CLAIMS_AI_RO` views via MCP tools**, runs **Medicare reportability** and **reserve forecasting** ML models, invokes **policy RAG over Azure AI Search** when regulatory context is needed, and returns a **synthesized recommendation with a full reasoning trace** — without the agent ever writing to OLTP or generating SQL.

---

## Three repos, one platform

| Repo | Role | Azure app |
|------|------|-----------|
| `medicare_classifier` | Medicare ML + Policy RAG (`/predict`, `/ask`) | `medicare-classifier-api` |
| `claims-intelligence` | Reserve forecasting ML (`/predict`) | `claims-reserve-api` |
| `claims-processing-agent` | LangGraph orchestrator (`/agent/process`) | `claims-processing-agent-api` |

The agent **does not own models or the search index**. It orchestrates existing services over HTTPS.

---

## End-to-end flow

```
User → POST /agent/process { claim_id, question }
              │
              ▼
       LangGraph workflow
              │
   ┌──────────┼──────────┬─────────────┐
   ▼          ▼          ▼             ▼
 Oracle     Medicare    Reserve     Policy RAG
 MCP tools  /predict    /predict    /ask → Azure AI Search
 (views)    (ML)        (ML)        (retrieval + LLM)
              │
              ▼
       synthesize → recommendation + reasoning_steps
```

### LangGraph nodes (execution order)

1. **fetch_claim** — MCP claim-history tools → Oracle read-only views
2. **check_medicare** — 20 features → Medicare classifier API
3. **predict_reserve** — 12 features → Reserve forecaster API
4. **search_policy** — contextual question → Medicare `/ask` (RAG)
5. **synthesize** — merge ML outputs + policy text → final recommendation

Shared **AgentState** carries `claim_id`, payloads, API results, and `reasoning_steps` for auditability.

---

## Oracle data layer (CLAIMS_AI_RO)

One Oracle instance, multiple OLTP schemas (CLAIMS, PARTY, PAYMENTS). The AI layer **never queries raw tables**.

DBAs expose four **read-only views** in schema **`CLAIMS_AI_RO`**:

| View | Purpose |
|------|---------|
| `V_CLAIM_SUMMARY_FOR_AI` | 20 Medicare classifier features |
| `V_PAYMENT_SUMMARY_FOR_AI` | Payment amounts (paid_1, paid_3, amount) |
| `V_RESERVE_CONTEXT_FOR_AI` | 12 reserve model features |
| `V_CLAIMANT_CONTEXT_FOR_AI` | Aggregated claimant history (hashed key, no raw SSN) |

All access is **parameterized SQL only** — never LLM-generated:

```sql
SELECT * FROM CLAIMS_AI_RO.V_CLAIM_SUMMARY_FOR_AI
WHERE claim_id = :claim_id
```

Read replica / dedicated read-only user `CLAIMS_AI_RO` — no writes to OLTP.

---

## MCP role

**MCP (Model Context Protocol)** exposes claim history as standard tools:

| MCP tool | Oracle view |
|----------|-------------|
| `get_claim_summary` | `V_CLAIM_SUMMARY_FOR_AI` |
| `get_payment_summary` | `V_PAYMENT_SUMMARY_FOR_AI` |
| `get_reserve_context` | `V_RESERVE_CONTEXT_FOR_AI` |
| `get_claimant_context` | `V_CLAIMANT_CONTEXT_FOR_AI` |

LangGraph's first node calls these tools. MCP provides a **stable tool contract**; the backend is Oracle in production.

---

## Where RAG fits (agentic, not standalone)

**Medicare `/ask` alone** = single-step retrieve → generate (policy chatbot).

**Inside the agent**, RAG is **one node** in a multi-step graph:

1. Agent already loaded claim context from Oracle (ORM threshold, WC flag, etc.).
2. Builds a contextual policy question: *"Should this be reported? ORM threshold met=1"*.
3. Calls Medicare API `POST /ask`.
4. Medicare RAG retrieves from **Azure AI Search** index `medicare-policy` (MMSEA, MCI, MCRC).
5. Returns answer + sources to the synthesize node.

> "RAG is not the agent — it is a **tool the agent invokes** when regulatory context is required."

---

## Example walkthrough

**Input:** `claim_id=1000000.639`, question *"Should this claim be reported to Medicare?"*

| Step | Action | Output |
|------|--------|--------|
| fetch_claim | MCP → Oracle views | WC claim, ORM threshold met, age 70 |
| check_medicare | `/predict` | Reportable, P=0.91 |
| predict_reserve | `/predict` | Reserve $12,500 |
| search_policy | `/ask` | ORM reporting rules + CMS sources |
| synthesize | merge | Full recommendation + reasoning_steps |

---

## Agentic vs basic RAG

| Basic RAG | LangGraph agent |
|-----------|-----------------|
| User asks policy question | User provides **claim_id** |
| Retrieve → answer | **Fetch claim → ML → RAG → synthesize** |
| Single step | 5-node graph with state |
| No ML integration | Two ML models orchestrated |
| No audit trail | `reasoning_steps` logged |

---

## Security & compliance talking points

- Read-only Oracle user on views only — no PHI in view layer (SSN hashed).
- Parameterized queries — SQL injection / LLM SQL generation not allowed.
- Agent has no write path to claims systems.
- Policy answers cite document sources from RAG retrieval.
- Reasoning steps support adjuster audit and explainability.

---

## Azure deployment topology

```
                    Internet
                        │
                        ▼
         claims-processing-agent-api (:8002)
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
  Oracle (prod)   medicare-classifier-api   claims-reserve-api
  CLAIMS_AI_RO    /predict + /ask              /predict
  read replica         │
                       ▼
                 Azure AI Search
                 medicare-policy index
```

---

## Future enhancements (mention if asked)

- **Conditional routing** — skip reserve if not Medicare-reportable
- **Human-in-the-loop** — adjuster approval node before final output
- **LLM synthesis node** — replace template with governed LLM summary
- **Azure OpenAI** — swap HF Inference for HIPAA-compliant generation

---

## Demo commands

```bash
# Health
curl https://<agent-fqdn>/health

# Process a claim
curl -X POST https://<agent-fqdn>/agent/process \
  -H "Content-Type: application/json" \
  -d '{"claim_id":"1000000.639","question":"Should this claim be reported to Medicare?"}'
```

---

## What not to say

- Do not describe local dev storage — say **Oracle read-only views on a read replica**.
- Do not say "the agent is RAG" — say **"RAG is one tool in the agent workflow"**.
- Do not say "MCP creates the database" — say **"MCP exposes Oracle views as tools"**.
