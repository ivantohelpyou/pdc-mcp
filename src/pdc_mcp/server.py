"""
PDC MCP Server

MCP server for Washington State Public Disclosure Commission data.
Covers campaign contributions, expenditures, independent expenditures,
lobbyist activity, enforcement cases, and campaign finance summaries —
all via the Socrata SODA API at data.wa.gov.

Requires: PDC_APP_TOKEN env var (get a free token at data.wa.gov/profile/app_tokens)
See .env.example for setup instructions.
"""

import logging
import os

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

logger = logging.getLogger("pdc-mcp")
logger.setLevel(logging.DEBUG if os.environ.get("PDC_DEBUG") else logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)


mcp = FastMCP(
    "pdc",
    instructions=(
        "Query Washington State PDC campaign finance data. "
        "Covers contributions, expenditures, independent expenditures, "
        "lobbyist compensation, enforcement cases, and campaign finance summaries. "
        "All data from data.wa.gov via Socrata SODA API."
    )
)

from pdc_mcp.tools import register_all_tools
register_all_tools(mcp)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="PDC MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "http"],
                        default="stdio")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    logger.info("Starting PDC MCP server (transport: %s)", args.transport)

    if args.transport in ("sse", "http"):
        import uvicorn
        app = mcp.http_app(transport=args.transport)
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
