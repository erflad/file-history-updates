from html import escape
from pathlib import Path
from datetime import datetime


def generate_report(findings, output_path):
    """Generate an HTML report of detected actions."""

    rows = []
    category_counts = {}

    for finding in findings:
        category = finding["category"]
        category_counts[category] = category_counts.get(category, 0) + 1

    document_count = len({
        finding["filename"] for finding in findings
    })

    category_summary = "".join(
        f"<li>{escape(category.title())}: {count}</li>"
        for category, count in sorted(category_counts.items())
    )

    for finding in sorted(
        findings,
        key=lambda item: item["priority"]["score"],
        reverse=True
    ):
        filename = escape(finding["filename"])
        category = escape(finding["category"].title())
        phrase = escape(finding["phrase"])
        context = escape(finding["context"])
        score = finding["priority"]["score"]

        dates = finding.get("dates", [])

        if dates:
            date_text = ", ".join(
                escape(item["date"]) for item in dates
            )
        else:
            date_text = "No date detected"

        reasons = "".join(
            f"<li>{escape(reason)}</li>"
            for reason in finding["priority"]["reasons"]
        )

        rows.append(f"""
        <article class="finding">
            <div class="topline">
                <span class="category">{category}</span>
                <span class="score">{score} points</span>
            </div>

            <h2>{phrase}</h2>
            <p class="context">{context}</p>

            <p><strong>Document:</strong> {filename}</p>
            <p><strong>Date:</strong> {date_text}</p>

            <details>
                <summary>Why this was prioritized</summary>
                <ul>{reasons}</ul>
            </details>
        </article>
        """)

    if not rows:
        rows.append("<p>No actionable findings detected.</p>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>File History Updates Report</title>

<style>
    body {{
        font-family: Arial, sans-serif;
        background: #f4f5f7;
        color: #20242a;
        max-width: 900px;
        margin: 40px auto;
        padding: 0 20px;
    }}

    header {{
        margin-bottom: 30px;
    }}

    h1 {{
        margin-bottom: 5px;
    }}

    .subtitle {{
        color: #68717d;
    }}

    .finding {{
        background: white;
        border: 1px solid #e1e4e8;
        border-radius: 10px;
        padding: 22px;
        margin-bottom: 16px;
    }}

    .topline {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .category {{
        font-size: 13px;
        font-weight: bold;
        color: #405b83;
        text-transform: uppercase;
    }}

    .score {{
        font-weight: bold;
        background: #edf1f6;
        padding: 7px 12px;
        border-radius: 20px;
    }}

    .context {{
        line-height: 1.6;
        color: #424b56;
    }}

    details {{
        margin-top: 15px;
    }}

    summary {{
        cursor: pointer;
        color: #405b83;
    }}

    footer {{
        color: #68717d;
        font-size: 12px;
        margin-top: 30px;
    }}

    .summary {{
        background: white;
        border: 1px solid #e1e4e8;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }}

    .summary h2 {{
        font-size: 18px;
    }}
</style>
</head>

<body>
    <header>
        <h1>File History Updates</h1>
        <p class="subtitle">
            Actionable information discovered in your documents.
        </p>

        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>

        <div class="summary">
            <p><strong>Total findings:</strong> {len(findings)}</p>
            <p><strong>Documents with findings:</strong> {document_count}</p>
            <h2>Category breakdown</h2>
            <ul>{category_summary or "<li>No findings</li>"}</ul>
        </div>
    </header>

    <main>
        {''.join(rows)}
    </main>

    <footer>
        Priority scores are estimates. Review findings before acting.
    </footer>
</body>
</html>
"""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")

    return output