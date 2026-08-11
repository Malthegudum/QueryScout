from src.dst.models import DSTQuery
from src.dst.tools import run_dst_query


query = DSTQuery(
    table_id="FOLK1A",
    variables={
        "OMRÅDE": ["000"],
        "Tid": ["2024K1"],
    },
)

result = run_dst_query(query)

print(result)