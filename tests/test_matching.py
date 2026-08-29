import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import dca_script_marker as marker


class SpeakerMatchingTests(unittest.TestCase):
    def test_title_case_english_colon_labels_are_dialogue(self):
        characters = {"tessa", "nola"}

        for text, expected in (
            ("Tessa：蓝灯亮起，样例测试开始。", "tessa"),
            ("Nola: Start the sample run!", "nola"),
        ):
            with self.subTest(text=text):
                names = marker.get_speaker_names(text, characters)
                self.assertEqual(names, [expected])
                self.assertTrue(
                    marker.looks_like_speaker_label(text, expected)
                )

    def test_title_case_english_without_colon_stays_rejected(self):
        self.assertFalse(
            marker.looks_like_speaker_label(
                "Tessa crosses the test platform.",
                "tessa",
            )
        )
        self.assertFalse(
            marker.looks_like_speaker_label(
                "Alden. Calibration.",
                "alden",
            )
        )

    def test_inline_title_case_shared_label_requires_complete_group(self):
        characters = {"orin", "mira", "alden"}

        self.assertEqual(
            marker.get_inline_english_shared_speaker_names(
                "Orin & Mira. Is the sample beacon ready?",
                characters,
            ),
            ["orin", "mira"],
        )
        self.assertEqual(
            marker.get_inline_english_shared_speaker_names(
                "Alden. Calibration.",
                characters,
            ),
            [],
        )

    def test_cast_reference_heading_accepts_ae_ligature(self):
        page_text = {
            "blocks": [{
                "lines": [{
                    "spans": [{"text": "Dramatis Personæ"}],
                }],
            }],
        }

        self.assertTrue(marker.page_has_cast_reference_heading(page_text))

    def test_isolated_title_case_fragments_need_positioned_layout_evidence(self):
        characters = {"all", "dorian", "orin", "felix", "bram"}

        self.assertEqual(
            marker.get_split_english_speaker_fragment_names(
                "Dorian. 7",
                characters,
            ),
            ["dorian"],
        )
        self.assertEqual(
            marker.get_split_english_speaker_fragment_names(
                "Orin, Dorian & Felix.",
                characters,
            ),
            ["orin", "dorian", "felix"],
        )
        self.assertEqual(
            marker.get_split_english_speaker_fragment_names(
                "Alden. Calibration.",
                characters | {"alden"},
            ),
            [],
        )
        self.assertEqual(
            marker.get_split_english_speaker_fragment_names(
                "Bram",
                characters,
            ),
            [],
        )
        self.assertEqual(
            marker.get_split_english_speaker_fragment_names(
                "Bram",
                characters,
                allow_bare=True,
            ),
            ["bram"],
        )

        self.assertTrue(
            marker.looks_like_positioned_speaker_label(
                "Dorian. Sample line.",
                ["dorian"],
                72,
                [72],
                layout_speaker_names=["dorian"],
            )
        )
        self.assertFalse(
            marker.looks_like_positioned_speaker_label(
                "Dorian. Sample line.",
                ["dorian"],
                180,
                [72],
                layout_speaker_names=["dorian"],
            )
        )

    def test_stage_directions_are_not_dialogue_labels(self):
        cases = (
            ("【Tessa拿着蓝色方块，和Nola一起离开测试区。", "tessa"),
            ("[Nola: crosses the test platform]", "nola"),
            ("（岑队⻓：进入测试区）", "岑队长"),
        )

        for text, speaker in cases:
            with self.subTest(text=text):
                self.assertFalse(
                    marker.looks_like_speaker_label(text, speaker)
                )

    def test_cast_track_prefixes_are_bounded_speaker_metadata(self):
        characters = {"阿岚", "墨星河"}

        for text, expected in (
            ("【A】阿岚：蓝灯亮了！", ["阿岚"]),
            ("【A&B】阿岚&墨星河：同步测试。", ["阿岚", "墨星河"]),
            (
                "【A/B】阿岚、墨星河（接上）：继续校准。",
                ["阿岚", "墨星河"],
            ),
        ):
            with self.subTest(text=text):
                names = marker.get_speaker_names(text, characters)
                self.assertEqual(names, expected)
                self.assertTrue(
                    marker.looks_like_positioned_speaker_label(
                        text,
                        names,
                        90,
                        [90],
                    )
                )

        for text in (
            "【阿岚进入测试区】",
            "【A】阿岚进入测试区",
            "【A】阿岚 进入测试区：标记闪烁。",
            "【MUSIC: 阿岚进入】",
            "【AB】阿岚：这是无效的双字母轨道。",
        ):
            with self.subTest(stage_direction=text):
                self.assertFalse(
                    any(
                        name in characters
                        for name in marker.get_speaker_names(
                            text,
                            characters,
                        )
                    )
                )
                self.assertFalse(
                    marker.looks_like_speaker_label(text, "阿岚")
                )

    def test_chinese_name_led_narration_is_not_a_shared_label(self):
        characters = {"星星", "圆圆", "云尾巴"}
        self.assertEqual(
            marker.get_speaker_names(
                "星星、圆圆和云尾巴从蓝色拱门后面走出来。",
                characters,
            ),
            [],
        )

    def test_pdf_radical_long_matches_workbook_character(self):
        characters = {"岑队长"}
        text = "岑队⻓：校准完成，备用通道已经开启。"

        self.assertEqual(
            marker.speaker_match_key("岑队⻓："),
            marker.speaker_match_key("岑队长"),
        )
        self.assertEqual(
            marker.get_speaker_names(text, characters),
            ["岑队长"],
        )
        self.assertTrue(
            marker.looks_like_speaker_label(text, "岑队长")
        )

    def test_existing_uppercase_full_stop_labels_still_work(self):
        self.assertTrue(
            marker.looks_like_speaker_label(
                "ALDEN. Calibration.",
                "alden",
            )
        )
        self.assertTrue(
            marker.looks_like_speaker_label(
                "CLOCKWORK PILOT. Nova, the sample beacon is ready.",
                "clockwork pilot",
            )
        )

    def test_chinese_shared_speaker_labels_include_every_known_name(self):
        characters = {"蓝月儿", "青禾", "紫星河"}

        cases = (
            ("青禾和蓝月儿：蓝光闪烁——", ["青禾", "蓝月儿"]),
            ("紫星河和蓝月儿：（唱）", ["紫星河", "蓝月儿"]),
            (
                "紫星河、蓝月儿，和青禾 （唱）：",
                ["紫星河", "蓝月儿", "青禾"],
            ),
            ("青禾与蓝月儿：同步测试。", ["青禾", "蓝月儿"]),
            ("青禾，合唱：同步测试。", ["青禾"]),
            ("青禾，（唱）：同步测试。", ["青禾"]),
        )

        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    marker.get_speaker_names(text, characters),
                    expected,
                )

        for text in (
            "紫星河和蓝月儿：（唱）",
            "紫星河、蓝月儿，和青禾 （唱）：",
        ):
            with self.subTest(standalone=text):
                self.assertTrue(
                    marker.is_standalone_speaker_label(text, characters)
                )

    def test_unknown_chinese_group_member_is_not_a_partial_label(self):
        characters = {"蓝月儿", "青禾", "紫星河"}

        for text in (
            "青禾和未知角色：同步测试。",
            "青禾、未知角色：同步测试。",
        ):
            with self.subTest(text=text):
                self.assertEqual(
                    marker.get_speaker_names(text, characters),
                    [],
                )


