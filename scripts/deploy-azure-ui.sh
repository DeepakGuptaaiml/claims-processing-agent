#!/usr/bin/env bash
# One-time bootstrap: create claims-processing-agent-ui (Streamlit examiner UI).
# Prerequisite: claims-processing-agent-api deployed and healthy.

set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-claims-intelligence}"
ENV_NAME="${ENV_NAME:-claims-env}"
APP_NAME="${APP_NAME:-claims-processing-agent-ui}"
AGENT_APP="${AGENT_APP:-claims-processing-agent-api}"
IMAGE="${IMAGE:-ghcr.io/deepakguptaaiml/claims-processing-agent-streamlit:latest}"

echo "==> Resource group: $RESOURCE_GROUP"
AGENT_FQDN=$(az containerapp show \
  --name "$AGENT_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)
API_URL="https://${AGENT_FQDN}"
echo "==> Agent API: $API_URL"

REGISTRY_ARGS=()
if [[ -n "${GHCR_TOKEN:-}" ]]; then
  REGISTRY_ARGS=(
    --registry-server ghcr.io
    --registry-username "${GHCR_USER:-DeepakGuptaaiml}"
    --registry-password "$GHCR_TOKEN"
  )
  echo "==> Using private GHCR credentials"
else
  echo "==> Assuming public GHCR image"
fi

echo "==> Container app: $APP_NAME"
if az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  echo "    Updating existing UI..."
  az containerapp update \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$IMAGE" \
    --set-env-vars API_URL="$API_URL" \
    --output none
else
  echo "    Creating new UI..."
  az containerapp create \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENV_NAME" \
    --image "$IMAGE" \
    --target-port 8501 \
    --ingress external \
    --cpu 0.5 \
    --memory 1.0Gi \
    --min-replicas 0 \
    --max-replicas 2 \
    --env-vars API_URL="$API_URL" \
    "${REGISTRY_ARGS[@]}" \
    --output none
fi

FQDN=$(az containerapp show \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "============================================"
echo " Claims Processing Agent UI deployed"
echo "============================================"
echo " UI URL:  https://${FQDN}"
echo " API URL: ${API_URL}"
echo "============================================"
