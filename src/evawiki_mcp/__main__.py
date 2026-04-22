"""Entry point for evawiki-mcp CLI."""

from __future__ import annotations

import argparse
import os
import sys

from .server import mcp


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="evawiki-mcp",
        description="MCP server for EVA Wiki / EVA Team",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=_env("MCP_TRANSPORT", "stdio"),
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
        default=int(_env("MCP_PORT", "8000")),
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
