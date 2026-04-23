"""Setup -- print environment and version info as the first test."""

import os
import subprocess
import sys

import pytest

from conftest import (
    MCP_HTTP_HOST,
    MCP_HTTP_PORT,
    MCP_HTTP_URL,
    MCP_IMAGE,
    MCP_VERBOSE,
    METRICS_BINARY,
)


def _cli_version() -> tuple[str, bool]:
    """Run ``kubectl-metrics version`` and return (output, ok)."""
    try:
        r = subprocess.run(
            [METRICS_BINARY, "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = r.stdout.strip() or r.stderr.strip() or "(no output)"
        lines = raw.splitlines()
        formatted = ("\n" + " " * 22).join(lines)
        return formatted, r.returncode == 0
    except FileNotFoundError:
        return "(kubectl-metrics binary not found)", False
    except Exception as exc:
        return f"(error: {exc})", False


def _section(title: str) -> str:
    return f"\n  --- {title} ---"


@pytest.mark.order(0)
async def test_print_banner(mcp_session):
    """Print versions and configuration. Fails if binary is missing."""
    cli_ver, cli_ok = _cli_version()

    if MCP_IMAGE:
        server_info = f"Container image: {MCP_IMAGE}"
    else:
        server_info = f"Binary: {METRICS_BINARY}"

    banner = "\n".join([
        "",
        "=" * 60,
        "  MCP E2E TEST SUITE (kubectl-metrics)",
        "=" * 60,
        _section("Versions"),
        f"  Python:           {sys.version.split()[0]}",
        f"  pytest:           {pytest.__version__}",
        f"  kubectl-metrics:  {cli_ver}",
        _section("MCP Server Connection"),
        f"  MCP HTTP URL:     {MCP_HTTP_URL}",
        f"  Server info:      {server_info}",
        _section("Diagnostics"),
        f"  MCP_VERBOSE:      {MCP_VERBOSE}",
        "",
        "=" * 60,
        "",
    ])
    print(banner)

    assert cli_ok, f"kubectl-metrics version failed — cannot continue.\n  {cli_ver}"
