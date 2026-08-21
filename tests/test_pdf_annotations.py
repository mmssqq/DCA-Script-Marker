import sys
import tempfile
import unittest
import re
from pathlib import Path

import fitz


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import dca_script_marker as marker


def appearance_colours(document, annotation):
    """Return stroke and fill RGB operators from an annotation appearance."""
    _, appearance = document.xref_get_key(annotation.xref, "AP")
    match = re.search(r"/N\s+(\d+)\s+0\s+R", appearance)
    if not match:
        return [], []

    tokens = document.xref_stream(int(match.group(1))).decode(
        "latin-1"
    ).split()
    strokes = []
    fills = []
    for index, token in enumerate(tokens):
        if token not in {"RG", "rg"} or index < 3:
            continue
        try:
            colour = tuple(float(value) for value in tokens[index - 3:index])
        except ValueError:
            continue
        (strokes if token == "RG" else fills).append(colour)
    return strokes, fills


def includes_colour(colours, expected):
    return any(
        all(abs(actual - target) < 0.01 for actual, target in zip(colour, expected))
        for colour in colours
    )


def coloured_pixel_count(page, rect, expected):
    """Count pixels close to an RGB colour inside one annotation rectangle."""
    pixmap = page.get_pixmap(
        matrix=fitz.Matrix(2, 2),
        clip=rect,
        alpha=False,
        annots=True,
    )
    targets = tuple(round(channel * 255) for channel in expected)
    return sum(
        1
        for index in range(0, len(pixmap.samples), pixmap.n)
        if all(
            abs(pixmap.samples[index + channel] - target) < 25
            for channel, target in enumerate(targets)
        )
    )


