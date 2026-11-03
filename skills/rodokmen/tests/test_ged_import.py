import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GED_IMPORT = Path(__file__).resolve().parents[1] / "tools" / "ged_import.py"


class GedImportRootSelectionTests(unittest.TestCase):
    def test_selects_duplicate_name_by_gedcom_id(self):
        gedcom = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Same /Name/
1 BIRT
2 DATE 1 JAN 1900
0 @I2@ INDI
1 NAME Same /Name/
1 BIRT
2 DATE 1 JAN 1950
0 TRLR
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tree.ged"
            path.write_text(gedcom, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(GED_IMPORT), str(path), "@I2@"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertIn("1 | Same Name | * 1950", result.stdout)
        self.assertNotIn("* 1900", result.stdout)


if __name__ == "__main__":
    unittest.main()
