import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = ROOT / "macOS App/DCA Script Marker/DCA Script Marker"
sys.path.insert(0, str(ROOT))

import dca_script_marker as marker


@unittest.skipUnless(sys.platform == "darwin" and shutil.which("swiftc"), "macOS Swift compiler required")
class DCARolePickerTests(unittest.TestCase):
    def test_role_choices_preserve_the_linked_dca_name(self):
        harness = r'''
import Foundation

@main struct RolePickerChecks {
    static func main() throws {
        let source = [
            DCAProjectCharacter(dcaName: " Jack ", otherCharacters: "Student\nGuard\nstudent\nJack"),
            DCAProjectCharacter(dcaName: "Anna", otherCharacters: "Student"),
            DCAProjectCharacter(dcaName: "", otherCharacters: "Orphan"),
            DCAProjectCharacter(dcaName: "jack", otherCharacters: "guard"),
        ]
        let choices = projectRoleChoices(from: source)
        precondition(choices.map(\.role) == ["Student", "Guard", "Student"])
        precondition(choices.map(\.dcaName) == ["Jack", "Jack", "Anna"])
        precondition(Set(choices.map(\.key)).count == 3)
        precondition(projectRoleChoices(from: []).isEmpty)
        precondition(projectRoleChoices(from: [DCAProjectCharacter(dcaName: "Jack")]).isEmpty)
        let aliased = projectRoleChoices(from: [
            DCAProjectCharacter(dcaName: "Jack [John]", otherCharacters: "Student\nJack")
        ])
        precondition(aliased.map(\.role) == ["Student"])
        precondition(aliased[0].dcaName == "Jack [John]")
        let chinese = projectRoleChoices(from: [
            DCAProjectCharacter(dcaName: "小明", otherCharacters: "学生，老师\n学生")
        ])
        precondition(chinese.map(\.role) == ["学生", "老师"])
        precondition(chinese.allSatisfy { $0.dcaName == "小明" })
        let multipleRoles = projectRoleChoices(from: [
            DCAProjectCharacter(dcaName: "M6", otherCharacters: "张警官\n兄弟3\n手下1")
        ])
        precondition(multipleRoles.map(\.assignmentLabel) == ["M6 [张警官]", "M6 [兄弟3]", "M6 [手下1]"])
        precondition(multipleRoles.allSatisfy { $0.dcaName == "M6" })
        precondition(projectRoleAssignmentLabel(dcaName: "M6", role: "兄弟3") == "M6 [兄弟3]")
        precondition(projectRoleAssignmentLabel(dcaName: "Jack [John, J.]", role: "Student") == "Jack [John, J., Student]")
        precondition(projectRoleAssignmentLabel(dcaName: "Jack [John]", role: "Teacher [Professor, Tutor]") == "Jack [John, Teacher, Professor, Tutor]")
        precondition(projectRoleAssignmentLabel(dcaName: "Ｍ６ [兄弟３]", role: "兄弟３") == "M6 [兄弟3]")
        precondition(projectRoleAssignmentLabel(dcaName: "Jack", role: "jack").isEmpty)
        precondition(projectRoleAssignmentLabel(dcaName: "", role: "Student").isEmpty)
        for pair in [
            ("M6", "张警官"),
            ("M6", "兄弟3"),
            ("Jack [John, J.]", "Student"),
            ("Jack [John]", "Teacher [Professor, Tutor]"),
            ("Ｍ６ [兄弟３]", "兄弟３"),
        ] {
            print("LABEL\t\(projectRoleAssignmentLabel(dcaName: pair.0, role: pair.1))")
        }
        var updated = source
        updated[0].otherCharacters += "\nTeacher"
        let refreshed = projectRoleChoices(from: updated)
        precondition(refreshed.contains { $0.role == "Teacher" && $0.dcaName == "Jack" })
        var legacy = DCAProjectDocument.newProject()
        legacy.characters = [
            DCAProjectCharacter(dcaName: "Jack [John]", otherCharacters: "ALL\nStudent [Pupil, Kid]"),
            DCAProjectCharacter(dcaName: "Jane", otherCharacters: "ALL\nTeacher")
        ]
        legacy.legacyAssignmentSets = [
            LegacyDCAAssignmentSet(name: "ALL", members: "Jack [John, J.], Jane; New Name"),
            LegacyDCAAssignmentSet(name: "all", members: "Jane\nExtra"),
            LegacyDCAAssignmentSet(name: "UNUSED", members: "Unused Person")
        ]
        legacy.states[0].dcaAssignments[0] = "all\nJane"
        let originalData = try JSONEncoder().encode(legacy)
        var decoded = try JSONDecoder().decode(DCAProjectDocument.self, from: originalData)
        precondition(decoded.needsAssignmentConversion)
        decoded.normalise()
        precondition(!decoded.needsAssignmentConversion)
        precondition(decoded.states[0].dcaAssignments[0] == "all\nJack [John, J.]\nJane\nNew Name\nExtra", decoded.states[0].dcaAssignments[0])
        precondition(decoded.characters[0].otherCharacters == "Student [Pupil, Kid]")
        precondition(decoded.characters[1].otherCharacters == "Teacher")
        precondition(decoded.characters.contains { $0.dcaName == "Unused Person" })
        let convertedData = try JSONEncoder().encode(decoded)
        precondition(!String(decoding: convertedData, as: UTF8.self).contains("shared_groups"))
        let stable = decoded
        decoded.normalise()
        precondition(decoded == stable)
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let originalURL = directory.appendingPathComponent("Original.dcamarker")
        try originalData.write(to: originalURL)
        let firstCopy = try decoded.writeConvertedCopy(beside: originalURL)
        let secondCopy = try decoded.writeConvertedCopy(beside: originalURL)
        precondition(firstCopy != originalURL && firstCopy != secondCopy)
        let preservedOriginal = try Data(contentsOf: originalURL)
        precondition(preservedOriginal == originalData)
        let reopened = try JSONDecoder().decode(DCAProjectDocument.self, from: Data(contentsOf: firstCopy))
        precondition(reopened == decoded && !reopened.needsAssignmentConversion)
        decoded.states[0].dcaAssignments[0] = "ALL"
        decoded.normalise()
        precondition(decoded.states[0].dcaAssignments[0] == "ALL")
        print("Role picker checks passed")
    }
}
'''
        with tempfile.TemporaryDirectory(prefix="dca-role-picker-") as directory:
            directory = Path(directory)
            main = directory / "RolePickerChecks.swift"
            main.write_text(harness, encoding="utf-8")
            executable = directory / "RolePickerChecks"
            environment = dict(os.environ)
            environment["CLANG_MODULE_CACHE_PATH"] = str(directory / "clang-cache")
            compiled = subprocess.run(
                [
                    shutil.which("swiftc"),
                    "-module-cache-path", str(directory / "swift-cache"),
                    str(APP_SOURCE / "AppLanguage.swift"),
                    str(APP_SOURCE / "DCAProjectEditor.swift"),
                    str(main), "-o", str(executable),
                ],
                capture_output=True, text=True, timeout=180, env=environment,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            result = subprocess.run(
                [str(executable)], capture_output=True, text=True, timeout=20
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Role picker checks passed", result.stdout)
            app_labels = [
                line.split("\t", 1)[1]
                for line in result.stdout.splitlines()
                if line.startswith("LABEL\t")
            ]
            cases = [
                ("M6", "张警官"),
                ("M6", "兄弟3"),
                ("Jack [John, J.]", "Student"),
                ("Jack [John]", "Teacher [Professor, Tutor]"),
                ("Ｍ６ [兄弟３]", "兄弟３"),
            ]
            self.assertEqual(
                app_labels,
                [marker.excel_role_choice(owner, role) for owner, role in cases],
            )


if __name__ == "__main__":
    unittest.main()
