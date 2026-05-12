"""
Campaign Finance Summary
Dataset: 3h9x-7bvm  (data.wa.gov)

Key fields:
  filer_name, filer_id, committee_id, election_year, party
  total_contributions, total_expenditures, total_debt
  cash_on_hand, reporting_period

Faster than building totals from individual transaction records.
"""

import logging
from fastmcp import FastMCP
from pydantic import Field
from pdc_mcp import client as pdc

logger = logging.getLogger(__name__)

DATASET = "3h9x-7bvm"


def register_summary_tools(mcp: FastMCP):

    @mcp.tool()
    def get_campaign_summary(
        filer_name: str = Field(default="", description="Committee or candidate name (partial match)"),
        election_year: str = Field(default="", description="4-digit election year"),
        party: str = Field(default="", description="Political party filter"),
        limit: int = Field(default=100, description="Max results (up to 1000)"),
        order: str = Field(default="election_year DESC", description="Sort order, e.g. 'total_contributions DESC'"),
    ) -> dict:
        """
        Get campaign finance summary rollups by committee (dataset 3h9x-7bvm).

        Returns total contributions, expenditures, and cash on hand per committee.
        Use for quick cycle-level comparisons without building from transactions.

        Example patterns:
        - filer_name='[PAC name]' → that PAC's fundraising across all election cycles
        - election_year='2024' + order='total_contributions DESC' → biggest spenders
        - filer_name='[candidate]' → career fundraising trajectory
        """
        clauses = []
        if filer_name:
            clauses.append(pdc.like("filer_name", filer_name))
        if election_year:
            clauses.append(pdc.eq("election_year", election_year))
        if party:
            clauses.append(pdc.eq("party", party))

        where = pdc.and_clauses(*clauses)
        kwargs = dict(limit=min(limit, 1000), order=order)
        if where:
            kwargs["where"] = where

        results = pdc.query(DATASET, **kwargs)
        return pdc.wrap(DATASET, results, where, limit)
