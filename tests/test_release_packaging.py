import re
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGING_ROOT = PROJECT_ROOT / "packaging" / "macos"
TEMPLATE_NAME = "DCA Script Marker — DCA State Template.xlsx"


class ReleasePackagingTests(unittest.TestCase):
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
