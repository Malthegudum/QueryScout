import json

from .client import DSTClient
from .models import DSTQuery


client = DSTClient()


def get_dst_subjects():
    """Get subject areas from Statistics Denmark."""
    return client.subjects()


def get_dst_tables(subject: str | None = None):
    """Get Statistics Denmark tables.

    Args:
        subject: Optional DST subject code.
    """
    return client.tables(subject)


def get_dst_table_metadata(table_id: str):
    """Get metadata for a DST table.

    Returns variables and valid values for the table.
    Always inspect this before constructing a DSTQuery.
    """
    return client.table(table_id)


def run_dst_query(query: DSTQuery):
    """Run a DSTQuery and return the tested HTTP request, standalone code and a preview."""
    request = client.build_request(query)
    data = client.execute(request)

    preview = json.loads(
        data.head(10).to_json(
            orient="records",
            force_ascii=False,
        )
    )

    return {
        "source": "dst",
        "request": request.model_dump(exclude_none=True),
        "code": client.to_python(request),
        "row_count": len(data),
        "columns": data.columns.tolist(),
        "preview": preview,
    }
