#!/bin/bash
# Start MCP server in container mode (docker/podman)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$(dirname "$SCRIPT_DIR")"

# Load shared library
# shellcheck disable=SC1091
source "$SCRIPT_DIR/lib.sh"

# Load environment
load_env "$MCP_DIR"

# Configuration
MCP_HTTP_HOST="${MCP_HTTP_HOST:-127.0.0.1}"
MCP_HTTP_PORT="${MCP_HTTP_PORT:-19091}"
MCP_IMAGE="${MCP_IMAGE:-}"
CONTAINER_NAME="mcp-metrics-e2e-${MCP_HTTP_PORT}"

# Validate required variables
require_env MCP_IMAGE

# Detect container engine
if ! ENGINE=$(detect_container_engine); then
    error "No container engine found (docker or podman)"
    info "Install one or set CONTAINER_ENGINE environment variable"
    exit 1
fi

# Check if container already exists
if $ENGINE ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
    if $ENGINE ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
        error "Container already running: $CONTAINER_NAME"
        exit 1
    else
        echo "Removing stopped container: $CONTAINER_NAME"
        $ENGINE rm "$CONTAINER_NAME" >/dev/null
    fi
fi

# Start container
echo "Starting MCP server (container mode)..."
info "Image:    $MCP_IMAGE"
info "Engine:   $ENGINE"
info "Host:     $MCP_HTTP_HOST"
info "Port:     $MCP_HTTP_PORT"

ENV_ARGS=(-e "MCP_PORT=8080" -e "MCP_HOST=0.0.0.0")
[ -n "${KUBE_API_URL:-}" ]      && ENV_ARGS+=(-e "MCP_KUBE_SERVER=${KUBE_API_URL}")
[ -n "${KUBE_TOKEN:-}" ]        && ENV_ARGS+=(-e "MCP_KUBE_TOKEN=${KUBE_TOKEN}")
[ -n "${MCP_KUBE_INSECURE:-}" ] && ENV_ARGS+=(-e "MCP_KUBE_INSECURE=${MCP_KUBE_INSECURE}")
[ -n "${MCP_CERT_FILE:-}" ]     && ENV_ARGS+=(-e "MCP_CERT_FILE=${MCP_CERT_FILE}")
[ -n "${MCP_KEY_FILE:-}" ]      && ENV_ARGS+=(-e "MCP_KEY_FILE=${MCP_KEY_FILE}")
[ -n "${MCP_METRICS_URL:-}" ]   && ENV_ARGS+=(-e "MCP_METRICS_URL=${MCP_METRICS_URL}")

$ENGINE run -d \
    --name "$CONTAINER_NAME" \
    -p "${MCP_HTTP_HOST}:${MCP_HTTP_PORT}:8080" \
    "${ENV_ARGS[@]}" \
    "$MCP_IMAGE" >/dev/null

# Verify container is still running
sleep 1
if ! $ENGINE ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
    error "Container stopped unexpectedly"
    info "Check logs: $ENGINE logs $CONTAINER_NAME"
    $ENGINE rm "$CONTAINER_NAME" 2>/dev/null || true
    exit 1
fi

# Wait for container to start listening
if ! wait_for_server "$MCP_HTTP_HOST" "$MCP_HTTP_PORT" 30 "Container"; then
    error "Container is running but not accepting connections"
    info "Check logs: $ENGINE logs $CONTAINER_NAME"
    exit 1
fi

success "Container started successfully: $CONTAINER_NAME"
info "URL:  http://$MCP_HTTP_HOST:$MCP_HTTP_PORT/mcp"
info "Logs: $ENGINE logs -f $CONTAINER_NAME"
exit 0
