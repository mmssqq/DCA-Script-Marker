import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import fitz

from tools import run_real_script_regressions as runner


class RealScriptRegressionRunnerTests(unittest.TestCase):
    def create_pdf(self, path):
        document = fitz.open()
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 100), "Synthetic regression source")
        document.save(path)
        document.close()

    def write_fake_marker(self, path):
        path.write_text(
            textwrap.dedent(
                """
                import argparse
                import json
                import shutil
                from pathlib import Path

                parser = argparse.ArgumentParser()
                parser.add_argument("--template")
                parser.add_argument("--script")
                parser.add_argument("--output")
                parser.add_argument("--output-mode")
                parser.add_argument("--result-json-file")
                arguments = parser.parse_args()

                output = Path(arguments.output)
                output_pdf = output / "synthetic_marked.pdf"
                review_report = output / "synthetic_review.txt"
                shutil.copyfile(arguments.script, output_pdf)
                review_report.write_text("Synthetic review", encoding="utf-8")
                result = {
                    "schema_version": 1,
                    "marked_count": 3,
                    "output_pdf": str(output_pdf),
                    "review_report": str(review_report),
                    "safety_level": "ok",
                    "safety_warning_count": 0,
                    "safety_warnings": [],
                    "configured_state_count": 1,
                    "activated_state_count": 1,
                    "missing_state_count": 0,
                    "unmatched_name_count": 0,
                    "activated_states": ["scene 1"],
                    "missing_states": [],
                    "state_activation_pages": {"scene 1": 1},
                    "marked_pages": [1],
                    "marked_page_counts": {"1": 3},
                    "marked_cue_counts": [{
                        "page": 1,
                        "state": "scene 1",
                        "speakers": ["SYNTHETIC"],
                        "dca": "1",
                        "count": 3,
                    }],
                    "pdf_page_count": 1,
                }
                Path(arguments.result_json_file).write_text(
                    json.dumps(result),
                    encoding="utf-8",
                )
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    def create_private_pack(self, root):
        assets = root / "assets"
        case_directory = assets / "Sample"
        case_directory.mkdir(parents=True)
        script = case_directory / "clean-script.pdf"
        template = case_directory / "DCA.xlsx"
        self.create_pdf(script)
        template.write_bytes(b"synthetic workbook placeholder")

        manifest = root / "manifest.json"
        manifest.write_text(
            json.dumps({
                "schema_version": 1,
                "cases": [{
                    "id": "sample",
                    "label": "Synthetic sample",
                    "suites": ["smoke", "full"],
                    "script": "Sample/clean-script.pdf",
                    "template": "Sample/DCA.xlsx",
                    "assertions": {
                        "required_mark_pages": [1],
                        "forbidden_mark_pages": [],
                    },
                }],
            }),
            encoding="utf-8",
        )
        marker = root / "fake_marker.py"
        self.write_fake_marker(marker)
        return assets, manifest, marker

    def test_manifest_rejects_generated_and_escaping_inputs(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets = root / "assets"
            case_directory = assets / "Sample"
            case_directory.mkdir(parents=True)
            generated = case_directory / "script_marked_2026-08-28.pdf"
            template = case_directory / "DCA.xlsx"
            generated.touch()
            template.touch()
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps({
                    "schema_version": 1,
                    "cases": [{
                        "id": "unsafe",
                        "script": "Sample/script_marked_2026-08-28.pdf",
                        "template": "Sample/DCA.xlsx",
                    }],
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                runner.RegressionSetupError,
                "marked PDFs cannot be inputs",
            ):
                runner.load_manifest(manifest, assets)

            with self.assertRaisesRegex(
                runner.RegressionSetupError,
                "must be relative",
            ):
                runner.resolve_private_asset(
                    assets,
                    "../outside.pdf",
                    expected_suffix=".pdf",
                    description="escaping script",
                )

    def test_manifest_arguments_use_style_only_allowlist(self):
        self.assertEqual(
            runner.validate_arguments(
                "safe",
                [
                    "--style=Full Marking",
                    "--number-y-offset",
                    "-1.5",
                    "--page-state-header-footer",
                ],
            ),
            (
                "--style",
                "Full Marking",
                "--number-y-offset",
                "-1.5",
                "--page-state-header-footer",
            ),
        )
        for unsafe in (
            ["--ocr-json", "outside.json"],
            ["--legend-overrides-file", "outside.json"],
            ["--scr", "outside.pdf"],
            ["--self-test"],
            ["--result-json-file=outside.json"],
        ):
            with self.subTest(arguments=unsafe), self.assertRaisesRegex(
                runner.RegressionSetupError,
                "not allowed",
            ):
                runner.validate_arguments("unsafe", unsafe)

    def test_manifest_rejects_unknown_critical_bypass(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets, manifest, _ = self.create_private_pack(root)
            value = json.loads(manifest.read_text(encoding="utf-8"))
            value["cases"][0]["allow_critical"] = "false"
            manifest.write_text(json.dumps(value), encoding="utf-8")

            with self.assertRaisesRegex(
                runner.RegressionSetupError,
                "Unsupported manifest case field",
            ):
                runner.load_manifest(manifest, assets)

    def test_accept_compare_and_mismatch_exit_codes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets, manifest, marker = self.create_private_pack(root)
            baseline = root / "approved_baseline.json"

            common = [
                "--assets-root",
                str(assets),
                "--manifest",
                str(manifest),
                "--baseline",
                str(baseline),
                "--marker",
                str(marker),
                "--python",
                sys.executable,
                "--jobs",
                "1",
            ]

            accepted = runner.main(
                common
                + [
                    "--accept-current",
                    "--all",
                    "--output-root",
                    str(root / "accept-output"),
                ]
            )
            self.assertEqual(accepted, 0)
            self.assertTrue(baseline.is_file())
            baseline_record = json.loads(
                baseline.read_text(encoding="utf-8")
            )["cases"]["sample"]["inputs"]
            self.assertEqual(baseline_record["arguments"], [])
            self.assertIn("assertions", baseline_record)
            self.assertEqual(len(baseline_record["config_sha256"]), 64)
            self.assertEqual(
                baseline_record["script"],
                "Sample/clean-script.pdf",
            )
            self.assertFalse(
                (root / "accept-output" / "sample" / ".isolated-inputs").exists()
            )

            matched = runner.main(
                common
                + [
                    "--all",
                    "--output-root",
                    str(root / "match-output"),
                ]
            )
            self.assertEqual(matched, 0)

            changed_baseline = json.loads(
                baseline.read_text(encoding="utf-8")
            )
            changed_baseline["cases"]["sample"]["metrics"][
                "marked_count"
            ] = 2
            baseline.write_text(
                json.dumps(changed_baseline),
                encoding="utf-8",
            )

            changed = runner.main(
                common
                + [
                    "--all",
                    "--output-root",
                    str(root / "changed-output"),
                ]
            )
            self.assertEqual(changed, runner.EXIT_REGRESSION)

    def test_engine_runs_against_copies_not_original_assets(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets, manifest, _ = self.create_private_pack(root)
            source = assets / "Sample" / "clean-script.pdf"
            original_bytes = source.read_bytes()
            destructive_marker = root / "destructive_marker.py"
            destructive_marker.write_text(
                textwrap.dedent(
                    """
                    import argparse
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--template")
                    parser.add_argument("--script")
                    parser.add_argument("--output")
                    parser.add_argument("--output-mode")
                    parser.add_argument("--result-json-file")
                    arguments = parser.parse_args()
                    Path(arguments.script).chmod(0o600)
                    Path(arguments.script).write_bytes(b"damaged isolated copy")
                    raise SystemExit(9)
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            exit_code = runner.main([
                "--assets-root",
                str(assets),
                "--manifest",
                str(manifest),
                "--baseline",
                str(root / "baseline.json"),
                "--marker",
                str(destructive_marker),
                "--python",
                sys.executable,
                "--accept-current",
                "--all",
                "--output-root",
                str(root / "destructive-output"),
            ])

            self.assertEqual(exit_code, runner.EXIT_SETUP)
            self.assertEqual(source.read_bytes(), original_bytes)

    def test_result_json_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets, manifest, _ = self.create_private_pack(root)
            outside_result = root / "outside-result.json"
            outside_result.write_text("{}", encoding="utf-8")
            escaping_marker = root / "escaping_marker.py"
            escaping_marker.write_text(
                textwrap.dedent(
                    f"""
                    import argparse
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--template")
                    parser.add_argument("--script")
                    parser.add_argument("--output")
                    parser.add_argument("--output-mode")
                    parser.add_argument("--result-json-file")
                    arguments = parser.parse_args()
                    Path(arguments.result_json_file).symlink_to(
                        {str(outside_result)!r}
                    )
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            exit_code = runner.main([
                "--assets-root",
                str(assets),
                "--manifest",
                str(manifest),
                "--baseline",
                str(root / "baseline.json"),
                "--marker",
                str(escaping_marker),
                "--python",
                sys.executable,
                "--accept-current",
                "--all",
                "--output-root",
                str(root / "escaping-output"),
            ])

            self.assertEqual(exit_code, runner.EXIT_SETUP)

    def test_write_targets_cannot_overwrite_manifest_or_baseline(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets, manifest, marker = self.create_private_pack(root)
            manifest_bytes = manifest.read_bytes()
            baseline = root / "baseline.json"
            common = [
                "--assets-root",
                str(assets),
                "--manifest",
                str(manifest),
                "--marker",
                str(marker),
                "--python",
                sys.executable,
                "--accept-current",
                "--all",
            ]

            baseline_collision = runner.main(
                common + ["--baseline", str(manifest)]
            )
            summary_collision = runner.main(
                common
                + [
                    "--baseline",
                    str(baseline),
                    "--summary-json",
                    str(manifest),
                ]
            )

            self.assertEqual(baseline_collision, runner.EXIT_SETUP)
            self.assertEqual(summary_collision, runner.EXIT_SETUP)
            self.assertEqual(manifest.read_bytes(), manifest_bytes)

    def test_critical_result_cannot_become_baseline_ready(self):
        case = runner.CaseSpec(
            case_id="critical",
            label="Critical",
            suites=("full",),
            script_relative="script.pdf",
            template_relative="template.xlsx",
            script_path=Path("script.pdf"),
            template_path=Path("template.xlsx"),
        )
        execution = runner.CaseExecution(
            case=case,
            duration_seconds=0,
            output_directory=Path("output"),
            actual_record={
                "inputs": {},
                "metrics": {
                    "safety_level": "warning",
                    "safety_warnings": [{
                        "code": "SYNTHETIC_CRITICAL",
                        "severity": "critical",
                    }],
                },
            },
        )

        has_regression, has_setup_error = runner.classify_executions(
            [execution],
            None,
            accepting=True,
        )

        self.assertTrue(has_regression)
        self.assertFalse(has_setup_error)
        self.assertEqual(execution.status, "CRITICAL")

    def test_comparison_reports_nested_metric_changes(self):
        expected = {
            "metrics": {
                "marked_count": 10,
                "marked_page_counts": {"1": 4, "2": 6},
            }
        }
        actual = {
            "metrics": {
                "marked_count": 9,
                "marked_page_counts": {"1": 4, "2": 5},
            }
        }
        differences = runner.compare_values(expected, actual)

        self.assertIn("metrics.marked_count: 10 -> 9", differences)
        self.assertIn(
            "metrics.marked_page_counts.2: 6 -> 5",
            differences,
        )


if __name__ == "__main__":
    unittest.main()
