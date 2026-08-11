from .models import DSTQuery


def query_to_python(query: DSTQuery) -> str:
    """Generate Python code for running a DSTQuery again."""

    query_json = query.model_dump_json(indent=4)

    return f'''from dst.client import DSTClient
from dst.models import DSTQuery


query = DSTQuery.model_validate_json(
    """{query_json}"""
)

client = DSTClient()
data = client.execute(query)

print(data)
'''