"""Statistics Denmark API client."""

from io import StringIO
import csv
from pprint import pformat

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
    payload = {
        "table": table_id,
        "format": "CSV",
        "variables": [
            {"code": code, "values": values}
            for code, values in variables.items()
        ],
    }
    return {
        "method": "POST",
        "url": f"{BASE_URL}/data",
        "json": payload,
    }


def query(table_id: str, variables: dict[str, list[str]]):
    request = build_request(table_id, variables)
    response = requests.request(**request, timeout=60)
    response.raise_for_status()

    rows = list(csv.DictReader(StringIO(response.text), delimiter=";"))
    return request, response.content, rows


def to_python(request: dict) -> str:
    """Generate standalone Python code from the exact HTTP request."""
    request_literal = pformat(request, width=88, sort_dicts=False)
    return f'''import requests

request = {request_literal}

response = requests.request(**request)
response.raise_for_status()

with open("data.csv", "wb") as file:
    file.write(response.content)
'''
