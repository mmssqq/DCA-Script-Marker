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
        page_hint_note = workbook["How to use"]["C14"].value
        states_reminder = workbook["DCA States"]["A2"].value
        self.assertIn("page number printed inside the script", page_hint_note)
        self.assertIn("sequential PDF page position", page_hint_note)
        self.assertIn("指定页码范围", page_hint_note)
        self.assertIn("Selected-page ranges", states_reminder)
        self.assertIn("剧本内印刷页码", states_reminder)

    def test_character_dropdowns_cover_all_dca_assignment_cells(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            workbook = load_workbook(TEMPLATE_FILE)
        self.addCleanup(workbook.close)

        validations = list(
            workbook["DCA States"].data_validations.dataValidation
        )
        self.assertEqual(len(validations), 2)
        self.assertEqual(
            {str(validation.sqref) for validation in validations},
            {"G2:R3", "G5:R1072"},
        )
        for validation in validations:
            self.assertEqual(validation.type, "list")
            self.assertEqual(
                validation.formula1,
                "'Character List'!$A$3:$A$202",
            )


if __name__ == "__main__":
    unittest.main()
