"""Storage and result pages for QueryScout outputs."""

from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from typing import Any

import pandas as pd

from queryscout import codegen


RESULTS_DIR = Path.home() / ".queryscout" / "results"
RESULT_BASE_URL = "http://127.0.0.1:8000"
_RESULT_ID = re.compile(r"[0-9a-f]{16}")


def save_result(
    *,
    title: str,
    dataframe: pd.DataFrame,
    pipeline: dict[str, Any],
) -> str:
    """Save a deterministic dataset and its reproduction pipeline."""
    csv_bytes = dataframe.to_csv(
        index=False,
        lineterminator="\n",
    ).encode("utf-8")

    canonical_pipeline = json.dumps(
        pipeline,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    result_id = sha256(
        canonical_pipeline + b"\0" + csv_bytes
    ).hexdigest()[:16]

    output_dir = RESULTS_DIR / result_id
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "title": title,
        "row_count": len(dataframe),
        "columns": [str(column) for column in dataframe.columns],
        "dtypes": {
            str(column): str(dtype)
            for column, dtype in dataframe.dtypes.items()
        },
        "preview": _preview(dataframe, 20),
        "pipeline": pipeline,
    }

    (output_dir / "data.csv").write_bytes(csv_bytes)
    (output_dir / "query.py").write_text(
        codegen.generate_python(pipeline),
        encoding="utf-8",
    )
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return result_id


def load_result(result_id: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load a stored dataset and its metadata."""
    dataframe = pd.read_csv(result_file(result_id, "data.csv"))
    return dataframe, load_metadata(result_id)


def load_metadata(result_id: str) -> dict[str, Any]:
    return json.loads(
        result_file(result_id, "metadata.json").read_text(encoding="utf-8")
    )


def result_summary(
    result_id: str,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the compact result shown to the model."""
    metadata = load_metadata(result_id)
    summary = {
        "result_id": result_id,
        "row_count": metadata["row_count"],
        "columns": metadata["columns"],
        "dtypes": metadata["dtypes"],
        "preview": metadata["preview"][:10],
        "result_url": result_url(result_id),
    }
    if extra:
        summary.update(extra)
    return summary


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
    if filename not in {"data.csv", "query.py", "metadata.json"}:
        raise FileNotFoundError(filename)

    path = _result_dir(result_id) / filename
    if not path.is_file():
        raise FileNotFoundError(filename)

    return path


def _preview(dataframe: pd.DataFrame, rows: int) -> list[dict[str, Any]]:
    text = dataframe.head(rows).to_json(
        orient="records",
        date_format="iso",
        force_ascii=False,
    )
    return json.loads(text)


def render_result_page(result_id: str) -> str:
    """Render a stored result as a small standalone HTML page."""
    metadata = load_metadata(result_id)
    code = result_file(result_id, "query.py").read_text(encoding="utf-8")

    columns = metadata["columns"]
    preview = metadata["preview"]

    headers = "".join(
        f"<th>{escape(str(column))}</th>"
        for column in columns
    )
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{escape(str(row.get(column, '')))}</td>"
            for column in columns
        )
        + "</tr>"
        for row in preview
    )

    table = (
        "<p>No rows.</p>"
        if not preview
        else f"<table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table>"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(metadata["title"])}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: 32px auto; padding: 0 20px; }}
    a {{ margin-right: 12px; }}
    .table {{ overflow-x: auto; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border-bottom: 1px solid #ddd; padding: 8px; text-align: left; white-space: nowrap; }}
    pre {{ overflow-x: auto; padding: 16px; background: #f5f5f5; }}
  </style>
</head>
<body>
  <h1>{escape(metadata["title"])}</h1>
  <p>{metadata["row_count"]:,} rows · {len(columns)} columns</p>
  <p>
    <a href="/results/{result_id}/data.csv">Download CSV</a>
    <a href="/results/{result_id}/query.py">Download Python</a>
  </p>

  <h2>Preview</h2>
  <p>Showing up to 20 rows.</p>
  <div class="table">{table}</div>

  <h2>Python</h2>
  <pre><code>{escape(code)}</code></pre>
</body>
</html>
"""
