# Eurostat

Use this source for official European statistics from Eurostat.

Mandatory workflow:
1. Use `search_eurostat_datasets` when the relevant dataset code is not known.
2. Use `get_eurostat_dataset_metadata` before every query.
3. Use only dataset, dimension and value codes verified from metadata.
4. If a dimension's value preview is truncated, use `get_eurostat_dimension_values`
   to find the required code before querying.
5. Pay particular attention to frequency, unit, measure, geography and time.
6. Use `start_period` and `end_period` for time ranges; do not put `TIME_PERIOD`
   in the `dimensions` argument.
7. Run the smallest query that answers the request.
8. Inspect row count, columns, dtypes and preview after the query.
9. If the result is wrong or unclear, revise the query before transforming it.

Eurostat dimension codes and values are case-insensitive in the SDMX API, but use
the codes exactly as returned by QueryScout where possible.

Never invent Eurostat dataset, dimension or value codes.
