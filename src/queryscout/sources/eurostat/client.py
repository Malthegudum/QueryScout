"""Eurostat API client."""

from functools import lru_cache
from io import StringIO
import xml.etree.ElementTree as ET

import pandas as pd
import requests


CATALOGUE_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/catalogue/toc/txt"
)
STRUCTURE_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/"
    "dataflow/ESTAT/{dataset_code}/1.0"
)
DATA_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0/"
    "data/dataflow/ESTAT/{dataset_code}/1.0"
)
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
VALUE_PREVIEW_LIMIT = 50


@lru_cache(maxsize=1)
def _catalogue() -> pd.DataFrame:
    response = requests.get(
        CATALOGUE_URL,
        params={"lang": "en"},
        timeout=30,
    )
    response.raise_for_status()
    return pd.read_csv(
        StringIO(response.text),
        sep="\t",
        dtype=str,
    ).fillna("")


def search_datasets(query: str, limit: int = 20) -> list[dict]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    catalogue = _catalogue()
    datasets = catalogue.loc[
        catalogue["type"].str.casefold() == "dataset"
    ].copy()

    terms = query.casefold().split()

    def score(row) -> tuple[int, int, int, str]:
        code = row["code"].strip().casefold()
        title = row["title"].strip().casefold()
        text = f"{code} {title}"
        matches = sum(term in text for term in terms)
        exact_code = int(code == query.strip().casefold())
        title_prefix = int(title.startswith(query.strip().casefold()))
        return exact_code, matches, title_prefix, title

    ranked = [
        (score(row), row)
        for _, row in datasets.iterrows()
        if any(term in f"{row['code']} {row['title']}".casefold() for term in terms)
    ]
    ranked.sort(key=lambda item: (-item[0][0], -item[0][1], -item[0][2], item[0][3]))

    return [
        {
            "code": row["code"].strip(),
            "title": row["title"].strip(),
            "last_update": row["last update of data"].strip(),
            "data_start": row["data start"].strip(),
            "data_end": row["data end"].strip(),
            "values": row["values"].strip(),
        }
        for _, row in ranked[:limit]
    ]


def dataset_metadata(dataset_code: str) -> dict:
    metadata = _parsed_metadata(dataset_code)
    return {
        "dataset_code": metadata["dataset_code"],
        "title": metadata["title"],
        "last_update": metadata["last_update"],
        "data_start": metadata["data_start"],
        "data_end": metadata["data_end"],
        "observation_count": metadata["observation_count"],
        "dimensions": [
            {
                "code": dimension["code"],
                "label": dimension["label"],
                "value_count": len(dimension["values"]),
                "values_preview": dimension["values"][:VALUE_PREVIEW_LIMIT],
                "values_truncated": len(dimension["values"]) > VALUE_PREVIEW_LIMIT,
            }
            for dimension in metadata["dimensions"]
        ],
        "time_dimension": "TIME_PERIOD",
        "measure": "OBS_VALUE",
    }


def dimension_values(
    dataset_code: str,
    dimension: str,
    query: str | None = None,
    limit: int = 100,
) -> dict:
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")

    metadata = _parsed_metadata(dataset_code)
    dimension_key = dimension.casefold()
    item = next(
        (
            candidate
            for candidate in metadata["dimensions"]
            if candidate["code"].casefold() == dimension_key
        ),
        None,
    )
    if item is None:
        valid = ", ".join(d["code"] for d in metadata["dimensions"])
        raise ValueError(f"Unknown dimension {dimension!r}. Valid dimensions: {valid}")

    values = item["values"]
    if query:
        terms = query.casefold().split()
        values = [
            value
            for value in values
            if all(
                term in f"{value['code']} {value['label']}".casefold()
                for term in terms
            )
        ]

    return {
        "dataset_code": metadata["dataset_code"],
        "dimension": item["code"],
        "label": item["label"],
        "match_count": len(values),
        "values": values[:limit],
        "truncated": len(values) > limit,
    }


def build_request(
    dataset_code: str,
    dimensions: dict[str, list[str]],
    start_period: str | None = None,
    end_period: str | None = None,
) -> dict:
    params: dict[str, str] = {
        "format": "csvdata",
        "formatVersion": "2.0",
        "labels": "id",
        "compress": "false",
    }

    for dimension, values in dimensions.items():
        if dimension.casefold() == "time_period":
            raise ValueError(
                "Use start_period/end_period instead of TIME_PERIOD in dimensions."
            )
        if not values:
            raise ValueError(f"Dimension {dimension!r} has no selected values.")
        params[f"c[{dimension}]"] = ",".join(values)

    time_filters = []
    if start_period:
        time_filters.append(f"ge:{start_period}")
    if end_period:
        time_filters.append(f"le:{end_period}")
    if time_filters:
        params["c[TIME_PERIOD]"] = "+".join(time_filters)

    return {
        "method": "GET",
        "url": DATA_URL.format(dataset_code=dataset_code.upper()),
        "params": params,
    }


