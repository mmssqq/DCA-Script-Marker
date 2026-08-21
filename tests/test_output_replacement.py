import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import dca_script_marker as marker


class OutputReplacementTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temporary_path = Path(self.temporary_directory.name)
        self.source_pdf = self.temporary_path / "source.pdf"
        self.output_pdf = self.temporary_path / "marked.pdf"

        source = fitz.open()
        page = source.new_page(width=595, height=842)
        page.insert_text((72, 72), "START", fontsize=12)
        page.insert_text((140, 120), "ALICE. Hello.", fontsize=12)
        source.save(self.source_pdf)
        source.close()

        self.states = [
            {
                "name": "Scene 1",
                "key": "scene 1",
                "cue": marker.cue_match_key("START"),
                "cue_speaker": "",
                "position": "before",
                "page_hint": "",
            }
        ]
        self.assignments = {"scene 1": {"alice": "1"}}

    def tearDown(self):
        self.temporary_directory.cleanup()

    def mark_with_vertical_offset(self, vertical_offset):
        marker.mark_pdf(
            self.states,
            self.assignments,
            str(self.source_pdf),
            str(self.output_pdf),
            editable=True,
            number_style={"vertical_offset": vertical_offset},
            state_style={
                "font_name": "helv",
                "font_file": None,
                "page_header_footer": True,
            },
        )

    def number_rect(self):
        document = fitz.open(self.output_pdf)
        try:
            number_rects = [
                fitz.Rect(annotation.rect)
                for annotation in document[0].annots() or []
                if annotation.type[1] == "FreeText"
                and annotation.info.get("content") == "1"
            ]
            self.assertEqual(len(number_rects), 1)
            return number_rects[0]
        finally:
            document.close()

    def test_replacing_from_clean_source_does_not_layer_annotations(self):
        self.mark_with_vertical_offset(0)
        first_rect = self.number_rect()

        self.mark_with_vertical_offset(3)
        replacement_rect = self.number_rect()

        self.assertAlmostEqual(replacement_rect.y0 - first_rect.y0, 3, places=2)
        self.assertAlmostEqual(replacement_rect.y1 - first_rect.y1, 3, places=2)

        document = fitz.open(self.output_pdf)
        try:
            scene_label_count = sum(
                1
                for annotation in document[0].annots() or []
                if annotation.type[1] == "FreeText"
                and annotation.info.get("content") == "Scene 1"
            )
            self.assertEqual(scene_label_count, 3)
        finally:
            document.close()

    def test_failed_atomic_swap_preserves_previous_output(self):
        self.mark_with_vertical_offset(0)
        previous_output = self.output_pdf.read_bytes()

        with patch.object(
            marker.os,
            "replace",
            side_effect=OSError("simulated replacement failure"),
        ):
            with self.assertRaisesRegex(
                OSError,
                "simulated replacement failure",
            ):
                self.mark_with_vertical_offset(3)

        self.assertEqual(self.output_pdf.read_bytes(), previous_output)
        temporary_outputs = list(
            self.temporary_path.glob(f".{self.output_pdf.name}.*.tmp.pdf")
        )
        self.assertEqual(temporary_outputs, [])


if __name__ == "__main__":
    unittest.main()
