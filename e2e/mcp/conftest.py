"""
Root conftest -- shared fixtures, helpers, and constants for MCP E2E tests.

Tests assume a running MCP server is available at MCP_HTTP_URL.

Server lifecycle management (start/stop) is handled separately via make
targets, allowing flexible deployment:
  - Binary mode: Local kubectl-metrics process
  - Container mode: Docker/podman container
  - Remote mode: External service
"""

import asyncio as _asyncio
import contextlib
import json
import os
import socket
import urllib.parse

import httpx
import pytest
import pytest_asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

# ---------------------------------------------------------------------------
# Environment -- load .env file if present
# ---------------------------------------------------------------------------
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)

# ---------------------------------------------------------------------------
# MCP server settings -- tests connect to a running server
# ---------------------------------------------------------------------------
MCP_HTTP_HOST: str = os.environ.get("MCP_HTTP_HOST", "127.0.0.1")
MCP_HTTP_PORT: str = os.environ.get("MCP_HTTP_PORT", "19091")
MCP_HTTP_URL: str = os.environ.get(
    "MCP_HTTP_URL",
    f"http://{MCP_HTTP_HOST}:{MCP_HTTP_PORT}/mcp",
)

METRICS_BINARY: str = os.environ.get(
    "METRICS_BINARY",
    os.path.join(os.path.dirname(__file__), "..", "..", "kubectl-metrics"),
)
MCP_IMAGE: str = os.environ.get("MCP_IMAGE", "")

MCP_VERBOSE: int = int(os.environ.get("MCP_VERBOSE", "1"))

# Optional cluster credentials (only needed for cluster-connected queries)
KUBE_TOKEN: str = os.environ.get("KUBE_TOKEN", "")


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------
class MCPToolError(Exception):
    """Raised when an MCP tool call returns an error."""

    def __init__(self, tool: str, message: str):
        self.tool = tool
        super().__init__(f"MCP tool '{tool}' error: {message}")


# ---------------------------------------------------------------------------
# Helper: call an MCP tool and return parsed result
# ---------------------------------------------------------------------------
async def call_tool(
    session: ClientSession,
    tool_name: str,
    arguments: dict,
    *,
    verbose: int | None = None,
) -> dict:
    """Call an MCP tool via the session and return the parsed response."""
    level = verbose if verbose is not None else MCP_VERBOSE

    if level >= 2:
        print(f"\n    [call] {tool_name} {json.dumps(arguments, indent=2)}")
    elif level >= 1:
        cmd = arguments.get("command", arguments.get("action", ""))
        flags_summary = arguments.get("flags", {})
        print(f"\n    [call] {tool_name} {cmd}  {flags_summary}")

    result = await session.call_tool(tool_name, arguments)

    if result.isError:
        parts = []
        for content in result.content:
            if hasattr(content, "text"):
                parts.append(content.text)
        error_msg = "\n".join(parts)
        if level >= 1:
            print(f"    [error] {tool_name}: {error_msg[:800]}")
        raise MCPToolError(tool_name, error_msg)

    if result.structuredContent is not None:
        parsed = result.structuredContent
    else:
        parsed = {}
        for content in result.content:
            if hasattr(content, "text"):
                try:
                    parsed = json.loads(content.text)
                except json.JSONDecodeError:
                    parsed = {"output": content.text}
                break

    if level >= 2:
        preview = json.dumps(parsed, indent=2)[:800] if isinstance(parsed, dict) else str(parsed)[:800]
        print(f"    [result] {preview}")
    elif level >= 1:
        if isinstance(parsed, dict):
            out_len = len(parsed.get("output", ""))
            print(f"    [result] output_len={out_len}")
        else:
            print(f"    [result] {str(parsed)[:200]}")

    return parsed


# ---------------------------------------------------------------------------
# Helper: verify MCP server is reachable
# ---------------------------------------------------------------------------
def _verify_server_reachable() -> None:
    parsed = urllib.parse.urlparse(MCP_HTTP_URL)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        if s.connect_ex((host, port)) != 0:
            raise RuntimeError(
                f"MCP server is not reachable at {MCP_HTTP_URL}\n"
                f"Please start the server first:\n"
                f"  make server-start          # Start binary mode server\n"
                f"  make server-start-image    # Start container mode server\n"
                f"Or use an existing server by setting MCP_HTTP_URL"
            )


# ---------------------------------------------------------------------------
# Fixture: verify server is running (session-scoped, runs once)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def mcp_server_process():
    """Verify MCP server is reachable before tests start."""
    _verify_server_reachable()
    print(f"\n[Connected] MCP server at {MCP_HTTP_URL}")
    yield None


# ---------------------------------------------------------------------------
# Helper: suppress harmless teardown race in streamable_http_client
# ---------------------------------------------------------------------------
@contextlib.asynccontextmanager
async def _safe_streamable_client(*args, **kwargs):
    """Wrap ``streamable_http_client`` and suppress anyio cancel-scope error.

    During pytest-asyncio session-scoped fixture teardown the event loop
    may finalize the context manager in a different task than the one that
    created it, causing::

        RuntimeError: Attempted to exit cancel scope in a different task …

    This wrapper catches that specific error so the test run exits cleanly.
    """
    try:
        async with streamable_http_client(*args, **kwargs) as streams:
            yield streams
    except RuntimeError as exc:
        if "Attempted to exit cancel scope in a different task" in str(exc):
            pass
        else:
            raise


# ---------------------------------------------------------------------------
# Helper: create an MCP session with custom headers
# ---------------------------------------------------------------------------
@contextlib.asynccontextmanager
async def _make_mcp_session(headers=None):
    """Create an MCP session via Streamable HTTP with arbitrary headers."""
    async with httpx.AsyncClient(
        headers=headers or {},
        timeout=httpx.Timeout(30, read=120),
    ) as http_client:
        async with _safe_streamable_client(
            url=MCP_HTTP_URL,
            http_client=http_client,
        ) as (read_stream, write_stream, _get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def mcp_session(mcp_server_process):
    """Connect to the running MCP HTTP server and yield a ClientSession.

    If KUBE_TOKEN is set, it is sent as a Bearer token on every request.
    """
    headers = {}
    if KUBE_TOKEN:
        headers["Authorization"] = f"Bearer {KUBE_TOKEN}"

    async with _make_mcp_session(headers=headers) as session:
        yield session
