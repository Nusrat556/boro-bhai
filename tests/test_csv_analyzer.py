import unittest
from pathlib import Path

from tools.csv_analyzer import analyze_csv


class CsvAnalyzerTests(unittest.TestCase):
    def test_analyze_simple_csv(self):
        csv_path = Path("data") / "sample.csv"
        csv_path.parent.mkdir(exist_ok=True)
        csv_path.write_text("name,score\nAlice,10\nBob,20\n", encoding="utf-8")
        result = analyze_csv(str(csv_path))
        self.assertEqual(result["row_count"], 2)
        self.assertIn("name", result["column_names"])
        self.assertIn("score", result["numeric_columns"])


if __name__ == "__main__":
    unittest.main()
