from __future__ import annotations

import argparse
from pathlib import Path

from ruyi_docx.adapters.mcp import build_mcp_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the path-restricted Ruyi DOCX MCP server")
    parser.add_argument("--root", type=Path, required=True, help="Only files below this directory are accessible")
    args = parser.parse_args()
    build_mcp_server(args.root).run()


if __name__ == "__main__":
    main()
