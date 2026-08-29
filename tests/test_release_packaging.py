import re
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

import fitz


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGING_ROOT = PROJECT_ROOT / "packaging" / "macos"
TEMPLATE_NAME = "DCA Script Marker — DCA State Template.xlsx"


class ReleasePackagingTests(unittest.TestCase):
    def test_monterey_deployment_target_is_consistent(self):
        project = (
            PROJECT_ROOT
            / "macOS App"
            / "DCA Script Marker"
            / "DCA Script Marker.xcodeproj"
            / "project.pbxproj"
        ).read_text(encoding="utf-8")
        content_view = (
            PROJECT_ROOT
            / "macOS App"
            / "DCA Script Marker"
            / "DCA Script Marker"
            / "ContentView.swift"
        ).read_text(encoding="utf-8")
        app_builder = (PACKAGING_ROOT / "build_private_beta.sh").read_text(
            encoding="utf-8"
        )
        engine_builder = (PACKAGING_ROOT / "build_engines.sh").read_text(
            encoding="utf-8"
        )
        source_builder = (PACKAGING_ROOT / "build_source_archive.sh").read_text(
            encoding="utf-8"
        )
        verifier = (PACKAGING_ROOT / "verify_beta_app.sh").read_text(
            encoding="utf-8"
        )

        self.assertEqual(project.count("MACOSX_DEPLOYMENT_TARGET = 12.0;"), 2)
        self.assertNotIn("MACOSX_DEPLOYMENT_TARGET = 13.0;", project)
        self.assertEqual(project.count("CURRENT_PROJECT_VERSION = 6;"), 2)
        self.assertEqual(project.count("MARKETING_VERSION = 1.0.0;"), 2)
        self.assertNotIn("path(percentEncoded: false)", content_view)

        for build_script in (app_builder, engine_builder):
            self.assertIn('DCA_MINIMUM_MACOS:-12.0', build_script)

        for build_script in (app_builder, engine_builder, source_builder):
            self.assertIn('DCA_BUILD_NUMBER:-6', build_script)
            self.assertIn('DCA_VERSION:-1.0.0', build_script)
        for release_script in (app_builder, source_builder):
            self.assertIn('DCA_RELEASE_CHANNEL:-stable', release_script)
            self.assertIn('DCA_RELEASE_CHANNEL must be stable or beta.', release_script)
        self.assertIn('RELEASE_TAG="v$APP_VERSION"', app_builder)
        self.assertIn('RELEASE_TAG="v$APP_VERSION-beta.$BUILD_NUMBER"', app_builder)
        self.assertIn('VOLUME_NAME="DCA Script Marker"', app_builder)
        self.assertIn('Release channel: %s\\n', app_builder)
        self.assertIn(
            'MACOSX_DEPLOYMENT_TARGET="$MINIMUM_MACOS_VERSION"', app_builder
        )
        self.assertIn(
            "printf 'Minimum macOS: %s\\n' \"$MINIMUM_MACOS_VERSION\"",
            app_builder,
        )
        self.assertIn(
            'LSMinimumSystemVersion -string "$MINIMUM_MACOS_VERSION"',
            engine_builder,
        )
        self.assertIn('DCA_MINIMUM_MACOS:-12.0', verifier)
        self.assertIn("LC_BUILD_VERSION", verifier)
        self.assertIn("LC_VERSION_MIN_MACOSX", verifier)

    def test_bilingual_user_guide_is_packaged(self):
        build_script = (PACKAGING_ROOT / "build_private_beta.sh").read_text(
            encoding="utf-8"
        )
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        guide = (PROJECT_ROOT / "USER_GUIDE.md").read_text(encoding="utf-8")
        guide_pdf = (
            PROJECT_ROOT
            / "output"
            / "pdf"
            / "START HERE - User Guide - 使用手册.pdf"
        )

        self.assertIn("USER_GUIDE.md", build_script)
        self.assertIn("START HERE - User Guide - 使用手册.pdf", build_script)
        self.assertIn("TESTING_AND_SAFETY.md", build_script)
        self.assertIn("ISSUE_REPORT_TEMPLATE.md", build_script)
        self.assertIn(
            'FEEDBACK_DOCUMENT_NAME="ISSUE_REPORT_TEMPLATE.md"', build_script
        )
        self.assertIn("Install and quick start / 安装与快速开始", readme)
        self.assertIn("Safety and limitations / 安全说明与限制", readme)
        self.assertIn("Version 1.0.0", guide)
        self.assertIn("Character List", guide)
        self.assertIn("Start Line Text", guide)
        self.assertIn("中文使用手册", guide)
        self.assertIn("故障排查与问题反馈", guide)
        self.assertTrue(guide_pdf.is_file())

        with fitz.open(guide_pdf) as document:
            self.assertGreaterEqual(document.page_count, 2)
            pdf_text = "\n".join(page.get_text() for page in document)

        self.assertIn("Install the app and copy the template", pdf_text)
        self.assertIn("安装软件并复制模板", pdf_text)
        self.assertIn("Version 1.0.0", pdf_text)

    def test_zero_mark_and_page_number_safety_copy_is_bundled(self):
        guide_pdf = (
            PROJECT_ROOT
            / "output"
            / "pdf"
            / "START HERE - User Guide - 使用手册.pdf"
        )
        content_view = (
            PROJECT_ROOT
            / "macOS App"
            / "DCA Script Marker"
            / "DCA Script Marker"
            / "ContentView.swift"
        ).read_text(encoding="utf-8")
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        guide = (PROJECT_ROOT / "USER_GUIDE.md").read_text(encoding="utf-8")
        testing = (PROJECT_ROOT / "TESTING_AND_SAFETY.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("No DCA numbers were added", content_view)
        self.assertIn("未添加任何 DCA 编号", content_view)
        self.assertIn('withTitle: "Try Another PDF"', content_view)
        self.assertIn("let generationStyle = selectedStyle", content_view)
        self.assertIn("completionResult.markedCount == 0", content_view)
        self.assertIn(
            'generationStyle != "DCA State Legend"',
            content_view,
        )
        for document in (readme, guide, testing):
            self.assertIn("Important page-number rule", document)
            self.assertIn("Page Hint", document)
            self.assertIn("Mark selected pages only", document)
            self.assertIn("PDF", document)
        self.assertIn("重要页码规则", readme)
        self.assertIn("重要页码规则", guide)
        with fitz.open(guide_pdf) as document:
            pdf_text = "\n".join(page.get_text() for page in document)
        self.assertIn("Important page-number rule", pdf_text)
        self.assertIn("重要页码规则", pdf_text)
        self.assertIn("If no dialogue DCA numbers are added", pdf_text)
        self.assertIn("如果没有添加任何对白 DCA 编号", pdf_text)

    def test_macos_version_comparison_executes(self):
        verifier = PACKAGING_ROOT / "verify_beta_app.sh"
        cases = (
            ("13.0", "12.0", 0),
            ("12.1", "12.0", 0),
            ("12.0", "12.0", 1),
            ("11.6.9", "12.0", 1),
            ("invalid", "12.0", 2),
        )

        for candidate, maximum, expected_status in cases:
            with self.subTest(candidate=candidate, maximum=maximum):
                result = subprocess.run(
                    [
                        str(verifier),
                        "--version-is-greater",
                        candidate,
                        maximum,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_status)

    def test_source_archive_is_published_beside_not_inside_installer(self):
        build_script = (PACKAGING_ROOT / "build_private_beta.sh").read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            'ditto "$SOURCE_ARCHIVE" "$PACKAGE_ROOT/', build_script
        )
        self.assertIn(
            '"$(basename "$SOURCE_ARCHIVE")"', build_script
        )
        self.assertIn(
            'echo "Matching source archive: $SOURCE_ARCHIVE"', build_script
        )
        self.assertIn(
            '[[ -e "$PACKAGE_ROOT/$(basename "$SOURCE_ARCHIVE")" ]]',
            build_script,
        )

    def test_source_allowlist_is_complete_and_private_data_free(self):
        allowlist_path = PACKAGING_ROOT / "source-files.txt"
        entries = [
            line.strip()
            for line in allowlist_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]

        self.assertEqual(len(entries), len(set(entries)))
        for entry in entries:
            self.assertFalse(Path(entry).is_absolute())
            self.assertNotIn("..", Path(entry).parts)
            self.assertTrue((PROJECT_ROOT / entry).is_file(), entry)

        joined = "\n".join(entries).lower()
        for forbidden in (
            ".venv",
            ".ds_store",
            "xcuserdata",
            ".xcuserstate",
            "review_",
            "marked_",
            "sample_script",
            "app_ui_backup",
        ):
            self.assertNotIn(forbidden, joined)

    def test_dependency_source_manifest_is_locked_and_https_only(self):
        manifest = PACKAGING_ROOT / "source-dependencies.tsv"
        rows = []
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            sha256, filename, url = line.split("\t")
            self.assertRegex(sha256, r"^[0-9a-f]{64}$")
            self.assertNotIn("/", filename)
            self.assertTrue(url.startswith("https://"))
            rows.append((sha256, filename, url))

        self.assertEqual(len(rows), len({row[1] for row in rows}))
        self.assertIn("pymupdf-1.27.2.3.tar.gz", {row[1] for row in rows})
        self.assertIn("mupdf-1.27.2-source.tar.gz", {row[1] for row in rows})
        self.assertIn("Python-3.11.5.tgz", {row[1] for row in rows})

    def test_release_template_removes_only_absolute_path_metadata(self):
        source = PROJECT_ROOT / TEMPLATE_NAME
        sanitizer = PACKAGING_ROOT / "sanitize_template.sh"

        with tempfile.TemporaryDirectory() as temp_directory:
            output = Path(temp_directory) / TEMPLATE_NAME
            subprocess.run(
                [str(sanitizer), str(source), str(output)],
                check=True,
                capture_output=True,
                text=True,
            )

            with zipfile.ZipFile(source) as original_zip, zipfile.ZipFile(
                output
            ) as sanitized_zip:
                self.assertEqual(
                    set(original_zip.namelist()), set(sanitized_zip.namelist())
                )
                for member in original_zip.namelist():
                    if member != "xl/workbook.xml":
                        self.assertEqual(
                            original_zip.read(member), sanitized_zip.read(member)
                        )

                original_xml = original_zip.read("xl/workbook.xml")
                expected_xml = re.sub(
                    rb"<mc:AlternateContent\b[^>]*>.*?"
                    rb"<x15ac:absPath\b[^>]*/>.*?"
                    rb"</mc:AlternateContent>",
                    b"",
                    original_xml,
                    flags=re.DOTALL,
                )
                sanitized_xml = sanitized_zip.read("xl/workbook.xml")

            self.assertNotIn(b"x15ac:absPath", sanitized_xml)
            self.assertNotIn(b"/Users/", sanitized_xml)
            self.assertEqual(expected_xml, sanitized_xml)


if __name__ == "__main__":
    unittest.main()
