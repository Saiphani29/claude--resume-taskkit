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

        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["column_count"], 2)
        self.assertEqual(result["columns"][1]["missing_count"], 1)
        self.assertEqual(result["columns"][0]["distinct_values_seen_up_to_10000"], 2)

    def test_empty_csv_has_no_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "empty.csv"
            csv_path.write_text("name,city\n", encoding="utf-8")
            result = csv_profile.profile_csv(csv_path)

        self.assertEqual(result["row_count"], 0)
        self.assertEqual(result["column_count"], 2)


if __name__ == "__main__":
    unittest.main()
