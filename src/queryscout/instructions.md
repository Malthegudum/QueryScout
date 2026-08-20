# QueryScout

QueryScout retrieves and transforms statistical data. The model chooses tools
and parameters, but QueryScout itself produces the canonical data and Python
reproduction code deterministically.

## Source workflow

1. Choose the source that best matches the request.
2. Call `enable_source` before using that source.
3. Follow the returned source instructions.
4. Inspect metadata before querying when the source requires it.
5. Run the source query.
6. Check row count, columns, dtypes and preview before continuing.

Do not guess source-specific identifiers, codes or query syntax.

## Transformations

Transform data one step at a time using QueryScout tools:

- `filter_result`
- `select_columns`
- `group_by`
- `join_results`

After every transformation, inspect the returned row count, columns, dtypes and
preview. For joins, also inspect the input row counts and duplicate-key
diagnostics. If a step looks wrong, correct that step before continuing.

The model may inspect data and choose transformations, but it must not create or
rewrite canonical output rows itself.

## Results

Every query or transformation returns a `result_id` and `result_url`.

The result page contains:

- the canonical `data.csv`;
- a deterministic `query.py` that reproduces the complete pipeline;
- a larger preview.

Treat these files as canonical. Do not regenerate the dataset or Python code in
the model response. Once the final preview has been validated, give the user the
`result_url`.
