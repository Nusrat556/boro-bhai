import unittest
from pathlib import Path

from tools.file_reader import read_text_file


class FileReaderTests(unittest.TestCase):
    def test_read_valid_txt_file(self):
        sample_path = Path("data") / "example.txt"
        sample_path.parent.mkdir(exist_ok=True)
        sample_path.write_text("BORO BHAI\nAI agent project", encoding="utf-8")
        content = read_text_file(str(sample_path))
        self.assertIn("BORO BHAI", content)

    def test_reject_path_traversal(self):
        with self.assertRaises(ValueError):
            read_text_file("../README.md")


if __name__ == "__main__":
    unittest.main()
