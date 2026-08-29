#!/usr/bin/env python3
"""Run private real-script golden regressions without touching source assets.

The public runner contains no copyrighted scripts or machine-specific paths.
It consumes a private manifest whose PDF and workbook paths are relative to an
explicit assets root, runs the normal marker CLI in isolated temporary output
directories, and compares stable structured metrics with an approved baseline.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import fitz


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MARKER = PROJECT_ROOT / "dca_script_marker.py"
DEFAULT_PYTHON = (
    Path(sys.prefix) / "bin" / "python"
    if sys.prefix != sys.base_prefix
    else Path(sys.executable)
)
EXIT_REGRESSION = 1
EXIT_SETUP = 2
GENERATED_PDF_PATTERN = re.compile(r"_marked_", re.IGNORECASE)
CASE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
ALLOWED_MANIFEST_ARGUMENTS = {
    "--number-colour": True,
    "--number-scale": True,
    "--number-font": True,
    "--number-x": True,
    "--number-gap": True,
    "--number-y-offset": True,
    "--state-colour": True,
    "--state-scale": True,
    "--state-font": True,
    "--state-position": True,
    "--state-placement": True,
    "--page-state-header-footer": False,
    "--page-state-display": True,
    "--page-state-text-colour": True,
    "--page-state-scale": True,
    "--page-state-font": True,
    "--page-state-border-colour": True,
    "--legend-position": True,
    "--start-page": True,
    "--end-page": True,
    "--style": True,
}


class RegressionSetupError(RuntimeError):
    """Raised for invalid configuration, assets, or engine output."""


@dataclasses.dataclass(frozen=True)
class CaseSpec:
    case_id: str
    label: str
    suites: tuple[str, ...]
    script_relative: str
    template_relative: str
    script_path: Path
    template_path: Path
    arguments: tuple[str, ...] = ()
    ocr_relative: str | None = None
    ocr_path: Path | None = None
    assertions: dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class CaseExecution:
    case: CaseSpec
    duration_seconds: float
    output_directory: Path
    baseline_record: dict[str, Any] | None = None
    actual_record: dict[str, Any] | None = None
    assertion_failures: list[str] = dataclasses.field(default_factory=list)
    differences: list[str] = dataclasses.field(default_factory=list)
    error: str | None = None
    status: str = "PENDING"


def load_json(path: Path, description: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RegressionSetupError(f"{description} not found: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise RegressionSetupError(
            f"Could not read {description} {path}: {error}"
        ) from error

    if not isinstance(value, dict):
        raise RegressionSetupError(f"{description} must contain a JSON object.")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def path_is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def resolve_private_asset(
    assets_root: Path,
    relative_value: Any,
    *,
    expected_suffix: str,
    description: str,
) -> tuple[str, Path]:
    if not isinstance(relative_value, str) or not relative_value.strip():
        raise RegressionSetupError(f"{description} must be a non-empty path.")

    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise RegressionSetupError(
            f"{description} must be relative to --assets-root: {relative_value}"
        )

    root = assets_root.resolve()
    resolved = (root / relative).resolve()
    if not path_is_within(resolved, root):
        raise RegressionSetupError(
            f"{description} escapes --assets-root: {relative_value}"
        )
    if resolved.suffix.lower() != expected_suffix:
        raise RegressionSetupError(
            f"{description} must end in {expected_suffix}: {relative_value}"
        )
    if not resolved.is_file():
        raise RegressionSetupError(f"{description} not found: {resolved}")

    return relative.as_posix(), resolved


def validate_arguments(case_id: str, raw_arguments: Any) -> tuple[str, ...]:
    if raw_arguments is None:
        return ()
    if not isinstance(raw_arguments, list) or not all(
        isinstance(value, str) for value in raw_arguments
    ):
        raise RegressionSetupError(
            f"Case {case_id}: arguments must be a list of strings."
        )
    validated: list[str] = []
    seen: set[str] = set()
    index = 0
    while index < len(raw_arguments):
        token = raw_arguments[index]
        option, separator, inline_value = token.partition("=")
        needs_value = ALLOWED_MANIFEST_ARGUMENTS.get(option)
        if needs_value is None:
            raise RegressionSetupError(
                f"Case {case_id}: engine option is not allowed in a private "
                f"regression manifest: {option or token}"
            )
        if option in seen:
            raise RegressionSetupError(
                f"Case {case_id}: engine option may appear only once: {option}"
            )
        seen.add(option)

        if not needs_value:
            if separator:
                raise RegressionSetupError(
                    f"Case {case_id}: flag {option} does not accept a value."
                )
            validated.append(option)
            index += 1
            continue

        if separator:
            if not inline_value:
                raise RegressionSetupError(
                    f"Case {case_id}: option {option} needs a value."
                )
            value = inline_value
        else:
            index += 1
            if index >= len(raw_arguments) or raw_arguments[index].startswith("--"):
                raise RegressionSetupError(
                    f"Case {case_id}: option {option} needs a value."
                )
            value = raw_arguments[index]
        validated.extend([option, value])
        index += 1

    return tuple(validated)


def validate_assertions(case_id: str, raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise RegressionSetupError(
            f"Case {case_id}: assertions must be a JSON object."
        )

    allowed = {
        "required_mark_pages",
        "forbidden_mark_pages",
        "required_text",
        "required_cue_marks",
        "forbidden_cue_marks",
    }
    unknown = set(raw) - allowed
    if unknown:
        raise RegressionSetupError(
            f"Case {case_id}: unsupported assertion(s): "
            + ", ".join(sorted(unknown))
        )

    validated: dict[str, Any] = {}
    for key in ("required_mark_pages", "forbidden_mark_pages"):
        values = raw.get(key, [])
        if not isinstance(values, list) or not all(
            isinstance(value, int) and value > 0 for value in values
        ):
            raise RegressionSetupError(
                f"Case {case_id}: {key} must be a list of positive page numbers."
            )
        validated[key] = sorted(set(values))

    text_checks = raw.get("required_text", [])
    if not isinstance(text_checks, list):
        raise RegressionSetupError(
            f"Case {case_id}: required_text must be a list."
        )
    validated_text = []
    for check in text_checks:
        if (
            not isinstance(check, dict)
            or not isinstance(check.get("page"), int)
            or check["page"] <= 0
            or not isinstance(check.get("text"), str)
            or not check["text"]
        ):
            raise RegressionSetupError(
                f"Case {case_id}: each required_text item needs a positive "
                "page and non-empty text."
            )
        validated_text.append({"page": check["page"], "text": check["text"]})
    validated["required_text"] = validated_text

    for key in ("required_cue_marks", "forbidden_cue_marks"):
        cue_checks = raw.get(key, [])
        if not isinstance(cue_checks, list):
            raise RegressionSetupError(
                f"Case {case_id}: {key} must be a list."
            )
        validated_checks = []
        for check in cue_checks:
            allowed_fields = {"page", "state", "speakers", "dca"}
            if key == "required_cue_marks":
                allowed_fields.update({"minimum_count", "exact_count"})
            if not isinstance(check, dict) or set(check) - allowed_fields:
                raise RegressionSetupError(
                    f"Case {case_id}: each {key} item has unsupported fields."
                )
            page = check.get("page")
            state = check.get("state")
            speakers = check.get("speakers")
            dca = check.get("dca")
            minimum_count = check.get("minimum_count", 1)
            exact_count = check.get("exact_count")
            if not isinstance(page, int) or page <= 0:
                raise RegressionSetupError(
                    f"Case {case_id}: each {key} item needs a positive page."
                )
            if state is not None and (
                not isinstance(state, str) or not state
            ):
                raise RegressionSetupError(
                    f"Case {case_id}: {key} state must be non-empty text."
                )
            if (
                not isinstance(speakers, list)
                or not speakers
                or not all(
                    isinstance(value, str) and value for value in speakers
                )
            ):
                raise RegressionSetupError(
                    f"Case {case_id}: each {key} item needs speaker names."
                )
            normalized_speakers = sorted(speakers, key=str.casefold)
            if len(set(normalized_speakers)) != len(normalized_speakers):
                raise RegressionSetupError(
                    f"Case {case_id}: {key} repeats a speaker."
                )
            if not isinstance(dca, str) or not dca:
                raise RegressionSetupError(
                    f"Case {case_id}: each {key} item needs a DCA value."
                )
            if (
                key == "required_cue_marks"
                and (not isinstance(minimum_count, int) or minimum_count <= 0)
            ):
                raise RegressionSetupError(
                    f"Case {case_id}: minimum_count must be positive."
                )
            if exact_count is not None and (
                not isinstance(exact_count, int) or exact_count <= 0
            ):
                raise RegressionSetupError(
                    f"Case {case_id}: exact_count must be positive."
                )
            if exact_count is not None and "minimum_count" in check:
                raise RegressionSetupError(
                    f"Case {case_id}: use exact_count or minimum_count, not both."
                )
            validated_check = {
                "page": page,
                "speakers": normalized_speakers,
                "dca": dca,
            }
            if state is not None:
                validated_check["state"] = state
            if key == "required_cue_marks":
                if exact_count is not None:
                    validated_check["exact_count"] = exact_count
                else:
                    validated_check["minimum_count"] = minimum_count
            validated_checks.append(validated_check)
        validated[key] = validated_checks
    return validated


def load_manifest(manifest_path: Path, assets_root: Path) -> list[CaseSpec]:
    manifest = load_json(manifest_path, "regression manifest")
    if manifest.get("schema_version") != 1:
        raise RegressionSetupError("Regression manifest schema_version must be 1.")

    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise RegressionSetupError("Regression manifest must contain cases.")

    cases: list[CaseSpec] = []
    seen_ids: set[str] = set()
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            raise RegressionSetupError("Every manifest case must be an object.")

        allowed_case_fields = {
            "id",
            "label",
            "suites",
            "script",
            "template",
            "arguments",
            "ocr_json",
            "assertions",
        }
        unknown_fields = set(raw_case) - allowed_case_fields
        if unknown_fields:
            raise RegressionSetupError(
                "Unsupported manifest case field(s): "
                + ", ".join(sorted(unknown_fields))
            )

        case_id = raw_case.get("id")
        if not isinstance(case_id, str) or not CASE_ID_PATTERN.fullmatch(case_id):
            raise RegressionSetupError(
                f"Invalid case id {case_id!r}; use lowercase letters, numbers, "
                "underscores, or hyphens."
            )
        if case_id in seen_ids:
            raise RegressionSetupError(f"Duplicate case id: {case_id}")
        seen_ids.add(case_id)

        label = raw_case.get("label", case_id)
        if not isinstance(label, str) or not label.strip():
            raise RegressionSetupError(f"Case {case_id}: label must be text.")

        raw_suites = raw_case.get("suites", ["full"])
        if not isinstance(raw_suites, list) or not raw_suites or not all(
            isinstance(value, str) and value.strip() for value in raw_suites
        ):
            raise RegressionSetupError(
                f"Case {case_id}: suites must be a non-empty list of names."
            )
        suites = tuple(dict.fromkeys(raw_suites))

        script_relative, script_path = resolve_private_asset(
            assets_root,
            raw_case.get("script"),
            expected_suffix=".pdf",
            description=f"Case {case_id} script",
        )
        if GENERATED_PDF_PATTERN.search(script_path.stem):
            raise RegressionSetupError(
                f"Case {case_id}: generated marked PDFs cannot be inputs: "
                f"{script_relative}"
            )

        template_relative, template_path = resolve_private_asset(
            assets_root,
            raw_case.get("template"),
            expected_suffix=".xlsx",
            description=f"Case {case_id} template",
        )

        ocr_relative = None
        ocr_path = None
        if raw_case.get("ocr_json") is not None:
            ocr_relative, ocr_path = resolve_private_asset(
                assets_root,
                raw_case.get("ocr_json"),
                expected_suffix=".json",
                description=f"Case {case_id} OCR data",
            )

        cases.append(CaseSpec(
            case_id=case_id,
            label=label.strip(),
            suites=suites,
            script_relative=script_relative,
            template_relative=template_relative,
            script_path=script_path,
            template_path=template_path,
            arguments=validate_arguments(case_id, raw_case.get("arguments")),
            ocr_relative=ocr_relative,
            ocr_path=ocr_path,
            assertions=validate_assertions(case_id, raw_case.get("assertions")),
        ))

    return cases


def select_cases(
    cases: list[CaseSpec],
    *,
    suite: str,
    requested_ids: list[str],
    select_all: bool,
) -> list[CaseSpec]:
    by_id = {case.case_id: case for case in cases}
    if requested_ids:
        missing = sorted(set(requested_ids) - set(by_id))
        if missing:
            raise RegressionSetupError(
                "Unknown regression case(s): " + ", ".join(missing)
            )
        requested = set(requested_ids)
        return [case for case in cases if case.case_id in requested]
    if select_all:
        return list(cases)

    selected = [case for case in cases if suite in case.suites]
    if not selected:
        raise RegressionSetupError(f"No cases belong to suite {suite!r}.")
    return selected


def load_baseline(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    baseline = load_json(path, "approved baseline")
    if baseline.get("schema_version") != 1:
        raise RegressionSetupError("Approved baseline schema_version must be 1.")
    if not isinstance(baseline.get("cases"), dict):
        raise RegressionSetupError("Approved baseline must contain a cases object.")
    return baseline


def pdf_geometry(path: Path) -> tuple[int, list[list[float]]]:
    try:
        with fitz.open(path) as document:
            geometry = [
                [round(page.rect.width, 3), round(page.rect.height, 3)]
                for page in document
            ]
            return document.page_count, geometry
    except Exception as error:
        raise RegressionSetupError(f"Invalid PDF {path}: {error}") from error


def ensure_runner_owned_output(path: Path, case_output: Path, description: str) -> Path:
    resolved = path.resolve()
    output_root = case_output.resolve()
    if not path_is_within(resolved, output_root) or not resolved.is_file():
        raise RegressionSetupError(
            f"Engine {description} escaped or was not created in its isolated "
            f"case folder: {path}"
        )
    return resolved


def normalize_result_metrics(
    result: dict[str, Any],
    *,
    output_page_count: int,
) -> dict[str, Any]:
    required_integer_fields = (
        "marked_count",
        "configured_state_count",
        "activated_state_count",
        "missing_state_count",
        "unmatched_name_count",
        "pdf_page_count",
    )
    for field in required_integer_fields:
        if not isinstance(result.get(field), int):
            raise RegressionSetupError(
                f"Engine result is missing integer field {field!r}."
            )

    if result.get("schema_version") != 1:
        raise RegressionSetupError("Engine result schema_version must be 1.")
    if result.get("safety_level") not in {"ok", "warning", "critical"}:
        raise RegressionSetupError("Engine result has an invalid safety_level.")

    activated_states = result.get("activated_states")
    missing_states = result.get("missing_states")
    marked_pages = result.get("marked_pages")
    state_activation_pages = result.get("state_activation_pages")
    marked_page_counts = result.get("marked_page_counts")
    marked_cue_counts = result.get("marked_cue_counts")
    if not isinstance(activated_states, list) or not all(
        isinstance(value, str) for value in activated_states
    ):
        raise RegressionSetupError("Engine result activated_states is invalid.")
    if not isinstance(missing_states, list) or not all(
        isinstance(value, str) for value in missing_states
    ):
        raise RegressionSetupError("Engine result missing_states is invalid.")
    if not isinstance(marked_pages, list) or not all(
        isinstance(value, int) and value > 0 for value in marked_pages
    ):
        raise RegressionSetupError("Engine result marked_pages is invalid.")
    if not isinstance(state_activation_pages, dict):
        raise RegressionSetupError("Engine result state_activation_pages is invalid.")
    if not isinstance(marked_page_counts, dict):
        raise RegressionSetupError("Engine result marked_page_counts is invalid.")
    if not isinstance(marked_cue_counts, list):
        raise RegressionSetupError("Engine result marked_cue_counts is invalid.")

    normalized_state_pages: dict[str, int] = {}
    for key, value in state_activation_pages.items():
        if not isinstance(key, str) or not isinstance(value, int) or value <= 0:
            raise RegressionSetupError(
                "Engine result state_activation_pages contains invalid data."
            )
        normalized_state_pages[key] = value

    normalized_page_counts: dict[str, int] = {}
    for key, value in marked_page_counts.items():
        try:
            page = int(key)
        except (TypeError, ValueError) as error:
            raise RegressionSetupError(
                "Engine result marked_page_counts has a non-page key."
            ) from error
        if page <= 0 or not isinstance(value, int) or value <= 0:
            raise RegressionSetupError(
                "Engine result marked_page_counts contains invalid data."
            )
        normalized_page_counts[str(page)] = value

    normalized_cue_counts = []
    seen_cue_identities: set[tuple[int, str, tuple[str, ...], str]] = set()
    cue_page_totals: dict[str, int] = {}
    for record in marked_cue_counts:
        if not isinstance(record, dict):
            raise RegressionSetupError(
                "Engine result marked_cue_counts must contain objects."
            )
        page = record.get("page")
        state = record.get("state")
        speakers = record.get("speakers")
        dca = record.get("dca")
        count = record.get("count")
        if not isinstance(page, int) or page <= 0:
            raise RegressionSetupError(
                "Engine marked cue identity has an invalid page."
            )
        if not isinstance(state, str) or not state:
            raise RegressionSetupError(
                "Engine marked cue identity has an invalid state."
            )
        if (
            not isinstance(speakers, list)
            or not speakers
            or not all(isinstance(value, str) and value for value in speakers)
        ):
            raise RegressionSetupError(
                "Engine marked cue identity has invalid speakers."
            )
        normalized_speakers = tuple(sorted(speakers, key=str.casefold))
        if len(set(normalized_speakers)) != len(normalized_speakers):
            raise RegressionSetupError(
                "Engine marked cue identity repeats a speaker."
            )
        if not isinstance(dca, str) or not dca:
            raise RegressionSetupError(
                "Engine marked cue identity has an invalid DCA value."
            )
        if not isinstance(count, int) or count <= 0:
            raise RegressionSetupError(
                "Engine marked cue identity has an invalid count."
            )
        identity = (page, state, normalized_speakers, dca)
        if identity in seen_cue_identities:
            raise RegressionSetupError(
                "Engine result contains a duplicate marked cue identity."
            )
        seen_cue_identities.add(identity)
        normalized_cue_counts.append({
            "page": page,
            "state": state,
            "speakers": list(normalized_speakers),
            "dca": dca,
            "count": count,
        })
        page_key = str(page)
        cue_page_totals[page_key] = cue_page_totals.get(page_key, 0) + count

    normalized_cue_counts.sort(key=lambda item: (
        item["page"],
        item["state"],
        tuple(value.casefold() for value in item["speakers"]),
        item["dca"],
    ))

    if len(set(activated_states)) != len(activated_states):
        raise RegressionSetupError("Engine result repeats an activated state.")
    if len(set(missing_states)) != len(missing_states):
        raise RegressionSetupError("Engine result repeats a missing state.")
    if set(activated_states) & set(missing_states):
        raise RegressionSetupError(
            "Engine result lists a state as both activated and missing."
        )
    if result["activated_state_count"] != len(activated_states):
        raise RegressionSetupError("Activated state count is inconsistent.")
    if result["missing_state_count"] != len(missing_states):
        raise RegressionSetupError("Missing state count is inconsistent.")
    if result["configured_state_count"] != (
        len(activated_states) + len(missing_states)
    ):
        raise RegressionSetupError("Configured state count is inconsistent.")
    if set(normalized_state_pages) != set(activated_states):
        raise RegressionSetupError(
            "State activation page map does not match activated states."
        )
    if len(set(marked_pages)) != len(marked_pages):
        raise RegressionSetupError("Engine result repeats a marked page.")
    if set(normalized_page_counts) != {str(page) for page in marked_pages}:
        raise RegressionSetupError(
            "Marked page counts do not match the marked page list."
        )
    if sum(normalized_page_counts.values()) != result["marked_count"]:
        raise RegressionSetupError("Marked page counts do not match marked_count.")
    if cue_page_totals != normalized_page_counts:
        raise RegressionSetupError(
            "Marked cue identity counts do not match marked page counts."
        )
    if any(page > output_page_count for page in marked_pages):
        raise RegressionSetupError("A marked page exceeds the output page count.")
    if any(page > output_page_count for page in normalized_state_pages.values()):
        raise RegressionSetupError(
            "A state activation page exceeds the output page count."
        )
    if any(
        record["state"] not in set(activated_states)
        for record in normalized_cue_counts
    ):
        raise RegressionSetupError(
            "A marked cue identity refers to an inactive state."
        )

    raw_warnings = result.get("safety_warnings")
    if not isinstance(raw_warnings, list):
        raise RegressionSetupError("Engine result safety_warnings is invalid.")
    warnings = []
    for warning in raw_warnings:
        if not isinstance(warning, dict):
            raise RegressionSetupError("Engine safety warning must be an object.")
        code = warning.get("code")
        severity = warning.get("severity")
        if (
            not isinstance(code, str)
            or severity not in {"warning", "critical"}
        ):
            raise RegressionSetupError(
                "Engine safety warnings need a code and warning/critical "
                "severity."
            )
        warnings.append({"code": code, "severity": severity})

    warnings.sort(key=lambda item: (item["code"], item["severity"]))
    return {
        "marked_count": result["marked_count"],
        "configured_state_count": result["configured_state_count"],
        "activated_state_count": result["activated_state_count"],
        "missing_state_count": result["missing_state_count"],
        "unmatched_name_count": result["unmatched_name_count"],
        "safety_level": result["safety_level"],
        "safety_warnings": warnings,
        "activated_states": activated_states,
        "missing_states": missing_states,
        "state_activation_pages": normalized_state_pages,
        "marked_pages": marked_pages,
        "marked_page_counts": dict(
            sorted(normalized_page_counts.items(), key=lambda item: int(item[0]))
        ),
        "marked_cue_counts": normalized_cue_counts,
        "source_pdf_page_count": result["pdf_page_count"],
        "output_pdf_page_count": output_page_count,
    }


def evaluate_assertions(
    case: CaseSpec,
    metrics: dict[str, Any],
    output_pdf: Path,
) -> list[str]:
    failures = []
    marked_pages = set(metrics["marked_pages"])
    for page in case.assertions.get("required_mark_pages", []):
        if page not in marked_pages:
            failures.append(f"required mark page {page} has no DCA marks")
    for page in case.assertions.get("forbidden_mark_pages", []):
        if page in marked_pages:
            failures.append(f"forbidden page {page} received DCA marks")

    required_text = case.assertions.get("required_text", [])
    if required_text:
        with fitz.open(output_pdf) as document:
            for check in required_text:
                page = check["page"]
                if page > document.page_count:
                    failures.append(
                        f"required text page {page} exceeds output page count"
                    )
                    continue
                page_text = document[page - 1].get_text()
                if check["text"] not in page_text:
                    failures.append(
                        f"page {page} does not contain required text "
                        f"{check['text']!r}"
                    )

    marked_cues = metrics["marked_cue_counts"]
    for key, forbidden in (
        ("required_cue_marks", False),
        ("forbidden_cue_marks", True),
    ):
        for check in case.assertions.get(key, []):
            matched_count = sum(
                record["count"]
                for record in marked_cues
                if record["page"] == check["page"]
                and record["speakers"] == check["speakers"]
                and record["dca"] == check["dca"]
                and (
                    "state" not in check
                    or record["state"] == check["state"]
                )
            )
            description = (
                f"page {check['page']} speakers "
                f"{' / '.join(check['speakers'])} DCA {check['dca']}"
            )
            if forbidden and matched_count:
                failures.append(
                    f"forbidden cue mark found for {description}"
                )
            elif not forbidden and "exact_count" in check and (
                matched_count != check["exact_count"]
            ):
                failures.append(
                    f"required cue mark count changed for {description}; "
                    f"found {matched_count}, expected exactly "
                    f"{check['exact_count']}"
                )
            elif not forbidden and matched_count < check.get("minimum_count", 1):
                failures.append(
                    f"required cue mark missing for {description}; found "
                    f"{matched_count}, expected at least "
                    f"{check.get('minimum_count', 1)}"
                )
    return failures


def run_case(
    case: CaseSpec,
    *,
    marker: Path,
    python_executable: Path,
    output_root: Path,
    timeout_seconds: int,
) -> CaseExecution:
    started = time.monotonic()
    case_output = output_root / case.case_id
    case_output.mkdir(parents=True, exist_ok=False)
    input_directory = case_output / ".isolated-inputs"
    generated_directory = case_output / "generated"
    input_directory.mkdir()
    generated_directory.mkdir()
    execution = CaseExecution(
        case=case,
        duration_seconds=0,
        output_directory=case_output,
    )

    input_paths = [case.script_path, case.template_path]
    if case.ocr_path is not None:
        input_paths.append(case.ocr_path)
    before_hashes: dict[Path, str] = {}

    copied_script = input_directory / "script" / case.script_path.name
    copied_template = input_directory / "template" / case.template_path.name
    copied_inputs = {
        case.script_path: copied_script,
        case.template_path: copied_template,
    }
    copied_ocr = None
    if case.ocr_path is not None:
        copied_ocr = input_directory / "ocr" / case.ocr_path.name
        copied_inputs[case.ocr_path] = copied_ocr

    result_file = case_output / "result.json"
    command = [
        str(python_executable),
        str(marker),
        "--template",
        str(copied_template),
        "--script",
        str(copied_script),
        "--output",
        str(generated_directory),
        "--output-mode",
        "replace",
        "--result-json-file",
        str(result_file),
    ]
    if copied_ocr is not None:
        command.extend(["--ocr-json", str(copied_ocr)])
    command.extend(case.arguments)

    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    try:
        before_hashes = {path: sha256_file(path) for path in input_paths}
        for original, copied in copied_inputs.items():
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, copied)
            if sha256_file(copied) != before_hashes[original]:
                raise RegressionSetupError(
                    f"Could not verify isolated copy of {original.name}."
                )
            copied.chmod(0o444)

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
            env=environment,
        )
        if process.returncode != 0:
            details = (process.stdout + process.stderr).strip()[-4000:]
            raise RegressionSetupError(
                f"Marker exited {process.returncode}: {details or 'no output'}"
            )

        safe_result_file = ensure_runner_owned_output(
            result_file,
            case_output,
            "result JSON",
        )
        result = load_json(safe_result_file, f"case {case.case_id} result")
        output_pdf = ensure_runner_owned_output(
            Path(result.get("output_pdf", "")),
            generated_directory,
            "PDF",
        )
        ensure_runner_owned_output(
            Path(result.get("review_report", "")),
            generated_directory,
            "review report",
        )

        source_page_count, source_geometry = pdf_geometry(case.script_path)
        output_page_count, output_geometry = pdf_geometry(output_pdf)
        if source_page_count != output_page_count:
            raise RegressionSetupError(
                f"Output page count changed from {source_page_count} to "
                f"{output_page_count}."
            )
        if source_geometry != output_geometry:
            raise RegressionSetupError("Output PDF page geometry changed.")

        metrics = normalize_result_metrics(
            result,
            output_page_count=output_page_count,
        )
        if metrics["source_pdf_page_count"] != source_page_count:
            raise RegressionSetupError(
                "Engine-reported source page count does not match the PDF."
            )

        configuration_record = {
            "script": case.script_relative,
            "template": case.template_relative,
            "arguments": list(case.arguments),
            "assertions": case.assertions,
        }
        if case.ocr_path is not None:
            configuration_record["ocr_json"] = case.ocr_relative

        input_record = {
            **configuration_record,
            "config_sha256": sha256_json(configuration_record),
            "script_sha256": before_hashes[case.script_path],
            "template_sha256": before_hashes[case.template_path],
        }
        if case.ocr_path is not None:
            input_record["ocr_sha256"] = before_hashes[case.ocr_path]
        execution.actual_record = {
            "inputs": input_record,
            "metrics": metrics,
        }
        execution.assertion_failures = evaluate_assertions(
            case,
            metrics,
            output_pdf,
        )
    except subprocess.TimeoutExpired as error:
        execution.error = f"Timed out after {timeout_seconds} seconds."
        if error.stdout or error.stderr:
            execution.error += " Marker output was captured in the case folder."
    except (OSError, RegressionSetupError, json.JSONDecodeError) as error:
        execution.error = str(error)
    finally:
        if before_hashes:
            try:
                after_hashes = {
                    path: sha256_file(path) for path in input_paths
                }
                changed_inputs = [
                    path.name
                    for path in input_paths
                    if before_hashes[path] != after_hashes[path]
                ]
                if changed_inputs:
                    source_error = (
                        "Source input changed during the run: "
                        + ", ".join(changed_inputs)
                    )
                    execution.error = (
                        f"{execution.error} {source_error}"
                        if execution.error
                        else source_error
                    )
            except OSError as error:
                execution.error = (
                    f"{execution.error} Could not re-hash source inputs: {error}"
                    if execution.error
                    else f"Could not re-hash source inputs: {error}"
                )
        shutil.rmtree(input_directory, ignore_errors=True)
        execution.duration_seconds = time.monotonic() - started

    return execution


def compare_values(expected: Any, actual: Any, prefix: str = "") -> list[str]:
    differences: list[str] = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            path = f"{prefix}.{key}" if prefix else key
            if key not in expected:
                differences.append(f"{path}: added {actual[key]!r}")
            elif key not in actual:
                differences.append(f"{path}: removed (was {expected[key]!r})")
            else:
                differences.extend(compare_values(expected[key], actual[key], path))
        return differences
    if expected != actual:
        differences.append(f"{prefix}: {expected!r} -> {actual!r}")
    return differences


def classify_executions(
    executions: list[CaseExecution],
    baseline: dict[str, Any] | None,
    *,
    accepting: bool,
) -> tuple[bool, bool]:
    """Return (has_regression, has_setup_error)."""
    has_regression = False
    has_setup_error = False
    baseline_cases = baseline.get("cases", {}) if baseline else {}

    for execution in executions:
        if execution.error:
            execution.status = "ERROR"
            has_setup_error = True
            continue
        if execution.actual_record is None:
            execution.status = "ERROR"
            execution.error = "No actual regression record was produced."
            has_setup_error = True
            continue

        metrics = execution.actual_record["metrics"]
        if execution.assertion_failures:
            execution.status = "ASSERT"
            execution.differences = list(execution.assertion_failures)
            has_regression = True
            continue
        if metrics["safety_level"] == "critical" or any(
            warning["severity"] == "critical"
            for warning in metrics["safety_warnings"]
        ):
            execution.status = "CRITICAL"
            execution.differences = [
                "positive regression cases may not accept a critical safety result"
            ]
            has_regression = True
            continue

        execution.baseline_record = baseline_cases.get(execution.case.case_id)
        if accepting:
            execution.status = "READY"
            continue
        if execution.baseline_record is None:
            execution.status = "NO BASELINE"
            execution.differences = ["case is missing from the approved baseline"]
            has_setup_error = True
            continue

        if execution.baseline_record.get("inputs") != execution.actual_record["inputs"]:
            execution.status = "INPUT CHANGED"
            execution.differences = compare_values(
                execution.baseline_record.get("inputs"),
                execution.actual_record["inputs"],
                "inputs",
            )
            has_setup_error = True
            continue

        execution.differences = compare_values(
            execution.baseline_record.get("metrics"),
            execution.actual_record["metrics"],
            "metrics",
        )
        if execution.differences:
            execution.status = "CHANGED"
            has_regression = True
        else:
            execution.status = "PASS"

    return has_regression, has_setup_error


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.remove(temporary_name)


def accept_baseline(
    baseline_path: Path,
    baseline: dict[str, Any] | None,
    executions: list[CaseExecution],
    *,
    allow_input_changes: bool,
) -> Path | None:
    updated = baseline or {"schema_version": 1, "cases": {}}
    updated = json.loads(json.dumps(updated))
    baseline_cases = updated.setdefault("cases", {})

    for execution in executions:
        if execution.actual_record is None or execution.status != "READY":
            raise RegressionSetupError(
                "Baseline acceptance requires every selected case to finish safely."
            )
        existing = baseline_cases.get(execution.case.case_id)
        if (
            existing
            and existing.get("inputs") != execution.actual_record["inputs"]
            and not allow_input_changes
        ):
            raise RegressionSetupError(
                f"Case {execution.case.case_id} inputs or configuration changed. "
                "Review them, then rerun with --allow-input-changes."
            )
        baseline_cases[execution.case.case_id] = execution.actual_record
        execution.status = "ACCEPTED"

    backup = None
    if baseline_path.exists():
        timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = baseline_path.with_name(
            f"{baseline_path.stem}.backup-{timestamp}{baseline_path.suffix}"
        )
        shutil.copy2(baseline_path, backup)
    atomic_write_json(baseline_path, updated)
    return backup


def print_results(executions: list[CaseExecution]) -> None:
    print("\nReal-script regression results")
    print("=" * 78)
    print(f"{'Case':<28} {'Status':<14} {'Marks':>7} {'States':>9} {'Seconds':>8}")
    print("-" * 78)
    for execution in executions:
        metrics = (
            execution.actual_record.get("metrics", {})
            if execution.actual_record
            else {}
        )
        marks = str(metrics.get("marked_count", "-"))
        states = (
            f"{metrics.get('activated_state_count', '-')}/"
            f"{metrics.get('configured_state_count', '-')}"
        )
        print(
            f"{execution.case.case_id:<28} {execution.status:<14} "
            f"{marks:>7} {states:>9} {execution.duration_seconds:>8.1f}"
        )
        if execution.error:
            print(f"  error: {execution.error}")
        for difference in execution.differences[:12]:
            print(f"  - {difference}")
        if len(execution.differences) > 12:
            print(f"  - and {len(execution.differences) - 12} more change(s)")
    print("=" * 78)


def summary_value(
    executions: list[CaseExecution],
    *,
    suite: str,
    accepting: bool,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "suite": suite,
        "baseline_acceptance": accepting,
        "cases": [
            {
                "id": execution.case.case_id,
                "label": execution.case.label,
                "status": execution.status,
                "duration_seconds": round(execution.duration_seconds, 3),
                "metrics": (
                    execution.actual_record.get("metrics")
                    if execution.actual_record
                    else None
                ),
                "differences": execution.differences,
                "error": execution.error,
            }
            for execution in executions
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run private real-script DCA regressions without modifying source "
            "PDFs or workbooks."
        )
    )
    parser.add_argument(
        "--assets-root",
        default=os.environ.get("DCA_REGRESSION_ASSETS_ROOT"),
        help="Private test collection root (or DCA_REGRESSION_ASSETS_ROOT)",
    )
    parser.add_argument(
        "--manifest",
        default=os.environ.get("DCA_REGRESSION_MANIFEST"),
        help="Private manifest JSON (or DCA_REGRESSION_MANIFEST)",
    )
    parser.add_argument(
        "--baseline",
        default=os.environ.get("DCA_REGRESSION_BASELINE"),
        help="Approved baseline JSON (or DCA_REGRESSION_BASELINE)",
    )
    parser.add_argument("--marker", default=str(DEFAULT_MARKER))
    parser.add_argument("--python", default=str(DEFAULT_PYTHON))
    parser.add_argument("--suite", default="smoke")
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--all", action="store_true", dest="select_all")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--output-root")
    parser.add_argument("--keep-output", action="store_true")
    parser.add_argument("--summary-json")
    parser.add_argument(
        "--accept-current",
        action="store_true",
        help="Atomically approve current results for explicitly selected cases",
    )
    parser.add_argument(
        "--allow-input-changes",
        "--allow-source-changes",
        action="store_true",
        dest="allow_input_changes",
        help=(
            "Allow --accept-current to replace changed source fingerprints "
            "or normalized manifest configuration"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    output_root: Path | None = None
    summary_path: Path | None = None
    runner_created_output = False

    try:
        if not arguments.assets_root:
            raise RegressionSetupError(
                "Provide --assets-root or DCA_REGRESSION_ASSETS_ROOT."
            )
        if not arguments.manifest:
            raise RegressionSetupError(
                "Provide --manifest or DCA_REGRESSION_MANIFEST."
            )
        if not arguments.baseline:
            raise RegressionSetupError(
                "Provide --baseline or DCA_REGRESSION_BASELINE."
            )
        if arguments.jobs <= 0 or arguments.timeout_seconds <= 0:
            raise RegressionSetupError("--jobs and --timeout-seconds must be positive.")
        if arguments.accept_current and not (
            arguments.case or arguments.select_all
        ):
            raise RegressionSetupError(
                "--accept-current requires explicit --case selections or --all."
            )

        assets_root = Path(arguments.assets_root).expanduser().resolve()
        manifest_path = Path(arguments.manifest).expanduser().resolve()
        baseline_path = Path(arguments.baseline).expanduser().resolve()
        marker = Path(arguments.marker).expanduser().resolve()
        # Preserve a virtual-environment launcher instead of resolving its
        # symlink to the base interpreter, which would lose installed modules.
        python_executable = Path(
            os.path.abspath(os.path.expanduser(arguments.python))
        )
        if not assets_root.is_dir():
            raise RegressionSetupError(f"Assets root not found: {assets_root}")
        if not marker.is_file():
            raise RegressionSetupError(f"Marker engine not found: {marker}")
        if not python_executable.is_file():
            raise RegressionSetupError(
                f"Python executable not found: {python_executable}"
            )

        cases = load_manifest(manifest_path, assets_root)
        protected_read_paths = {
            manifest_path,
            *(
                path
                for case in cases
                for path in (
                    case.script_path,
                    case.template_path,
                    case.ocr_path,
                )
                if path is not None
            ),
        }
        if baseline_path.suffix.lower() != ".json":
            raise RegressionSetupError("Approved baseline must be a .json file.")
        if baseline_path in protected_read_paths:
            raise RegressionSetupError(
                "Approved baseline path collides with the manifest or a "
                "source asset."
            )
        if arguments.summary_json:
            summary_path = Path(
                arguments.summary_json
            ).expanduser().resolve()
            if summary_path.suffix.lower() != ".json":
                raise RegressionSetupError("--summary-json must end in .json.")
            if summary_path == baseline_path or summary_path in protected_read_paths:
                raise RegressionSetupError(
                    "Summary path collides with the baseline, manifest, or a "
                    "source asset."
                )

        selected = select_cases(
            cases,
            suite=arguments.suite,
            requested_ids=arguments.case,
            select_all=arguments.select_all,
        )
        if arguments.list_cases:
            for case in selected:
                print(f"{case.case_id}\t{case.label}\t{','.join(case.suites)}")
            return 0

        baseline = load_baseline(baseline_path)
        if baseline is None and not arguments.accept_current:
            raise RegressionSetupError(
                f"Approved baseline not found: {baseline_path}. Run selected "
                "cases, visually review them, then use --accept-current."
            )

        if arguments.output_root:
            output_root = Path(arguments.output_root).expanduser().resolve()
            if path_is_within(output_root, assets_root) or output_root == assets_root:
                raise RegressionSetupError(
                    "--output-root must not be inside the private source assets root."
                )
            output_root.mkdir(parents=True, exist_ok=False)
        else:
            output_root = Path(tempfile.mkdtemp(prefix="dca-real-regression-"))
            runner_created_output = True

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(arguments.jobs, len(selected))
        ) as executor:
            futures = [
                executor.submit(
                    run_case,
                    case,
                    marker=marker,
                    python_executable=python_executable,
                    output_root=output_root,
                    timeout_seconds=arguments.timeout_seconds,
                )
                for case in selected
            ]
            executions = [future.result() for future in futures]

        has_regression, has_setup_error = classify_executions(
            executions,
            baseline,
            accepting=arguments.accept_current,
        )

        backup = None
        if arguments.accept_current:
            if has_regression or has_setup_error:
                print_results(executions)
                raise RegressionSetupError(
                    "Unsafe results were not written to the approved baseline."
                )
            backup = accept_baseline(
                baseline_path,
                baseline,
                executions,
                allow_input_changes=arguments.allow_input_changes,
            )

        print_results(executions)
        if arguments.accept_current:
            print(f"Approved baseline updated: {baseline_path}")
            if backup:
                print(f"Previous baseline preserved: {backup}")

        summary = summary_value(
            executions,
            suite=arguments.suite,
            accepting=arguments.accept_current,
        )
        atomic_write_json(output_root / "summary.json", summary)
        if summary_path is not None:
            atomic_write_json(summary_path, summary)

        failed = has_regression or has_setup_error
        if failed or arguments.keep_output or not runner_created_output:
            print(f"Regression outputs preserved: {output_root}")
        elif runner_created_output:
            shutil.rmtree(output_root)
            output_root = None

        if has_setup_error:
            return EXIT_SETUP
        if has_regression:
            return EXIT_REGRESSION
        return 0
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except RegressionSetupError as error:
        print(f"Regression setup error: {error}", file=sys.stderr)
        if output_root is not None:
            print(f"Partial outputs preserved: {output_root}", file=sys.stderr)
        return EXIT_SETUP


if __name__ == "__main__":
    raise SystemExit(main())