class PageStateAnnotationTests(unittest.TestCase):
    def test_editable_header_footer_border_moves_with_text(self):
        state_colour = (0.0, 0.35, 0.75)

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            moved_pdf = temporary_path / "moved.pdf"
            annotations_removed_pdf = temporary_path / "annotations-removed.pdf"

            source = fitz.open()
            source_page = source.new_page(width=595, height=842)
            source_page.insert_text((72, 72), "START", fontsize=12)
            source.save(source_pdf)
            source.close()

            states = [
                {
                    "name": "Scene 1",
                    "key": "scene 1",
                    "cue": marker.cue_match_key("START"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                }
            ]

            marker.mark_pdf(
                states,
                {"scene 1": {}},
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "colour": state_colour,
                    "size": 14.4,
                    "font_name": "helv",
                    "font_file": None,
                    "page_header_footer": True,
                },
            )

            document = fitz.open(marked_pdf)
            page = document[0]
            page_labels = [
                annotation
                for annotation in page.annots() or []
                if annotation.type[1] == "FreeText"
                and annotation.info.get("content") == "Scene 1"
                and (
                    annotation.rect.y1 < 50
                    or annotation.rect.y0 > page.rect.height - 50
                )
            ]

            self.assertEqual(len(page_labels), 2)
            for annotation in page_labels:
                self.assertAlmostEqual(annotation.border["width"], 0.8, places=3)

            header = min(page_labels, key=lambda annotation: annotation.rect.y0)
            moved_rect = header.rect + (60, 60, 60, 60)
            header.set_rect(moved_rect)
            header.update()
            document.save(moved_pdf)
            document.close()

            moved_document = fitz.open(moved_pdf)
            moved_page = moved_document[0]
            moved_header = next(
                annotation
                for annotation in moved_page.annots() or []
                if annotation.type[1] == "FreeText"
                and annotation.info.get("content") == "Scene 1"
                and abs(annotation.rect.x0 - moved_rect.x0) < 0.1
                and abs(annotation.rect.y0 - moved_rect.y0) < 0.1
            )
            self.assertAlmostEqual(moved_header.border["width"], 0.8, places=3)

            for annotation in list(moved_page.annots() or []):
                moved_page.delete_annot(annotation)
            moved_document.save(annotations_removed_pdf)
            moved_document.close()

            cleaned_document = fitz.open(annotations_removed_pdf)
            permanent_state_boxes = [
                drawing
                for drawing in cleaned_document[0].get_drawings()
                if drawing["type"] == "s"
                and abs(drawing["width"] - 0.8) < 0.01
                and drawing["color"] is not None
                and all(
                    abs(actual - expected) < 0.01
                    for actual, expected in zip(
                        drawing["color"],
                        state_colour,
                    )
                )
            ]
            cleaned_document.close()

            self.assertEqual(permanent_state_boxes, [])

    def test_editable_header_footer_has_independent_text_and_border_style(self):
        state_colour = (0.0, 0.35, 0.75)
        text_colour = (0.85, 0.0, 0.35)
        border_colour = (0.0, 0.45, 0.25)

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            moved_pdf = temporary_path / "moved.pdf"

            source = fitz.open()
            source_page = source.new_page(width=595, height=842)
            source_page.insert_text((72, 72), "START", fontsize=12)
            source.save(source_pdf)
            source.close()

            states = [
                {
                    "name": "Scene 1",
                    "key": "scene 1",
                    "cue": marker.cue_match_key("START"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                }
            ]

            marker.mark_pdf(
                states,
                {"scene 1": {}},
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "colour": state_colour,
                    "size": 14.4,
                    "font_name": "helv",
                    "font_file": None,
                    "page_header_footer": True,
                    "page_header_footer_text_colour": text_colour,
                    "page_header_footer_border_colour": border_colour,
                    "page_header_footer_size": 17.4,
                    "page_header_footer_font_name": "tiro",
                    "page_header_footer_font_file": None,
                },
            )

            document = fitz.open(marked_pdf)
            page = document[0]
            page_labels = [
                annotation
                for annotation in page.annots() or []
                if annotation.type[1] == "FreeText"
                and annotation.info.get("content") == "Scene 1"
                and (
                    annotation.rect.y1 < 50
                    or annotation.rect.y0 > page.rect.height - 50
                )
            ]
            body_labels = [
                annotation
                for annotation in page.annots() or []
                if annotation.type[1] == "FreeText"
                and annotation.info.get("content") == "Scene 1"
                and annotation.rect.y1 >= 50
                and annotation.rect.y0 <= page.rect.height - 50
            ]

            self.assertEqual(len(page_labels), 2)
            self.assertEqual(len(body_labels), 1)
            for annotation in page_labels:
                self.assertAlmostEqual(annotation.border["width"], 0.8, places=3)
                strokes, fills = appearance_colours(document, annotation)
                self.assertTrue(includes_colour(strokes, border_colour))
                self.assertTrue(includes_colour(fills, text_colour))

                _, default_style = document.xref_get_key(
                    annotation.xref,
                    "DS",
                )
                self.assertIn("Times New Roman", default_style)
                self.assertIn("17.4pt", default_style)
                rich_type, rich_content = document.xref_get_key(
                    annotation.xref,
                    "RC",
                )
                self.assertNotEqual(rich_type, "null")
                self.assertIn("Scene 1", rich_content)
                self.assertIn("</body>", rich_content)
                self.assertGreater(
                    coloured_pixel_count(
                        page,
                        annotation.rect,
                        text_colour,
                    ),
                    5,
                )

            body_strokes, body_fills = appearance_colours(
                document,
                body_labels[0],
            )
            self.assertTrue(includes_colour(body_fills, state_colour))
            self.assertFalse(includes_colour(body_fills, text_colour))

            header = min(page_labels, key=lambda annotation: annotation.rect.y0)
            moved_rect = header.rect + (60, 60, 60, 60)
            header.set_rect(moved_rect)
            header.update()
            document.save(moved_pdf)
            document.close()

            moved_document = fitz.open(moved_pdf)
            moved_page = moved_document[0]
            moved_header = next(
                annotation
                for annotation in moved_page.annots() or []
                if annotation.type[1] == "FreeText"
                and annotation.info.get("content") == "Scene 1"
                and abs(annotation.rect.x0 - moved_rect.x0) < 0.1
                and abs(annotation.rect.y0 - moved_rect.y0) < 0.1
            )
            strokes, fills = appearance_colours(
                moved_document,
                moved_header,
            )
            self.assertTrue(includes_colour(strokes, border_colour))
            self.assertTrue(includes_colour(fills, text_colour))
            self.assertAlmostEqual(moved_header.border["width"], 0.8, places=3)
            rich_type, rich_content = moved_document.xref_get_key(
                moved_header.xref,
                "RC",
            )
            self.assertNotEqual(rich_type, "null")
            self.assertIn("Scene 1", rich_content)
            self.assertIn("</body>", rich_content)
            self.assertGreater(
                coloured_pixel_count(
                    moved_page,
                    moved_header.rect,
                    text_colour,
                ),
                5,
            )
            moved_document.close()

    def test_static_header_footer_uses_independent_colours(self):
        text_colour = (0.85, 0.0, 0.35)
        border_colour = (0.0, 0.45, 0.25)

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            source_page = source.new_page(width=595, height=842)
            source_page.insert_text((72, 72), "START", fontsize=12)
            source.save(source_pdf)
            source.close()

            states = [
                {
                    "name": "Scene 1",
                    "key": "scene 1",
                    "cue": marker.cue_match_key("START"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                }
            ]

            marker.mark_pdf(
                states,
                {"scene 1": {}},
                str(source_pdf),
                str(marked_pdf),
                editable=False,
                state_style={
                    "colour": (0.0, 0.35, 0.75),
                    "size": 14.4,
                    "font_name": "helv",
                    "font_file": None,
                    "page_header_footer": True,
                    "page_header_footer_text_colour": text_colour,
                    "page_header_footer_border_colour": border_colour,
                    "page_header_footer_size": 17.4,
                    "page_header_footer_font_name": "tiro",
                    "page_header_footer_font_file": None,
                },
            )

            document = fitz.open(marked_pdf)
            page = document[0]
            self.assertEqual(list(page.annots() or []), [])

            boxes = [
                drawing
                for drawing in page.get_drawings()
                if drawing["type"] == "s"
                and abs(drawing["width"] - 0.8) < 0.01
                and drawing["color"] is not None
                and all(
                    abs(actual - expected) < 0.01
                    for actual, expected in zip(
                        drawing["color"],
                        border_colour,
                    )
                )
            ]
            self.assertEqual(len(boxes), 2)

            expected_text_colour = sum(
                round(channel * 255) << shift
                for channel, shift in zip(text_colour, (16, 8, 0))
            )
            margin_spans = [
                span
                for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", [])
                for span in line.get("spans", [])
                if span["text"] == "Scene 1"
                and (
                    span["bbox"][3] < 50
                    or span["bbox"][1] > page.rect.height - 50
                )
            ]
            self.assertGreaterEqual(len(margin_spans), 2)
            self.assertTrue(
                all(span["color"] == expected_text_colour for span in margin_spans)
            )
            self.assertTrue(
                all(abs(span["size"] - 17.4) < 0.1 for span in margin_spans)
            )
            self.assertTrue(
                all("Times" in span["font"] for span in margin_spans)
            )
            document.close()

    def test_header_footer_style_is_ignored_when_hidden(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            source_page = source.new_page(width=595, height=842)
            source_page.insert_text((72, 72), "START", fontsize=12)
            source.save(source_pdf)
            source.close()

            states = [
                {
                    "name": "Scene 1",
                    "key": "scene 1",
                    "cue": marker.cue_match_key("START"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                }
            ]
            marker.mark_pdf(
                states,
                {"scene 1": {}},
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "colour": (0.0, 0.35, 0.75),
                    "size": 14.4,
                    "font_name": "helv",
                    "font_file": None,
                    "page_header_footer": False,
                    "page_header_footer_text_colour": (0.85, 0.0, 0.35),
                    "page_header_footer_border_colour": (0.0, 0.45, 0.25),
                },
            )

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
            body_labels = [
                annotation
                for annotation in page.annots() or []
                if annotation.info.get("content") == "Scene 1"
            ]
            document.close()

            self.assertEqual(margin_labels, [])
            self.assertEqual(len(body_labels), 1)

    def test_cjk_header_footer_keeps_a_compatible_font(self):
        text_colour = (0.85, 0.0, 0.35)
        border_colour = (0.0, 0.45, 0.25)

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            source_page = source.new_page(width=595, height=842)
            source_page.insert_text((72, 72), "START", fontsize=12)
            source.save(source_pdf)
            source.close()

            states = [
                {
                    "name": "场景一",
                    "key": "场景一",
                    "cue": marker.cue_match_key("START"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                }
            ]
            marker.mark_pdf(
                states,
                {"场景一": {}},
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "colour": (0.0, 0.35, 0.75),
                    "size": 14.4,
                    "font_name": "helv",
                    "font_file": None,
                    "page_header_footer": True,
                    "page_header_footer_text_colour": text_colour,
                    "page_header_footer_border_colour": border_colour,
                    "page_header_footer_size": 17.4,
                    # The engine must override this English-only request for
                    # a CJK label while preserving every other page setting.
                    "page_header_footer_font_name": "tiro",
                    "page_header_footer_font_file": None,
                },
            )

            document = fitz.open(marked_pdf)
            page = document[0]
            page_labels = [
                annotation
                for annotation in page.annots() or []
                if annotation.info.get("content") == "场景一"
                and (
                    annotation.rect.y1 < 50
                    or annotation.rect.y0 > page.rect.height - 50
                )
            ]
            self.assertEqual(len(page_labels), 2)
            self.assertIn("场景一", page.get_text())
            for annotation in page_labels:
                strokes, fills = appearance_colours(document, annotation)
                self.assertTrue(includes_colour(strokes, border_colour))
                self.assertTrue(includes_colour(fills, text_colour))
                rich_type, _ = document.xref_get_key(
                    annotation.xref,
                    "RC",
                )
                self.assertNotEqual(rich_type, "null")
                self.assertGreater(
                    coloured_pixel_count(
                        page,
                        annotation.rect,
                        text_colour,
                    ),
                    5,
                )
            document.close()


if __name__ == "__main__":
    unittest.main()
