# wa-campaign-finance

Query Washington State campaign finance data with plain English.

All data from the [Washington State Public Disclosure Commission](https://pdc.wa.gov) via [data.wa.gov](https://data.wa.gov). No scraping, no FOIA requests — it's all public.

**The easy stuff** — candidate funding, employer sweeps, individual contributions — is already on [pdc.wa.gov's own search interface](https://pdc.wa.gov/political-disclosure-reporting-data/search-databases). This tool is for the hard stuff: multi-hop structural analysis that traces money through pass-through networks, maps cross-industry coalitions, and connects governance rosters to the industries that fund them.

---

## What this tool is for

Washington State's campaign finance records are public. Every contribution, every PAC transfer, every lobbying dollar is disclosed — theoretically traceable by anyone.

In practice, the money moves through layers. An oil company funds a PAC. The PAC funds a network vehicle. The network vehicle creates geographically-named committees. Those committees buy cable TV ads. The ad says "Paid for by Citizens for Progress." The oil company is four hops back.

The same structure runs in both directions. Start from an organization and follow its money forward to see where it lands. Start from an ad disclaimer and trace backward to the original funders. Cross-reference a board roster against contribution records to see which industries have built networks around appointed bodies that make consequential public decisions.

Every transaction is in PDC. The opacity comes from the structure, not from hidden records. No single query surfaces it — it requires chaining contributions, expenditures, lobbying records, and governance data across multiple datasets. That's what the recipes below do.

---

## Recipes

### 3-hop — Governance fingerprint
*Fetch the board roster → extract institutional affiliations → cross-reference each against PDC.*

> *"Show me the PDC footprint of the Washington State Convention Center Public Facilities District board."*

The PFD board oversees $100M/year in lodging tax revenue. Its members are appointed by the Mayor of Seattle, the King County Executive, and the Governor. Running the governance fingerprint:

1. Fetch roster from the agency's governance page
2. Identify each member's employer or institutional affiliation
3. For each institution: contributions as donor, lobbying spend as employer, PAC funding as entity

What surfaces for the PFD: Washington Hospitality Association-affiliated members whose industry has built an extensive campaign finance network across WA elections, and observable patterns of contributions from the same donor network to key races. That's a documented pattern of connections — not a finding of wrongdoing.

**This tool doesn't presuppose capture.** Regulatory capture — the process by which appointed bodies come to serve the industries they oversee rather than the public interest — requires more than institutional connections to establish. It requires documenting how those connections shaped specific decisions. The PDC data surfaces the connections. Whether they constitute capture is a question for reporting, not for a database query.

Not every board shows the pattern. Run this recipe on the Washington Forest Practices Board and you'll find that individual members have minimal PDC footprints. That's also a result — the tool reports what the data shows, and absence is information too.

**This recipe runs on any appointed board.** The Governor's [boards and commissions directory](https://governor.wa.gov/boards-and-commissions/boards-commissions/board-commission-profiles) lists every Washington State board and commission. As a public service, you can run the governance fingerprint on any of them — Puget Sound Clean Air Agency, WA State Investment Board, WA Housing Finance Commission, WA Liquor and Cannabis Board, and hundreds more. Each has a governance page. Each has members with institutional affiliations. Each affiliation has a PDC footprint — or doesn't.

---

### 3-hop — Lobbying agenda
*Compensation records → L2 filings → parse subject matter. Claude handles all three.*

> *"What lobbying firms does the Port of Seattle pay, what do they lobby for, and how much?"*

Returns four firms totaling $1M+ since 2016, along with what each lobbied for: Transportation Committees and Local Government Committees on *Real ID, rideshares, taxis, and Port Commissioner elections* — the core regulatory agenda for an airport operator.

The subject matter isn't a top-level field. It's embedded in a JSON blob inside `report_data` on a different dataset. Without the skill, this query returns nothing and gives no indication why.

---

### 2-hop — Coalition mapping
*Find which PACs an organization funds, then see who else is in the pool.*

> *"Who does the Washington Hospitality Association pool money with?"*

WHA contributes to Jobs PAC ($232K), The Leadership Council ($250K), and Evergreen Leadership Fund ($206K), among others. Looking at who else funds Jobs PAC reveals the full coalition: BP America ($2M), Amazon ($1M), Tesoro ($500K), Washington State Dental PAC ($335K), Marathon Petroleum ($290K), BIAW ($320K). Hospitality, oil, tech, realtors, and dentists — all in the same vehicle. The shared PAC is where cross-industry coordination becomes visible.

---

### Recursive — PAC money trail
*Run forward from a known organization, or backward from an ad disclaimer. Both directions work.*

**Forward:** *"Where did Jobs PAC's $12.7M ultimately go?"*

Jobs PAC routes through Enterprise Washington geographic vehicles — People for Jobs, Citizens for Progress, South Sound Future, Our Olympic Communities — which buy targeted cable TV and digital ads in specific legislative districts. By the time a voter sees a Comcast cable ad opposing a state Senate candidate, the connection to the original funders is four hops back.

**Backward:** *"I just saw an ad paid for by Citizens for Progress. Who actually funded it?"*

Hop 1 — Citizens for Progress received money from: Phillips 66 directly ($350K) and Enterprise Washington's Jobs PAC ($658K+).

Hop 2 — Jobs PAC was funded by: BP America ($2M), Amazon ($1M), Phillips 66 ($750K), WA Realtors PAC ($1M+), Washington State Dental PAC ($335K), Marathon Petroleum ($290K), and others.

The ad in a voter's living room traces back to oil companies, tech corporations, real estate associations, and dentists — none named in the disclaimer. Every transaction is disclosed in PDC. The opacity comes from the structure, not from hiding the records.

This is path-complete tracing, not a single query. Claude runs it iteratively in either direction.

---

### 4-hop — Electioneering communications: closing the chain to candidates
*Electioneering communications are issue ads that run within 60 days of an election and mention candidates without explicitly advocating. PDC's API records the spend — vendor, amount, dates — but not the candidate name. The candidate is in the C6 filing PDF.*

> *"Citizens for Progress ran TV ads in 2024. Which candidates were they targeting?"*

The API confirms the spend: Citizens for Progress paid Progressive Strategies NW $27,499 for Comcast cable TV advertising in October 2024. `report_type: Electioneering Communication` explains why no candidate field appears in the data — it's a legally distinct filing category from independent expenditures.

The `url` field on each record links to the C6 filing PDF at apollo.pdc.wa.gov. WA law requires C6 PDFs to disclose which candidates appeared in the ad. Fetching report C6-12751 closes the chain: Section 3 names **Larry Springer, Democrat, House District 45 — OPPOSE — $58,588**.

Full chain, fully sourced: Jobs PAC → Citizens for Progress → $58,588 in Comcast cable TV ads opposing Larry Springer, Democrat, House District 45, 2024. Every hop is in PDC. The candidate is in the PDF.

---

### 2-hop — Ballot measure
*Any campaign for or against a ballot measure must register a political committee with PDC and report all funding. Start with a policy question — the recipe finds the committee, then traces who funded each side.*

> *"Who funded the campaigns for and against minimum wage increases for restaurant workers in Burien and Tukwila?"*

Two committees, two coalitions. Pro-wage side: Transit Riders Union ($78K), WA Community Action Network ($27K), SEIU, UFCW, Working Washington. Counter-campaign ("Raise the Wage Responsibly Sponsored by Washington Hospitality Association"): WHA PAC ($28K), Bloomin' Brands PAC — the Outback Steakhouse parent company, based in Florida ($5K), Washington Food Industry Association, Washington Beverage Association.

> *"Who funded both sides of Washington's 2018 carbon tax initiative?"*

**Against — $31.6M:** BP America ($11.5M), Phillips 66 ($7M), Andeavor/Marathon ($4.2M), Valero ($1M), Chevron ($423K). Almost entirely out-of-state oil. Committee name: "NO ON 1631 (SPONSORED BY WESTERN STATES PETROLEUM ASSOCIATION)."

**For — $15.3M:** Nature Conservancy ($2.3M), Bill Gates ($1M), Michael Bloomberg ($1M, NY), League of Conservation Voters ($1.2M), Nick Hanauer ($250K).

Oil outspent environmentalists 2:1. The initiative failed 56–44.

---

## Why the skill?

*Can't anyone just ask Claude about PDC data without installing anything?*

Yes. The skill doesn't unlock the data — it's all public. What it adds:

**Pre-loaded dataset knowledge.** Six dataset IDs, their key fields, and how they join — looked up once, available every session. Without it, Claude has to find these on its own, which takes turns and sometimes produces wrong IDs.

**Debugged query patterns.** The two-hop ballot measure lookup, the three-hop subject matter parse, the employer sweep, the governance fan-out — these were built by running real queries against live data, hitting the edge cases, and fixing them. The most consequential: `subject_matter` isn't a top-level field on the lobbying dataset. It's embedded in a JSON blob inside `report_data` on a different dataset entirely. A query for subject matter without the skill returns nothing and gives no indication why.

**Verified results.** Every example in this README came from a live PDC query: $31.6M from oil companies to No on 1631, $1M+ from the Port of Seattle to four lobbying firms, the WHA coalition across Jobs PAC. The data is real. The patterns that surfaced it are what the skill encodes.

The skill is the research we already did, reusable without redoing it.

**Caveat emptor.** Zero results mean one of three things: the data doesn't exist, the committee name is different than expected, or the year is wrong. The skill can't anticipate every jurisdiction's election schedule or committee naming convention across WA's 500+ local governments. Verify before you publish.

---

## Install (2 steps)

### Step 1 — Get a free API token (2 minutes, requires browser)

1. Go to [data.wa.gov](https://data.wa.gov) and click **Sign In** (top right)
2. Create an account or sign in with Google
3. Click your name → **Edit Profile**
4. Scroll to **App Tokens** → **Create New App Token**
5. Give it any name (e.g. "PDC Research") and click **Save**
6. Copy the **App Token** value

### Step 2 — Paste this into Claude Code

Replace `YOUR_TOKEN_HERE` with your token, then paste into [Claude Code](https://claude.ai/code) *(requires a Claude subscription — [plans and pricing](https://claude.ai/pricing))*:

```
Install the PDC campaign finance research skill. My data.wa.gov API token is: YOUR_TOKEN_HERE

Please:
1. Download https://raw.githubusercontent.com/ivantohelpyou/wa-campaign-finance/main/skills/pdc.md to ~/.claude/skills/pdc.md (create the directory if needed)
2. Add PDC_APP_TOKEN to the env section of ~/.claude/settings.json — create the file if it doesn't exist, merge carefully if it does
3. Confirm both files are in place and show me an example query I can try
```

Claude Code handles the rest. Once installed, ask anything from the recipes above.

---

## Manual install (if you prefer)

<details>
<summary>Step-by-step without Claude Code</summary>

**1. Download the skill file**

```bash
mkdir -p ~/.claude/skills
curl -o ~/.claude/skills/pdc.md \
  https://raw.githubusercontent.com/ivantohelpyou/wa-campaign-finance/main/skills/pdc.md
```

**2. Add your token to Claude Code settings**

Open `~/.claude/settings.json` in any text editor (create it if it doesn't exist) and add the `env` section:

```json
{
  "env": {
    "PDC_APP_TOKEN": "paste-your-token-here"
  }
}
```

If the file already has content, add the `env` block inside the existing `{` `}`:

```json
{
  "model": "sonnet",
  "env": {
    "PDC_APP_TOKEN": "paste-your-token-here"
  }
}
```

**Where is `~/.claude/settings.json`?**
- Mac/Linux: `/Users/yourname/.claude/settings.json`
- Windows: `C:\Users\yourname\.claude\settings.json`

</details>

---

## MCP Server (for developers)

The MCP server gives Claude native tool access — works in Claude Desktop as well as Claude Code.

**Requirements:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/ivantohelpyou/wa-campaign-finance
cd wa-campaign-finance
uv sync
cp .env.example .env
# Edit .env and add your PDC_APP_TOKEN
chmod +x run-mcp.sh
```

**Claude Code** — add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "pdc": {
      "command": "/path/to/wa-campaign-finance/run-mcp.sh",
      "args": [],
      "env": {}
    }
  }
}
```

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pdc": {
      "command": "/path/to/wa-campaign-finance/run-mcp.sh"
    }
  }
}
```

---

## What's covered

| Dataset | What it contains |
|---------|-----------------|
| Contributions | Who gave to whom, how much, from what employer |
| Expenditures | What campaigns spent money on and with whom |
| Independent expenditures | PAC ad buys and electioneering communications |
| Lobbyist compensation | Who paid whom to lobby, on what subjects |
| Lobbyist filings | L1/L2/L3 reports linking lobbying to legislators and bills |
| Enforcement cases | PDC violation and penalty history |
| Campaign summaries | Cycle-level fundraising totals |

---

## Related

- [Model Citizen Developer](https://modelcitizendeveloper.com) — civic research tools and methodology
- [Convention City Dispatch](https://dispatch.conventioncityseattle.com) — where this tool was built
- [Washington State PDC](https://pdc.wa.gov) — the source data
- [WA Governor's boards and commissions directory](https://governor.wa.gov/boards-and-commissions/boards-commissions/board-commission-profiles) — entry point for governance fingerprint queries

---

MIT License
