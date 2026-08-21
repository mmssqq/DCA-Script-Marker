#!/bin/bash

set -euo pipefail

INPUT_PATH="${1:-}"
OUTPUT_PATH="${2:-}"

if [[ -z "$INPUT_PATH" || -z "$OUTPUT_PATH" ]]; then
    echo "Usage: $0 <input.xlsx> <output.xlsx>" >&2
    exit 2
fi
if [[ ! -f "$INPUT_PATH" ]]; then
    echo "Template not found: $INPUT_PATH" >&2
    exit 1
fi
if [[ "$INPUT_PATH" == "$OUTPUT_PATH" ]]; then
    echo "The canonical template is never edited in place." >&2
    exit 1
fi

TEMP_ROOT="$(mktemp -d "${TMPDIR:-/private/tmp}/dca-template-sanitize.XXXXXX")"
EXPANDED_ROOT="$TEMP_ROOT/expanded"
SANITIZED_ARCHIVE="$TEMP_ROOT/sanitized.xlsx"
mkdir -p "$EXPANDED_ROOT" "$(dirname "$OUTPUT_PATH")"

cleanup() {
    rm -r "$TEMP_ROOT"
}
trap cleanup EXIT

unzip -qq "$INPUT_PATH" -d "$EXPANDED_ROOT"
WORKBOOK_XML="$EXPANDED_ROOT/xl/workbook.xml"
if [[ ! -f "$WORKBOOK_XML" ]]; then
    echo "The workbook has no xl/workbook.xml." >&2
    exit 1
fi

# Excel writes the author's local folder into an optional AlternateContent
# element. It is unrelated to workbook data and is removed only from release
# copies so testers never receive a developer-machine path.
perl -0pi -e \
    's#<mc:AlternateContent\b[^>]*>.*?<x15ac:absPath\b[^>]*/>.*?</mc:AlternateContent>##s' \
    "$WORKBOOK_XML"

if grep -q '<x15ac:absPath' "$WORKBOOK_XML"; then
    echo "Could not remove the private Excel absolute-path metadata." >&2
    exit 1
fi

(
    cd "$EXPANDED_ROOT"
    zip -q -X -D -r "$SANITIZED_ARCHIVE" .
)
ditto "$SANITIZED_ARCHIVE" "$OUTPUT_PATH"
unzip -tq "$OUTPUT_PATH" >/dev/null

if unzip -p "$OUTPUT_PATH" xl/workbook.xml | grep -q '<x15ac:absPath'; then
    echo "The sanitized workbook still contains absolute-path metadata." >&2
    exit 1
fi
