"""Deterministic dataset transformations exposed as MCP tools."""

from numbers import Number
from typing import Any

import pandas as pd
from pandas.api.types import is_numeric_dtype

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

DERIVE_OPERATIONS = {
    "add",
    "subtract",
    "multiply",
    "divide",
}

TIME_CHANGE_OPERATIONS = {
    "lag",
    "difference",
    "pct_change",
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


def sort_result(
    result_id: str,
    by: list[str],
    ascending: bool | list[bool] = True,
):
    """Sort a saved result deterministically using a stable sort."""
    if not by:
        raise ValueError("by must contain at least one column.")

    dataframe, metadata = results.load_result(result_id)
    _require_columns(dataframe, by)

    if isinstance(ascending, list) and len(ascending) != len(by):
        raise ValueError("ascending must have the same length as by.")

    output = (
        dataframe.sort_values(
            by=by,
            ascending=ascending,
            kind="stable",
        )
        .reset_index(drop=True)
    )
    pipeline = {
        "type": "sort",
        "input": metadata["pipeline"],
        "by": by,
        "ascending": ascending,
    }

    new_id = results.save_result(
        title=f'{metadata["title"]} — sort',
        dataframe=output,
        pipeline=pipeline,
    )
    return results.result_summary(
        new_id,
        extra={"input_result_id": result_id},
    )


def derive_column(
    result_id: str,
    output_column: str,
    operation: str,
    left_column: str,
    right_column: str | None = None,
    right_value: float | int | None = None,
):
    """Create one numeric column using a restricted arithmetic operation."""
    if operation not in DERIVE_OPERATIONS:
        raise ValueError(
            f"Unknown operation: {operation}. "
            f"Use one of {sorted(DERIVE_OPERATIONS)}."
        )

    has_column = right_column is not None
    has_value = right_value is not None
    if has_column == has_value:
        raise ValueError("Provide exactly one of right_column or right_value.")

    dataframe, metadata = results.load_result(result_id)
    _require_columns(dataframe, [left_column])
    if output_column in dataframe.columns:
        raise ValueError(f"Output column already exists: {output_column!r}")

    if not is_numeric_dtype(dataframe[left_column]):
        raise ValueError(f"Column {left_column!r} must be numeric.")

    if right_column is not None:
        _require_columns(dataframe, [right_column])
        if not is_numeric_dtype(dataframe[right_column]):
            raise ValueError(f"Column {right_column!r} must be numeric.")
        right = dataframe[right_column]
        right_operand = {"type": "column", "value": right_column}
    else:
        if not isinstance(right_value, Number):
            raise ValueError("right_value must be numeric.")
        right = right_value
        right_operand = {"type": "constant", "value": right_value}

    left = dataframe[left_column]
    if operation == "add":
        derived = left + right
    elif operation == "subtract":
        derived = left - right
    elif operation == "multiply":
        derived = left * right
    else:
        derived = left / right

    output = dataframe.copy()
    output[output_column] = derived

    pipeline = {
        "type": "derive",
        "input": metadata["pipeline"],
        "output_column": output_column,
        "operation": operation,
        "left": {"type": "column", "value": left_column},
        "right": right_operand,
    }

    new_id = results.save_result(
        title=f'{metadata["title"]} — derive {output_column}',
        dataframe=output,
        pipeline=pipeline,
    )
    return results.result_summary(
        new_id,
        extra={"input_result_id": result_id},
    )


def time_change(
    result_id: str,
    column: str,
    output_column: str,
    operation: str,
    order_by: str,
    by: list[str] | None = None,
    periods: int = 1,
):
    """Compute a lag, difference or percent change within ordered groups."""
    if operation not in TIME_CHANGE_OPERATIONS:
        raise ValueError(
            f"Unknown operation: {operation}. "
            f"Use one of {sorted(TIME_CHANGE_OPERATIONS)}."
        )
    if periods < 1:
        raise ValueError("periods must be at least 1.")

    by = by or []
    dataframe, metadata = results.load_result(result_id)
    _require_columns(dataframe, by + [order_by, column])

    if output_column in dataframe.columns:
        raise ValueError(f"Output column already exists: {output_column!r}")
    if not is_numeric_dtype(dataframe[column]):
        raise ValueError(f"Column {column!r} must be numeric.")

    keys = by + [order_by]
    duplicate_rows = int(dataframe.duplicated(subset=keys, keep=False).sum())
    if duplicate_rows:
        raise ValueError(
            "Time-change keys are not unique: "
            f"{duplicate_rows} rows share the same {keys}. "
            "Filter or aggregate the data first."
        )

    output = (
        dataframe.sort_values(by=keys, kind="stable")
        .reset_index(drop=True)
        .copy()
    )

    if by:
        grouped = output.groupby(by, dropna=False, sort=False)[column]
        if operation == "lag":
            changed = grouped.shift(periods)
        elif operation == "difference":
            changed = grouped.diff(periods)
        else:
            changed = grouped.pct_change(periods=periods, fill_method=None)
    else:
        series = output[column]
        if operation == "lag":
            changed = series.shift(periods)
        elif operation == "difference":
            changed = series.diff(periods)
        else:
            changed = series.pct_change(periods=periods, fill_method=None)

    output[output_column] = changed

    pipeline = {
        "type": "time_change",
        "input": metadata["pipeline"],
        "column": column,
        "output_column": output_column,
        "operation": operation,
        "order_by": order_by,
        "by": by,
        "periods": periods,
    }

    new_id = results.save_result(
        title=f'{metadata["title"]} — {operation}',
        dataframe=output,
        pipeline=pipeline,
    )
    return results.result_summary(
        new_id,
        extra={
            "input_result_id": result_id,
            "duplicate_time_key_rows": duplicate_rows,
        },
    )


def pivot_result(
    result_id: str,
    index: list[str],
    columns: str,
    values: str,
):
    """Pivot a long result to wide form when pivot keys are unique."""
    if not index:
        raise ValueError("index must contain at least one column.")

    dataframe, metadata = results.load_result(result_id)
    _require_columns(dataframe, index + [columns, values])

    keys = index + [columns]
    duplicate_rows = int(dataframe.duplicated(subset=keys, keep=False).sum())
    if duplicate_rows:
        raise ValueError(
            "Pivot keys are not unique: "
            f"{duplicate_rows} rows share the same {keys}. "
            "Filter remaining dimensions or aggregate before pivoting."
        )

    output = dataframe.pivot(index=index, columns=columns, values=values).reset_index()
    output.columns.name = None
    output.columns = [str(column) for column in output.columns]

    pipeline = {
        "type": "pivot",
        "input": metadata["pipeline"],
        "index": index,
        "columns": columns,
        "values": values,
    }

    new_id = results.save_result(
        title=f'{metadata["title"]} — pivot',
        dataframe=output,
        pipeline=pipeline,
    )
    return results.result_summary(
        new_id,
        extra={
            "input_result_id": result_id,
            "duplicate_pivot_key_rows": duplicate_rows,
        },
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


def concat_results(result_ids: list[str]):
    """Concatenate compatible saved results row-wise."""
    if len(result_ids) < 2:
        raise ValueError("result_ids must contain at least two results.")

    loaded = [(*results.load_result(result_id), result_id) for result_id in result_ids]
    first_columns = list(loaded[0][0].columns)
    first_set = set(first_columns)

    dataframes = []
    input_rows = {}
    pipelines = []
    for dataframe, metadata, result_id in loaded:
        if set(dataframe.columns) != first_set:
            raise ValueError(
                "All concatenated results must contain the same columns. "
                f"Result {result_id!r} has {list(dataframe.columns)!r}; "
                f"expected {first_columns!r}."
            )
        dataframes.append(dataframe.loc[:, first_columns])
        input_rows[result_id] = len(dataframe)
        pipelines.append(metadata["pipeline"])

    output = pd.concat(dataframes, axis=0, ignore_index=True, sort=False)

    pipeline = {
        "type": "concat",
        "inputs": pipelines,
        "columns": first_columns,
    }

    new_id = results.save_result(
        title=f"Concatenated {len(result_ids)} results",
        dataframe=output,
        pipeline=pipeline,
    )
    return results.result_summary(
        new_id,
        extra={
            "input_result_ids": result_ids,
            "input_rows": input_rows,
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
        sort_result,
        name="sort_result",
        description=(
            "Sort a QueryScout result using one or more columns and a stable "
            "deterministic ordering."
        ),
    )
    mcp.add_tool(
        derive_column,
        name="derive_column",
        description=(
            "Create a numeric column using add, subtract, multiply or divide. "
            "The right operand must be either another column or a constant."
        ),
    )
    mcp.add_tool(
        time_change,
        name="time_change",
        description=(
            "Compute a lag, difference or percent change after deterministic "
            "sorting, optionally within groups. Time keys must be unique."
        ),
    )
    mcp.add_tool(
        pivot_result,
        name="pivot_result",
        description=(
            "Pivot a long QueryScout result to wide form. Pivot keys must be "
            "unique; filter or aggregate first if they are not."
        ),
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
    mcp.add_tool(
        concat_results,
        name="concat_results",
        description=(
            "Concatenate two or more QueryScout results row-wise. All inputs "
            "must contain the same set of columns."
        ),
    )
