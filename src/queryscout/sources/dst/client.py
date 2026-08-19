"""Deterministic client for the Statistics Denmark StatBank API."""

from io import StringIO
from pprint import pformat
from typing import Any

import pandas as pd
import requests

from ...models import RequestSpec


class DSTClient:
    """Small deterministic wrapper around the StatBank API."""

    BASE_URL = "https://api.statbank.dk/v1"

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def subjects(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.BASE_URL}/subjects",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def tables(self, subject: str | None = None) -> list[dict[str, Any]]:
        params = {"subjects": subject} if subject else {}
        response = requests.get(
            f"{self.BASE_URL}/tables",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def table(self, table_id: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.BASE_URL}/tableinfo",
            params={"id": table_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def build_request(
        self,
        table_id: str,
        variables: dict[str, list[str]],
    ) -> RequestSpec:
        request_variables = [
            {"code": code, "values": values}
            for code, values in variables.items()
        ]
        return RequestSpec(
            method="POST",
            url=f"{self.BASE_URL}/data",
            json={
                "table": table_id,
                "format": "CSV",
                "variables": request_variables,
            },
        )

    def execute(self, request: RequestSpec) -> pd.DataFrame:
        response = requests.request(
            method=request.method,
            url=request.url,
            params=request.params,
            json=request.json,
            headers=request.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text), sep=";")

    def to_python(self, request: RequestSpec) -> str:
        request_dict = request.model_dump(exclude_none=True)
        request_literal = pformat(request_dict, width=88, sort_dicts=False)
        return f"""from io import StringIO

import pandas as pd
import requests

request = {request_literal}
response = requests.request(**request, timeout=30)
response.raise_for_status()
data = pd.read_csv(StringIO(response.text), sep=";")
print(data)
"""
