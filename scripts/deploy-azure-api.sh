#!/usr/bin/env bash
# One-time bootstrap: create claims-processing-agent-api on Azure Container Apps.
# CD workflow (deploy-azure.yml) updates the image on each push to main.
#
# Prerequisites: az login, medicare-classifier-api + claims-reserve-api already deployed.

set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-claims-intelligence}"
LOCATION="${LOCATION:-eastus}"
ENV_NAME="${ENV_NAME:-claims-env}"
APP_NAME="${APP_NAME:-claims-processing-agent-api}"
MEDICARE_APP="${MEDICARE_APP:-medicare-classifier-api}"
RESERVE_APP="${RESERVE_APP:-claims-reserve-api}"
IMAGE="${IMAGE:-ghcr.io/deepakguptaaiml/claims-processing-agent:latest}"

echo "==> Resource group: $RESOURCE_GROUP"
MEDICARE_FQDN=$(az containerapp show \
  --name "$MEDICARE_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)
RESERVE_FQDN=$(az containerapp show \
  --name "$RESERVE_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)
MEDICARE_API_URL="https://${MEDICARE_FQDN}"
RESERVE_API_URL="https://${RESERVE_FQDN}"
echo "==> Medicare API: $MEDICARE_API_URL"
echo "==> Reserve API:  $RESERVE_API_URL"

REGISTRY_ARGS=()
if [[ -n "${GHCR_TOKEN:-}" ]]; then
  REGISTRY_ARGS=(
    --registry-server ghcr.io
    --registry-username "${GHCR_USER:-DeepakGuptaaiml}"
    --registry-password "$GHCR_TOKEN"
  )
  echo "==> Using private GHCR credentials"
else
  echo "==> Assuming public GHCR image (no registry credentials)"
fi

echo "==> Container app: $APP_NAME"
if az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  echo "    Updating existing app..."
  az containerapp update \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$IMAGE" \
    --set-env-vars \
      MEDICARE_API_URL="$MEDICARE_API_URL" \
      RESERVE_API_URL="$RESERVE_API_URL" \
      STORE_BACKEND=sqlite \
      SQLITE_DB_PATH=/app/mcp_server/data/claims_ai.db \
    --output none
else
  echo "    Creating new app..."
  az containerapp create \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENV_NAME" \
    --image "$IMAGE" \
    --target-port 8002 \
    --ingress external \
    --cpu 0.5 \
    --memory 1.0Gi \
    --min-replicas 0 \
    --max-replicas 2 \
    --env-vars \
      MEDICARE_API_URL="$MEDICARE_API_URL" \
      RESERVE_API_URL="$RESERVE_API_URL" \
      STORE_BACKEND=sqlite \
      SQLITE_DB_PATH=/app/mcp_server/data/claims_ai.db \
    "${REGISTRY_ARGS[@]}" \
    --output none
fi

FQDN=$(az containerapp show \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv)

echo ""
echo "============================================"
echo " Claims Processing Agent deployed"
echo "============================================"
echo " URL:     https://${FQDN}"
echo " Health:  https://${FQDN}/health"
echo " Swagger: https://${FQDN}/docs"
echo ""
echo "Test:"
echo "  curl https://${FQDN}/health"
echo ""
echo '  curl -X POST https://'"${FQDN}"'/agent/process \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{"claim_id":"1000000.639","question":"Should this claim be reported to Medicare?"}'"'"
echo "============================================"
