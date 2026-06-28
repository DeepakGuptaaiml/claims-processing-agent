# Azure CD Setup — Claims Processing Agent

GitHub Actions **CI** builds and pushes the Docker image to GHCR. **CD** (`.github/workflows/deploy-azure.yml`) runs after green CI on `main` and updates `claims-processing-agent-api`.

```
git push main → CI (test, build, push GHCR) → Deploy to Azure
```

---

## Prerequisites

These must already be running (same resource group):

| App | Name |
|-----|------|
| Medicare API | `medicare-classifier-api` |
| Reserve API | `claims-reserve-api` |
| Resource group | `rg-claims-intelligence` |

The agent calls both APIs over HTTPS. Policy RAG flows through Medicare `/ask` (no separate Search config on the agent).

---

## GitHub secrets

Reuse from your other repos:

| Secret | Purpose |
|--------|---------|
| `AZURE_CREDENTIALS` | Service principal JSON (Contributor on `rg-claims-intelligence`) |
| `GHCR_TOKEN` | Optional — private GHCR packages |
| `GHCR_USER` | Optional — GitHub username for GHCR |

No Azure Search or HF secrets needed on this repo.

---

## One-time bootstrap

CD **updates** an existing Container App; it does not create one. Run once:

```bash
cd claims-processing-agent
chmod +x scripts/deploy-azure-api.sh

# After first CI push builds the image:
IMAGE=ghcr.io/deepakguptaaiml/claims-processing-agent:latest \
  ./scripts/deploy-azure-api.sh
```

Or with private GHCR:

```bash
export GHCR_TOKEN=<pat>
export GHCR_USER=DeepakGuptaaiml
./scripts/deploy-azure-api.sh
```

---

## GHCR package public

**Packages** → `claims-processing-agent` → **Package settings** → **Public**

(or use `GHCR_TOKEN` secret)

---

## What happens on each push to `main`

1. **CI** — pytest, Docker build, push `latest` + `{7-char-sha}` to GHCR.
2. **Deploy** — triggered on CI success.
3. Resolves Medicare + Reserve FQDNs automatically.
4. `az containerapp update` with new image + env vars.
5. Curls `/health` on the live agent API.

---

## Environment variables (set by CD)

| Variable | Source |
|----------|--------|
| `MEDICARE_API_URL` | Auto-resolved from `medicare-classifier-api` FQDN |
| `RESERVE_API_URL` | Auto-resolved from `claims-reserve-api` FQDN |
| `STORE_BACKEND` | `sqlite` (claim store baked into image at build) |
| `SQLITE_DB_PATH` | `/app/mcp_server/data/claims_ai.db` |

---

## Verify deployment

```bash
FQDN=$(az containerapp show \
  -n claims-processing-agent-api \
  -g rg-claims-intelligence \
  --query "properties.configuration.ingress.fqdn" -o tsv)

curl -s "https://${FQDN}/health" | python3 -m json.tool

curl -s -X POST "https://${FQDN}/agent/process" \
  -H "Content-Type: application/json" \
  -d '{"claim_id":"1000000.639","question":"Should this claim be reported to Medicare?"}' \
  | python3 -m json.tool
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Deploy fails "app not found" | Run `scripts/deploy-azure-api.sh` once |
| `/agent/process` medicare error | Check `medicare-classifier-api` is healthy |
| `/agent/process` reserve error | Check `claims-reserve-api` is healthy |
| Policy empty / error | Check Medicare `/ask` + Azure Search on medicare app |
| GHCR pull failed | Make package public or set `GHCR_TOKEN` |
| Cold start slow | First request after scale-from-zero takes ~30s |

See also: [INTERVIEW_ARCHITECTURE.md](INTERVIEW_ARCHITECTURE.md)
