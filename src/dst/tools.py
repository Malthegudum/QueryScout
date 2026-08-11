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
    """Run a DSTQuery and return a compact preview.

    Inspect the result before deciding that the query is correct.
    """
    rows = client.execute(query)

    return {
        "query": query.model_dump(),
        "row_count": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "preview": rows[:10],
    }