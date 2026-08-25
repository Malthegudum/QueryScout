"""Tests for deterministic QueryScout transformations and code generation."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from queryscout import results, transforms


SOURCE_PIPELINE = {
    "type": "source",
    "source": "test",
    "request": {"method": "GET", "url": "https://example.invalid/data.csv"},
    "parser": {"type": "csv", "kwargs": {}},
}


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.original_results_dir = results.RESULTS_DIR
        results.RESULTS_DIR = Path(self.temp_dir.name)

    def tearDown(self):
        results.RESULTS_DIR = self.original_results_dir
        self.temp_dir.cleanup()

    def seed(self, dataframe: pd.DataFrame, title: str = "test") -> str:
        return results.save_result(
            title=title,
            dataframe=dataframe,
            pipeline=SOURCE_PIPELINE,
        )

    def dataframe(self, summary: dict) -> pd.DataFrame:
        dataframe, _ = results.load_result(summary["result_id"])
        return dataframe

    def assert_generated_code_compiles(self, result_id: str) -> None:
        code = results.result_file(result_id, "query.py").read_text(encoding="utf-8")
        compile(code, "query.py", "exec")

    def test_sort_derive_and_time_change(self):
        result_id = self.seed(pd.DataFrame({
            "geo": ["DK", "DK", "SE", "SE"],
            "year": [2021, 2020, 2021, 2020],
            "gdp": [110.0, 100.0, 220.0, 200.0],
            "population": [5.9, 5.8, 10.5, 10.4],
        }))
        sorted_result = transforms.sort_result(result_id, by=["geo", "year"])
        derived_result = transforms.derive_column(
            sorted_result["result_id"],
            output_column="gdp_per_capita",
            operation="divide",
            left_column="gdp",
            right_column="population",
        )
        changed_result = transforms.time_change(
            derived_result["result_id"],
            column="gdp",
            output_column="gdp_growth",
            operation="pct_change",
            order_by="year",
            by=["geo"],
        )
        dataframe = self.dataframe(changed_result)
        self.assertEqual(dataframe["year"].tolist(), [2020, 2021, 2020, 2021])
        self.assertIn("gdp_per_capita", dataframe.columns)
        self.assertTrue(pd.isna(dataframe.loc[0, "gdp_growth"]))
        self.assertAlmostEqual(dataframe.loc[1, "gdp_growth"], 0.1)
        self.assert_generated_code_compiles(changed_result["result_id"])

    def test_pivot_result(self):
        result_id = self.seed(pd.DataFrame({
            "year": [2020, 2020, 2021, 2021],
            "geo": ["DK", "SE", "DK", "SE"],
            "value": [1.0, 2.0, 3.0, 4.0],
        }))
        summary = transforms.pivot_result(
            result_id, index=["year"], columns="geo", values="value"
        )
        dataframe = self.dataframe(summary)
        self.assertEqual(list(dataframe.columns), ["year", "DK", "SE"])
        self.assertEqual(dataframe["DK"].tolist(), [1.0, 3.0])
        self.assert_generated_code_compiles(summary["result_id"])

    def test_duplicate_keys_are_rejected(self):
        result_id = self.seed(pd.DataFrame({
            "geo": ["DK", "DK"], "year": [2020, 2020], "value": [1.0, 2.0]
        }))
        with self.assertRaisesRegex(ValueError, "Time-change keys are not unique"):
            transforms.time_change(
                result_id,
                column="value",
                output_column="difference",
                operation="difference",
                order_by="year",
                by=["geo"],
            )
        with self.assertRaisesRegex(ValueError, "Pivot keys are not unique"):
            transforms.pivot_result(
                result_id, index=["year"], columns="geo", values="value"
            )

    def test_concat_results_aligns_column_order(self):
        left = self.seed(pd.DataFrame({"x": [1], "y": [2]}), title="left")
        right = self.seed(pd.DataFrame({"y": [4], "x": [3]}), title="right")
        summary = transforms.concat_results([left, right])
        dataframe = self.dataframe(summary)
        self.assertEqual(
            dataframe.to_dict("records"),
            [{"x": 1, "y": 2}, {"x": 3, "y": 4}],
        )
        self.assert_generated_code_compiles(summary["result_id"])

    def test_concat_rejects_incompatible_columns(self):
        left = self.seed(pd.DataFrame({"x": [1], "y": [2]}), title="left")
        right = self.seed(pd.DataFrame({"x": [3], "z": [4]}), title="right")
        with self.assertRaisesRegex(ValueError, "same columns"):
            transforms.concat_results([left, right])


if __name__ == "__main__":
    unittest.main()
