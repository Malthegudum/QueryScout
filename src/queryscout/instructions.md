# QueryScout

QueryScout provides tools for retrieving official statistical data from multiple APIs.

## General workflow

1. Choose the source that best matches the user's request.
2. Follow the source-specific instructions for that source.
3. Discover the relevant dataset or table before querying it.
4. Inspect metadata before constructing a query.
5. Use only identifiers, dimensions, variables, and value codes verified from source metadata.
6. Run the query and inspect the returned row count, columns, and preview.
7. Revise the query if the result does not match the user's request.

## General rules

- Never invent dataset IDs, table IDs, dimension codes, variable codes, or value codes.
- Do not guess a material filter or dimension when it changes the meaning of the result.
- Prefer official source metadata over assumptions.
- Keep tool calls focused: retrieve enough data to answer the request without unnecessarily large results.
- When possible, preserve the returned request and reproducible code so the result can be retrieved again without an LLM.
