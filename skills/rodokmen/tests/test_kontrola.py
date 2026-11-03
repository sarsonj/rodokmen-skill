import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from kontrola import research_log_stats


class ResearchLogStatsTests(unittest.TestCase):
    def test_counts_numeric_and_text_identifiers(self):
        contents = "\n".join(
            (
                "| # | datum | zdroj |",
                "|---|---|---|",
                "| 1 | datum | zdroj |",
                "| BA-1 | datum | zdroj |",
                "| KA-1 | datum | zdroj |",
                "| STR-10 | datum | zdroj |",
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "research_log.md"
            path.write_text(contents, encoding="utf-8")
            self.assertEqual(research_log_stats(str(path)), (4, []))

    def test_reports_duplicate_identifiers_case_insensitively(self):
        contents = "| BA-1 | a |\n| ba-1 | b |\n| 2 | c |\n| 2 | d |"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "research_log.md"
            path.write_text(contents, encoding="utf-8")
            self.assertEqual(research_log_stats(str(path)), (4, ["2", "BA-1"]))

    def test_missing_log_has_zero_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(research_log_stats(str(Path(tmp) / "missing.md")), (0, []))


if __name__ == "__main__":
    unittest.main()
