# QueryScout

QueryScout provides tools for statistical data sources. All source tools are visible from server startup for client compatibility, but they must not be used before the relevant source has been enabled.

## Mandatory workflow

1. Read the list of available sources in the server instructions and choose the source that best matches the user's request.
2. Before calling any source-specific tool, call `enable_source` with that source ID.
3. Read the returned source instructions completely.
4. Follow the source-specific workflow and tool order exactly.
5. Only use tools belonging to sources whose instructions have been loaded with `enable_source`.
6. If you need to switch to another source, call `enable_source` for that source before using any of its tools.

## Tool discipline

- Tool visibility does not mean a tool should be called immediately.
- Do not skip `enable_source` even if the desired source-specific tools are already visible.
- Do not guess source-specific identifiers, codes, parameters, or query syntax. Follow the enabled source's instructions and inspect metadata where required.
- Do not skip discovery or metadata steps unless the enabled source's instructions explicitly allow it.
- Prefer a single appropriate source when it can answer the question. Do not mix sources unnecessarily.
- After retrieving data, verify that the result matches the user's requested concepts, dimensions, geography, units, and time period before answering.

## Example

For a question that requires Statistics Denmark:

1. Call `enable_source("dst")`.
2. Read and follow the returned DST instructions.
3. Only then call the DST tools in the order described there.
