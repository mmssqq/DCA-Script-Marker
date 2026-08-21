import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import dca_script_marker as marker


class SpeakerMatchingTests(unittest.TestCase):
    def test_title_case_english_colon_labels_are_dialogue(self):
        characters = {"mary", "fanny"}

        for text, expected in (
            ("Mary：亲爱的，快许愿吹蜡烛吧。", "mary"),
            ("Fanny: Make a wish!", "fanny"),
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
                "Mary appears in the doorway.",
                "mary",
            )
        )
        self.assertFalse(
            marker.looks_like_speaker_label("Henri. Hello.", "henri")
        )

    def test_stage_directions_are_not_dialogue_labels(self):
        cases = (
            ("【Mary拿着蛋糕，和Fanny一起走出。", "mary"),
            ("[Fanny: enters]", "fanny"),
            ("（梁科⻓：走进房间）", "梁科长"),
        )

        for text, speaker in cases:
            with self.subTest(text=text):
                self.assertFalse(
                    marker.looks_like_speaker_label(text, speaker)
                )

    def test_pdf_radical_long_matches_workbook_character(self):
        characters = {"梁科长"}
        text = "梁科⻓：这个不用担心，我有方案和人选。"

        self.assertEqual(
            marker.speaker_match_key("梁科⻓："),
            marker.speaker_match_key("梁科长"),
        )
        self.assertEqual(
            marker.get_speaker_names(text, characters),
            ["梁科长"],
        )
        self.assertTrue(
            marker.looks_like_speaker_label(text, "梁科长")
        )

    def test_existing_uppercase_full_stop_labels_still_work(self):
        self.assertTrue(
            marker.looks_like_speaker_label("HENRI. Hello.", "henri")
        )
        self.assertTrue(
            marker.looks_like_speaker_label(
                "AMERICAN SOLDIER. Jerry, there you are.",
                "american soldier",
            )
        )


class StateMatchingTests(unittest.TestCase):
    def setUp(self):
        self.scene_100 = {
            "name": "Scene 100",
            "key": "scene 100",
            "cue": marker.cue_match_key("M0《无间地狱》"),
            "cue_speaker": "",
            "position": "after",
            "page_hint": "3",
        }
        self.scene_101 = {
            "name": "Scene 101",
            "key": "scene 101",
            "cue": marker.cue_match_key("M1 《光与黑暗》"),
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

    def test_cue_identifier_requires_a_complete_leading_token(self):
        self.assertEqual(marker.cue_identifier("M1 《光与黑暗》"), "m1")
        self.assertEqual(marker.cue_identifier("M10!789:&"), "m10")
        self.assertEqual(marker.cue_identifier("PB3《被遗忘的时光》"), "pb3")
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


if __name__ == "__main__":
    unittest.main()
