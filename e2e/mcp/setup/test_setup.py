"""Setup -- verify MCP server is up and responding."""

import pytest

from conftest import (
    MCP_HTTP_PORT,
    MCP_HTTP_URL,
    call_tool,
)


@pytest.mark.order(1)
async def test_mcp_server_running(mcp_session):
    """Verify the MCP HTTP server is up and the client session is connected."""
    result = await call_tool(mcp_session, "metrics_help", {"command": "query"})
    assert result, "MCP server returned empty response to metrics_help"

    print(f"\n  MCP HTTP server responding on port {MCP_HTTP_PORT}")
    print(f"  Client connected to {MCP_HTTP_URL}")


@pytest.mark.order(2)
async def test_list_tools(mcp_session):
    """Verify the server exposes the expected tools."""
    tools_result = await mcp_session.list_tools()
    tool_names = {t.name for t in tools_result.tools}

    assert "metrics_read" in tool_names, f"metrics_read not found in {tool_names}"
    assert "metrics_help" in tool_names, f"metrics_help not found in {tool_names}"

    print(f"\n  Available tools: {sorted(tool_names)}")
