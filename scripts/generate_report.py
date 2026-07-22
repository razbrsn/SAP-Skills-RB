#!/usr/bin/env python3
"""Generate a self-contained HTML report from SAP opportunity scan data."""

import json
import argparse
import sys
from datetime import datetime


def generate_html(data: dict) -> str:
    """Generate the HTML report string."""
    meta = data["metadata"]
    opportunities = data["opportunities"]

    # Count stats
    new_logos = sum(1 for o in opportunities if o["crm_status"] == "New Logo Prospect")
    existing = sum(1 for o in opportunities if o["crm_status"] == "Existing Customer")
    unknown = sum(1 for o in opportunities if o["crm_status"] == "Lookup unavailable")

    # Build table rows
    rows_html = ""
    for i, opp in enumerate(opportunities, 1):
        # Badge color
        if opp["crm_status"] == "New Logo Prospect":
            badge_class = "badge-new"
            badge_text = "New Logo"
        elif opp["crm_status"] == "Existing Customer":
            badge_class = "badge-existing"
            badge_text = "Existing"
            if opp.get("crm_account_type"):
                badge_text += f" ({opp['crm_account_type']})"
        else:
            badge_class = "badge-unknown"
            badge_text = "Unknown"

        source_link = f'<a href="{opp["source_url"]}" target="_blank" rel="noopener">Source</a>' if opp.get("source_url") else "N/A"

        rows_html += f"""
        <tr data-status="{opp['crm_status']}" data-signal="{opp['signal']}">
            <td class="col-num">{i}</td>
            <td class="col-company"><strong>{opp['company']}</strong></td>
            <td class="col-signal"><span class="signal-tag">{opp['signal']}</span></td>
            <td class="col-solution">{opp['sap_solution']}</td>
            <td class="col-justification">{opp['justification']}</td>
            <td class="col-status"><span class="badge {badge_class}">{badge_text}</span></td>
            <td class="col-source">{source_link}</td>
        </tr>"""

    # Build the full HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAP Opportunity Scan Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #1a2b42;
            padding: 2rem;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #0070f2 0%, #0053b8 100%);
            color: white;
            padding: 2rem 2.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }}
        .header h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
        .header .meta {{ opacity: 0.9; font-size: 0.9rem; }}
        .header .meta span {{ margin-right: 1.5rem; }}
        .kpis {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .kpi-card {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .kpi-card .number {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #0070f2;
        }}
        .kpi-card .label {{
            font-size: 0.85rem;
            color: #5a6f8a;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 0.25rem;
        }}
        .kpi-card.new-logo .number {{ color: #0d9f6e; }}
        .kpi-card.existing .number {{ color: #0070f2; }}
        .filters {{
            background: white;
            border-radius: 10px;
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }}
        .filters label {{ font-size: 0.85rem; font-weight: 600; color: #5a6f8a; }}
        .filters select, .filters input {{
            padding: 0.4rem 0.8rem;
            border: 1px solid #dde3ea;
            border-radius: 6px;
            font-size: 0.85rem;
            background: #f8fafc;
        }}
        .table-wrapper {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            overflow-x: auto;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
        th {{
            background: #f0f4f8;
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 600;
            color: #3d5170;
            border-bottom: 2px solid #dde3ea;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }}
        th:hover {{ background: #e2e8f0; }}
        td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #edf2f7; vertical-align: top; }}
        tr:hover {{ background: #f8fafc; }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            white-space: nowrap;
        }}
        .badge-new {{ background: #d1fae5; color: #065f46; }}
        .badge-existing {{ background: #dbeafe; color: #1e40af; }}
        .badge-unknown {{ background: #f3f4f6; color: #6b7280; }}
        .signal-tag {{
            background: #fef3c7;
            color: #92400e;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        .col-num {{ width: 40px; color: #9ca3af; }}
        .col-company {{ min-width: 150px; }}
        .col-signal {{ min-width: 120px; }}
        .col-solution {{ min-width: 180px; }}
        .col-justification {{ min-width: 250px; }}
        .col-status {{ min-width: 120px; }}
        .col-source {{ min-width: 60px; }}
        a {{ color: #0070f2; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .footer {{
            text-align: center;
            margin-top: 2rem;
            font-size: 0.8rem;
            color: #9ca3af;
        }}
        .no-results {{
            text-align: center;
            padding: 3rem;
            color: #6b7280;
        }}
        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            .kpis {{ grid-template-columns: 1fr 1fr; }}
            .filters {{ flex-direction: column; align-items: stretch; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SAP Opportunity Scan Report</h1>
            <div class="meta">
                <span>Geography: <strong>{meta['geography']}</strong></span>
                <span>Sources: <strong>{', '.join(meta['sources'])}</strong></span>
                <span>Generated: <strong>{meta['generated_at']}</strong></span>
            </div>
        </div>

        <div class="kpis">
            <div class="kpi-card">
                <div class="number">{len(opportunities)}</div>
                <div class="label">Total Opportunities</div>
            </div>
            <div class="kpi-card new-logo">
                <div class="number">{new_logos}</div>
                <div class="label">New Logos</div>
            </div>
            <div class="kpi-card existing">
                <div class="number">{existing}</div>
                <div class="label">Existing Customers</div>
            </div>
        </div>

        <div class="filters">
            <label for="filter-status">CRM Status:</label>
            <select id="filter-status" onchange="filterTable()">
                <option value="all">All</option>
                <option value="New Logo Prospect">New Logos Only</option>
                <option value="Existing Customer">Existing Only</option>
            </select>
            <label for="filter-signal">Signal:</label>
            <select id="filter-signal" onchange="filterTable()">
                <option value="all">All Signals</option>
            </select>
            <label for="filter-search">Search:</label>
            <input type="text" id="filter-search" placeholder="Company name..." oninput="filterTable()">
        </div>

        <div class="table-wrapper">
            <table id="opp-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th onclick="sortTable(1)">Company</th>
                        <th onclick="sortTable(2)">Signal</th>
                        <th onclick="sortTable(3)">SAP Solution</th>
                        <th>Justification</th>
                        <th onclick="sortTable(5)">CRM Status</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>SAP Opportunity Scanner &middot; Generated by Joule Desktop &middot; {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
    </div>

    <script>
        // Populate signal filter
        (function() {{
            const signals = new Set();
            document.querySelectorAll('#opp-table tbody tr').forEach(row => {{
                signals.add(row.dataset.signal);
            }});
            const sel = document.getElementById('filter-signal');
            [...signals].sort().forEach(s => {{
                const opt = document.createElement('option');
                opt.value = s;
                opt.textContent = s;
                sel.appendChild(opt);
            }});
        }})();

        function filterTable() {{
            const status = document.getElementById('filter-status').value;
            const signal = document.getElementById('filter-signal').value;
            const search = document.getElementById('filter-search').value.toLowerCase();
            document.querySelectorAll('#opp-table tbody tr').forEach(row => {{
                const matchStatus = (status === 'all' || row.dataset.status === status);
                const matchSignal = (signal === 'all' || row.dataset.signal === signal);
                const matchSearch = (search === '' || row.children[1].textContent.toLowerCase().includes(search));
                row.style.display = (matchStatus && matchSignal && matchSearch) ? '' : 'none';
            }});
        }}

        let sortDir = {{}};
        function sortTable(colIdx) {{
            const table = document.getElementById('opp-table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            sortDir[colIdx] = !sortDir[colIdx];
            rows.sort((a, b) => {{
                const aText = a.children[colIdx].textContent.trim().toLowerCase();
                const bText = b.children[colIdx].textContent.trim().toLowerCase();
                return sortDir[colIdx] ? aText.localeCompare(bText) : bText.localeCompare(aText);
            }});
            rows.forEach(row => tbody.appendChild(row));
        }}
    </script>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate SAP Opportunity Scan HTML Report")
    parser.add_argument("--input", required=True, help="Path to opportunities.json")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(1)

    if not data.get("opportunities"):
        print("WARNING: No opportunities found in input data.")
        # Still generate an empty report
        data["opportunities"] = []

    html = generate_html(data)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    total = len(data["opportunities"])
    new_logos = sum(1 for o in data["opportunities"] if o["crm_status"] == "New Logo Prospect")
    existing = sum(1 for o in data["opportunities"] if o["crm_status"] == "Existing Customer")
    print(f"Report generated successfully: {args.output}")
    print(f"  Total opportunities: {total}")
    print(f"  New logos: {new_logos}")
    print(f"  Existing customers: {existing}")


if __name__ == "__main__":
    main()
