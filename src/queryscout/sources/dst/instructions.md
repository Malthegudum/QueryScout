# Statistics Denmark (DST / StatBank)

Use this source for official Danish statistics from Statistics Denmark.

Mandatory workflow:
1. Use `get_dst_subjects` when the relevant table is not known.
2. Use `get_dst_tables` to find candidate tables.
3. Use `get_dst_table_metadata` before every query.
4. Use only table, variable and value codes verified from metadata.
5. Run the smallest query that answers the request.
6. Inspect row count, columns, dtypes and preview after the query.
7. If the result is wrong or unclear, revise the query before transforming it.

Useful DST value syntax:
- `"*"` selects all values.
- `"(1)"` selects the newest value where supported.
- Ordered periods can use one range expression such as `">=2020K1<=2024K4"`.

Never invent DST identifiers or codes. Pay particular attention to measures,
units, geography and time periods.
