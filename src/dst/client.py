"""Deterministic client for the Statistics Denmark StatBank API."""

from io import StringIO
from pprint import pformat

import pandas as pd
import requests

from models import RequestSpec


class DSTClient:
    """Handle DST metadata lookup, request construction and response parsing."""

    BASE_URL = "https://api.statbank.dk/v1"

    def subjects(self):
        """Return the available Statistics Denmark subject areas."""
        response = requests.get(f"{self.BASE_URL}/subjects")
        response.raise_for_status()
        return response.json()

    def tables(self, subject: str | None = None):
        """Return available DST tables, optionally filtered by subject."""
        params = {"subjects": subject} if subject else {}

        response = requests.get(
            f"{self.BASE_URL}/tables",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def table(self, table_id: str):
        """Return metadata for a single DST table."""
        response = requests.get(
            f"{self.BASE_URL}/tableinfo",
            params={"id": table_id},
        )
        response.raise_for_status()
        return response.json()

    def build_request(
        self,
        table_id: str,
        variables: dict[str, list[str]],
    ) -> RequestSpec:
        """Translate DST-specific arguments into a portable HTTP request."""
        # StatBank expects variables as a list of objects rather than a mapping.
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
        """Execute a tested-style request and parse the DST CSV into a DataFrame."""
        # requests.request lets the shared RequestSpec carry the HTTP method.
        response = requests.request(
            method=request.method,
            url=request.url,
            params=request.params,
            json=request.json,
            headers=request.headers,
        )
        response.raise_for_status()

        # StatBank's CSV response uses semicolons as separators.
        return pd.read_csv(
            StringIO(response.text),
            sep=";",
        )

    def to_python(self, request: RequestSpec) -> str:
        """Generate standalone Python for repeating this request and parsing it."""
        # Remove unused optional fields and pretty-print a valid Python literal.
        request_dict = request.model_dump(exclude_none=True)
        request_literal = pformat(
            request_dict,
            width=88,
            sort_dicts=False,
        )

        # The generated code intentionally imports nothing from QueryScout.
        return f'''from io import StringIO

import pandas as pd
import requests


request = {request_literal}

response = requests.request(**request)
response.raise_for_status()

data = pd.read_csv(
    StringIO(response.text),
    sep=";",
)

print(data)
'''
