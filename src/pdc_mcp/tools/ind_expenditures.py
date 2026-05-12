"""
Independent Expenditures & Electioneering Communications
Dataset: 67cp-h962  (data.wa.gov)

C6 filings — itemized IE ad expenses.

Key fields:
  sponsor_name, sponsor_description, sponsor_id
  sponsor_address, sponsor_city, sponsor_state
  election_year
  expenditure_amount
  expenditure_description
  vendor_name, vendor_address, vendor_city
  total_cycle, total_this_report, total_unitemized
  date_expense_obligated, date_advertising_presented
  report_number, report_type
  url (link to filing on apollo.pdc.wa.gov)

Note: candidate target is not a field on C6 line items — it appears only on the
C6 cover form. For PAC spending with candidate names in descriptions, also check
search_expenditures() on the C4 dataset (tijg-9zyp).
"""

import logging
from fastmcp import FastMCP
from pydantic import Field
from pdc_mcp import client as pdc

logger = logging.getLogger(__name__)

DATASET = "67cp-h962"


def register_ie_tools(mcp: FastMCP):

    @mcp.tool()
    def search_independent_expenditures(
        sponsor_name: str = Field(default="", description="IE sponsor/committee name (partial match)"),
        vendor_name: str = Field(default="", description="Ad vendor or contractor name (partial match)"),
        description_contains: str = Field(default="", description="Text in expenditure description (partial match)"),
        election_year: str = Field(default="", description="4-digit election year"),
        min_amount: str = Field(default="", description="Minimum per-line expenditure amount"),
        limit: int = Field(default=200, description="Max results (up to 1000)"),
        offset: int = Field(default=0, description="Pagination offset"),
        order: str = Field(default="date_expense_obligated DESC", description="Sort order, e.g. 'expenditure_amount DESC'"),
    ) -> dict:
        """
        Search PDC C6 independent expenditure filings (dataset 67cp-h962).

        Shows IE ad buys by PACs and individuals — vendor payments for ads,
        mailers, and media that support or oppose candidates.

        Example patterns:
        - sponsor_name='[PAC name]' → all ad buys by this PAC
        - vendor_name='[media firm]' → track which PACs use the same vendors
        - election_year='2024' + min_amount='50000' → major IE buys last cycle
        - description_contains='television' → TV ad expenditures across all sponsors
        """
        clauses = []
        if sponsor_name:
            clauses.append(pdc.like("sponsor_name", sponsor_name))
        if vendor_name:
            clauses.append(pdc.like("vendor_name", vendor_name))
        if description_contains:
            clauses.append(pdc.like("expenditure_description", description_contains))
        if election_year:
            clauses.append(pdc.eq("election_year", election_year))
        if min_amount:
            clauses.append(f"expenditure_amount >= '{pdc._sanitize(min_amount)}'")

        where = pdc.and_clauses(*clauses)
        kwargs = dict(limit=min(limit, 1000), offset=offset, order=order)
        if where:
            kwargs["where"] = where

        results = pdc.query(DATASET, **kwargs)
        return pdc.wrap(DATASET, results, where, limit)