def query(
    dataset_code: str,
    dimensions: dict[str, list[str]],
    start_period: str | None = None,
    end_period: str | None = None,
) -> tuple[dict, pd.DataFrame]:
    request = build_request(
        dataset_code,
        dimensions,
        start_period=start_period,
        end_period=end_period,
    )
    response = requests.request(**request, timeout=60)
    response.raise_for_status()

    dataframe = pd.read_csv(StringIO(response.text))
    return request, dataframe


@lru_cache(maxsize=128)
def _parsed_metadata(dataset_code: str) -> dict:
    normalized_code = dataset_code.strip().upper()
    if not normalized_code:
        raise ValueError("dataset_code must not be empty")

    catalogue_entry = _catalogue_entry(normalized_code)

    response = requests.get(
        STRUCTURE_URL.format(dataset_code=normalized_code),
        params={
            "references": "descendants",
            "detail": "referencepartial",
        },
        timeout=60,
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    data_structure = _first(root, "DataStructure")
    if data_structure is None:
        raise ValueError(f"No data structure returned for {normalized_code}")

    concept_labels = _concept_labels(root)
    codelists = _codelists(root)

    dimensions = []
    for element in data_structure.iter():
        kind = _local_name(element.tag)
        if kind not in {"Dimension", "TimeDimension"}:
            continue

        code = element.attrib.get("id", "").upper()
        if not code:
            continue

        position = int(element.attrib.get("position", "999"))
        codelist_id = None
        for ref in element.iter():
            if (
                _local_name(ref.tag) == "Ref"
                and ref.attrib.get("class") == "Codelist"
            ):
                codelist_id = ref.attrib.get("id", "").upper()
                break

        dimensions.append(
            {
                "position": position,
                "code": code,
                "label": concept_labels.get(code, code),
                "values": codelists.get(codelist_id, []) if codelist_id else [],
            }
        )

    dimensions.sort(key=lambda item: item["position"])

    dataflow = _first(root, "Dataflow")
    title = _english_name(dataflow) if dataflow is not None else ""
    if not title and catalogue_entry:
        title = catalogue_entry["title"]

    return {
        "dataset_code": normalized_code,
        "title": title,
        "last_update": catalogue_entry.get("last_update", ""),
        "data_start": catalogue_entry.get("data_start", ""),
        "data_end": catalogue_entry.get("data_end", ""),
        "observation_count": catalogue_entry.get("values", ""),
        "dimensions": dimensions,
    }


def _catalogue_entry(dataset_code: str) -> dict[str, str]:
    catalogue = _catalogue()
    matches = catalogue.loc[
        catalogue["code"].str.casefold() == dataset_code.casefold()
    ]
    if matches.empty:
        return {}

    row = matches.iloc[0]
    return {
        "title": row["title"].strip(),
        "last_update": row["last update of data"].strip(),
        "data_start": row["data start"].strip(),
        "data_end": row["data end"].strip(),
        "values": row["values"].strip(),
    }


def _concept_labels(root: ET.Element) -> dict[str, str]:
    labels = {}
    for element in root.iter():
        if _local_name(element.tag) != "Concept":
            continue
        code = element.attrib.get("id", "").upper()
        if code:
            labels[code] = _english_name(element) or code
    return labels


def _codelists(root: ET.Element) -> dict[str, list[dict[str, str]]]:
    codelists = {}
    for element in root.iter():
        if _local_name(element.tag) != "Codelist":
            continue

        codelist_id = element.attrib.get("id", "").upper()
        if not codelist_id:
            continue

        values = []
        for code_element in element:
            if _local_name(code_element.tag) != "Code":
                continue
            code = code_element.attrib.get("id", "")
            if code:
                values.append(
                    {
                        "code": code,
                        "label": _english_name(code_element) or code,
                    }
                )
        codelists[codelist_id] = values

    return codelists


def _english_name(element: ET.Element) -> str:
    fallback = ""
    for child in element:
        if _local_name(child.tag) != "Name":
            continue
        text = (child.text or "").strip()
        if not fallback:
            fallback = text
        if child.attrib.get(XML_LANG) == "en":
            return text
    return fallback


def _first(root: ET.Element, local_name: str) -> ET.Element | None:
    return next(
        (
            element
            for element in root.iter()
            if _local_name(element.tag) == local_name
        ),
        None,
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
