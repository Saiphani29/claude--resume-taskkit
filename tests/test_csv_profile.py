import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "skills" / "excel-data-analyzer" / "scripts" / "csv_profile.py"
SPEC = importlib.util.spec_from_file_location("csv_profile", SCRIPT)
csv_profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(csv_profile)


class CsvProfileTests(unittest.TestCase):
    def test_profiles_rows_missing_values_and_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "sample.csv"
            csv_path.write_text("name,city\nAda,London\nLinus,\n", encoding="utf-8")
            result = csv_profile.profile_csv(csv_path)

        self.assertEqual(result["format"]["row_count"], 2)
        self.assertEqual(result["format"]["column_count"], 2)
        self.assertEqual(result["columns"][1]["missing_count"], 1)
        self.assertEqual(result["columns"][0]["distinct_values_seen_up_to_10000"], 2)

    def test_empty_csv_has_no_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "empty.csv"
            csv_path.write_text("name,city\n", encoding="utf-8")
            result = csv_profile.profile_csv(csv_path)

        self.assertEqual(result["format"]["row_count"], 0)
        self.assertEqual(result["format"]["column_count"], 2)

    def test_numeric_statistics_and_currency_cleaning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "sales.csv"
            csv_path.write_text(
                "item,price,quantity\nWidget,$10.50,4\nGadget,$20.50,6\nDoohickey,$30.00,0\n",
                encoding="utf-8",
            )
            result = csv_profile.profile_csv(csv_path)

        col_map = {col["name"]: col for col in result["columns"]}
        price_stats = col_map["price"]["statistics"]
        self.assertEqual(price_stats["min"], 10.5)
        self.assertEqual(price_stats["max"], 30.0)
        self.assertEqual(price_stats["mean"], 20.333)
        self.assertEqual(price_stats["sum"], 61.0)

        qty_stats = col_map["quantity"]["statistics"]
        self.assertEqual(qty_stats["zero_count"], 1)
        self.assertEqual(col_map["quantity"]["inferred_type"], "integer")

    def test_semicolon_delimited_sniffing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "european.csv"
            csv_path.write_text(
                "id;name;score\n1;Alice;95\n2;Bob;88\n3;Charlie;72\n",
                encoding="utf-8",
            )
            result = csv_profile.profile_csv(csv_path)

        self.assertEqual(result["format"]["detected_delimiter"], ";")
        self.assertEqual(result["format"]["column_count"], 3)
        self.assertEqual(result["format"]["row_count"], 3)

    def test_temporal_span_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "timeline.csv"
            csv_path.write_text(
                "event,date\nStart,2023-01-01\nMidpoint,2023-06-15\nFinish,2023-12-31\n",
                encoding="utf-8",
            )
            result = csv_profile.profile_csv(csv_path)

        col_map = {col["name"]: col for col in result["columns"]}
        time_span = col_map["date"]["temporal_span"]
        self.assertEqual(time_span["earliest"], "2023-01-01")
        self.assertEqual(time_span["latest"], "2023-12-31")
        self.assertEqual(time_span["timespan_days"], 364)

    def test_duplicate_row_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "dupes.csv"
            csv_path.write_text(
                "user,role\nAdmin,Owner\nAdmin,Owner\nEditor,Staff\nAdmin,Owner\n",
                encoding="utf-8",
            )
            result = csv_profile.profile_csv(csv_path)

        self.assertEqual(result["format"]["duplicate_rows_estimated"], 2)


if __name__ == "__main__":
    unittest.main()
