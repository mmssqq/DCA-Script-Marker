import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

import fitz
from openpyxl import Workbook


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
    def test_after_state_label_avoids_following_speaker_number(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((150, 100), "OPENING", fontsize=14)
            page.insert_text((72, 122), "ORB.", fontsize=12)
            page.insert_text((144, 122), "Chime together.", fontsize=12)
            source.save(source_pdf)
            source.close()

            marked_count, _, _ = marker.mark_pdf(
                [{
                    "name": "Scene 1",
                    "key": "scene 1",
                    "cue": marker.cue_match_key("OPENING"),
                    "cue_speaker": "",
                    "position": "after",
                    "page_hint": "",
                }],
                {"scene 1": {"orb": "2"}},
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                    "position": "Left Gutter",
                    "size": 17.4,
                },
            )

            document = fitz.open(marked_pdf)
            annotation_rects = {}
            for annotation in document[0].annots() or []:
                content = annotation.info.get("content", "")
                if content in {"Scene 1", "2"}:
                    annotation_rects[content] = fitz.Rect(annotation.rect)
            state_rect = annotation_rects["Scene 1"]
            number_rect = annotation_rects["2"]

            self.assertEqual(marked_count, 1)
            self.assertFalse(state_rect.intersects(number_rect))
            self.assertLessEqual(state_rect.x1 + 4, 150)
            document.close()

    def test_page_state_display_selects_header_footer_both_or_off(self):
        expected_labels = {
            "off": set(),
            "header": {("Scene 1", "header")},
            "footer": {("Scene 2", "footer")},
            "both": {
                ("Scene 1", "header"),
                ("Scene 2", "footer"),
            },
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((72, 72), "FIRST", fontsize=12)
            page.insert_text((72, 420), "SECOND", fontsize=12)
            source.save(source_pdf)
            source.close()

            states = [
                {
                    "name": "Scene 1",
                    "key": "scene 1",
                    "cue": marker.cue_match_key("FIRST"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                },
                {
                    "name": "Scene 2",
                    "key": "scene 2",
                    "cue": marker.cue_match_key("SECOND"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                },
            ]
            assignments = {"scene 1": {}, "scene 2": {}}

            for editable in (True, False):
                for display, expected in expected_labels.items():
                    with self.subTest(editable=editable, display=display):
                        marked_pdf = temporary_path / (
                            f"marked-{editable}-{display}.pdf"
                        )
                        marker.mark_pdf(
                            states,
                            assignments,
                            str(source_pdf),
                            str(marked_pdf),
                            editable=editable,
                            state_style={
                                "font_name": "helv",
                                "font_file": None,
                                "page_state_display": display,
                            },
                        )

                        document = fitz.open(marked_pdf)
                        marked_page = document[0]
                        actual = set()

                        if editable:
                            for annotation in marked_page.annots() or []:
                                content = annotation.info.get("content", "")
                                if content not in {"Scene 1", "Scene 2"}:
                                    continue
                                if annotation.rect.y1 < 50:
                                    actual.add((content, "header"))
                                elif (
                                    annotation.rect.y0
                                    > marked_page.rect.height - 50
                                ):
                                    actual.add((content, "footer"))
                        else:
                            for block in marked_page.get_text("dict")["blocks"]:
                                for line in block.get("lines", []):
                                    for span in line.get("spans", []):
                                        content = span.get("text", "")
                                        if content not in {"Scene 1", "Scene 2"}:
                                            continue
                                        if span["bbox"][3] < 50:
                                            actual.add((content, "header"))
                                        elif (
                                            span["bbox"][1]
                                            > marked_page.rect.height - 50
                                        ):
                                            actual.add((content, "footer"))

                        document.close()
                        self.assertEqual(actual, expected)

    def test_current_state_is_not_announced_twice_for_repeated_cue_text(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((72, 72), "ZEPHYR", fontsize=12)
            page.insert_text(
                (72, 110),
                "Zephyr music continues.",
                fontsize=12,
            )
            source.save(source_pdf)
            source.close()

            states = [{
                "name": "Scene 1",
                "key": "scene 1",
                "cue": marker.cue_match_key("ZEPHY"),
                "cue_speaker": "",
                "position": "before",
                "page_hint": "",
            }]

            _, _, activated_states = marker.mark_pdf(
                states,
                {"scene 1": {}},
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
            )

            document = fitz.open(marked_pdf)
            state_labels = [
                annotation
                for annotation in document[0].annots() or []
                if annotation.info.get("content") == "Scene 1"
            ]
            document.close()

            self.assertEqual(len(state_labels), 1)
            self.assertEqual(activated_states, {"scene 1"})

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


class PaddedSpeakerAnnotationTests(unittest.TestCase):
    def check_padded_speaker_positions(self, *, editable, first_appearance=False):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((72, 50), "START", fontsize=12)
            labels = [
                (72, 100, " " * 60 + "NOVA"),
                (72, 170, " " * 63 + "ELI"),
                (72, 240, " " * 61 + "DANA"),
                (72, 310, " " * 52 + "NOVA and ELI"),
                (300, 380, "NOVA"),
            ]
            if first_appearance:
                labels = labels[:3]
            for x, y, label in labels:
                page.insert_text((x, y), label, fontsize=12, fontname="tibo")
                page.insert_text((72, y + 25), "The next line.", fontsize=12)
            source.save(source_pdf)
            source.close()
            original_bytes = source_pdf.read_bytes()

            with fitz.open(source_pdf) as document:
                expected_boxes = [
                    fitz.Rect(next(
                        char["bbox"] for char in span["chars"]
                        if not char["c"].isspace()
                    ))
                    for block in document[0].get_text("rawdict")["blocks"]
                    for line in block.get("lines", [])
                    for span in line["spans"]
                    if "".join(char["c"] for char in span["chars"]).strip()
                    in {"NOVA", "ELI", "DANA", "NOVA and ELI"}
                ]
            expected_numbers = ["1", "2", "3", "1/2", "1"]
            if first_appearance:
                expected_boxes = expected_boxes[:3]
                expected_numbers = expected_numbers[:3]
            gap = 19
            vertical_offset = 3
            marked_count, unmatched, _ = marker.mark_pdf(
                [{
                    "name": "Scene 1", "key": "scene 1",
                    "cue": marker.cue_match_key("START"),
                    "cue_speaker": "", "position": "before", "page_hint": "",
                }],
                {"scene 1": {"nova": "1", "eli": "2", "dana": "3"}},
                str(source_pdf), str(marked_pdf),
                editable=editable, first_appearance=first_appearance,
                number_style={"gap": gap, "vertical_offset": vertical_offset},
                state_style={"font_name": "helv", "font_file": None},
            )
            self.assertEqual(marked_count, len(expected_numbers))
            self.assertEqual(unmatched, [])
            self.assertEqual(source_pdf.read_bytes(), original_bytes)
            with fitz.open(marked_pdf) as document:
                page = document[0]
                if editable:
                    marks = [
                        (annotation.info["content"], fitz.Rect(annotation.rect))
                        for annotation in page.annots() or []
                        if re.fullmatch(r"\d+(?:/\d+)*", annotation.info["content"])
                    ]
                    self.assertTrue(all(
                        annotation.type[1] == "FreeText"
                        for annotation in page.annots() or []
                    ))
                else:
                    marks = [
                        (span["text"], fitz.Rect(span["bbox"]))
                        for block in page.get_text("dict")["blocks"]
                        for line in block.get("lines", [])
                        for span in line["spans"]
                        if re.fullmatch(r"\d+(?:/\d+)*", span["text"])
                    ]
                self.assertEqual([text for text, _ in marks], expected_numbers)
                for (_, actual), visible in zip(marks, expected_boxes):
                    self.assertAlmostEqual(actual.x1, visible.x0 - gap, places=2)
                    if editable:
                        self.assertAlmostEqual(
                            actual.y0, visible.y0 + vertical_offset, places=2
                        )

    def test_editable_numbers_ignore_invisible_speaker_padding(self):
        self.check_padded_speaker_positions(editable=True)

    def test_static_numbers_ignore_invisible_speaker_padding(self):
        self.check_padded_speaker_positions(editable=False)

    def test_first_appearance_numbers_ignore_invisible_speaker_padding(self):
        self.check_padded_speaker_positions(editable=True, first_appearance=True)


class SpeakerRowAnnotationTests(unittest.TestCase):
    def test_split_title_case_period_labels_require_trusted_columns(self):
        def ocr_line(text, x0, x1, y):
            return {
                "text": text,
                "bbox": [x0, y, x1 - x0, 13],
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            ocr_json = temporary_path / "ocr.json"

            source = fitz.open()
            source.new_page(width=595, height=842)
            source.new_page(width=595, height=842)
            source.save(source_pdf)
            source.close()

            ocr_data = [
                {
                    "lines": [
                        ocr_line("START", 72, 115, 50),
                        ocr_line("Trio.", 72, 92, 100),
                        ocr_line("Chime together.", 144, 220, 100),
                        ocr_line("Orlena. 7", 72, 122, 140),
                        ocr_line("A footnoted cue.", 144, 245, 140),
                        ocr_line(
                            "Vega, Orlena & Neris.",
                            72,
                            215,
                            180,
                        ),
                        ocr_line("A shared cue.", 240, 330, 180),
                        ocr_line("(TOVA drifts up and off.)", 220, 365, 220),
                        ocr_line("Vega.", 180, 215, 260),
                        ocr_line("Indented prose.", 240, 330, 260),
                        ocr_line("Zane", 72, 100, 300),
                        ocr_line("A trusted bare cue.", 126, 240, 300),
                        ocr_line("Trio turns.", 72, 135, 340),
                    ]
                },
                {
                    "lines": [
                        ocr_line("Tova.", 72, 105, 100),
                        ocr_line("Inherited gutter cue.", 144, 275, 100),
                        ocr_line("Tova.", 180, 213, 160),
                        ocr_line("Body-column prose.", 240, 350, 160),
                        ocr_line("Elara.", 72, 110, 220),
                        ocr_line("Left-column dialogue.", 144, 252, 220),
                        ocr_line("Zane.", 304, 338, 220),
                        ocr_line("Parallel-column cue.", 376, 500, 220),
                        ocr_line(
                            "Vega & Tova. Is the prism ready?",
                            72,
                            285,
                            260,
                        ),
                        ocr_line("Zane. Greetings.", 72, 145, 300),
                    ]
                },
            ]
            ocr_json.write_text(json.dumps(ocr_data), encoding="utf-8")

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
            assignments = {
                "scene 1": {
                    "trio": "2",
                    "orlena": "1",
                    "vega": "3",
                    "zane": "4",
                    "tova": "5",
                    "neris": "6",
                }
            }

            marked_count, unmatched_names, _ = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
                ocr_json_file=str(ocr_json),
            )

            annotations_by_page_and_row = {}
            document = fitz.open(marked_pdf)
            for page_number, page in enumerate(document, start=1):
                for annotation in page.annots() or []:
                    content = annotation.info.get("content", "")
                    if not re.fullmatch(r"\d+(?:/\d+)*", content):
                        continue
                    key = (page_number, round(annotation.rect.y0))
                    annotations_by_page_and_row.setdefault(key, []).append(
                        content
                    )
            document.close()

            self.assertEqual(marked_count, 7)
            self.assertEqual(annotations_by_page_and_row[(1, 100)], ["2"])
            self.assertEqual(annotations_by_page_and_row[(1, 140)], ["1"])
            self.assertEqual(
                annotations_by_page_and_row[(1, 180)],
                ["1/3/6"],
            )
            self.assertNotIn((1, 220), annotations_by_page_and_row)
            self.assertNotIn((1, 260), annotations_by_page_and_row)
            self.assertEqual(annotations_by_page_and_row[(1, 300)], ["4"])
            self.assertNotIn((1, 340), annotations_by_page_and_row)
            self.assertEqual(annotations_by_page_and_row[(2, 100)], ["5"])
            self.assertNotIn((2, 160), annotations_by_page_and_row)
            self.assertEqual(annotations_by_page_and_row[(2, 220)], ["4"])
            self.assertEqual(
                annotations_by_page_and_row[(2, 260)],
                ["3/5"],
            )
            self.assertNotIn((2, 300), annotations_by_page_and_row)
            self.assertEqual(unmatched_names, [])

    def test_bold_title_case_prefix_marks_and_activates_speaker_cue(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            writer = fitz.TextWriter(page.rect)
            regular = fitz.Font("helv")
            bold = fitz.Font("hebo")
            italic = fitz.Font("heit")

            writer.append((72, 50), "START", font=regular, fontsize=12)
            writer.append(
                (72, 90),
                "Lumen appears in the doorway.",
                font=regular,
                fontsize=12,
            )
            writer.append(
                (72, 120),
                "Lumen traces the circle.",
                font=italic,
                fontsize=12,
            )
            writer.append(
                (72, 140),
                "Orin and Selkie trace the circle.",
                font=italic,
                fontsize=12,
            )

            def append_dialogue(y, speaker, dialogue):
                writer.append(
                    (72, y),
                    speaker,
                    font=bold,
                    fontsize=12,
                )
                speaker_right = 72 + bold.text_length(
                    speaker,
                    fontsize=12,
                )
                writer.append(
                    (speaker_right + 2, y),
                    f" {dialogue}",
                    font=regular,
                    fontsize=12,
                )

            append_dialogue(160, "Lumen", "O'bright.")

            writer.append((72, 190), "Orin", font=bold, fontsize=12)
            writer.append((98, 190), " and ", font=italic, fontsize=12)
            writer.append((126, 190), "Selkie", font=bold, fontsize=12)

            append_dialogue(220, "Branna", "Clouds drift.")
            append_dialogue(260, "Vale Meridian", "The bell is nine.")
            writer.write_text(page)
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
                },
                {
                    "name": "Scene 2",
                    "key": "scene 2",
                    "cue": marker.cue_match_key("Clouds drift."),
                    "cue_speaker": "branna",
                    "position": "after",
                    "page_hint": "",
                },
            ]
            assignments = {
                "scene 1": {
                    "lumen": "1",
                    "branna": "2",
                    "orin": "4",
                    "selkie": "5",
                },
                "scene 2": {"vale meridian": "3"},
            }

            marked_count, unmatched_names, activated_states = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
            )

            document = fitz.open(marked_pdf)
            number_annotations = sorted(
                annotation.info.get("content", "")
                for annotation in document[0].annots() or []
                if re.fullmatch(
                    r"\d+(?:/\d+)*",
                    annotation.info.get("content", ""),
                )
            )
            document.close()

            self.assertEqual(marked_count, 4)
            self.assertEqual(
                number_annotations,
                ["1", "2", "3", "4/5"],
            )
            self.assertEqual(activated_states, {"scene 1", "scene 2"})
            self.assertEqual(unmatched_names, [])

    def test_blank_tab_stop_fragments_do_not_bridge_speaker_columns(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            page = source.new_page(width=612, height=792)
            page.insert_text((72, 50), "START", fontsize=11)
            for x, text in (
                (125.9, " "),
                (161.9, "SUN"),
                (197.9, " "),
                (233.9, " "),
                (269.9, " "),
                (305.9, " "),
                (341.9, " "),
                (377.9, " "),
                (413.9, " "),
                (449.9, "MOONS"),
            ):
                page.insert_text((x, 100), text, fontsize=11)
            source.save(source_pdf)
            source.close()

            extracted_source = fitz.open(source_pdf)
            extracted_lines = [
                line
                for block in extracted_source[0].get_text("dict")["blocks"]
                for line in block.get("lines", [])
            ]
            blank_lines = [
                line
                for line in extracted_lines
                if not "".join(
                    span["text"] for span in line["spans"]
                ).strip()
            ]
            extracted_source.close()
            self.assertGreaterEqual(len(blank_lines), 8)

            states = [{
                "name": "Scene 100",
                "key": "scene 100",
                "cue": marker.cue_match_key("START"),
                "cue_speaker": "",
                "position": "before",
                "page_hint": "",
            }]
            assignments = {
                "scene 100": {
                    "sun": "1",
                    "moons": "2",
                }
            }

            marked_count, _, _ = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
            )

            document = fitz.open(marked_pdf)
            marked_page = document[0]
            annotations = sorted(
                (
                    annotation
                    for annotation in marked_page.annots() or []
                    if re.fullmatch(
                        r"\d+(?:/\d+)*",
                        annotation.info.get("content", ""),
                    )
                ),
                key=lambda annotation: annotation.rect.x0,
            )
            annotation_contents = [
                annotation.info["content"]
                for annotation in annotations
            ]
            annotation_positions = [
                (annotation.rect.x0, annotation.rect.y0)
                for annotation in annotations
            ]
            document.close()

            self.assertEqual(marked_count, 2)
            self.assertEqual(annotation_contents, ["1", "2"])
            self.assertAlmostEqual(
                annotation_positions[0][1],
                annotation_positions[1][1],
                places=1,
            )
            self.assertGreater(
                annotation_positions[1][0] - annotation_positions[0][0],
                200,
            )

    def test_continued_group_and_right_column_labels(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            page = source.new_page(width=612, height=792)
            page.insert_text((72, 50), "START", fontsize=11)

            for x, y, text in (
                (161.9, 100, "SUN"),
                (449.9, 100, "MOONS"),
                (161.9, 150, "ZED (CONTINUED)"),
                (305.9, 150, "STARWEAVERS (CONTINUED)"),
                (197.9, 200, "ZED"),
                (377.9, 200, "ORB"),
                (233.9, 250, "ZED AND ORB"),
                (377.9, 300, "QUASAR"),
            ):
                page.insert_text((x, y), text, fontsize=11)

            source.save(source_pdf)
            source.close()

            states = [{
                "name": "Scene 100",
                "key": "scene 100",
                "cue": marker.cue_match_key("START"),
                "cue_speaker": "",
                "position": "before",
                "page_hint": "",
            }]
            assignments = {
                "scene 100": {
                    "sun": "1",
                    "moons": "2",
                    "orb": "3",
                    "zed": "4",
                    "starweavers": "7",
                    "quasar": "8",
                }
            }

            marked_count, _, _ = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
            )

            document = fitz.open(marked_pdf)
            marked_page = document[0]
            annotations = [
                annotation
                for annotation in marked_page.annots() or []
                if re.fullmatch(
                    r"\d+(?:/\d+)*",
                    annotation.info.get("content", ""),
                )
            ]
            contents = sorted(
                annotation.info["content"]
                for annotation in annotations
            )
            quasar_positions = [
                annotation.rect.x0
                for annotation in annotations
                if annotation.info.get("content") == "8"
            ]
            document.close()

            self.assertEqual(marked_count, 8)
            self.assertEqual(
                contents,
                ["1", "2", "3", "3/4", "4", "4", "7", "8"],
            )
            self.assertEqual(len(quasar_positions), 1)
            self.assertGreater(quasar_positions[0], 300)

    def test_synthetic_header_page_hint_activates_first_state(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            source.new_page(width=612, height=792)
            page = source.new_page(width=612, height=792)
            page.insert_text((72, 36), "MOON TEST", fontsize=11)
            page.insert_text((260, 36), "9/99/99", fontsize=11)
            page.insert_text((510, 36), "1", fontsize=11)
            page.insert_text(
                (72, 90),
                "Scene l - SKYWARD/INWARD THE DOME",
                fontsize=11,
            )
            page.insert_text((233.9, 140), "VOYAGER", fontsize=11)
            page.insert_text((161.9, 190), "SUN", fontsize=11)
            page.insert_text((449.9, 190), "MOONS", fontsize=11)
            source.save(source_pdf)
            source.close()

            states = [{
                "name": "Scene 100",
                "key": "scene 100",
                "cue": marker.cue_match_key(
                    "Scene l - SKYWARD/INWARD THE DOME"
                ),
                "cue_speaker": "",
                "position": "after",
                "page_hint": "1",
            }]
            assignments = {
                "scene 100": {
                    "voyager": ["1", "2"],
                    "sun": "1",
                    "moons": "2",
                }
            }

            marked_count, _, activated_states = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
            )

            document = fitz.open(marked_pdf)
            page_number_contents = []
            for marked_page in document:
                page_number_contents.append(sorted(
                    annotation.info.get("content", "")
                    for annotation in marked_page.annots() or []
                    if re.fullmatch(
                        r"\d+(?:/\d+)*",
                        annotation.info.get("content", ""),
                    )
                ))
            document.close()

            self.assertEqual(marked_count, 3)
            self.assertEqual(activated_states, {"scene 100"})
            self.assertEqual(page_number_contents[0], [])
            self.assertEqual(page_number_contents[1], ["1", "1/2", "2"])

    def test_same_row_state_heading_fragments_activate_once(self):
        def ocr_line(text, x0, x1, y):
            return {
                "text": text,
                "bbox": [x0, y, x1 - x0, 13],
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            ocr_json = temporary_path / "ocr.json"

            source = fitz.open()
            source.new_page(width=595, height=842)
            source.save(source_pdf)
            source.close()

            # Word can draw these as one visible heading while exposing the
            # Roman numeral and title as independent same-baseline lines.
            ocr_data = [{
                "lines": [
                    # The title words also appear in earlier prose. Without
                    # the Roman numeral this must not activate the state.
                    ocr_line(
                        "星官——巡守七色云工坊",
                        72,
                        260,
                        100,
                    ),
                    ocr_line("星官", 72, 102, 140),
                    ocr_line("这是虚构介绍。", 136, 220, 140),
                    ocr_line("I.", 77, 94, 293),
                    ocr_line("七色云工坊", 108, 186, 293),
                    ocr_line("星官", 72, 102, 350),
                    ocr_line("亮了?", 136, 178, 350),
                    ocr_line("4", 518, 526, 792),
                ]
            }]
            ocr_json.write_text(
                json.dumps(ocr_data),
                encoding="utf-8",
            )

            states = [{
                "name": "Scene 1",
                "key": "scene 1",
                "cue": marker.cue_match_key("I. 七色云工坊"),
                "cue_speaker": "",
                "position": "after",
                "page_hint": "4",
            }]

            marked_count, _, activated_states = marker.mark_pdf(
                states,
                {"scene 1": {"星官": "1"}},
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
                ocr_json_file=str(ocr_json),
            )

            document = fitz.open(marked_pdf)
            annotations = [
                annotation.info.get("content", "")
                for annotation in document[0].annots() or []
            ]
            document.close()

            self.assertEqual(marked_count, 1)
            self.assertEqual(activated_states, {"scene 1"})
            self.assertEqual(annotations.count("Scene 1"), 1)
            self.assertEqual(annotations.count("1"), 1)

    def test_cast_track_cues_mark_without_narration_or_table_names(self):
        def ocr_line(text, x0, x1, y):
            return {
                "text": text,
                "bbox": [x0, y, x1 - x0, 13],
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            ocr_json = temporary_path / "ocr.json"

            source = fitz.open()
            source.new_page(width=595, height=842)
            source.new_page(width=595, height=842)
            source.save(source_pdf)
            source.close()

            ocr_data = [
                {
                    "lines": [
                        ocr_line("START", 72, 110, 50),
                        ocr_line("【A】阿澜：早安。", 90, 220, 100),
                        ocr_line(
                            "【A/B】阿澜、诺星河（接上）：数星星。",
                            90,
                            330,
                            140,
                        ),
                        ocr_line(
                            "星芽、云豆和月铃草从水晶门出来。",
                            200,
                            430,
                            180,
                        ),
                        ocr_line("【A】阿澜进入星舱。", 90, 240, 220),
                        # A genuine later cue may switch back to an ordinary
                        # bare label and must remain supported.
                        ocr_line("阿澜", 90, 120, 260),
                        ocr_line("NEXT", 90, 140, 300),
                    ]
                },
                {
                    "lines": [
                        ocr_line("附录：虚构角色表", 72, 190, 50),
                        ocr_line("轨道分配", 72, 140, 90),
                        # A role-table cell is not a spoken cue.
                        ocr_line("阿澜", 143, 170, 130),
                    ]
                },
            ]
            ocr_json.write_text(
                json.dumps(ocr_data),
                encoding="utf-8",
            )

            states = [
                {
                    "name": "Scene 1",
                    "key": "scene 1",
                    "cue": marker.cue_match_key("START"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                },
                {
                    "name": "Scene 2",
                    "key": "scene 2",
                    "cue": marker.cue_match_key("NEXT"),
                    "cue_speaker": "阿澜",
                    "position": "before",
                    "page_hint": "",
                },
            ]
            assignments = {
                "scene 1": {
                    "阿澜": "1",
                    "诺星河": "2",
                    "星芽": "3",
                    "云豆": "4",
                    "月铃草": "5",
                },
                "scene 2": {"阿澜": "9"},
            }

            marked_count, _, activated_states = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
                ocr_json_file=str(ocr_json),
            )

            document = fitz.open(marked_pdf)
            numbers = sorted(
                annotation.info.get("content", "")
                for page in document
                for annotation in page.annots() or []
                if re.fullmatch(
                    r"\d+(?:/\d+)*",
                    annotation.info.get("content", ""),
                )
            )
            document.close()

            self.assertEqual(marked_count, 3)
            self.assertEqual(numbers, ["1", "1", "1/2"])
            self.assertEqual(
                activated_states,
                {"scene 1", "scene 2"},
            )

    def test_mixed_style_spans_keep_speaker_dialogue_boundary(self):
        fragments = [
            {
                "bbox": (90, 321.98, 252, 335.95),
                "spans": [
                    {
                        "text": "林星遥",
                        "bbox": (90, 321.98, 126, 335.95),
                    },
                    {
                        "text": "今晚云层，闪着银光！",
                        "bbox": (132, 321.98, 252, 335.95),
                    },
                ],
            }
        ]

        visual_text = marker.join_visual_line_fragments(
            fragments,
            {"林星遥"},
        )

        self.assertEqual(visual_text, "林星遥 今晚云层，闪着银光！")
        self.assertEqual(
            marker.get_speaker_names(visual_text, {"林星遥"}),
            ["林星遥"],
        )
        self.assertTrue(
            marker.looks_like_speaker_label(visual_text, "林星遥")
        )

        existing_space_text = marker.join_visual_line_fragments(
            [
                {
                    "bbox": (90, 350, 114, 364),
                    "spans": [
                        {
                            "text": "云舟 ",
                            "bbox": (90, 350, 114, 364),
                        }
                    ],
                },
                {
                    "bbox": (154, 350, 252, 364),
                    "spans": [
                        {
                            "text": "下一段讯号",
                            "bbox": (154, 350, 252, 364),
                        }
                    ],
                },
            ],
            set(),
        )
        self.assertEqual(existing_space_text, "云舟 下一段讯号")

    def test_fragmented_chinese_speaker_label_activates_next_state(self):
        def ocr_line(text, x0, x1, y):
            return {
                "text": text,
                "bbox": [x0, y, x1 - x0, 13],
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            ocr_json = temporary_path / "ocr.json"

            source = fitz.open()
            source.new_page(width=595, height=842)
            source.save(source_pdf)
            source.close()

            # Some WPS-generated scripts store a bold speaker name, a trailing
            # digit, and the following dialogue as three separate PDF lines on
            # the same visual baseline. Small gaps belong inside the speaker
            # name; the larger gap before dialogue must remain a boundary.
            ocr_data = [
                {
                    "lines": [
                        ocr_line("START", 72, 110, 50),
                        ocr_line("星港卫兵", 90, 138, 100),
                        ocr_line("2", 141, 148.2, 100),
                        ocr_line(
                            "队长说了，只找那颗发蓝的星星，其他光点别动。",
                            160.2,
                            430,
                            100,
                        ),
                        ocr_line("陆星野", 90, 126, 150),
                        ocr_line("看哪里？！", 138, 220, 150),
                        ocr_line("星", 90, 102, 200),
                        ocr_line("岚", 114, 126, 200),
                        ocr_line("大家看星图。", 138, 230, 200),
                        ocr_line("【陆星野走进舱室】", 90, 230, 250),
                    ]
                }
            ]
            ocr_json.write_text(
                json.dumps(ocr_data),
                encoding="utf-8",
            )

            states = [
                {
                    "name": "S50",
                    "key": "s50",
                    "cue": marker.cue_match_key("START"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                },
                {
                    "name": "S51",
                    "key": "s51",
                    "cue": marker.cue_match_key("只找那颗发蓝的星星，"),
                    "cue_speaker": "星港卫兵2",
                    "position": "after",
                    "page_hint": "",
                },
            ]
            assignments = {
                "s50": {"星港卫兵2": "7"},
                "s51": {"陆星野": "2", "星岚": "8"},
            }

            marked_count, _, activated_states = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
                ocr_json_file=str(ocr_json),
            )

            document = fitz.open(marked_pdf)
            page = document[0]
            annotations = [
                annotation
                for annotation in page.annots() or []
                if re.fullmatch(
                    r"\d+(?:/\d+)*",
                    annotation.info.get("content", ""),
                )
            ]
            by_row = {
                y: [
                    annotation.info["content"]
                    for annotation in annotations
                    if abs(annotation.rect.y0 - y) < 1
                ]
                for y in (100, 150, 200, 250)
            }
            document.close()

            self.assertEqual(marked_count, 3)
            self.assertEqual(activated_states, {"s50", "s51"})
            self.assertEqual(by_row[100], ["7"])
            self.assertEqual(by_row[150], ["2"])
            self.assertEqual(by_row[200], ["8"])
            self.assertEqual(by_row[250], [])

    def test_chinese_groups_and_indented_dialogue_are_disambiguated(self):
        def ocr_line(text, x0, x1, y):
            return {
                "text": text,
                "bbox": [x0, y, x1 - x0, 13],
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            ocr_json = temporary_path / "ocr.json"

            source = fitz.open()
            source.new_page(width=595, height=842)
            source.save(source_pdf)
            source.close()

            ocr_data = [
                {
                    "lines": [
                        ocr_line("START", 72, 110, 50),
                        ocr_line("云洛：开场。", 72, 180, 100),
                        ocr_line("星米娅：回应。", 72, 190, 140),
                        ocr_line("云洛和月卡拉：一起唱。", 72, 260, 180),
                        ocr_line("星米娅和月卡拉：（唱）", 72, 270, 220),
                        ocr_line(
                            "星米娅、月卡拉，和云洛 （唱）：",
                            72,
                            320,
                            260,
                        ),
                        ocr_line(
                            "星米娅，我看见蓝色流星了。",
                            144,
                            340,
                            300,
                        ),
                        ocr_line("星米娅。", 180, 240, 340),
                        ocr_line(
                            "云洛，你能过来跟我一起看星吗？",
                            144,
                            360,
                            380,
                        ),
                        # A no-colon cue remains valid when it is aligned with
                        # the trusted speaker column established above.
                        ocr_line("星米娅。", 72, 132, 420),
                        # A short comma suffix can describe delivery rather
                        # than addressed dialogue, as in ``云洛，合唱``.
                        ocr_line("云洛，合唱", 260, 340, 460),
                        ocr_line("【星米娅走进舱室】", 72, 220, 500),
                    ]
                }
            ]
            ocr_json.write_text(
                json.dumps(ocr_data),
                encoding="utf-8",
            )

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
            assignments = {
                "scene 1": {
                    "月卡拉": "1",
                    "云洛": "2",
                    "星米娅": "3",
                }
            }

            marked_count, unmatched_names, _ = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
                ocr_json_file=str(ocr_json),
            )

            document = fitz.open(marked_pdf)
            page = document[0]
            annotations = [
                annotation
                for annotation in page.annots() or []
                if re.fullmatch(
                    r"\d+(?:/\d+)*",
                    annotation.info.get("content", ""),
                )
            ]
            by_row = {
                y: [
                    annotation.info["content"]
                    for annotation in annotations
                    if abs(annotation.rect.y0 - y) < 1
                ]
                for y in (
                    100,
                    140,
                    180,
                    220,
                    260,
                    300,
                    340,
                    380,
                    420,
                    460,
                    500,
                )
            }
            document.close()

            self.assertEqual(marked_count, 7)
            self.assertEqual(by_row[100], ["2"])
            self.assertEqual(by_row[140], ["3"])
            self.assertEqual(by_row[180], ["1/2"])
            self.assertEqual(by_row[220], ["1/3"])
            self.assertEqual(by_row[260], ["1/2/3"])
            self.assertEqual(by_row[300], [])
            self.assertEqual(by_row[340], [])
            self.assertEqual(by_row[380], [])
            self.assertEqual(by_row[420], ["3"])
            self.assertEqual(by_row[460], ["2"])
            self.assertEqual(by_row[500], [])
            self.assertEqual(unmatched_names, [])

    def test_full_stop_label_can_inherit_the_previous_page_column(self):
        def ocr_line(text, x0, x1, y):
            return {
                "text": text,
                "bbox": [x0, y, x1 - x0, 13],
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            ocr_json = temporary_path / "ocr.json"

            source = fitz.open()
            source.new_page(width=595, height=842)
            source.new_page(width=595, height=842)
            source.save(source_pdf)
            source.close()

            ocr_data = [
                {
                    "lines": [
                        ocr_line("START", 72, 110, 50),
                        ocr_line("云洛：开场。", 72, 180, 100),
                    ]
                },
                {
                    "lines": [
                        ocr_line("月卡拉：另一栏。", 300, 430, 100),
                        ocr_line("星米娅。", 72, 132, 160),
                        ocr_line("星米娅。", 180, 240, 220),
                    ]
                },
            ]
            ocr_json.write_text(
                json.dumps(ocr_data),
                encoding="utf-8",
            )

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
            assignments = {
                "scene 1": {
                    "月卡拉": "1",
                    "云洛": "2",
                    "星米娅": "3",
                }
            }

            marked_count, _, _ = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
                ocr_json_file=str(ocr_json),
            )

            document = fitz.open(marked_pdf)
            rows = {}
            for page_number, page in enumerate(document, start=1):
                for annotation in page.annots() or []:
                    content = annotation.info.get("content", "")
                    if re.fullmatch(r"\d+(?:/\d+)*", content):
                        rows[
                            (page_number, round(annotation.rect.y0))
                        ] = content
            document.close()

            self.assertEqual(marked_count, 3)
            self.assertEqual(rows[(1, 100)], "2")
            self.assertEqual(rows[(2, 100)], "1")
            self.assertEqual(rows[(2, 160)], "3")
            self.assertNotIn((2, 220), rows)

    def test_close_speaker_columns_split_without_splitting_shared_labels(self):
        def ocr_line(text, x0, x1, y):
            return {
                "text": text,
                "bbox": [x0, y, x1 - x0, 13],
            }

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"
            ocr_json = temporary_path / "ocr.json"

            source = fitz.open()
            source.new_page(width=595, height=842)
            source.save(source_pdf)
            source.close()

            ocr_data = [
                {
                    "lines": [
                        ocr_line("START", 72, 110, 50),
                        ocr_line("ZEV.", 133.05, 156.52, 100),
                        ocr_line(
                            "VOR/STARKEEP/ (BACKGROUND)",
                            216.33,
                            299.90,
                            100,
                        ),
                        ocr_line("LUX.", 349.16, 372.63, 100),
                        ocr_line("RYNN.", 443.12, 466.59, 100),
                        ocr_line("VELA &", 100, 145, 160),
                        ocr_line("HÉ LÈ NE.", 195, 260, 160),
                        ocr_line("VELOR.", 100, 140, 220),
                        ocr_line("PAXEN, signal.", 190, 280, 220),
                        ocr_line("(LUX enters)", 100, 180, 280),
                    ]
                }
            ]
            ocr_json.write_text(
                json.dumps(ocr_data),
                encoding="utf-8",
            )

            states = [
                {
                    "name": "S104",
                    "key": "s104",
                    "cue": marker.cue_match_key("START"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                }
            ]
            assignments = {
                "s104": {
                    "zev": "5",
                    "vor": "3",
                    "starkeep": "4",
                    "lux": "2",
                    "rynn": "1",
                    "vela": "6",
                    "helene": "7",
                    "velor": "8",
                    "paxen": "9",
                }
            }

            marked_count, _, _ = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
                ocr_json_file=str(ocr_json),
            )

            document = fitz.open(marked_pdf)
            page = document[0]
            annotations = [
                annotation
                for annotation in page.annots() or []
                if re.fullmatch(
                    r"\d+(?:/\d+)*",
                    annotation.info.get("content", ""),
                )
            ]
            by_row = {
                y: [
                    annotation.info["content"]
                    for annotation in sorted(
                        annotations,
                        key=lambda item: item.rect.x0,
                    )
                    if abs(annotation.rect.y0 - y) < 1
                ]
                for y in (100, 160, 220, 280)
            }
            annotation_contents = [
                annotation.info["content"] for annotation in annotations
            ]
            document.close()

            self.assertEqual(marked_count, 6)
            self.assertEqual(by_row[100], ["5", "3/4", "2", "1"])
            self.assertEqual(by_row[160], ["6/7"])
            self.assertEqual(by_row[220], ["8"])
            self.assertEqual(by_row[280], [])
            self.assertNotIn("9", annotation_contents)

    def test_tight_cjk_duet_columns_and_tabbed_right_speaker_both_mark(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((72, 50), "START", fontsize=11)

            cjk_font = "cjk"
            cjk_font_file = marker.CHINESE_FONT_FILE
            font_size = 11.88

            # Two independent lyric columns share a baseline, but the gap
            # between their first lines is below the old unconditional
            # 60-point split threshold.
            page.insert_text(
                (72, 100),
                "姚澜       我想要的到底是什么现在呢",
                fontsize=font_size,
                fontname=cjk_font,
                fontfile=cjk_font_file,
            )
            page.insert_text(
                (297, 100),
                "程柯文     他会答应我的请求吗",
                fontsize=font_size,
                fontname=cjk_font,
                fontfile=cjk_font_file,
            )

            # Word can place a right-column speaker after a long tab inside
            # the same extracted span as the left lyric. The following
            # right-hand fragment is that speaker's first lyric.
            page.insert_text(
                (72, 180),
                "姚澜",
                fontsize=font_size,
                fontname=cjk_font,
                fontfile=cjk_font_file,
            )
            page.insert_text(
                (135, 180),
                "遇见你的画面                                  周文卓",
                fontsize=font_size,
                fontname=cjk_font,
                fontfile=cjk_font_file,
            )
            page.insert_text(
                (388, 180),
                "告别你的画面",
                fontsize=font_size,
                fontname=cjk_font,
                fontfile=cjk_font_file,
            )

            # A similar tabbed name without a separate left speaker anchor
            # is dialogue text, not a second-column cue.
            page.insert_text(
                (144, 260),
                "人生孤独                                    程柯文    为他干杯",
                fontsize=font_size,
                fontname=cjk_font,
                fontfile=cjk_font_file,
            )
            source.save(source_pdf)
            source.close()

            states = [{
                "name": "Scene 100",
                "key": "scene 100",
                "cue": marker.cue_match_key("START"),
                "cue_speaker": "",
                "position": "before",
                "page_hint": "",
            }]
            assignments = {
                "scene 100": {
                    "姚澜": "1",
                    "程柯文": "2",
                    "周文卓": "3",
                }
            }

            marked_count, unmatched_names, _ = marker.mark_pdf(
                states,
                assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
            )

            document = fitz.open(marked_pdf)
            number_annotations = []
            for annotation in document[0].annots() or []:
                content = annotation.info.get("content", "")
                if re.fullmatch(r"\d+(?:/\d+)*", content):
                    number_annotations.append({
                        "content": content,
                        "x0": annotation.rect.x0,
                        "y0": annotation.rect.y0,
                    })
            by_row = {
                y: [
                    annotation["content"]
                    for annotation in sorted(
                        number_annotations,
                        key=lambda item: item["x0"],
                    )
                    if abs(annotation["y0"] - y) < 1
                ]
                for y in (90, 170, 250)
            }
            right_x_positions = [
                annotation["x0"]
                for annotation in number_annotations
                if annotation["content"] in {"2", "3"}
            ]
            document.close()

            self.assertEqual(marked_count, 4)
            self.assertEqual(by_row[90], ["1", "2"])
            self.assertEqual(by_row[170], ["1", "3"])
            self.assertEqual(by_row[250], [])
            self.assertTrue(
                all(position > 200 for position in right_x_positions)
            )
            self.assertEqual(len(unmatched_names), 1)
            self.assertIn("人生孤独", unmatched_names[0][2])


class ReviewSafetyWarningTests(unittest.TestCase):
    def setUp(self):
        self.states = [
            {
                "name": "Scene 1",
                "key": "scene 1",
                "cue": marker.cue_match_key("START"),
                "cue_speaker": "",
                "position": "before",
                "page_hint": "",
            },
            {
                "name": "Scene 2",
                "key": "scene 2",
                "cue": marker.cue_match_key("NEXT"),
                "cue_speaker": "",
                "position": "before",
                "page_hint": "",
            },
        ]
        self.assignments = {
            "scene 1": {"lyria": "1", "vexel": "2"},
            "scene 2": {"lyria": "3"},
        }

    def notice_codes(self, *args, **kwargs):
        return {
            notice["code"]
            for notice in marker.build_review_notices(*args, **kwargs)
        }

    def test_high_risk_failures_are_deduplicated(self):
        no_states = marker.build_review_notices(
            [], {}, 0, set(), diagnostics={"full_document": True}
        )
        self.assertEqual(
            [notice["code"] for notice in no_states],
            ["NO_STATES_CONFIGURED"],
        )

        no_activation = marker.build_review_notices(
            self.states,
            self.assignments,
            0,
            set(),
            diagnostics={"full_document": True},
        )
        self.assertEqual(
            [notice["code"] for notice in no_activation],
            ["NO_STATES_ACTIVATED"],
        )
        self.assertEqual(no_activation[0]["severity"], "critical")

        first_missing = self.notice_codes(
            self.states,
            self.assignments,
            1,
            {"scene 2"},
            diagnostics={
                "full_document": True,
                "marked_pages": [16],
            },
        )
        self.assertEqual(first_missing, {"FIRST_STATE_NOT_ACTIVATED"})

    def test_zero_mark_warning_respects_legend_and_partial_exports(self):
        full_notices = marker.build_review_notices(
            self.states[:1],
            self.assignments,
            0,
            {"scene 1"},
            diagnostics={"full_document": True},
        )
        self.assertEqual(full_notices[0]["code"], "ZERO_CUES_MARKED")
        self.assertEqual(full_notices[0]["severity"], "critical")
        self.assertIn("speaker-label layout", full_notices[0]["message"])
        self.assertIn("names and aliases", full_notices[0]["message"])
        self.assertIn("PDF text is selectable", full_notices[0]["message"])

        partial_notices = marker.build_review_notices(
            self.states[:1],
            self.assignments,
            0,
            {"scene 1"},
            diagnostics={"full_document": False},
        )
        self.assertEqual(partial_notices[0]["code"], "ZERO_CUES_MARKED")
        self.assertEqual(partial_notices[0]["severity"], "warning")

        legend_notices = marker.build_review_notices(
            self.states[:1],
            self.assignments,
            0,
            {"scene 1"},
            diagnostics={"full_document": True},
            legend_only=True,
        )
        self.assertEqual(legend_notices, [])

    def test_zero_mark_completion_result_and_report_are_critical(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            template_file = temporary_path / "template.xlsx"
            output_folder = temporary_path / "output"
            result_file = temporary_path / "result.json"
            output_folder.mkdir()

            source = fitz.open()
            page = source.new_page(width=612, height=792)
            page.insert_text((72, 50), "START", fontsize=11)
            page.insert_text((100, 100), "VEXEL:", fontsize=11)
            page.insert_text((150, 100), "Nothing is assigned.", fontsize=11)
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
            worksheet.append(["Scene 1", "START", "Before", "LYRIA"])
            workbook.save(template_file)
            workbook.close()

            completion = {}
            marked_count, _, review_report = marker.run_marker(
                str(template_file),
                str(source_pdf),
                str(output_folder),
                editable=True,
                result_json_file=str(result_file),
                result_data=completion,
            )
            saved_result = json.loads(
                result_file.read_text(encoding="utf-8")
            )
            report = Path(review_report).read_text(encoding="utf-8")

            self.assertEqual(marked_count, 0)
            self.assertEqual(saved_result, completion)
            self.assertEqual(saved_result["safety_level"], "critical")
            self.assertIn(
                "ZERO_CUES_MARKED",
                {
                    warning["code"]
                    for warning in saved_result["safety_warnings"]
                },
            )
            self.assertIn("Marked character cues: 0", report)
            self.assertIn("speaker-label layout", report)

    def test_sparse_long_script_does_not_trigger_a_density_warning(self):
        notices = marker.build_review_notices(
            self.states[:1],
            self.assignments,
            1,
            {"scene 1"},
            diagnostics={
                "full_document": True,
                "pdf_page_count": 100,
                "state_activation_pages": {"scene 1": 1},
                "marked_pages": [1],
                "known_speakers_without_active_assignment": [],
            },
        )
        self.assertEqual(notices, [])

    def test_name_only_placeholder_rows_do_not_trigger_a_warning(self):
        codes = self.notice_codes(
            self.states[:1],
            self.assignments,
            1,
            {"scene 1"},
            diagnostics={
                "full_document": True,
                "named_states_without_cues": ["Scene 108", "Scene 109"],
            },
        )
        self.assertEqual(codes, set())

        configured_codes = self.notice_codes(
            self.states[:1],
            self.assignments,
            1,
            {"scene 1"},
            diagnostics={
                "full_document": True,
                "assignment_states_without_start_cues": ["scene 108"],
            },
        )
        self.assertEqual(
            configured_codes,
            {"ASSIGNMENTS_WITHOUT_START_CUES"},
        )

    def test_positioned_unassigned_speaker_flags_incomplete_final_state(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            page = source.new_page(width=612, height=792)
            page.insert_text((72, 50), "START", fontsize=11)
            page.insert_text((100, 100), "LYRIA:", fontsize=11)
            page.insert_text((72, 150), "NEXT", fontsize=11)
            page.insert_text((100, 200), "VEXEL", fontsize=11)
            page.insert_text(
                (100, 250),
                "VEXEL traces the stars.",
                fontsize=11,
                fontname="heit",
            )
            page.insert_text((100, 275), "(VEXEL glides)", fontsize=11)
            source.save(source_pdf)
            source.close()

            diagnostics = {}
            result = marker.mark_pdf(
                self.states,
                self.assignments,
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
                diagnostics=diagnostics,
            )

            self.assertEqual(len(result), 3)
            self.assertEqual(result[0], 1)
            self.assertEqual(
                diagnostics["known_speakers_without_active_assignment"],
                [{
                    "page": 1,
                    "state": "scene 2",
                    "speakers": ["vexel"],
                    "label": "VEXEL",
                }],
            )

            notices = marker.build_review_notices(
                self.states,
                self.assignments,
                result[0],
                result[2],
                diagnostics=diagnostics,
            )
            final_state_notice = next(
                notice
                for notice in notices
                if notice["code"]
                == "POSSIBLE_INCOMPLETE_FINAL_STATE"
            )
            self.assertIn("PDF page 1", final_state_notice["message"])
            self.assertIn("Scene 2", final_state_notice["message"])
            self.assertIn("vexel", final_state_notice["message"])

            report_file = temporary_path / "review.txt"
            marker.write_review_report(
                self.states,
                result[0],
                result[1],
                result[2],
                str(report_file),
                notices=notices,
                diagnostics=diagnostics,
            )
            report = report_file.read_text(encoding="utf-8")
            self.assertIn(
                "Scene 2 | vexel | PDF page(s) 1 | 1 label(s) | "
                "Example: VEXEL",
                report,
            )

    def test_report_places_safety_summary_before_detail_lists(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            report_file = Path(temporary_directory) / "review.txt"
            notices = [{
                "code": "ZERO_CUES_MARKED",
                "severity": "critical",
                "message": "No DCA numbers were placed.",
            }]
            marker.write_review_report(
                self.states,
                0,
                [(1, "scene 1", "VEXEL")],
                {"scene 1"},
                str(report_file),
                notices=notices,
                diagnostics={"marked_pages": []},
            )
            report = report_file.read_text(encoding="utf-8")

            self.assertLess(
                report.index("Automatic safety check"),
                report.index("Possible character names"),
            )
            self.assertIn("Status: REVIEW REQUIRED", report)
            self.assertIn("Human review is always required", report)

    def test_run_marker_writes_structured_completion_result(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            template_file = temporary_path / "template.xlsx"
            output_folder = temporary_path / "output"
            result_file = temporary_path / "result.json"
            output_folder.mkdir()

            source = fitz.open()
            page = source.new_page(width=612, height=792)
            page.insert_text((72, 50), "START", fontsize=11)
            page.insert_text((100, 100), "LYRIA:", fontsize=11)
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
            worksheet.append(["Scene 1", "START", "Before", "LYRIA"])
            workbook.save(template_file)
            workbook.close()

            completion = {}
            marked_count, output_pdf, review_report = marker.run_marker(
                str(template_file),
                str(source_pdf),
                str(output_folder),
                editable=True,
                result_json_file=str(result_file),
                result_data=completion,
            )
            saved_result = json.loads(
                result_file.read_text(encoding="utf-8")
            )

            self.assertEqual(marked_count, 1)
            self.assertEqual(saved_result, completion)
            self.assertEqual(saved_result["schema_version"], 1)
            self.assertEqual(saved_result["safety_level"], "ok")
            self.assertEqual(saved_result["safety_warnings"], [])
            self.assertEqual(saved_result["activated_states"], ["scene 1"])
            self.assertEqual(saved_result["missing_states"], [])
            self.assertEqual(
                saved_result["state_activation_pages"],
                {"scene 1": 1},
            )
            self.assertEqual(
                saved_result["performer_role_mapping_pages"],
                {},
            )
            self.assertEqual(saved_result["marked_pages"], [1])
            self.assertEqual(saved_result["marked_page_counts"], {"1": 1})
            self.assertEqual(saved_result["marked_cue_counts"], [{
                "page": 1,
                "state": "scene 1",
                "speakers": ["lyria"],
                "dca": "1",
                "count": 1,
            }])
            self.assertEqual(saved_result["pdf_page_count"], 1)
            self.assertEqual(saved_result["output_pdf"], output_pdf)
            self.assertEqual(saved_result["review_report"], review_report)
            self.assertTrue(Path(output_pdf).exists())
            self.assertTrue(Path(review_report).exists())

    def test_performer_role_mapping_card_is_opt_in_single_annotation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            disabled_pdf = temporary_path / "disabled.pdf"
            enabled_pdf = temporary_path / "enabled.pdf"

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((72, 110), "START", fontsize=12)
            source.save(source_pdf)
            source.close()

            states = [{
                "name": "Scene 1",
                "key": "scene 1",
                "cue": marker.cue_match_key("START"),
                "cue_speaker": "",
                "position": "before",
                "page_hint": "",
                "performer_role_rows": [{
                    "dca": ["2"],
                    "performer": "Ben",
                    "roles": ["Barber", "Butcher", "Coach"],
                }],
            }]

            marker.mark_pdf(
                states,
                {"scene 1": {}},
                str(source_pdf),
                str(disabled_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                },
            )
            disabled = fitz.open(disabled_pdf)
            disabled_contents = [
                annotation.info.get("content", "")
                for annotation in disabled[0].annots() or []
            ]
            self.assertFalse(any(
                "Performer / Role Mapping" in content
                for content in disabled_contents
            ))
            disabled.close()

            diagnostics = {}
            marker.mark_pdf(
                states,
                {"scene 1": {}},
                str(source_pdf),
                str(enabled_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                    "show_performer_role_mapping": True,
                    "page_header_footer_text_colour": (0.0, 0.0, 1.0),
                    "page_header_footer_border_colour": (0.0, 0.0, 1.0),
                },
                diagnostics=diagnostics,
            )
            self.assertEqual(
                diagnostics["performer_role_mapping_pages"],
                {"scene 1": 1},
            )

            document = fitz.open(enabled_pdf)
            marked_page = document[0]
            mapping_annotations = [
                annotation
                for annotation in marked_page.annots() or []
                if "Performer / Role Mapping"
                in annotation.info.get("content", "")
            ]
            self.assertEqual(len(mapping_annotations), 1)
            annotation = mapping_annotations[0]
            self.assertIn("DCA 2 | Ben", annotation.info["content"])
            self.assertIn(
                "Barber / Butcher / Coach",
                annotation.info["content"],
            )
            self.assertEqual(annotation.type[1], "FreeText")
            self.assertAlmostEqual(annotation.border["width"], 0.8, places=3)
            _, appearance = document.xref_get_key(annotation.xref, "AP")
            self.assertNotEqual(appearance, "null")
            square_annotations = [
                candidate
                for candidate in marked_page.annots() or []
                if candidate.type[1] == "Square"
            ]
            self.assertEqual(square_annotations, [])
            document.close()

    def test_multiple_mapping_cards_on_one_page_do_not_overlap(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            page = source.new_page(width=595, height=842)
            page.insert_text((72, 180), "FIRST", fontsize=12)
            page.insert_text((72, 580), "SECOND", fontsize=12)
            source.save(source_pdf)
            source.close()

            states = [
                {
                    "name": "Scene 1",
                    "key": "scene 1",
                    "cue": marker.cue_match_key("FIRST"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                    "performer_role_rows": [{
                        "dca": ["1"],
                        "performer": "Ben",
                        "roles": ["Barber", "Coach"],
                    }],
                },
                {
                    "name": "Scene 2",
                    "key": "scene 2",
                    "cue": marker.cue_match_key("SECOND"),
                    "cue_speaker": "",
                    "position": "before",
                    "page_hint": "",
                    "performer_role_rows": [{
                        "dca": ["3"],
                        "performer": "Mary",
                        "roles": ["Queen", "Doctor"],
                    }],
                },
            ]

            marker.mark_pdf(
                states,
                {"scene 1": {}, "scene 2": {}},
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={
                    "font_name": "helv",
                    "font_file": None,
                    "show_performer_role_mapping": True,
                },
            )

            document = fitz.open(marked_pdf)
            mapping_rects = [
                fitz.Rect(annotation.rect)
                for annotation in document[0].annots() or []
                if "Performer / Role Mapping"
                in annotation.info.get("content", "")
            ]
            self.assertEqual(len(mapping_rects), 2)
            self.assertFalse(mapping_rects[0].intersects(mapping_rects[1]))
            document.close()

    def test_selected_page_export_carries_active_mapping_card_forward(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_pdf = temporary_path / "source.pdf"
            marked_pdf = temporary_path / "marked.pdf"

            source = fitz.open()
            first_page = source.new_page(width=595, height=842)
            first_page.insert_text((72, 110), "START", fontsize=12)
            source.new_page(width=595, height=842)
            source.save(source_pdf)
            source.close()

            states = [{
                "name": "Scene 1",
                "key": "scene 1",
                "cue": marker.cue_match_key("START"),
                "cue_speaker": "",
                "position": "before",
                "page_hint": "",
                "performer_role_rows": [{
                    "dca": ["1"],
                    "performer": "Ben",
                    "roles": ["Barber"],
                }],
            }]

            diagnostics = {}
            marker.mark_pdf(
                states,
                {"scene 1": {}},
                str(source_pdf),
                str(marked_pdf),
                editable=True,
                state_style={"show_performer_role_mapping": True},
                start_page=2,
                end_page=2,
                diagnostics=diagnostics,
            )

            document = fitz.open(marked_pdf)
            first_page_cards = [
                annotation
                for annotation in document[0].annots() or []
                if "Performer / Role Mapping"
                in annotation.info.get("content", "")
            ]
            second_page_cards = [
                annotation
                for annotation in document[1].annots() or []
                if "Performer / Role Mapping"
                in annotation.info.get("content", "")
            ]
            self.assertEqual(first_page_cards, [])
            self.assertEqual(len(second_page_cards), 1)
            self.assertEqual(
                diagnostics["performer_role_mapping_pages"],
                {"scene 1": 2},
            )
            document.close()


if __name__ == "__main__":
    unittest.main()
