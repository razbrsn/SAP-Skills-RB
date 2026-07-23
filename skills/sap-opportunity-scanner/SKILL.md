---
name: sap-opportunity-scanner
description: >-
  Scans news sources for potential SAP sales opportunities triggered by divestments, mergers, funding rounds, market expansions, IT challenges, and other business events. Identifies private-sector companies, maps them to relevant SAP solutions, checks CRM for existing customer status, and generates a shareable HTML report. Use when the user says "scan for SAP opportunities", "find SAP leads", "opportunity scanner", "news opportunities", "prospect scan", "lead scanner", "find new logos", "market signals", or "SAP pipeline scan".
allowed-tools: web_search mcp_d72e5b21_search-accounts write_file execute read_file task
metadata:
  author: Territory Ecosystem Manager
  version: 1.0.1
  tags: sales prospecting news-scanning lead-generation sap-solutions
  required-mcp-servers: "*.hana.ondemand.com/mcp"
---

# SAP Opportunity Scanner

Scan news sources for private-sector business events that signal SAP sales opportunities. Generate a shareable HTML report with company names, SAP solution recommendations, justifications, and CRM status.

---

## Step 1 — Collect Inputs

Ask the user for the following (all required):

1. **Geography / Territory** — Which countries or regions to focus on?
   - Example: "East Africa", "Kenya, Nigeria, Ghana, Tanzania"
2. **News sources** — Which websites or news domains to prioritize?
   - Example: "reuters.com, bloomberg.com, techcrunch.com, disrupt-africa.com"
   - Accept a comma-separated list of domains
3. **Depth** — How many search results to process per keyword? (max 50)
   - Default: 10 if not specified

If the user provides all three in their initial message, skip asking and proceed directly.

---

## Step 2 — Search for Opportunity Signals

Use the `web_search` tool to find recent news matching opportunity keywords scoped to the user's geography and sources.

### Keywords (20 total)

Use these keywords combined with the geography:

1. Divestment
2. Acquisition
3. Merger
4. Carve-out
5. Funding round
6. IPO
7. Digital transformation
8. ERP migration
9. Cloud migration
10. Market expansion
11. New market entry
12. IT modernization
13. Legacy system replacement
14. Supply chain disruption
15. Cybersecurity breach
16. Data compliance
17. Workforce expansion
18. New headquarters
19. Joint venture
20. Startup investment

### Search Strategy

Construct search queries in this format:
```
"<keyword>" <geography> site:<source1> OR site:<source2> OR site:<source3>
```

If the user provided many sources (>5), split into batches.

Run searches in **parallel batches of 5 web_search calls per message**. Each call uses `recency: "month"` to focus on recent news.

Example:
```
web_search(query: "divestment Kenya Nigeria site:reuters.com OR site:bloomberg.com", recency: "month")
web_search(query: "acquisition Kenya Nigeria site:reuters.com OR site:bloomberg.com", recency: "month")
web_search(query: "funding round Kenya Nigeria site:reuters.com OR site:bloomberg.com", recency: "month")
web_search(query: "market expansion Kenya Nigeria site:reuters.com OR site:bloomberg.com", recency: "month")
web_search(query: "digital transformation Kenya Nigeria site:reuters.com OR site:bloomberg.com", recency: "month")
```

Continue with remaining keywords in subsequent parallel batches until all 20 are covered.

Respect the user's depth setting — use it as the number of results to scan per keyword batch.

---

## Step 3 — Filter and Extract

From the search results, extract opportunities. For each result:

1. **Identify the company** — extract the private-sector company name involved
2. **Identify the signal** — which keyword/event type does this match?
3. **Capture the source** — URL of the news article
4. **Capture a snippet** — 1-2 sentence summary of what happened

### Public Sector Exclusion Filter