class StateMatchingTests(unittest.TestCase):
    def setUp(self):
        self.scene_100 = {
            "name": "Fixture State A",
            "key": "fixture state a",
            "cue": marker.cue_match_key("M0《纸月车站》"),
            "cue_speaker": "",
            "position": "after",
            "page_hint": "3",
        }
        self.scene_101 = {
            "name": "Fixture State B",
            "key": "fixture state b",
            "cue": marker.cue_match_key("M1 《蓝灯与风铃》"),
            "cue_speaker": "",
            "position": "after",
            "page_hint": "5",
        }

    def test_page_hinted_cue_code_recovers_garbled_title(self):
        self.assertIs(
            marker.get_matching_state(
                [self.scene_100, self.scene_101],
                'M0!"#$%&',
                {"3"},
            ),
            self.scene_100,
        )
        self.assertIs(
            marker.get_matching_state(
                [self.scene_100, self.scene_101],
                "M1!'()*&",
                {"5"},
            ),
            self.scene_101,
        )

    def test_cue_code_does_not_activate_on_wrong_page(self):
        self.assertIsNone(
            marker.get_matching_state(
                [self.scene_100],
                'M0!"#$%&',
                {"2"},
            )
        )

    def test_exact_cue_on_wrong_page_reports_page_hint_mismatch(self):
        diagnostics = {}

        self.assertIsNone(
            marker.get_matching_state(
                [self.scene_100],
                "M0《纸月车站》",
                {"2", "33"},
                diagnostics=diagnostics,
                pdf_page_number=33,
            )
        )
        self.assertEqual(
            diagnostics["page_hint_mismatches"],
            [{
                "state_key": "fixture state a",
                "state_name": "Fixture State A",
                "cue": marker.cue_match_key("M0《纸月车站》"),
                "page_hint": "3",
                "pdf_page": 33,
                "observed_page_hints": ["2", "33"],
            }],
        )

        # Retrying the same visual line must not duplicate the report item.
        marker.get_matching_state(
            [self.scene_100],
            "M0《纸月车站》",
            {"2", "33"},
            diagnostics=diagnostics,
            pdf_page_number=33,
        )
        self.assertEqual(
            len(diagnostics["page_hint_mismatches"]),
            1,
        )

    def test_inexact_cue_matches_do_not_report_page_hint_mismatch(self):
        for text in (
            "M0《纸月车站》 appears in a sample index",
            'M0!"#$%&',
        ):
            with self.subTest(text=text):
                diagnostics = {}
                self.assertIsNone(
                    marker.get_matching_state(
                        [self.scene_100],
                        text,
                        {"2"},
                        diagnostics=diagnostics,
                        pdf_page_number=2,
                    )
                )
                self.assertNotIn(
                    "page_hint_mismatches",
                    diagnostics,
                )

    def test_page_hint_mismatch_is_exposed_as_review_notice(self):
        diagnostics = {
            "full_document": True,
            "page_hint_mismatches": [{
                "state_key": "fixture state a",
                "state_name": "Fixture State A",
                "cue": marker.cue_match_key("M0《纸月车站》"),
                "page_hint": "35",
                "pdf_page": 33,
                "observed_page_hints": ["33"],
            }],
        }

        notices = marker.build_review_notices(
            [self.scene_100],
            {},
            0,
            set(),
            diagnostics=diagnostics,
        )
        mismatch_notice = next(
            notice
            for notice in notices
            if notice["code"] == "PAGE_HINT_MISMATCH"
        )

        self.assertEqual(mismatch_notice["severity"], "warning")
        self.assertIn(
            "sequential PDF page position",
            mismatch_notice["message"],
        )
        self.assertIn(
            "number printed inside the script",
            mismatch_notice["message"],
        )
        self.assertIn("Fixture State A", mismatch_notice["message"])
        self.assertIn("PDF page 33", mismatch_notice["message"])
        self.assertIn("Page Hint 35", mismatch_notice["message"])

    def test_page_hint_mismatch_is_suppressed_after_state_activates(self):
        diagnostics = {
            "full_document": True,
            "page_hint_mismatches": [{
                "state_key": "fixture state a",
                "state_name": "Fixture State A",
                "cue": marker.cue_match_key("M0《纸月车站》"),
                "page_hint": "35",
                "pdf_page": 33,
                "observed_page_hints": ["33"],
            }],
        }

        notices = marker.build_review_notices(
            [self.scene_100],
            {},
            1,
            {"fixture state a"},
            diagnostics=diagnostics,
        )

        self.assertNotIn(
            "PAGE_HINT_MISMATCH",
            {notice["code"] for notice in notices},
        )

    def test_cue_identifier_requires_a_complete_leading_token(self):
        self.assertEqual(marker.cue_identifier("M1 《蓝灯与风铃》"), "m1")
        self.assertEqual(marker.cue_identifier("M10!789:&"), "m10")
        self.assertEqual(marker.cue_identifier("PB3《琥珀回声》"), "pb3")
        self.assertEqual(marker.cue_identifier("M1A transition"), "")
        self.assertEqual(marker.cue_identifier("prefix M1"), "")

    def test_cue_code_requires_a_page_hint_and_stays_unambiguous(self):
        no_hint = dict(self.scene_100, page_hint="")
        duplicate = dict(self.scene_100, name="Duplicate")

        self.assertIsNone(
            marker.get_matching_state([no_hint], 'M0!"#$%&', {"3"})
        )
        self.assertIsNone(
            marker.get_matching_state(
                [self.scene_100, duplicate],
                'M0!"#$%&',
                {"3"},
            )
        )

    def test_page_hint_alone_does_not_activate_state(self):
        self.assertIsNone(
            marker.get_matching_state(
                [self.scene_100],
                "unrelated text",
                {"3"},
            )
        )


