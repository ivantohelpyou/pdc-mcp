"""
Contributions to Candidates & Committees
Dataset: kv7h-kjye  (data.wa.gov)

Key fields:
  filer_name, filer_id, committee_id, election_year
  contributor_name, contributor_employer_name, contributor_occupation
  contributor_category, contributor_address, contributor_city, contributor_state
  amount, cash_or_in_kind, receipt_date, primary_general
  url (link to PDC filing)
"""

import logging
from fastmcp import FastMCP
from pydantic import Field
from pdc_mcp import client as pdc

logger = logging.getLogger(__name__)

DATASET = "kv7h-kjye"


def register_contribution_tools(mcp: FastMCP):

    @mcp.tool()
    def search_contributions(
        filer_name: str = Field(default="", description="Candidate or committee name (partial match)"),
        contributor_name: str = Field(default="", description="Donor name (partial match, use 'Last, First' format)"),
        contributor_employer: str = Field(default="", description="Donor employer name (partial match)"),
        election_year: str = Field(default="", description="4-digit election year, e.g. '2024'"),
        min_amount: str = Field(default="", description="Minimum contribution amount, e.g. '1000'"),
        max_amount: str = Field(default="", description="Maximum contribution amount"),
        cash_or_in_kind: str = Field(default="", description="'Cash' or 'In-Kind'"),
        limit: int = Field(default=100, description="Max results (up to 1000)"),
        offset: int = Field(default=0, description="Pagination offset"),
        order: str = Field(default="receipt_date DESC", description="Sort order, e.g. 'amount DESC'"),
    ) -> dict:
        """
        Search PDC campaign contributions (dataset kv7h-kjye).

        Returns contributions matching the filters. Combine fields to narrow results.
        All string filters use case-insensitive partial match except election_year (exact)
        and amount (range).

        Example patterns:
        - contributor_employer='Washington Hospitality' → all donors from that industry
        - filer_name='Seattle City Council' + election_year='2023'
        - contributor_name='Smith' + min_amount='5000'
        - contributor_employer='Port of Seattle' → track institutional donor networks
        """
        clauses = []
        if filer_name:
            clauses.append(pdc.like("filer_name", filer_name))
        if contributor_name:
            clauses.append(pdc.like("contributor_name", contributor_name))
        if contributor_employer:
            clauses.append(pdc.like("contributor_employer_name", contributor_employer))
        if election_year:
            clauses.append(pdc.eq("election_year", election_year))
        if cash_or_in_kind:
            clauses.append(pdc.eq("cash_or_in_kind", cash_or_in_kind))
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

    @mcp.tool()
    def find_donors_by_employer(
        employer_terms: list[str] = Field(
            description="List of employer name fragments. Each term is OR'd. "
                        "E.g. ['Port of Seattle', 'Sound Transit'] finds donors "
                        "from multiple institutions in one sweep."
        ),
        election_year: str = Field(default="", description="Filter to a single election year"),
        limit: int = Field(default=500, description="Max results per employer term (up to 1000)"),
    ) -> dict:
        """
        Sweep all donors from a set of employers — the network mapping tool.

        Runs one query per employer term, merges and deduplicates results.
        Use this to map the full donor network connected to a set of institutions
        without knowing individual names in advance.

        Example: employer_terms=['Sound Transit', 'Port of Seattle']
        returns every individual who listed either institution as their employer
        when making a political contribution.
        """
        all_results = {}
        for term in employer_terms:
            clauses = [pdc.like("contributor_employer_name", term)]
            if election_year:
                clauses.append(pdc.eq("election_year", election_year))
            where = pdc.and_clauses(*clauses)
            rows = pdc.query(DATASET, where=where, limit=min(limit, 1000),
                             order="receipt_date DESC")
            for row in rows:
                key = row.get("id", row.get("report_number", str(row)))
                all_results[key] = row

        results = list(all_results.values())
        results.sort(key=lambda r: r.get("receipt_date", ""), reverse=True)
        return {
            "dataset": DATASET,
            "employer_terms": employer_terms,
            "count": len(results),
            "results": results,
        }
