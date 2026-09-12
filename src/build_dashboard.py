import argparse
import csv
import html
from collections import Counter
from pathlib import Path


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def bars(counter, class_name):
    max_value = max(counter.values()) if counter else 1
    rows = []
    for label, value in counter.most_common():
        width = int((value / max_value) * 100)
        rows.append(
            f"""
            <div class="bar-row">
              <span>{html.escape(label)}</span>
              <div class="bar-track"><div class="bar {class_name}" style="width:{width}%"></div></div>
              <strong>{value}</strong>
            </div>
            """
        )
    return "\n".join(rows)


def stat(label, value, tone):
    return f"""
    <article class="stat {tone}">
      <span>{html.escape(label)}</span>
      <strong>{html.escape(str(value))}</strong>
    </article>
    """


def main():
    parser = argparse.ArgumentParser(description="Build the NetSage dashboard.")
    parser.add_argument("--cases", default="cases.csv")
    parser.add_argument("--reviews", default="review_log.csv")
    parser.add_argument("--responses", default="ai_responses.csv")
    parser.add_argument("--out", default="dashboard.html")
    args = parser.parse_args()

    cases = read_csv(args.cases)
    reviews = read_csv(args.reviews)
    responses = read_csv(args.responses)

    concept_counts = Counter(row["concept_tag"] for row in cases)
    severity_counts = Counter(row["severity"] for row in cases)
    decision_counts = Counter(row["human_decision"] for row in reviews)
    agreement = round((decision_counts["Accepted"] / len(reviews)) * 100, 1)
    corrected = decision_counts["Edited"] + decision_counts["Rejected"]

    demo_case = next(row for row in cases if row["case_id"] == "NET-007")
    demo_review = next(row for row in reviews if row["case_id"] == "NET-007")
    demo_response = next(row for row in responses if row["case_id"] == "NET-007")

    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NetSage AI Dashboard</title>
  <style>
    :root {{
      --ink: #172026;
      --muted: #5c6870;
      --line: #d9e1e5;
      --paper: #f7faf8;
      --panel: #ffffff;
      --teal: #0f8b8d;
      --navy: #23395b;
      --amber: #d58a1f;
      --red: #c44949;
      --green: #2f7d4f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--paper);
      letter-spacing: 0;
    }}
    header {{
      background: var(--navy);
      color: white;
      padding: 28px 32px 22px;
      border-bottom: 6px solid var(--teal);
    }}
    header h1 {{
      margin: 0;
      font-size: 32px;
      line-height: 1.1;
      font-weight: 700;
    }}
    header p {{
      margin: 8px 0 0;
      color: #dce8ee;
      max-width: 920px;
      line-height: 1.45;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-left: 5px solid var(--teal);
      border-radius: 8px;
      padding: 16px;
      min-height: 94px;
    }}
    .stat.amber {{ border-left-color: var(--amber); }}
    .stat.red {{ border-left-color: var(--red); }}
    .stat.green {{ border-left-color: var(--green); }}
    .stat span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 12px;
    }}
    .stat strong {{
      font-size: 30px;
      line-height: 1;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 16px;
      align-items: start;
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 16px;
    }}
    h2 {{
      margin: 0 0 16px;
      font-size: 18px;
      color: var(--navy);
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: minmax(135px, 190px) 1fr 34px;
      align-items: center;
      gap: 10px;
      min-height: 32px;
      color: var(--muted);
      font-size: 14px;
    }}
    .bar-track {{
      height: 12px;
      background: #edf2f4;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar {{
      height: 100%;
      border-radius: 999px;
      background: var(--teal);
    }}
    .bar.severity {{ background: var(--amber); }}
    .bar.review {{ background: var(--green); }}
    .demo {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fbfdfd;
    }}
    .panel h3 {{
      margin: 0 0 8px;
      font-size: 15px;
      color: var(--navy);
    }}
    .panel p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.45;
      font-size: 14px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--navy);
      background: #eef5f5;
    }}
    .badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 9px;
      background: #e8f4ef;
      color: var(--green);
      font-weight: 700;
      font-size: 12px;
    }}
    .badge.edit {{ background: #fff3df; color: #8f5d11; }}
    .badge.reject {{ background: #fdecec; color: #a23535; }}
    @media (max-width: 820px) {{
      header {{ padding: 22px 18px; }}
      main {{ padding: 16px; }}
      .stats, .grid, .demo {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: 112px 1fr 28px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>NetSage AI Dashboard</h1>
    <p>Packet Tracer troubleshooting cases with deterministic checks, AI-style diagnoses, and mandatory human review.</p>
  </header>
  <main>
    <div class="stats">
      {stat("Troubleshooting cases", len(cases), "")}
      {stat("Issue types", len(concept_counts), "green")}
      {stat("AI accepted by reviewer", f"{agreement}%", "amber")}
      {stat("Corrected by human", corrected, "red")}
    </div>

    <div class="grid">
      <section>
        <h2>Coverage By Issue Type</h2>
        {bars(concept_counts, "concept")}
      </section>
      <section>
        <h2>Severity Mix</h2>
        {bars(severity_counts, "severity")}
      </section>
    </div>

    <section>
      <h2>Human Review Decisions</h2>
      {bars(decision_counts, "review")}
    </section>

    <section>
      <h2>Demo Case: Broken Guest Wi-Fi Isolation</h2>
      <div class="demo">
        <div class="panel">
          <h3>Symptom</h3>
          <p>{html.escape(demo_case["symptom"])}</p>
        </div>
        <div class="panel">
          <h3>Evidence</h3>
          <p>{html.escape(demo_case["show_outputs"])}</p>
        </div>
        <div class="panel">
          <h3>AI Output</h3>
          <p>{html.escape(demo_response["root_cause"])}</p>
        </div>
        <div class="panel">
          <h3>Human Review</h3>
          <p><span class="badge edit">{html.escape(demo_review["human_decision"])}</span> {html.escape(demo_review["human_root_cause"])}</p>
        </div>
      </div>
    </section>

    <section>
      <h2>Corrected AI Responses</h2>
      <table>
        <thead>
          <tr>
            <th>Case</th>
            <th>Decision</th>
            <th>AI answer</th>
            <th>Final reviewer answer</th>
          </tr>
        </thead>
        <tbody>
          {''.join(f'<tr><td>{html.escape(r["case_id"])}</td><td><span class="badge {"reject" if r["human_decision"] == "Rejected" else "edit"}">{html.escape(r["human_decision"])}</span></td><td>{html.escape(r["ai_root_cause"])}</td><td>{html.escape(r["human_root_cause"])}</td></tr>' for r in reviews if r["human_decision"] != "Accepted")}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    Path(args.out).write_text(content, encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
