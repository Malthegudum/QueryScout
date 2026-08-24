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
    if source != "dst":
        raise ValueError(f"Unsupported source in code generation: {source}")

    request_name = _new_name(state, "request")
    response_name = _new_name(state, "response")
    df_name = _new_name(state, "df")
    request = pformat(step["request"], width=88, sort_dicts=False)

    lines.extend([
        f"{request_name} = {request}",
        f"{response_name} = requests.request(**{request_name}, timeout=60)",
        f"{response_name}.raise_for_status()",
        f'{df_name} = pd.read_csv(StringIO({response_name}.text), sep=";")',
    ])
    return df_name


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
