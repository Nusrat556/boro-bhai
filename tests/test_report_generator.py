import os
import tempfile
import unittest

from reports.report_generator import generate_report


class ReportGeneratorTests(unittest.TestCase):
    def test_generate_report_creates_markdown_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = generate_report(
                title="Weekly Technology Report",
                sections={
                    "Technology developments": ["AI tooling continues to mature."],
                    "Job market": ["Python and cloud skills remain important."],
                    "Learning priorities": ["Study Git, Python, and SQL."],
                },
                output_dir=tmp_dir,
            )
            self.assertTrue(os.path.exists(report_path))
            with open(report_path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("Weekly Technology Report", content)
            self.assertIn("Technology developments", content)
            self.assertIn("Job market", content)
            self.assertIn("Learning priorities", content)


if __name__ == "__main__":
    unittest.main()
