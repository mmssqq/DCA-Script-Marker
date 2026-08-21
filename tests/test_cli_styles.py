import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz
from openpyxl import Workbook


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MARKER_FILE = PROJECT_ROOT / "dca_script_marker.py"
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_pdf_annotations import appearance_colours, includes_colour


class PageStateStyleCLITests(unittest.TestCase):
    def test_page_state_style_arguments_reach_the_pdf(self):
        text_colour = (0.85, 0.0, 0.35)
        border_colour = (0.0, 0.45, 0.25)

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            template_file = temporary_path / "template.xlsx"
            output_folder = temporary_path / "output"
            output_folder.mkdir()

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((72, 72), "START", fontsize=12)
            source.save(source_pdf)
            source.close()

            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "DCA States"
            worksheet.append(
                [
                    "DCA State",
                    "Start Line Text",
                    "State Start Position",
                ]
            )
            worksheet.append(["Scene 1", "START", "Before"])
            workbook.save(template_file)
            workbook.close()

            result = subprocess.run(
                [
                    sys.executable,
                    str(MARKER_FILE),
                    "--template",
                    str(template_file),
                    "--script",
                    str(source_pdf),
                    "--output",
                    str(output_folder),
                    "--style",
                    "Editable Full Marking",
                    "--state-colour",
                    "blue",
                    "--state-scale",
                    "1.2",
                    "--state-font",
                    "Helvetica",
                    "--page-state-header-footer",
                    "--page-state-text-colour",
                    "red",
                    "--page-state-scale",
                    "1.45",
                    "--page-state-font",
                    "Times",
                    "--page-state-border-colour",
                    "green",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            marked_pdf = next(output_folder.glob("*_marked_*.pdf"))
            document = fitz.open(marked_pdf)
            page = document[0]
            page_labels = [
                annotation
                for annotation in page.annots() or []
                if annotation.info.get("content") == "Scene 1"
                and (
                    annotation.rect.y1 < 50
                    or annotation.rect.y0 > page.rect.height - 50
                )
            ]

            self.assertEqual(len(page_labels), 2)
            for annotation in page_labels:
                strokes, fills = appearance_colours(document, annotation)
                self.assertTrue(includes_colour(strokes, border_colour))
                self.assertTrue(includes_colour(fills, text_colour))
                _, default_style = document.xref_get_key(
                    annotation.xref,
                    "DS",
                )
                self.assertIn("Times New Roman", default_style)
                self.assertIn("17.4pt", default_style)
            document.close()


if __name__ == "__main__":
    unittest.main()
