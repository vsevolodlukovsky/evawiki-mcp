"""Entry point for evawiki-mcp CLI."""

from __future__ import annotations

import argparse
import os
import sys

from .server import mcp

TRANSPORTS = ("stdio", "http")


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_transport(default: str = "stdio") -> str:
    raw = os.environ.get("MCP_TRANSPORT", default)
    value = raw.strip().lower()
    if value not in TRANSPORTS:
        raise SystemExit(
            f"Invalid MCP_TRANSPORT={raw!r}: expected one of {', '.join(TRANSPORTS)}"
        )
    return value


def _env_port(default: int = 8000) -> int:
    raw = os.environ.get("MCP_PORT")
    if raw is None or raw == "":
        return default
    try:
        port = int(raw)
    except ValueError:
        raise SystemExit(f"Invalid MCP_PORT={raw!r}: must be an integer") from None
    if not 1 <= port <= 65535:
        raise SystemExit(f"Invalid MCP_PORT={port}: must be in 1..65535")
    return port


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="evawiki-mcp",
        description="MCP server for EVA Wiki / EVA Team",
    )
    parser.add_argument(
        "--transport",
        choices=list(TRANSPORTS),
        default=_env_transport(),
        help="Transport mode (default: stdio, env MCP_TRANSPORT)",
    )
    parser.add_argument(
        "--host",
        default=_env("MCP_HOST", "127.0.0.1"),
        help="HTTP listen host (default: 127.0.0.1, env MCP_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_env_port(),
        help="HTTP listen port (default: 8000, env MCP_PORT)",
    )
    parser.add_argument(
        "--path",
        default=_env("MCP_PATH", "/mcp"),
        help="HTTP endpoint path (default: /mcp, env MCP_PATH)",
    )
    args = parser.parse_args()

    if args.transport == "http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.settings.streamable_http_path = args.path
        mcp.run(transport="streamable-http")
    else:
        mcp.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
