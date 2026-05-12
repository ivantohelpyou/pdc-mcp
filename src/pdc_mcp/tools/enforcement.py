"""
PDC Enforcement Cases
Dataset: a4ma-dq6s  (data.wa.gov)

Key fields:
  filer_name, filer_type, case_number
  violation_date, resolution_date, resolution_type
  penalty_amount, description
  url (link to enforcement action document)
"""

import logging
from fastmcp import FastMCP
from pydantic import Field
from pdc_mcp import client as pdc

logger = logging.getLogger(__name__)

DATASET = "a4ma-dq6s"


def register_enforcement_tools(mcp: FastMCP):

    @mcp.tool()
    def search_enforcement_cases(
        filer_name: str = Field(default="", description="Filer, committee, or individual name (partial match)"),
        resolution_type: str = Field(default="", description="Outcome type, e.g. 'Agreed Order', 'Dismissal'"),
        min_penalty: str = Field(default="", description="Minimum penalty amount"),
        limit: int = Field(default=100, description="Max results (up to 1000)"),
        order: str = Field(default="violation_date DESC", description="Sort order"),
    ) -> dict:
        """
        Search PDC enforcement cases and penalties (dataset a4ma-dq6s).

        Useful for checking whether a committee or individual has a PDC violation
        history before relying on their filings, or for enforcement pattern analysis.

        Example patterns:
        - filer_name='[committee name]' → all violation history for this entity
        - min_penalty='10000' → significant enforcement actions
        - resolution_type='Agreed Order' → settled cases with penalties
        """
        clauses = []
        if filer_name:
            clauses.append(pdc.like("filer_name", filer_name))
        if resolution_type:
            clauses.append(pdc.like("resolution_type", resolution_type))
        if min_penalty:
            clauses.append(f"penalty_amount >= '{pdc._sanitize(min_penalty)}'")

        where = pdc.and_clauses(*clauses)
        kwargs = dict(limit=min(limit, 1000), order=order)
        if where:
            kwargs["where"] = where

        results = pdc.query(DATASET, **kwargs)
        return pdc.wrap(DATASET, results, where, limit)