EXCLUDE any result where the entity involved is:
- A government ministry, department, or agency
- A municipality or local government
- A state-owned enterprise (unless it's being privatized — that IS an opportunity)
- A public tender or government procurement
- An NGO, intergovernmental org (UN, AU, World Bank, etc.)
- A public university or public hospital

Keywords that signal public sector (exclude if present as the PRIMARY entity):
- Ministry, Government, Municipal, State-owned, Public tender, Procurement authority, County government, Federal, Senate, Parliament, Public service, Civil service

**Exception:** If a private company is winning a contract FROM government, keep it — the private company is the prospect.

---

## Step 4 — Deduplicate

If the same company appears multiple times across different keyword searches:
- Merge into a single entry
- List ALL signals found (e.g., "Acquisition + Market expansion")
- Keep the most informative source URL

---

## Step 5 — Map to SAP Solutions

For each opportunity, assign the most relevant SAP solution(s) using this mapping:

| Signal | SAP Solution(s) | Rationale |
|--------|-----------------|-----------|
| Divestment / Carve-out / Spin-off | S/4HANA Cloud, RISE with SAP | New entity needs standalone ERP |
| Merger / Acquisition | S/4HANA, Integration Suite, Master Data Governance | System consolidation and data harmonization |
| Startup Funding (Series B+) | Grow with SAP, S/4HANA Cloud Public Edition, BTP | Scaling operations need enterprise platform |
| Digital Transformation | RISE with SAP, S/4HANA Cloud, Analytics Cloud, BTP | End-to-end modernization |
| ERP Migration / Legacy Replacement | RISE with SAP, S/4HANA Cloud | Replace aging systems |
| Market Expansion / New Market Entry | S/4HANA (multi-country), SuccessFactors, Concur | Multi-country operations, HR, travel |
| Supply Chain Disruption | SAP IBP, Ariba, Business Network | Resilience and visibility |
| Cybersecurity / Data Compliance | BTP Security, Data Privacy, GRC | Risk and compliance |
| Workforce Expansion | SuccessFactors (HXM) | Talent management at scale |
| IT Modernization | RISE with SAP, BTP, Integration Suite | Technical refresh |
| IPO Preparation | S/4HANA, Analytics Cloud | Financial compliance and reporting |
| Joint Venture | S/4HANA Cloud, Integration Suite | New entity with integration needs |
| New Headquarters | SuccessFactors, Concur, S/4HANA RE | Facilities and workforce |
| Cloud Migration | BTP, Integration Suite, S/4HANA Cloud | Move to cloud-native |

Write a **short justification** (1-2 sentences) for each opportunity explaining WHY this signal creates an SAP need for this specific company.

---

## Step 6 — CRM Lookup

For each identified company, check if it exists in SAP's CRM using the MXP connector.

Call `mcp_d72e5b21_search-accounts` with:
```json
{
  "searchTerm": "<company_name>"
}
```

Run CRM lookups in **parallel batches of 5** per message.

Interpret the results:
- If results are returned → **Existing Customer** (note the account type if available: Global Ultimate, Planning Entity, or Business Partner)
- If no results → **New Logo Prospect**

If the MXP connector is unavailable (tool call fails), mark CRM status as "Lookup unavailable" and continue generating the report. Do NOT stop the skill.

---

## Step 7 — Generate HTML Report

After all data is collected, generate the HTML report.

Write the opportunity data as a JSON file to the scratch directory:
```
<SCRATCH_DIR>/opportunities.json
```

The JSON structure:
```json
{
  "metadata": {
    "geography": "<user input>",
    "sources": ["<source1>", "<source2>"],
    "depth": <number>,
    "generated_at": "<ISO datetime>",
    "total_opportunities": <count>,
    "new_logos": <count>,
    "existing_customers": <count>
  },
  "opportunities": [
    {
      "company": "<name>",
      "signal": "<event type>",
      "sap_solution": "<recommended solution(s)>",
      "justification": "<1-2 sentence explanation>",
      "crm_status": "Existing Customer" | "New Logo Prospect" | "Lookup unavailable",
      "crm_account_type": "<if available>",
      "source_url": "<article URL>",
      "snippet": "<1-2 sentence news summary>"
    }
  ]
}
```

Then run the HTML generation script:
```bash
python3 "<SKILL_DIR>/scripts/generate_report.py" --input "<SCRATCH_DIR>/opportunities.json" --output "sap_opportunity_scan.html"
```

The script generates a self-contained HTML file with:
- Header with scan metadata (geography, date, sources)
- Summary KPIs: Total Opportunities, New Logos, Existing Customers
- Filterable/sortable table with all opportunities
- Visual badges: green for "New Logo", blue for "Existing Customer", gray for "Lookup unavailable"
- Each row shows: Company | Signal | SAP Solution | Justification | CRM Status | Source link

---

## Step 8 — Present Results

After the HTML file is generated, tell the user:

1. Summary: "Found X potential SAP opportunities (Y new logos, Z existing customers)"
2. File location: "Report saved as `sap_opportunity_scan.html` — open it in any browser to view, filter, and share."
3. Offer next steps: "Would you like me to dive deeper into any specific company, or refine the search with different keywords or sources?"

---

## Error Handling

- **No results found**: Tell the user "No private-sector opportunities found for these keywords in the specified geography. Try broadening the geography, adding more news sources, or adjusting the time window."
- **MXP unavailable**: Continue without CRM lookup, note in report header that CRM status is unavailable.
- **Search rate limiting**: If web_search fails, reduce batch size and retry with delays.

---

## Important Notes

- NEVER include public sector entities in the final report (see exclusion filter in Step 3)
- Always attribute the source URL for each opportunity
- Keep justifications concise and actionable — written for a sales rep
- The report must be a single self-contained HTML file (all CSS/JS inline)
- Cap total opportunities at 30 to keep the report actionable