import json
import platform
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MARKER_FILE = PROJECT_ROOT / "dca_script_marker.py"


class RuntimeCLITests(unittest.TestCase):
    def test_self_test_reports_runtime_details(self):
        result = subprocess.run(
            [sys.executable, str(MARKER_FILE), "--self-test"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        details = json.loads(result.stdout)
        self.assertTrue(details["ok"])
        self.assertEqual(details["architecture"], platform.machine())
        self.assertTrue(details["python"])
        self.assertTrue(details["pymupdf"])
        self.assertTrue(details["openpyxl"])
        self.assertIn("pymupdf", details["module_paths"])
        self.assertIn("openpyxl", details["module_paths"])


if __name__ == "__main__":
    unittest.main()
