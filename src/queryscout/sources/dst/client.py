"""Statistics Denmark API client."""

from io import StringIO

import pandas as pd
import requests


BASE_URL = "https://api.statbank.dk/v1"


def subjects():
    response = requests.get(f"{BASE_URL}/subjects", timeout=30)
    response.raise_for_status()
    return response.json()


def tables(subject: str | None = None):
    params = {"subjects": subject} if subject else None
    response = requests.get(f"{BASE_URL}/tables", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def table(table_id: str):
    response = requests.get(
        f"{BASE_URL}/tableinfo",
        params={"id": table_id},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def build_request(
    table_id: str,
    variables: dict[str, list[str]],
) -> dict:
    return {
        "method": "POST",
        "url": f"{BASE_URL}/data",
        "json": {
            "table": table_id,
            "format": "CSV",
            "variables": [
                {"code": code, "values": values}
                for code, values in variables.items()
            ],
        },
    }


def query(
    table_id: str,
    variables: dict[str, list[str]],
) -> tuple[dict, pd.DataFrame]:
    request = build_request(table_id, variables)
    response = requests.request(**request, timeout=60)
    response.raise_for_status()

    dataframe = pd.read_csv(StringIO(response.text), sep=";")
    return request, dataframe
