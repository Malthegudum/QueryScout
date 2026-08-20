"""Deterministic dataset transformations exposed as MCP tools."""

from typing import Any

import pandas as pd

from queryscout import results


FILTER_OPERATORS = {
    "eq",
    "ne",
    "lt",
    "lte",
    "gt",
    "gte",
    "in",
    "not_in",
    "isna",
    "notna",
}

AGGREGATIONS = {
    "sum",
    "mean",
    "min",
    "max",
    "count",
}


def filter_result(
    result_id: str,
    column: str,
    operator: str,
    value: Any = None,
):
    """Filter a saved result using one deterministic condition."""
    dataframe, metadata = results.load_result(result_id)

    _require_columns(dataframe, [column])
    if operator not in FILTER_OPERATORS:
        raise ValueError(
            f"Unknown operator: {operator}. "
            f"Use one of {sorted(FILTER_OPERATORS)}."
        )

    if operator in {"in", "not_in"} and not isinstance(value, list):
        raise ValueError(f"{operator} requires a list value.")

    series = dataframe[column]
    if operator == "eq":
        mask = series == value
    elif operator == "ne":
        mask = series != value
    elif operator == "lt":
        mask = series < value
    elif operator == "lte":
        mask = series <= value
    elif operator == "gt":
        mask = series > value
    elif operator == "gte":
        mask = series >= value
    elif operator == "in":
        mask = series.isin(value)
    elif operator == "not_in":
        mask = ~series.isin(value)
    elif operator == "isna":
        mask = series.isna()
    else:
        mask = series.notna()

    output = dataframe.loc[mask].copy()
    pipeline = {
        "type": "filter",
        "input": metadata["pipeline"],
        "column": column,
        "operator": operator,
        "value": value,
    }

    new_id = results.save_result(
        title=f'{metadata["title"]} — filter',
        dataframe=output,
        pipeline=pipeline,
    )
    return results.result_summary(
        new_id,
        extra={
            "input_result_id": result_id,
            "input_rows": len(dataframe),
        },
    )


def select_columns(result_id: str, columns: list[str]):
    """Keep only selected columns from a saved result."""
    dataframe, metadata = results.load_result(result_id)
    _require_columns(dataframe, columns)

    output = dataframe.loc[:, columns].copy()
    pipeline = {
        "type": "select",
        "input": metadata["pipeline"],
        "columns": columns,
    }

    new_id = results.save_result(
        title=f'{metadata["title"]} — select',
        dataframe=output,
        pipeline=pipeline,
    )
    return results.result_summary(
        new_id,
        extra={"input_result_id": result_id},
    )


def group_by(
    result_id: str,
    by: list[str],
    aggregations: dict[str, str],
):
    """Group a saved result and aggregate selected columns."""
    if not by:
        raise ValueError("by must contain at least one column.")
    if not aggregations:
        raise ValueError("aggregations must not be empty.")

    dataframe, metadata = results.load_result(result_id)
    _require_columns(dataframe, by + list(aggregations))

    for function in aggregations.values():
        if function not in AGGREGATIONS:
            raise ValueError(
                f"Unknown aggregation: {function}. "
                f"Use one of {sorted(AGGREGATIONS)}."
            )

    output = (
        dataframe.groupby(by, as_index=False, dropna=False)
        .agg(aggregations)
        .sort_values(by, kind="stable")
        .reset_index(drop=True)
    )

    pipeline = {
        "type": "group_by",
        "input": metadata["pipeline"],
        "by": by,
        "aggregations": aggregations,
    }

    new_id = results.save_result(
        title=f'{metadata["title"]} — group by',
        dataframe=output,
        pipeline=pipeline,
    )
    return results.result_summary(
        new_id,
        extra={
            "input_result_id": result_id,
            "input_rows": len(dataframe),
        },
    )


def join_results(
    left_result_id: str,
    right_result_id: str,
    left_on: list[str],
    right_on: list[str] | None = None,
    how: str = "inner",
):
    """Join two saved results and return diagnostics with the preview."""
    if how not in {"inner", "left", "right", "outer"}:
        raise ValueError("how must be inner, left, right, or outer.")

    right_on = right_on or left_on
    if len(left_on) != len(right_on):
        raise ValueError("left_on and right_on must have the same length.")

    left, left_metadata = results.load_result(left_result_id)
    right, right_metadata = results.load_result(right_result_id)

    _require_columns(left, left_on)
    _require_columns(right, right_on)

    output = pd.merge(
        left,
        right,
        how=how,
        left_on=left_on,
        right_on=right_on,
        suffixes=("_left", "_right"),
        sort=False,
    )

    pipeline = {
        "type": "join",
        "left": left_metadata["pipeline"],
        "right": right_metadata["pipeline"],
        "left_on": left_on,
        "right_on": right_on,
        "how": how,
    }

    new_id = results.save_result(
        title=f'{left_metadata["title"]} + {right_metadata["title"]}',
        dataframe=output,
        pipeline=pipeline,
    )
    return results.result_summary(
        new_id,
        extra={
            "left_result_id": left_result_id,
            "right_result_id": right_result_id,
            "left_rows": len(left),
            "right_rows": len(right),
            "left_duplicate_key_rows": int(
                left.duplicated(subset=left_on, keep=False).sum()
            ),
            "right_duplicate_key_rows": int(
                right.duplicated(subset=right_on, keep=False).sum()
            ),
        },
    )


def _require_columns(dataframe: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"Unknown columns: {missing}")


def register(mcp) -> None:
    mcp.add_tool(
        filter_result,
        name="filter_result",
        description=(
            "Filter a QueryScout result. Inspect the returned row count, "
            "dtypes and preview before continuing."
        ),
    )
    mcp.add_tool(
        select_columns,
        name="select_columns",
        description="Keep selected columns from a QueryScout result.",
    )
    mcp.add_tool(
        group_by,
        name="group_by",
        description=(
            "Group and aggregate a QueryScout result. Supported aggregations "
            "are sum, mean, min, max and count."
        ),
    )
    mcp.add_tool(
        join_results,
        name="join_results",
        description=(
            "Join two QueryScout results. Inspect row counts, duplicate-key "
            "diagnostics and the preview before continuing."
        ),
    )
