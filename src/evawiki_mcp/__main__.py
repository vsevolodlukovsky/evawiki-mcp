"""Entry point for evawiki-mcp CLI."""

from __future__ import annotations

import argparse
import sys

from .server import mcp


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="evawiki-mcp",
        description="MCP server for EVA Wiki / EVA Team (stdio)",
    )
    parser.parse_args()
    mcp.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
