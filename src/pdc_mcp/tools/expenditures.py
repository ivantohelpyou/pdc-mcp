"""
Expenditures by Candidates & Committees
Dataset: tijg-9zyp  (data.wa.gov)

Key fields:
  filer_name, filer_id, committee_id, election_year, party
  recipient_name, description, code
  amount, itemized_or_non_itemized, expenditure_date
  for_or_against, jurisdiction, jurisdiction_county, jurisdiction_type
  url (link to apollo.pdc.wa.gov filing PDF)

The description field reveals what money was actually spent on —
useful for tracing PAC spending to specific vendors, venues, or activities.
"""

import logging
from fastmcp import FastMCP
from pydantic import Field
from pdc_mcp import client as pdc

logger = logging.getLogger(__name__)

DATASET = "tijg-9zyp"


def register_expenditure_tools(mcp: FastMCP):

    @mcp.tool()
    def search_expenditures(
        filer_name: str = Field(default="", description="Committee or candidate name (partial match)"),
        recipient_name: str = Field(default="", description="Vendor or recipient name (partial match)"),
        description_contains: str = Field(default="", description="Text in expenditure description (partial match)"),
        election_year: str = Field(default="", description="4-digit election year"),
        for_or_against: str = Field(default="", description="'For' or 'Against' (relevant for ballot measures)"),
        jurisdiction: str = Field(default="", description="Jurisdiction name filter"),
        min_amount: str = Field(default="", description="Minimum expenditure amount"),
        max_amount: str = Field(default="", description="Maximum expenditure amount"),
        limit: int = Field(default=100, description="Max results (up to 1000)"),
        offset: int = Field(default=0, description="Pagination offset"),
        order: str = Field(default="expenditure_date DESC", description="Sort order, e.g. 'amount DESC'"),
    ) -> dict:
        """
        Search PDC expenditures by candidates and committees (dataset tijg-9zyp).

        The description field reveals what money was actually spent on —
        trace how PAC money flows to specific activities, vendors, and events.

        Example patterns:
        - filer_name='Seattle Chamber' → all Chamber PAC spending
        - description_contains='polling' → find polling expenditures across all committees
        - filer_name='[PAC name]' + election_year='2024' → single cycle breakdown
        - recipient_name='[consulting firm]' → track which campaigns use the same vendors
        """
        clauses = []
        if filer_name:
            clauses.append(pdc.like("filer_name", filer_name))
        if recipient_name:
            clauses.append(pdc.like("recipient_name", recipient_name))
        if description_contains:
            clauses.append(pdc.like("description", description_contains))
        if election_year:
            clauses.append(pdc.eq("election_year", election_year))
        if for_or_against:
            clauses.append(pdc.eq("for_or_against", for_or_against))
        if jurisdiction:
            clauses.append(pdc.like("jurisdiction", jurisdiction))
        if min_amount:
            clauses.append(f"amount >= '{pdc._sanitize(min_amount)}'")
        if max_amount:
            clauses.append(f"amount <= '{pdc._sanitize(max_amount)}'")

        where = pdc.and_clauses(*clauses)
        kwargs = dict(limit=min(limit, 1000), offset=offset, order=order)
        if where:
            kwargs["where"] = where

        results = pdc.query(DATASET, **kwargs)
        return pdc.wrap(DATASET, results, where, limit)
