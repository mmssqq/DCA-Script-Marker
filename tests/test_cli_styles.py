import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz
from openpyxl import Workbook


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MARKER_FILE = PROJECT_ROOT / "dca_script_marker.py"
CONTENT_VIEW_FILE = (
    PROJECT_ROOT
    / "macOS App"
    / "DCA Script Marker"
    / "DCA Script Marker"
    / "ContentView.swift"
)
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_pdf_annotations import appearance_colours, includes_colour


class PageStateStyleCLITests(unittest.TestCase):
    def test_macos_app_exposes_only_the_three_editable_styles(self):
        content_view = CONTENT_VIEW_FILE.read_text(encoding="utf-8")
        self.assertIn(
            'let styles = [\n'
            '        "Editable Full Marking",\n'
            '        "First Appearance Only",\n'
            '        "DCA State Legend"\n'
            '    ]',
            content_view,
        )
        self.assertNotIn('\n        "Full Marking",', content_view)

    def test_page_state_display_argument_selects_footer_only(self):
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
                    "--page-state-display",
                    "footer",
                    "--state-font",
                    "Helvetica",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            marked_pdf = next(output_folder.glob("*_marked_*.pdf"))
            document = fitz.open(marked_pdf)
            page = document[0]
            margin_labels = [
                annotation
                for annotation in page.annots() or []
                if annotation.info.get("content") == "Scene 1"
                and (
                    annotation.rect.y1 < 50
                    or annotation.rect.y0 > page.rect.height - 50
                )
            ]

            self.assertEqual(len(margin_labels), 1)
            self.assertGreater(
                margin_labels[0].rect.y0,
                page.rect.height - 50,
            )
            document.close()

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

    def test_extended_palette_reaches_every_annotation_group(self):
        number_colour = (0.78, 0.24, 0.0)
        state_colour = (0.50, 0.20, 0.65)
        page_text_colour = (0.35, 0.35, 0.35)
        page_border_colour = (0.45, 0.25, 0.10)

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            template_file = temporary_path / "template.xlsx"
            output_folder = temporary_path / "output"
            output_folder.mkdir()

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((140, 72), "START", fontsize=12)
            page.insert_text((140, 120), "ALICE:", fontsize=12)
            source.save(source_pdf)
            source.close()

            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "DCA States"
            worksheet.append([
                "DCA State",
                "Start Line Text",
                "State Start Position",
                "DCA 1",
            ])
            worksheet.append(["Scene 1", "START", "Before", "ALICE"])
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
                    "--number-colour",
                    "orange",
                    "--state-colour",
                    "purple",
                    "--state-font",
                    "Helvetica",
                    "--page-state-display",
                    "both",
                    "--page-state-text-colour",
                    "grey",
                    "--page-state-font",
                    "Helvetica",
                    "--page-state-border-colour",
                    "brown",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                result.returncode,
                0,
                result.stdout + result.stderr,
            )

            marked_pdf = next(output_folder.glob("*_marked_*.pdf"))
            document = fitz.open(marked_pdf)
            page = document[0]
            number_seen = False
            body_state_seen = False
            margin_state_count = 0

            for annotation in page.annots() or []:
                content = annotation.info.get("content", "")
                strokes, fills = appearance_colours(document, annotation)

                if content == "1":
                    number_seen = includes_colour(fills, number_colour)
                elif content == "Scene 1" and (
                    annotation.rect.y1 < 50
                    or annotation.rect.y0 > page.rect.height - 50
                ):
                    margin_state_count += 1
                    self.assertTrue(
                        includes_colour(strokes, page_border_colour)
                    )
                    self.assertTrue(
                        includes_colour(fills, page_text_colour)
                    )
                elif content == "Scene 1":
                    body_state_seen = includes_colour(fills, state_colour)

            document.close()

            self.assertTrue(number_seen)
            self.assertTrue(body_state_seen)
            self.assertEqual(margin_state_count, 2)

    def test_retained_special_styles_create_only_editable_output(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            template_file = temporary_path / "template.xlsx"

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((140, 72), "START", fontsize=12)
            page.insert_text((140, 120), "ALICE:", fontsize=12)
            page.insert_text((140, 180), "ALICE:", fontsize=12)
            source.save(source_pdf)
            source.close()

            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "DCA States"
            worksheet.append([
                "DCA State",
                "Start Line Text",
                "State Start Position",
                "DCA 1",
            ])
            worksheet.append(["Scene 1", "START", "Before", "ALICE"])
            workbook.save(template_file)
            workbook.close()

            for style, expected_dca_count, expected_legend_count in (
                ("First Appearance Only", 1, 0),
                ("DCA State Legend", 0, 1),
            ):
                with self.subTest(style=style):
                    output_folder = temporary_path / style.replace(" ", "-")
                    output_folder.mkdir()
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
                            style,
                            "--number-font",
                            "Helvetica",
                            "--state-font",
                            "Helvetica",
                            "--page-state-display",
                            "both",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(
                        result.returncode,
                        0,
                        result.stdout + result.stderr,
                    )

                    marked_pdf = next(output_folder.glob("*_marked_*.pdf"))
                    moved_pdf = output_folder / "moved.pdf"
                    annotations_removed_pdf = (
                        output_folder / "annotations-removed.pdf"
                    )
                    document = fitz.open(marked_pdf)
                    page = document[0]
                    annotations = list(page.annots() or [])
                    self.assertTrue(annotations)
                    self.assertTrue(all(
                        annotation.type[1] == "FreeText"
                        for annotation in annotations
                    ))

                    margin_labels = [
                        annotation
                        for annotation in annotations
                        if annotation.info.get("content") == "Scene 1"
                        and (
                            annotation.rect.y1 < 50
                            or annotation.rect.y0 > page.rect.height - 50
                        )
                    ]
                    self.assertEqual(len(margin_labels), 2)
                    for annotation in margin_labels:
                        self.assertAlmostEqual(
                            annotation.border["width"],
                            0.8,
                            places=3,
                        )

                    dca_numbers = [
                        annotation
                        for annotation in annotations
                        if annotation.info.get("content") == "1"
                    ]
                    legends = [
                        annotation
                        for annotation in annotations
                        if annotation.info.get("content", "")
                        .casefold()
                        .startswith("scene 1\n1: alice")
                    ]
                    self.assertEqual(len(dca_numbers), expected_dca_count)
                    self.assertEqual(len(legends), expected_legend_count)

                    movable = (dca_numbers or legends)[0]
                    movable_content = movable.info.get("content")
                    moved_rect = movable.rect + (30, 35, 30, 35)
                    movable.set_rect(moved_rect)
                    movable.update()
                    document.save(moved_pdf)
                    document.close()

                    moved_document = fitz.open(moved_pdf)
                    moved_page = moved_document[0]
                    moved_annotation = next(
                        annotation
                        for annotation in moved_page.annots() or []
                        if annotation.info.get("content") == movable_content
                    )
                    self.assertAlmostEqual(
                        moved_annotation.rect.x0,
                        moved_rect.x0,
                        places=1,
                    )
                    self.assertAlmostEqual(
                        moved_annotation.rect.y0,
                        moved_rect.y0,
                        places=1,
                    )
                    self.assertEqual(
                        moved_document.xref_get_key(
                            moved_annotation.xref,
                            "AP",
                        )[0],
                        "dict",
                    )
                    for annotation in list(moved_page.annots() or []):
                        moved_page.delete_annot(annotation)
                    moved_document.save(annotations_removed_pdf)
                    moved_document.close()

                    cleaned_document = fitz.open(annotations_removed_pdf)
                    cleaned_page = cleaned_document[0]
                    self.assertEqual(list(cleaned_page.annots() or []), [])
                    self.assertNotIn("Scene 1", cleaned_page.get_text())
                    self.assertNotIn(
                        "1: alice",
                        cleaned_page.get_text().casefold(),
                    )
                    self.assertEqual(cleaned_page.get_drawings(), [])
                    cleaned_document.close()


if __name__ == "__main__":
    unittest.main()
