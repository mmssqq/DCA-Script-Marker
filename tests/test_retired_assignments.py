import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import dca_script_marker as marker


class RetiredAssignmentTests(unittest.TestCase):
    def fixture(self):
        project = marker.blank_project("Migration test")
        project["characters"] = [
            {"id": "jack", "dca_name": "Jack [John]", "other_characters": "ALL\nStudent [Pupil, Kid]"},
            {"id": "jane", "dca_name": "Jane", "other_characters": "ALL\nTeacher"},
        ]
        project["shared_groups"] = [
            {"name": "ALL", "members": "Jack [John, J.], Jane; New Name"},
            {"name": "all", "members": "Jane\nExtra"},
            {"name": "UNUSED", "members": "Unused Person"},
        ]
        project["states"] = [{"id": "s1", "name": "S1", "start_line_text": "Opening",
                              "dca_assignments": ["all\nJane", "Jack [John]", ""]}]
        return project

    def test_conversion_is_one_way_and_retains_aliases_and_unused_names(self):
        project = marker.convert_legacy_assignments(self.fixture())
        self.assertNotIn("shared_groups", project)
        self.assertEqual(project["states"][0]["dca_assignments"],
                         ["all\nJack [John, J.]\nJane\nNew Name\nExtra", "Jack [John]", ""])
        self.assertEqual(project["characters"][0]["other_characters"], "Student [Pupil, Kid]")
        self.assertEqual(project["characters"][1]["other_characters"], "Teacher")
        self.assertTrue({"ALL", "New Name", "Extra", "UNUSED", "Unused Person"}.issubset(
            {item["dca_name"] for item in project["characters"]}))
        before = copy.deepcopy(project)
        self.assertEqual(marker.convert_legacy_assignments(project), before)
        project["states"][0]["dca_assignments"][0] = "ALL"
        marker.convert_legacy_assignments(project)
        self.assertEqual(project["states"][0]["dca_assignments"][0], "ALL")

    def test_read_and_export_do_not_mutate_originals(self):
        project = self.fixture()
        before = copy.deepcopy(project)
        workbook = marker.project_to_workbook(project)
        self.addCleanup(workbook.close)
        self.assertEqual(project, before)
        self.assertNotIn("Shared Groups", workbook.sheetnames)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "old.dcamarker"
            path.write_text(json.dumps(project), encoding="utf-8")
            original = path.read_bytes()
            converted = marker.read_project_file(path)
            self.assertNotIn("shared_groups", converted)
            self.assertEqual(path.read_bytes(), original)

    def test_new_project_and_user_facing_material_have_no_retired_feature(self):
        self.assertNotIn("shared_groups", marker.blank_project())
        for relative in ("USER_GUIDE.md", "README.md", "RELEASE_NOTES.md", "TESTING_AND_SAFETY.md",
                         "macOS App/DCA Script Marker/DCA Script Marker/ContentView.swift",
                         "macOS App/DCA Script Marker/DCA Script Marker/AppLanguage.swift"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertFalse(
                any(term in text.casefold() for term in (
                    "shared group", "shared-group", "共享群组"
                )),
                f"Retired feature wording in {relative}",
            )
        editor = (ROOT / "macOS App/DCA Script Marker/DCA Script Marker/DCAProjectEditor.swift").read_text()
        self.assertNotIn("case sharedGroups", editor)
        self.assertNotIn("Add Shared Group", editor)
        self.assertIn("writeConvertedCopy(beside: url)", (ROOT / "macOS App/DCA Script Marker/DCA Script Marker/ContentView.swift").read_text())


if __name__ == "__main__":
    unittest.main()
