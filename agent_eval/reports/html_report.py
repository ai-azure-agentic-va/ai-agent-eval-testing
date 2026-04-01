"""Generates an HTML evaluation report from results."""

import html
from datetime import datetime


def _score_class(value, threshold=3):
    """Return CSS class based on pass/fail threshold."""
    if not isinstance(value, (int, float)):
        return "neutral"
    return "pass-bg" if value >= threshold else "fail-bg"


def _extract_score(metric_name, score_obj):
    """Extract numeric score from a score object based on metric type."""
    key_map = {
        "relevance": "relevance",
        "groundedness": "groundedness",
        "retrieval": "retrieval_score",
        "citations": "citation_accuracy",
        "jailbreak": "severity",
        "fallback": "fallback_score",
        "content_safety": "safety_score",
    }
    key = key_map.get(metric_name, metric_name)
    return score_obj.get(key, "N/A")


def generate_report(results, output_path="eval_report.html"):
    """Generate a styled HTML report from evaluation results."""
    latencies = sorted([r["latency"] for r in results])
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    p95_idx = int(len(latencies) * 0.95) if latencies else 0
    p95_latency = latencies[min(p95_idx, len(latencies) - 1)] if latencies else 0

    # Aggregate scores per metric
    all_scores = {}
    for r in results:
        for metric_name, score_obj in r.get("scores", {}).items():
            if not isinstance(score_obj, dict):
                continue
            val = _extract_score(metric_name, score_obj)
            if isinstance(val, (int, float)):
                all_scores.setdefault(metric_name, []).append(val)

    def avg(lst):
        return sum(lst) / len(lst) if lst else 0

    # Group by category
    grouped = {}
    for r in results:
        cat = r.get("category", "Uncategorized")
        grouped.setdefault(cat, []).append(r)

    summary_cards = ""
    summary_cards += f'<div class="summary-item"><h3>Total Tests</h3><p>{len(results)}</p></div>'
    summary_cards += f'<div class="summary-item"><h3>Avg Latency</h3><p>{avg_latency:.2f}s</p></div>'
    summary_cards += f'<div class="summary-item"><h3>p95 Latency</h3><p>{p95_latency:.2f}s</p></div>'
    for metric_name, scores in all_scores.items():
        label = metric_name.replace("_", " ").title()
        summary_cards += f'<div class="summary-item"><h3>{label}</h3><p>{avg(scores):.1f}/5</p></div>'

    rows_html = ""
    for category, cat_results in grouped.items():
        rows_html += f'<div class="category-header">{html.escape(category)}</div>'
        rows_html += """<table>
            <tr>
                <th style="width:15%">Test Case</th>
                <th style="width:30%">Prompt / Response</th>
                <th style="width:40%">Evaluation Scores</th>
                <th style="width:15%">Latency</th>
            </tr>"""

        for r in cat_results:
            scores_html = ""
            for m_name, score_obj in r.get("scores", {}).items():
                if not isinstance(score_obj, dict):
                    continue
                val = _extract_score(m_name, score_obj)
                reasoning = score_obj.get("reasoning", score_obj.get(f"{m_name}_reason", ""))
                label = m_name.replace("_", " ").title()
                css = _score_class(val)
                display_val = f"{val}/5" if isinstance(val, (int, float)) else str(val)

                scores_html += f"""<div class="score-row">
                    <span class="metric-label">{label}:</span>
                    <span class="{css}">{display_val}</span><br>
                    <span class="reason">{html.escape(str(reasoning))}</span>
                </div>"""

            expected = r.get('expected_behavior', '')
            context = r.get('context', '')

            rows_html += f"""<tr>
                <td><strong>{html.escape(r.get('name', ''))}</strong><br>
                    <small>{html.escape(r.get('id', ''))}</small></td>
                <td>
                    <div class="prompt-block"><small class="metric-label">PROMPT:</small><br>
                        <pre>{html.escape(r.get('query', ''))}</pre></div>
                    <div class="prompt-block"><small class="metric-label">EXPECTED RESPONSE:</small><br>
                        <pre>{html.escape(expected) if expected else '<em>Not specified</em>'}</pre></div>
                    <div class="prompt-block"><small class="metric-label">ACTUAL RESPONSE:</small><br>
                        <pre>{html.escape(r.get('response', ''))}</pre></div>
                    <div><small class="metric-label">CITATIONS:</small><br>
                        <pre>{html.escape(context) if context else '<em>No sources cited</em>'}</pre></div>
                </td>
                <td>{scores_html}</td>
                <td style="text-align:center"><strong>{r.get('latency', 0):.2f}s</strong></td>
            </tr>"""

        rows_html += "</table>"

    report = f"""<!DOCTYPE html>
<html>
<head>
<title>Agent Evaluation Report</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background: #f3f2f1; line-height: 1.5; }}
.header {{ background: #0078d4; color: white; padding: 25px; border-radius: 8px; margin-bottom: 25px; }}
.summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 25px; }}
.summary-item {{ background: white; padding: 18px; border-radius: 8px; text-align: center; border: 1px solid #edebe9; }}
.summary-item h3 {{ margin: 0; color: #605e5c; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.5px; }}
.summary-item p {{ margin: 6px 0 0; font-size: 1.6em; font-weight: 700; color: #0078d4; }}
.category-header {{ background: #323130; color: white; padding: 10px 18px; border-radius: 4px; margin-top: 25px; margin-bottom: 12px; font-weight: 600; }}
table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; margin-bottom: 20px; }}
th, td {{ border: 1px solid #edebe9; padding: 12px; text-align: left; vertical-align: top; }}
th {{ background: #f3f2f1; color: #323130; font-weight: 600; font-size: 0.9em; }}
.metric-label {{ font-weight: 600; color: #323130; font-size: 0.85em; }}
.pass-bg {{ background: #dff6dd; color: #107c10; border-radius: 4px; padding: 2px 8px; font-weight: 700; }}
.fail-bg {{ background: #fde7e9; color: #d13438; border-radius: 4px; padding: 2px 8px; font-weight: 700; }}
.neutral {{ color: #605e5c; }}
.score-row {{ border-bottom: 1px solid #f3f2f1; padding: 8px 0; }}
.score-row:last-child {{ border-bottom: none; }}
.reason {{ font-size: 0.8em; color: #605e5c; }}
.prompt-block {{ margin-bottom: 10px; border-bottom: 1px dashed #edebe9; padding-bottom: 5px; }}
pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 0.9em; margin: 0; color: #444; }}
</style>
</head>
<body>
<div class="header">
    <h1>Agent Evaluation Report</h1>
    <p>RAG Quality + Safety | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</div>
<div class="summary-grid">{summary_cards}</div>
{rows_html}
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    return output_path
