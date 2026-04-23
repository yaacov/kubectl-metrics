"""Test the metrics_help MCP tool."""

import pytest

from conftest import call_tool


@pytest.mark.order(10)
async def test_help_overview(mcp_session):
    """metrics_help with no command returns an overview."""
    result = await call_tool(mcp_session, "metrics_help", {"command": ""})
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert len(output) > 0, "Help overview is empty"
    print(f"\n  Overview length: {len(output)} chars")


@pytest.mark.order(11)
async def test_help_query(mcp_session):
    """metrics_help for 'query' subcommand returns relevant help."""
    result = await call_tool(mcp_session, "metrics_help", {"command": "query"})
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert "query" in output.lower(), f"Help for 'query' does not mention query: {output[:200]}"


@pytest.mark.order(12)
async def test_help_query_range(mcp_session):
    """metrics_help for 'query_range' subcommand."""
    result = await call_tool(mcp_session, "metrics_help", {"command": "query_range"})
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert len(output) > 0, "Help for query_range is empty"


@pytest.mark.order(13)
async def test_help_discover(mcp_session):
    """metrics_help for 'discover' subcommand."""
    result = await call_tool(mcp_session, "metrics_help", {"command": "discover"})
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert len(output) > 0, "Help for discover is empty"


@pytest.mark.order(14)
async def test_help_preset(mcp_session):
    """metrics_help for 'preset' subcommand."""
    result = await call_tool(mcp_session, "metrics_help", {"command": "preset"})
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert len(output) > 0, "Help for preset is empty"


@pytest.mark.order(15)
async def test_help_promql(mcp_session):
    """metrics_help for 'promql' reference."""
    result = await call_tool(mcp_session, "metrics_help", {"command": "promql"})
    output = result.get("output", "") if isinstance(result, dict) else str(result)
    assert "promql" in output.lower(), (
        f"Help for 'promql' does not mention PromQL: {output[:200]}"
    )
