# Statistics Denmark

Use this source for official Danish statistics from StatBank Denmark.

Workflow:
1. Use `get_dst_subjects` to identify a relevant subject area when the table is not already known.
2. Use `get_dst_tables` with the relevant subject ID to inspect available tables.
3. Use `get_dst_table_metadata` for the selected table.
4. Identify the exact variable codes and allowed value codes from the metadata.
5. Use `run_dst_query` with only verified codes.
6. Inspect the result and revise the query if needed.

Rules:
- Never invent subject IDs, table IDs, variable codes, or value codes.
- Do not guess a table from the user's wording alone; inspect the available subjects/tables first when necessary.
- Always inspect table metadata before querying.
- Prefer the most specific table that answers the user's request.
