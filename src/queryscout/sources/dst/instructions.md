# Statistics Denmark (DST / StatBank)

Use this source for official Danish statistics from Statistics Denmark's StatBank.

## Mandatory workflow

Follow this order unless the user already gives an exact, verified table ID and you still verify its metadata before querying:

1. Use `get_dst_subjects` to identify the relevant subject area when the table is not already known.
2. Use `get_dst_tables(subject)` to inspect the available tables in the relevant subject.
3. Choose the table whose title, subject and scope best match the user's question.
4. Use `get_dst_table_metadata(table_id)` before querying.
5. From the metadata, identify the exact variable codes and allowed value codes.
6. Construct the smallest query that answers the user's question.
7. Use `run_dst_query(table_id, variables)` with only verified codes and supported DST value syntax.
8. Inspect the returned columns, row count and preview. If the result does not match the intended concepts, units, geography or periods, revise the query before answering.

Do not jump directly to `run_dst_query` from the user's wording.

## Discovery rules

- Never invent subject IDs, table IDs, variable codes or value codes.
- Do not guess a table ID because its name sounds plausible.
- When several tables look relevant, compare their metadata before deciding.
- Prefer the most specific table that directly answers the question.
- Prefer current/maintained tables when equivalent alternatives exist.
- Use the table metadata as the source of truth for dimension names, codes and available values.

## Building a good query

Keep queries deliberate and compact:

- Select only dimensions and values needed for the answer.
- Avoid `"*"` on several large dimensions at once unless the user truly needs the full cross-product.
- For dimensions such as geography, industry, sex, age, unit or measure, inspect the metadata and choose the exact codes rather than relying on labels from memory.
- Pay particular attention to units and measures. Two values with similar labels can represent different quantities, indices, prices, percentages or seasonal adjustments.
- For totals, use an official total value from the metadata when one exists rather than manually summing categories unless aggregation is explicitly required.
- For time series, prefer DST's range/latest-value syntax when it represents the requested period cleanly.
- If a first query is too broad, narrow it and query again instead of trying to reason from an unwieldy result.

## DST value syntax

DST supports special value selectors in many StatBank queries:

- `"*"` selects all values for a variable.
- Wildcards can match parts of value codes when supported, for example `"*K1"`.
- Ordered values such as periods can use range syntax, for example `">=2020K1<=2024K4"`.
- A bounded range must be written as **one value**. Do not write:
  `[">=2020K1", "<=2024K4"]`
  because DST interprets those as separate selections rather than one interval.
- `"(1)"` selects the newest value/period where supported.
- If no time value is selected, DST may default to the newest period depending on the endpoint/table. Do not rely on that behavior when the user requested a specific period.

Only use special syntax where it is meaningful for the selected variable and compatible with that table's values.

## Query examples

A query for all values of one dimension:

```json
{
  "Tid": ["2024"],
  "OMRÅDE": ["*"]
}
```

A bounded quarterly time range:

```json
{
  "Tid": [">=2020K1<=2024K4"]
}
```

The newest available period where supported:

```json
{
  "Tid": ["(1)"]
}
```

These are syntax examples only. Always use the actual variable codes from `get_dst_table_metadata` for the chosen table.

## Validation after querying

Before using the result in the final answer, verify:

- the table is the intended table;
- the requested geography/population/category is represented correctly;
- the measure and unit are correct;
- the time period is correct;
- the result is not accidentally a subtotal, index or seasonally adjusted series when the user asked for something else;
- the row count and preview are plausible for the requested selection.

If any of these are unclear, inspect metadata again or revise the query.
