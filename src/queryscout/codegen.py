"""Deterministic Python generation for QueryScout pipelines."""

from pprint import pformat
from typing import Any


def generate_python(pipeline: dict[str, Any]) -> str:
    """Generate standalone Python that reproduces a saved result."""
    lines = [
        "from io import StringIO",
        "",
        "import pandas as pd",
        "import requests",
        "",
    ]
    state = {"next_id": 1}
    final_df = _emit_step(pipeline, lines, state)
    lines.extend([
        "",
        f"df = {final_df}",
        'df.to_csv("data.csv", index=False, lineterminator="\\n")',
        "",
    ])
    return "\n".join(lines)


def _new_name(state: dict[str, int], prefix: str) -> str:
    number = state["next_id"]
    state["next_id"] += 1
    return f"{prefix}_{number}"


def _emit_step(
    step: dict[str, Any],
    lines: list[str],
    state: dict[str, int],
) -> str:
    step_type = step["type"]

    if step_type == "source":
        return _emit_source(step, lines, state)

    if step_type == "join":
        left = _emit_step(step["left"], lines, state)
        right = _emit_step(step["right"], lines, state)
        output = _new_name(state, "df")
        lines.extend([
            "",
            f"{output} = pd.merge(",
            f"    {left},",
            f"    {right},",
            f"    how={step['how']!r},",
            f"    left_on={step['left_on']!r},",
            f"    right_on={step['right_on']!r},",
            '    suffixes=("_left", "_right"),',
            "    sort=False,",
            ")",
        ])
        return output

    if step_type == "concat":
        inputs = [_emit_step(item, lines, state) for item in step["inputs"]]
        output = _new_name(state, "df")
        columns = step["columns"]
        aligned = ", ".join(
            f"{input_df}.loc[:, {columns!r}]" for input_df in inputs
        )
        lines.extend([
            "",
            f"{output} = pd.concat(",
            f"    [{aligned}],",
            "    axis=0,",
            "    ignore_index=True,",
            "    sort=False,",
            ")",
        ])
        return output

    input_df = _emit_step(step["input"], lines, state)
    output = _new_name(state, "df")

    if step_type == "filter":
        column = step["column"]
        operator = step["operator"]
        value = step.get("value")
        expression = _filter_expression(input_df, column, operator, value)
        lines.extend(["", f"{output} = {input_df}.loc[{expression}].copy()"])
        return output

    if step_type == "select":
        lines.extend([
            "",
            f"{output} = {input_df}.loc[:, {step['columns']!r}].copy()",
        ])
        return output

    if step_type == "sort":
        lines.extend([
            "",
            f"{output} = (",
            f"    {input_df}.sort_values(",
            f"        by={step['by']!r},",
            f"        ascending={step['ascending']!r},",
            '        kind="stable",',
            "    )",
            "    .reset_index(drop=True)",
            ")",
        ])
        return output

    if step_type == "derive":
        left = _operand_expression(input_df, step["left"])
        right = _operand_expression(input_df, step["right"])
        operators = {
            "add": "+",
            "subtract": "-",
            "multiply": "*",
            "divide": "/",
        }
        symbol = operators[step["operation"]]
        lines.extend([
            "",
            f"{output} = {input_df}.copy()",
            f"{output}[{step['output_column']!r}] = {left} {symbol} {right}",
        ])
        return output

    if step_type == "time_change":
        keys = step["by"] + [step["order_by"]]
        lines.extend([
            "",
            f"{output} = (",
            f"    {input_df}.sort_values(by={keys!r}, kind='stable')",
            "    .reset_index(drop=True)",
            "    .copy()",
            ")",
        ])
        periods = step["periods"]
        column = step["column"]
        if step["by"]:
            grouped = _new_name(state, "grouped")
            lines.extend([
                f"{grouped} = {output}.groupby(",
                f"    {step['by']!r},",
                "    dropna=False,",
                "    sort=False,",
                f")[{column!r}]",
            ])
            series = grouped
        else:
            series = f"{output}[{column!r}]"

        if step["operation"] == "lag":
            expression = f"{series}.shift({periods})"
        elif step["operation"] == "difference":
            expression = f"{series}.diff({periods})"
        else:
            expression = f"{series}.pct_change(periods={periods}, fill_method=None)"

        lines.append(f"{output}[{step['output_column']!r}] = {expression}")
        return output

    if step_type == "pivot":
        lines.extend([
            "",
            f"{output} = {input_df}.pivot(",
            f"    index={step['index']!r},",
            f"    columns={step['columns']!r},",
            f"    values={step['values']!r},",
            ").reset_index()",
            f"{output}.columns.name = None",
            f"{output}.columns = [str(column) for column in {output}.columns]",
        ])
        return output

    if step_type == "group_by":
        by = step["by"]
        aggregations = step["aggregations"]
        lines.extend([
            "",
            f"{output} = (",
            f"    {input_df}.groupby({by!r}, as_index=False, dropna=False)",
            f"    .agg({aggregations!r})",
            f"    .sort_values({by!r}, kind='stable')",
            "    .reset_index(drop=True)",
            ")",
        ])
        return output

    raise ValueError(f"Unknown pipeline step: {step_type}")


def _emit_source(
    step: dict[str, Any],
    lines: list[str],
    state: dict[str, int],
) -> str:
    source = step["source"]
    parser = step.get("parser")

    if parser is None:
        if source == "dst":
            parser = {"type": "csv", "kwargs": {"sep": ";"}}
        else:
            raise ValueError(
                f"Source {source!r} does not define a reproducible parser."
            )

    if parser.get("type") != "csv":
        raise ValueError(f"Unsupported source parser: {parser.get('type')!r}")

    request_name = _new_name(state, "request")
    response_name = _new_name(state, "response")
    df_name = _new_name(state, "df")
    request = pformat(step["request"], width=88, sort_dicts=False)
    parser_kwargs = pformat(parser.get("kwargs", {}), width=88, sort_dicts=False)

    lines.extend([
        f"{request_name} = {request}",
        f"{response_name} = requests.request(**{request_name}, timeout=60)",
        f"{response_name}.raise_for_status()",
        f"{df_name} = pd.read_csv(StringIO({response_name}.text), **{parser_kwargs})",
    ])
    return df_name


def _operand_expression(df: str, operand: dict[str, Any]) -> str:
    if operand["type"] == "column":
        return f"{df}[{operand['value']!r}]"
    if operand["type"] == "constant":
        return repr(operand["value"])
    raise ValueError(f"Unknown derive operand: {operand['type']!r}")


def _filter_expression(
    df: str,
    column: str,
    operator: str,
    value: Any,
) -> str:
    series = f"{df}[{column!r}]"
    comparisons = {
        "eq": "==",
        "ne": "!=",
        "lt": "<",
        "lte": "<=",
        "gt": ">",
        "gte": ">=",
    }

    if operator in comparisons:
        return f"{series} {comparisons[operator]} {value!r}"
    if operator == "in":
        return f"{series}.isin({value!r})"
    if operator == "not_in":
        return f"~{series}.isin({value!r})"
    if operator == "isna":
        return f"{series}.isna()"
    if operator == "notna":
        return f"{series}.notna()"

    raise ValueError(f"Unknown filter operator: {operator}")
