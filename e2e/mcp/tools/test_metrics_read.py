"""Test the metrics_read MCP tool.

These tests exercise the tool's command dispatch and error handling.
Tests that require a live Prometheus endpoint (query, discover, preset, etc.)
are skipped when no cluster credentials are configured.
"""

import os

import pytest

from conftest import call_tool, MCPToolError

# Skip cluster-dependent tests when no Prometheus is available.
# The MCP server needs a reachable Prometheus to run actual queries.
_has_cluster = bool(os.environ.get("KUBE_TOKEN") or os.environ.get("MCP_METRICS_URL"))
requires_cluster = pytest.mark.skipif(
    not _has_cluster,
    reason="No KUBE_TOKEN or MCP_METRICS_URL set — skipping cluster-dependent test",
)


@pytest.mark.order(20)
async def test_read_missing_command(mcp_session):
    """metrics_read with empty command returns a helpful error."""
    result = await call_tool(mcp_session, "metrics_read", {
        "command": "",
        "flags": {},
    })
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert "command" in output.lower(), f"Expected guidance about missing command: {output[:300]}"


@pytest.mark.order(21)
async def test_read_unknown_command(mcp_session):
    """metrics_read with unknown command returns an error."""
    result = await call_tool(mcp_session, "metrics_read", {
        "command": "nonexistent_xyz",
        "flags": {},
    })
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert "unknown" in output.lower() or "nonexistent" in output.lower(), (
        f"Expected error about unknown command: {output[:300]}"
    )


@requires_cluster
@pytest.mark.order(30)
async def test_read_query_up(mcp_session):
    """metrics_read query 'up' returns results."""
    result = await call_tool(mcp_session, "metrics_read", {
        "command": "query",
        "flags": {"query": "up"},
    })
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert len(output) > 0, "Query 'up' returned empty output"
    print(f"\n  Query 'up' returned {len(output)} chars")


@requires_cluster
@pytest.mark.order(31)
async def test_read_discover(mcp_session):
    """metrics_read discover returns metric names."""
    result = await call_tool(mcp_session, "metrics_read", {
        "command": "discover",
        "flags": {},
    })
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert len(output) > 0, "Discover returned empty output"
    assert "up" in output.lower() or "container" in output.lower(), (
        f"Expected common metrics in discover output: {output[:300]}"
    )


@requires_cluster
@pytest.mark.order(32)
async def test_read_discover_keyword(mcp_session):
    """metrics_read discover with keyword filter."""
    result = await call_tool(mcp_session, "metrics_read", {
        "command": "discover",
        "flags": {"keyword": "container_cpu"},
    })
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert "container_cpu" in output.lower(), (
        f"Keyword filter 'container_cpu' not in output: {output[:300]}"
    )


@requires_cluster
@pytest.mark.order(33)
async def test_read_labels(mcp_session):
    """metrics_read labels for 'up' metric."""
    result = await call_tool(mcp_session, "metrics_read", {
        "command": "labels",
        "flags": {"metric": "up"},
    })
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert "job" in output.lower(), (
        f"Expected 'job' label in labels for 'up': {output[:300]}"
    )


@requires_cluster
@pytest.mark.order(34)
async def test_read_preset(mcp_session):
    """metrics_read preset cluster_cpu_utilization."""
    result = await call_tool(mcp_session, "metrics_read", {
        "command": "preset",
        "flags": {"name": "cluster_cpu_utilization"},
    })
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert len(output) > 0, "Preset cluster_cpu_utilization returned empty output"
