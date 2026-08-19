# Statistics Denmark / StatBank

Use this source for official Danish statistics, including population, labour market, prices, businesses, public finance, national accounts, and other Statistics Denmark datasets.

## Workflow

1. Search for relevant StatBank tables with `dst_search_tables`.
2. Inspect promising tables with `dst_get_table_metadata`.
3. Identify the exact variable codes and allowed value codes from the metadata.
4. Call `dst_query_table` only after the metadata has been inspected.
5. Inspect the returned row count, columns, and preview.
6. If the result does not match the user's request, revise the variables and query again.

## Rules

- Never invent a StatBank table ID.
- Never invent variable codes or value codes.
- Always inspect table metadata before querying a table.
- Use the exact codes returned by StatBank metadata, not display labels unless they are also valid codes.
- Pay attention to units, geography, time, seasonal adjustment, prices, and other dimensions that materially change interpretation.
- Prefer the most specific table that answers the user's request.
