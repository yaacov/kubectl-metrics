#!/bin/bash
# Start MCP server in binary mode (background process)

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
METRICS_BINARY="${METRICS_BINARY:-$MCP_DIR/../../kubectl-metrics}"
SERVER_PID_FILE="$MCP_DIR/.server.pid"
SERVER_LOG_FILE="$MCP_DIR/.server.log"
KUBECONFIG_FILE="$MCP_DIR/.kubeconfig"

# Check if server already running
if [ -f "$SERVER_PID_FILE" ]; then
    PID=$(cat "$SERVER_PID_FILE")
    if is_process_running "$PID"; then
        error "Server already running (PID $PID)"
        exit 1
    else
        echo "Removing stale PID file"
        rm -f "$SERVER_PID_FILE"
    fi
fi

# Check binary exists
if [ ! -x "$METRICS_BINARY" ]; then
    error "kubectl-metrics binary not found or not executable: $METRICS_BINARY"
    info "Build it with: make build"
    exit 1
fi

# Start server
echo "Starting MCP server (binary mode)..."
info "Binary: $METRICS_BINARY"
info "Host:   $MCP_HTTP_HOST"
info "Port:   $MCP_HTTP_PORT"

ARGS=(mcp-server --http --port "$MCP_HTTP_PORT" --host "$MCP_HTTP_HOST")

# When credentials are provided, write a temporary kubeconfig
# instead of passing --token on the command line (avoids leaking
# the token in `ps` output).
KUBECONFIG_ENV="/dev/null"
if [ -n "${KUBE_API_URL:-}" ] || [ -n "${KUBE_TOKEN:-}" ]; then
    cat > "$KUBECONFIG_FILE" <<KUBEEOF
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: ${KUBE_API_URL:-https://kubernetes.default.svc}
    insecure-skip-tls-verify: true
  name: e2e
contexts:
- context:
    cluster: e2e
    user: e2e
  name: e2e
current-context: e2e
users:
- name: e2e
  user:
    token: ${KUBE_TOKEN:-}
KUBEEOF
    chmod 600 "$KUBECONFIG_FILE"
    KUBECONFIG_ENV="$KUBECONFIG_FILE"
    info "API:    ${KUBE_API_URL:-(default)}"
fi

KUBECONFIG="$KUBECONFIG_ENV" "$METRICS_BINARY" "${ARGS[@]}" \
    > "$SERVER_LOG_FILE" 2>&1 &

SERVER_PID=$!
echo "$SERVER_PID" > "$SERVER_PID_FILE"

# Verify process started and is still running
sleep 1
if ! is_process_running "$SERVER_PID"; then
    error "Server process died"
    info "Check log: $SERVER_LOG_FILE"
    rm -f "$SERVER_PID_FILE" "$KUBECONFIG_FILE"
    exit 1
fi

# Wait for server to start listening
if ! wait_for_server "$MCP_HTTP_HOST" "$MCP_HTTP_PORT" 30 "Server"; then
    error "Server is running but not accepting connections"
    info "Check log: $SERVER_LOG_FILE"
    kill "$SERVER_PID" 2>/dev/null || true
    rm -f "$SERVER_PID_FILE" "$KUBECONFIG_FILE"
    exit 1
fi

success "Server started successfully (PID $SERVER_PID)"
info "Log: $SERVER_LOG_FILE"
info "URL: http://$MCP_HTTP_HOST:$MCP_HTTP_PORT/mcp"
exit 0
