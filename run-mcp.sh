#!/bin/bash
# PDC MCP Server — stdio transport for Claude Desktop / Claude Code
# Add to ~/.claude/mcp.json or Claude Desktop config

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

exec uv run python -m pdc_mcp.server 2>> /tmp/pdc-mcp.log
