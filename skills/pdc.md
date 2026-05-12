# PDC Campaign Finance Research

Query Washington State Public Disclosure Commission data at data.wa.gov via the Socrata SODA API.

## When to use this skill
Invoke when the user asks about campaign contributions, lobbying activity, independent expenditures, or enforcement cases involving Washington State candidates, PACs, or lobbyists.

## Auth
Check `$PDC_APP_TOKEN` or `$PDC_KEY_ID`/`$PDC_KEY_SECRET` in the environment. If unset, queries still work but hit the shared unauthenticated rate limit (throttled). Recommend users get a free app token at data.wa.gov.

## API pattern
```
GET https://data.wa.gov/resource/{dataset_id}.json?$where=...&$limit=...&$order=...
```
- All string matches: `upper(field) LIKE '%VALUE%'` (case-insensitive)
- Equality: `field='value'`
- Numeric range: `amount >= '1000'`
- Combine with ` AND `
- Always include `$limit` (default Socrata cap is 1000 rows)
- Add `X-App-Token: $PDC_APP_TOKEN` header when token is available

## Datasets

### Contributions to candidates & committees
**Dataset:** `kv7h-kjye`
Key fields: `filer_name`, `contributor_name`, `contributor_employer_name`, `contributor_occupation`, `amount`, `receipt_date`, `election_year`, `cash_or_in_kind`, `url`

Common queries:
- Donor employer sweep: `upper(contributor_employer_name) LIKE '%WASHINGTON HOSPITALITY%'`
- All donations to a candidate: `upper(filer_name) LIKE '%NELSON%'`
- Single donor across all candidates: `upper(contributor_name) LIKE '%FINNERAN%'`
- By election year: `election_year='2024'`
- Large donations: `amount >= '10000'`

### Campaign expenditures
**Dataset:** `tijg-9ris`
Key fields: `filer_name`, `recipient_name`, `amount`, `expenditure_date`, `code`, `description`

### Independent expenditures (PAC spending)
**Dataset:** `bought-in` → `i86e-fatj`
Key fields: `filer_name`, `candidate_name`, `support_or_oppose`, `amount`, `expenditure_date`, `election_year`

Common: find all PAC spending for/against a candidate, total PAC spend by election cycle.

### Lobbyist compensation
**Dataset:** `9nnw-c693`
Key fields: `filer_name`, `firm_name`, `employer_name`, `subject_matter`, `year`, `compensation`, `expenses`, `total`

Common queries:
- Who's lobbying on lodging/convention issues: `upper(subject_matter) LIKE '%LODGING%'`
- All lobbying by an employer: `upper(employer_name) LIKE '%ENTERPRISE WASHINGTON%'`
- Shared lobbying firms: find clients of a firm to map conflicts

### Lobbyist filing history (L1/L2/L3)
**Dataset:** `nuwx-ay5h`
Key fields: `filer_name`, `filer_type`, `year`, `receipt_date`, `url`
The `url` field links directly to the filing PDF — which legislators were contacted and on which bills.

### Campaign finance summaries
**Dataset:** `jxzt-ab8h`
Key fields: `filer_name`, `election_year`, `total_contributions`, `total_expenditures`, `cash_on_hand`, `outstanding_loans`
Use for: total fundraising by candidate/PAC across a cycle.

### Enforcement cases
**Dataset:** `gqt6-byb3`
Key fields: `filer_name`, `case_number`, `violation_description`, `penalty`, `case_status`, `case_date`

## Board/commission governance fingerprint

For questions like "show me the PDC footprint of the [agency] board":

1. **Fetch the roster** — use WebFetch on the agency's governance/board page. If no URL provided, try `[agency name] board members` + common patterns:
   - `[agency].gov/governance` or `[agency].org/board`
   - WA State Auditor portal (sao.wa.gov) lists governing boards for public agencies
   - Search for the agency's official site first; don't guess URLs

2. **Extract affiliations** — for each member, get their listed employer or institutional affiliation. Board rosters typically list title + employer. If not listed, check the appointing authority's press release or appointment packet (often findable via `site:[city/county].gov "[member name]" appointed`).

3. **Run PDC queries per institution** — for each member's employer, check all three angles:
   - As **contributor**: `search_contributions(contributor_employer=institution)`
   - As **lobbying employer**: `search_lobbyist_compensation(employer_name=institution)`
   - As **PAC funder**: `search_contributions(contributor_name=institution)` (catches when the org itself donates as an entity)

4. **Present as a table**: Member → Affiliation → PDC footprint (total contributions, lobbying spend, PAC activity). Note which members' institutions have NO PDC footprint — absence is also signal.

5. **Go one level deeper if warranted**: use `find_donors_by_employer` to sweep all individual donors from that institution across all candidates, not just the ones who disclosed their employer in a specific race.

This recipe is wide, not deep — one pass per board member rather than chaining into the same record. For a 9-member board expect 9–27 queries. Claude handles the fan-out automatically.

---

## Critical: Misattribution and Spelling Traps

**Never assume A→C because A→B and B→C without a direct query confirming it.**

