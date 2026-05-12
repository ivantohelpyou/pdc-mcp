"""
PDC MCP Tools — modular tool registration.

Datasets covered (all via data.wa.gov Socrata SODA API):
- contributions.py    kv7h-kjye  Contributions to Candidates & Committees
- expenditures.py     tijg-9zyp  Expenditures by Candidates & Committees
- ind_expenditures.py 67cp-h962  Independent Expenditures & Electioneering
- lobbyists.py        9nnw-c693  Lobbyist Compensation | nuwx-ay5h Reporting History
- enforcement.py      a4ma-dq6s  PDC Enforcement Cases
- summaries.py        3h9x-7bvm  Campaign Finance Summary

To add new datasets: create tools/newdataset.py, add register fn, import here.
"""

from fastmcp import FastMCP
from .contributions import register_contribution_tools
from .expenditures import register_expenditure_tools
from .ind_expenditures import register_ie_tools
from .lobbyists import register_lobbyist_tools
from .enforcement import register_enforcement_tools
from .summaries import register_summary_tools


def register_all_tools(mcp: FastMCP):
    register_contribution_tools(mcp)
    register_expenditure_tools(mcp)
    register_ie_tools(mcp)
    register_lobbyist_tools(mcp)
    register_enforcement_tools(mcp)
    register_summary_tools(mcp)


__all__ = ["register_all_tools"]
