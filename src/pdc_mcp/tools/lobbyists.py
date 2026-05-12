"""
Lobbyist Compensation & Reporting History
Datasets:
  9nnw-c693  Lobbyist Compensation & Expenses by Source
  nuwx-ay5h  Lobbyist Reporting History (L1/L2/L3 filings)

Compensation (9nnw-c693) key fields:
  filer_name, firm_name, employer_name, client_name
  year, compensation, expenses, total
  subject_matter, legislative_session

Reporting History (nuwx-ay5h) key fields:
  filer_name, filer_type, firm_id, entity_id
  year, receipt_date, filing_method
  report_from, report_through, url
"""

import logging
from fastmcp import FastMCP
from pydantic import Field
from pdc_mcp import client as pdc

logger = logging.getLogger(__name__)

COMPENSATION_DATASET = "9nnw-c693"
FILINGS_DATASET = "nuwx-ay5h"


def register_lobbyist_tools(mcp: FastMCP):

    @mcp.tool()
    def search_lobbyist_compensation(
        employer_name: str = Field(default="", description="Organization paying for lobbying (partial match)"),
        firm_name: str = Field(default="", description="Lobbying firm doing the work (partial match)"),
        filer_name: str = Field(default="", description="Individual lobbyist name (partial match)"),
        subject_matter: str = Field(default="", description="Subject lobbied on (partial match). Try 'Lodging', 'Housing', 'Transit', 'RCW'"),
        year: str = Field(default="", description="4-digit reporting year"),
        min_compensation: str = Field(default="", description="Minimum compensation amount"),
        limit: int = Field(default=200, description="Max results (up to 1000)"),
        offset: int = Field(default=0, description="Pagination offset"),
        order: str = Field(default="year DESC", description="Sort order"),
    ) -> dict:
        """
        Search PDC lobbyist compensation records (dataset 9nnw-c693).

        Shows who paid whom to lobby, how much, and on what subjects.

        Example patterns:
        - employer_name='Port of Seattle' → all their lobbying spend + subjects
        - subject_matter='Housing' + year='2024' → who lobbied on housing last year
        - firm_name='[firm]' → all clients sharing a lobbying firm (conflict mapping)
        - employer_name='[agency]' → verify whether a public agency is lobbying
        """
        clauses = []
        if employer_name:
            clauses.append(pdc.like("employer_name", employer_name))
        if firm_name:
            clauses.append(pdc.like("firm_name", firm_name))
        if filer_name:
            clauses.append(pdc.like("filer_name", filer_name))
        if subject_matter:
            clauses.append(pdc.like("subject_matter", subject_matter))
        if year:
            clauses.append(pdc.eq("year", year))
        if min_compensation:
            clauses.append(f"compensation >= '{pdc._sanitize(min_compensation)}'")

        where = pdc.and_clauses(*clauses)
        kwargs = dict(limit=min(limit, 1000), offset=offset, order=order)
        if where:
            kwargs["where"] = where

        results = pdc.query(COMPENSATION_DATASET, **kwargs)
        return pdc.wrap(COMPENSATION_DATASET, results, where, limit)

    @mcp.tool()
    def search_lobbyist_filings(
        filer_name: str = Field(default="", description="Lobbyist or firm name (partial match)"),
        year: str = Field(default="", description="4-digit reporting year"),
        filer_type: str = Field(default="", description="Filer type filter"),
        limit: int = Field(default=200, description="Max results (up to 1000)"),
        offset: int = Field(default=0, description="Pagination offset"),
        order: str = Field(default="receipt_date DESC", description="Sort order"),
    ) -> dict:
        """
        Search PDC lobbyist L1/L2/L3 reporting history (dataset nuwx-ay5h).

        L1/L2/L3 filings connect lobbying money to specific legislators and bills.
        The url field links directly to the filing PDF on apollo.pdc.wa.gov.

        Example patterns:
        - filer_name='[lobbyist]' → their full legislative contact history
        - year='2023' + filer_name='[firm]' → all filings during a specific session
        """
        clauses = []
        if filer_name:
            clauses.append(pdc.like("filer_name", filer_name))
        if year:
            clauses.append(pdc.eq("year", year))
        if filer_type:
            clauses.append(pdc.like("filer_type", filer_type))

        where = pdc.and_clauses(*clauses)
        kwargs = dict(limit=min(limit, 1000), offset=offset, order=order)
        if where:
            kwargs["where"] = where

        results = pdc.query(FILINGS_DATASET, **kwargs)
        return pdc.wrap(FILINGS_DATASET, results, where, limit)
