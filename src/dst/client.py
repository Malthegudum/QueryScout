import csv
from io import StringIO

import requests

from .models import DSTQuery


class DSTClient:
    BASE_URL = "https://api.statbank.dk/v1"

    def subjects(self):
        response = requests.get(f"{self.BASE_URL}/subjects")
        response.raise_for_status()
        return response.json()

    def tables(self, subject: str | None = None):
        params = {"subjects": subject} if subject else {}

        response = requests.get(
            f"{self.BASE_URL}/tables",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def table(self, table_id: str):
        response = requests.get(
            f"{self.BASE_URL}/tableinfo",
            params={"id": table_id},
        )
        response.raise_for_status()
        return response.json()

    def execute(self, query: DSTQuery):
        variables = [
            {"code": code, "values": values}
            for code, values in query.variables.items()
        ]

        response = requests.post(
            f"{self.BASE_URL}/data",
            json={
                "table": query.table_id,
                "format": "CSV",
                "variables": variables,
            },
        )
        response.raise_for_status()

        return list(
            csv.DictReader(
                StringIO(response.text),
                delimiter=";",
            )
        )