Enterprise Washington operates *multiple* named committees simultaneously — "Citizens for Progress," "Citizens for Working Courts Enterprise Washington," "South Sound Future," "Our Olympic Communities," and others. A donor to one EW vehicle is NOT automatically a donor to all of them. Always verify the specific filer name before asserting a chain. Example of how this goes wrong: Vulcan Inc., Bill Gates, and the Ballmers gave $525K to "Citizens for Working Courts Enterprise Washington" in 2016 — a different committee than "Citizens for Progress," which ran the Larry Springer ads. Attributing their money to Citizens for Progress would be false.

**When a query returns fewer results than expected, search for spelling variations.**

PDC data is entered by filers and contains real transcription errors. A contribution may exist under a misspelled name and be invisible to a correctly-spelled query. Always run a broad LIKE search and scan for variants. Real example: "PHILLLIPS 66" (triple L) filed a $100K contribution to Citizens for Progress that a query for "PHILLIPS 66" would miss entirely. If you find a suspiciously round total, try: `upper(contributor_name) LIKE "%PHIL%"` and compare. Report what you found AND what spelling variants turned up.

**Before publishing any dollar figure, state the query that produced it.** If the total changes when you broaden the search, note both numbers and explain why they differ.

## Example curl
```bash
curl -s -G "https://data.wa.gov/resource/kv7h-kjye.json" \
  --data-urlencode '$where=upper(contributor_employer_name) LIKE "%WASHINGTON HOSPITALITY%" AND election_year='"'"'2024'"'" \
  --data-urlencode '$limit=200' \
  --data-urlencode '$order=amount DESC' \
  -H "X-App-Token: ${PDC_APP_TOKEN:-}" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} results'); [print(f\"{r.get('receipt_date','')[:10]} \${float(r.get('amount',0)):,.0f} {r.get('contributor_name','')} → {r.get('filer_name','')}\") for r in d[:20]]"
```

## Notes

**Lobbying subjects — three-hop query:**
Subject matter isn't a top-level field on the compensation dataset. It's embedded as JSON inside the `report_data` field of L2 filings (dataset nuwx-ay5h). To get it:
1. Get lobbyist firm names from `9nnw-c693` (filter by `employer_name`)
2. Get L2 filings from `nuwx-ay5h` (filter by `filer_name` for each firm)
3. Parse `report_data` JSON → `field_sub_mat.und[]` → filter entries where `field_employer.und[].target_id` matches the employer's PDC ID → extract `field_mat_of_prop`, `field_legislative_agency`, `field_issue_or_bill_number`

Example result: Port of Seattle → Trent M House ($639K) → Transportation Committees → "Real ID, TNC's, Taxi Cabs, Elections" (2017–2024). Makes sense for an airport operator: rideshare/taxi regulation and Real ID both affect SeaTac.

Note: not all firms file per-employer subjects — some report at firm level. When employer-specific subjects aren't found, fall back to the PDF link in the `url` field of the L2 filing.

**Electioneering communications — completing the chain to candidates:**
Electioneering comms (C6 filings) are issue ads run within 60 days of an election that mention candidates but don't explicitly advocate. The API records the spend (vendor, amount, dates) but NOT the candidate name — because C6 report_type doesn't expose it at the data level. However, WA law requires the C6 filing PDF to disclose which candidates appeared in the ad.

To close the chain from funder to candidate:
1. Query `67cp-h962` for the committee: `upper(sponsor_name) LIKE "%CITIZENS FOR PROGRESS%"`
2. Confirm `report_type = "Electioneering Communication"` — this is why no candidate field appears
3. Use the `url` field → fetch the C6 filing PDF from apollo.pdc.wa.gov → Section 3 of the form names the candidate(s) and whether the ad supported or opposed them
4. Cross-reference with the contributions chain to connect original funders to that candidate

Example: Citizens for Progress C6-12751 → Section 3 → SPRINGER, LARRY — STATE REPRESENTATIVE/LEG DISTRICT 45 – HOUSE — DEMOCRAT — OPPOSE — $58,588. Full chain: Jobs PAC → Citizens for Progress → Comcast cable TV ads opposing Larry Springer, 2024.

This is a 4-hop recipe: funder → PAC → electioneering comm committee → ad vendor (API) → candidate (PDF). The API proves the money flow; the PDF closes the loop to the race.

**Ballot measure money — two-hop query:**
Corporate and out-of-state money flows through ballot measure committees, not individual contributions. To find it:
1. Search `filer_name` for the initiative number or topic: `upper(filer_name) LIKE "%1631%"` → returns "NO ON 1631 (SPONSORED BY WESTERN STATES PETROLEUM ASSOCIATION)"
2. Then search contributions to that committee by exact filer name
This is how you find e.g. $31.6M in out-of-state oil money opposing a carbon tax.

**Washington election cycles:**
- State legislative races: even years (2022, 2024)
- Seattle/King County local races (mayor, city council, county council): odd years (2023, 2025)
- Statewide ballot measures: can appear in either; check election_year in your query
When a user asks about "2024 King County Council races," correct to 2023.

**PDC data updates continuously.** Bond/EMMA data is separate (use EMMA at emma.msrb.org).
**The `url` field** in contribution records links to the actual PDC filing — always include it.
**For WA-specific investigations:** check both PDC (state) and FEC (federal) for complete picture.