class PageHintDetectionTests(unittest.TestCase):
    def setUp(self):
        self.page = SimpleNamespace(
            rect=SimpleNamespace(height=800),
        )

    @staticmethod
    def page_text(*lines):
        return {
            "blocks": [{
                "lines": [
                    {
                        "bbox": (72, y, 540, y + 14),
                        "spans": [
                            {
                                "text": text,
                                "bbox": (x, y, x + 30, y + 14),
                            }
                            for text, x in spans
                        ],
                    }
                    for y, spans in lines
                ],
            }],
        }

    def test_top_header_page_number_is_available_with_pdf_index(self):
        page_text = self.page_text(
            (18, [("FIXTURE SHOW", 72)]),
            (36, [("01/02/30", 260)]),
            (36, [("1", 510), ("7", 520)]),
        )

        self.assertEqual(
            marker.find_page_hints(
                self.page,
                18,
                page_text=page_text,
            ),
            {"17", "18"},
        )

    def test_footer_page_number_remains_supported(self):
        page_text = self.page_text(
            (730, [("Page ", 276), ("42", 306)]),
        )

        self.assertEqual(
            marker.find_page_hints(
                self.page,
                45,
                page_text=page_text,
            ),
            {"42", "45"},
        )

    def test_decorated_footer_page_number_is_supported(self):
        page_text = self.page_text(
            (730, [("~ 1 ~", 276)]),
            (90, [("~ 14 ~", 306)]),
            # A decorated number in the lower body is not a page footer.
            (620, [("~ 15 ~", 306)]),
            (744, [("~ 1/10/15 ~", 260)]),
        )

        self.assertEqual(
            marker.find_page_hints(
                self.page,
                2,
                page_text=page_text,
            ),
            {"1", "2"},
        )

    def test_body_number_and_number_inside_header_text_are_rejected(self):
        page_text = self.page_text(
            (36, [("Section ", 72), ("2", 112)]),
            # This is inside the former 15% header band but below the guarded
            # 10% band. Real musical scores can place DCA numbers here.
            (90, [("14", 306)]),
        )

        self.assertEqual(
            marker.find_page_hints(
                self.page,
                9,
                page_text=page_text,
            ),
            {"9"},
        )


if __name__ == "__main__":
    unittest.main()
