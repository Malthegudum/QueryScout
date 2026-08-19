"""Local storage and result pages for QueryScout outputs."""

from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from typing import Any


RESULTS_DIR = Path.home() / ".queryscout" / "results"
RESULT_BASE_URL = "http://127.0.0.1:8000"
_RESULT_ID = re.compile(r"[0-9a-f]{16}")


def save_result(
    *,
    source: str,
    title: str,
    request: dict[str, Any],
    csv_bytes: bytes,
    code: str,
    power_query: str,
    rows: list[dict[str, str]],
) -> str:
    """Persist one deterministic query result and return its result ID."""
    canonical_request = json.dumps(
        {"source": source, "request": request},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    digest = sha256(canonical_request + b"\0" + csv_bytes).hexdigest()
    result_id = digest[:16]

    output_dir = RESULTS_DIR / result_id
    output_dir.mkdir(parents=True, exist_ok=True)

    columns = list(rows[0]) if rows else []
    metadata = {
        "source": source,
        "title": title,
        "request": request,
        "row_count": len(rows),
        "columns": columns,
        "preview": rows[:20],
    }

    (output_dir / "data.csv").write_bytes(csv_bytes)
    (output_dir / "query.py").write_text(code, encoding="utf-8")
    (output_dir / "powerquery.m").write_text(power_query, encoding="utf-8")
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return result_id


def result_url(result_id: str) -> str:
    return f"{RESULT_BASE_URL}/results/{result_id}"


def _result_dir(result_id: str) -> Path:
    if not _RESULT_ID.fullmatch(result_id):
        raise FileNotFoundError(result_id)

    path = RESULTS_DIR / result_id
    if not path.is_dir():
        raise FileNotFoundError(result_id)

    return path


def result_file(result_id: str, filename: str) -> Path:
    if filename not in {"data.csv", "query.py", "powerquery.m", "metadata.json"}:
        raise FileNotFoundError(filename)

    path = _result_dir(result_id) / filename
    if not path.is_file():
        raise FileNotFoundError(filename)

    return path


def _metadata(result_id: str) -> dict[str, Any]:
    return json.loads(
        result_file(result_id, "metadata.json").read_text(encoding="utf-8")
    )


def render_result_page(result_id: str) -> str:
    """Render the stored result as a standalone local HTML page."""
    metadata = _metadata(result_id)
    code = result_file(result_id, "query.py").read_text(encoding="utf-8")
    power_query = result_file(result_id, "powerquery.m").read_text(encoding="utf-8")

    columns = metadata["columns"]
    preview = metadata["preview"]

    headers = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{escape(str(row.get(column, '')))}</td>"
            for column in columns
        )
        + "</tr>"
        for row in preview
    )

    if not preview:
        table = "<p class='muted'>The query returned no rows.</p>"
    else:
        table = (
            "<div class='table-wrap'><table><thead><tr>"
            + headers
            + "</tr></thead><tbody>"
            + body
            + "</tbody></table></div>"
        )

    code_html = escape(code)
    power_query_html = escape(power_query)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(metadata["title"])}</title>
  <style>
    :root {{
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
      color: #171717;
      background: #f7f7f8;
    }}
    body {{
      margin: 0;
      padding: 28px;
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    .card {{
      background: white;
      border: 1px solid #e5e5e5;
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 18px;
    }}
    h1 {{
      margin-top: 0;
      margin-bottom: 22px;
    }}
    .meta {{
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
      color: #525252;
    }}
    .actions {{
      margin-top: 18px;
    }}
    a.button {{
      display: inline-block;
      padding: 10px 14px;
      border-radius: 9px;
      background: #171717;
      color: white;
      text-decoration: none;
      font-weight: 600;
    }}
    .tabs-card {{
      padding: 0;
      overflow: hidden;
    }}
    .tabs {{
      display: flex;
      gap: 2px;
      padding: 0 16px;
      border-bottom: 1px solid #e5e5e5;
      background: #fafafa;
    }}
    .tab {{
      appearance: none;
      border: 0;
      background: transparent;
      padding: 15px 18px 13px;
      font: inherit;
      font-weight: 700;
      font-size: 16px;
      cursor: pointer;
      color: #525252;
      border-bottom: 3px solid transparent;
    }}
    .tab:hover {{
      color: #171717;
    }}
    .tab.active {{
      color: #171717;
      border-bottom-color: #171717;
      background: white;
    }}
    .tab-panel {{
      display: none;
      padding: 24px;
    }}
    .tab-panel.active {{
      display: block;
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid #e5e5e5;
      padding: 9px 12px;
      text-align: left;
      white-space: nowrap;
    }}
    th {{
      background: #fafafa;
      position: sticky;
      top: 0;
    }}
    .code-wrap {{
      position: relative;
    }}
    pre {{
      overflow-x: auto;
      background: #111827;
      color: #f9fafb;
      border-radius: 10px;
      padding: 18px;
      padding-top: 48px;
      line-height: 1.5;
      font-size: 13px;
      margin: 0;
    }}
    .copy {{
      position: absolute;
      right: 10px;
      top: 10px;
      z-index: 1;
      border: 1px solid #4b5563;
      border-radius: 7px;
      padding: 6px 10px;
      background: #1f2937;
      color: white;
      cursor: pointer;
      font: inherit;
      font-size: 12px;
    }}
    .muted {{
      color: #737373;
    }}
  </style>
</head>
<body>
<main>
  <section class="card">
    <h1>{escape(metadata["title"])}</h1>
    <div class="meta">
      <span><strong>Source:</strong> {escape(metadata["source"])}</span>
      <span><strong>Rows:</strong> {metadata["row_count"]:,}</span>
      <span><strong>Columns:</strong> {len(columns)}</span>
    </div>
    <div class="actions">
      <a class="button" href="/results/{result_id}/data.csv">Download CSV</a>
    </div>
  </section>

  <section class="card tabs-card">
    <div class="tabs" role="tablist">
      <button class="tab active" data-tab="preview" role="tab">Preview</button>
      <button class="tab" data-tab="python" role="tab">Python</button>
      <button class="tab" data-tab="powerquery" role="tab">Power Query</button>
    </div>

    <div id="preview" class="tab-panel active" role="tabpanel">
      <p class="muted">Showing up to 20 rows.</p>
      {table}
    </div>

    <div id="python" class="tab-panel" role="tabpanel">
      <div class="code-wrap">
        <button class="copy" data-copy="python-code">Copy</button>
        <pre><code id="python-code">{code_html}</code></pre>
      </div>
    </div>

    <div id="powerquery" class="tab-panel" role="tabpanel">
      <div class="code-wrap">
        <button class="copy" data-copy="powerquery-code">Copy</button>
        <pre><code id="powerquery-code">{power_query_html}</code></pre>
      </div>
    </div>
  </section>
</main>
<script>
  const tabs = document.querySelectorAll('.tab');
  const panels = document.querySelectorAll('.tab-panel');

  tabs.forEach((tab) => {{
    tab.addEventListener('click', () => {{
      tabs.forEach((item) => item.classList.remove('active'));
      panels.forEach((panel) => panel.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.tab).classList.add('active');
    }});
  }});

  document.querySelectorAll('.copy').forEach((button) => {{
    button.addEventListener('click', async () => {{
      const code = document.getElementById(button.dataset.copy).innerText;
      await navigator.clipboard.writeText(code);
      const oldText = button.textContent;
      button.textContent = 'Copied';
      setTimeout(() => button.textContent = oldText, 1200);
    }});
  }});
</script>
</body>
</html>
"""
