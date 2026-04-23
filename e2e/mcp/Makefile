# ============================================================================
# MCP E2E Test Suite – Makefile
#
# Server Lifecycle (3 steps):
#   1. Start server:    make server-start (binary) or server-start-image (container)
#   2. Run tests:       make test
#   3. Stop server:     make server-stop
#
# Quick workflow:
#   make test-full              # Start server, run all tests, stop server (binary)
#   make test-full-image        # Start server, run all tests, stop server (container)
# ============================================================================

SHELL   := /bin/bash
PYTHON  ?= python3
VENV    := .venv
PIP     := $(VENV)/bin/pip
PYTEST  := $(VENV)/bin/pytest

PYTEST_ARGS ?= -v -s --tb=short

SCRIPTS_DIR := scripts

.DEFAULT_GOAL := help

# ── Setup ──────────────────────────────────────────────────────────────────

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)

## install: Create virtualenv and install all dependencies
.PHONY: install
install: $(VENV)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install "."

# ── Server Management ──────────────────────────────────────────────────────

## server-start: Start MCP server (binary mode) in background
.PHONY: server-start
server-start:
	@$(SCRIPTS_DIR)/server-start.sh

## server-start-image: Start MCP server (container mode) in background
.PHONY: server-start-image
server-start-image:
	@$(SCRIPTS_DIR)/server-start-image.sh

## server-stop: Stop MCP server (binary mode)
.PHONY: server-stop
server-stop:
	@$(SCRIPTS_DIR)/server-stop.sh

## server-stop-image: Stop MCP server (container mode)
.PHONY: server-stop-image
server-stop-image:
	@$(SCRIPTS_DIR)/server-stop-image.sh

## server-stop-all: Stop all MCP servers (both binary and container)
.PHONY: server-stop-all
server-stop-all:
	@$(SCRIPTS_DIR)/server-stop.sh || true
	@$(SCRIPTS_DIR)/server-stop-image.sh || true

## server-status: Check if MCP server is running
.PHONY: server-status
server-status:
	@$(SCRIPTS_DIR)/server-status.sh

# ── Test Targets ───────────────────────────────────────────────────────────

## test: Run the full ordered test suite (requires running server)
.PHONY: test
test: install
	$(PYTEST) $(PYTEST_ARGS)

## test-full: Start server (binary), run tests, stop server
.PHONY: test-full
test-full: install server-stop
	@trap 'make server-stop' EXIT; $(SCRIPTS_DIR)/server-start.sh && $(PYTEST) $(PYTEST_ARGS)

## test-full-image: Start server (container), run tests, stop server (set MCP_IMAGE)
.PHONY: test-full-image
test-full-image: install server-stop-image
	@trap 'make server-stop-image' EXIT; $(SCRIPTS_DIR)/server-start-image.sh && $(PYTEST) $(PYTEST_ARGS)

## test-setup: Run only MCP server connectivity tests
.PHONY: test-setup
test-setup: install
	$(PYTEST) $(PYTEST_ARGS) setup/

## test-tools: Run only MCP tool tests (metrics_help, metrics_read)
.PHONY: test-tools
test-tools: install
	$(PYTEST) $(PYTEST_ARGS) tools/

# ── Cleanup ────────────────────────────────────────────────────────────────

## clean: Remove virtualenv, server artifacts, and caches
.PHONY: clean
clean:
	@$(SCRIPTS_DIR)/server-stop.sh || true
	@$(SCRIPTS_DIR)/server-stop-image.sh || true
	rm -rf $(VENV) .pytest_cache __pycache__ .server.log .server.pid .kubeconfig
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# ── Help ───────────────────────────────────────────────────────────────────

## help: Show this help message
.PHONY: help
help:
	@echo ""
	@echo "MCP E2E Test Suite (kubectl-metrics)"
	@echo "====================================="
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | \
		sed 's/^## //' | \
		awk -F': ' '{printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'
	@echo ""
