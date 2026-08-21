import importlib.util
import pathlib
import unittest
import warnings

from openpyxl import load_workbook


ROOT = pathlib.Path(__file__).resolve().parents[1]
MARKER_FILE = ROOT / "dca_script_marker.py"
TEMPLATE_FILE = ROOT / "DCA Script Marker — DCA State Template.xlsx"

SPEC = importlib.util.spec_from_file_location("dca_script_marker", MARKER_FILE)
MARKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MARKER)


class CanonicalTemplateTests(unittest.TestCase):
    def test_blank_template_loads_without_placeholder_states(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            states, assignments = MARKER.load_template(TEMPLATE_FILE)

        self.assertEqual(states, [])
        self.assertEqual(assignments, {})

    def test_beta_template_keeps_the_supported_horizontal_schema(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            workbook = load_workbook(
                TEMPLATE_FILE,
                read_only=True,
                data_only=True,
            )
        self.addCleanup(workbook.close)

        self.assertEqual(
            workbook.sheetnames,
            ["How to use", "Character List", "DCA States"],
        )
        headers = [
            workbook["DCA States"].cell(row=4, column=column).value
            for column in range(1, 19)
        ]
        self.assertEqual(
            headers,
            [
                "DCA State",
                "Start Line Character",
                "Start Line Text",
                "State Start position",
                "Page Hint",
                "Notes",
                *[f"DCA {number}" for number in range(1, 13)],
            ],
        )


if __name__ == "__main__":
    unittest.main()
