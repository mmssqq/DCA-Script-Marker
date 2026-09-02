#!/bin/bash

set -euo pipefail
export COPYFILE_DISABLE=1
export COPY_EXTENDED_ATTRIBUTES_DISABLE=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_PATH="${1:-}"
APP_VERSION="${DCA_VERSION:-2.0.0}"
BUILD_NUMBER="${DCA_BUILD_NUMBER:-8}"
RELEASE_CHANNEL="${DCA_RELEASE_CHANNEL:-stable}"
case "$RELEASE_CHANNEL" in
    stable)
        SOURCE_NAME="DCA-Script-Marker-v$APP_VERSION-source"
        ;;
    beta)
        SOURCE_NAME="DCA-Script-Marker-v$APP_VERSION-beta.$BUILD_NUMBER-source"
        ;;
    *)
        echo "DCA_RELEASE_CHANNEL must be stable or beta." >&2
        exit 2
        ;;
esac
SOURCE_FILE_LIST="$SCRIPT_DIR/source-files.txt"
DEPENDENCY_LIST="$SCRIPT_DIR/source-dependencies.tsv"
SOURCE_CACHE="${DCA_SOURCE_CACHE:-$REPOSITORY_ROOT/build/source-cache}"

if [[ -z "$OUTPUT_PATH" ]]; then
    echo "Usage: $0 <source-archive.zip>" >&2
    exit 2
fi
if [[ "${OUTPUT_PATH##*.}" != "zip" ]]; then
    echo "The source archive must use a .zip filename." >&2
    exit 2
fi

STAGING_ROOT="$(mktemp -d "${TMPDIR:-/private/tmp}/dca-source-release.XXXXXX")"
SNAPSHOT_ROOT="$STAGING_ROOT/$SOURCE_NAME"
TEMP_ARCHIVE="$STAGING_ROOT/$SOURCE_NAME.zip"
mkdir -p "$SNAPSHOT_ROOT" "$SOURCE_CACHE" "$(dirname "$OUTPUT_PATH")"

cleanup() {
    rm -r "$STAGING_ROOT"
}
trap cleanup EXIT

while IFS= read -r relative_path || [[ -n "$relative_path" ]]; do
    if [[ -z "$relative_path" || "$relative_path" == \#* ]]; then
        continue
    fi
    if [[ "$relative_path" == /* || "$relative_path" == *"../"* ]]; then
        echo "Unsafe source allowlist entry: $relative_path" >&2
        exit 1
    fi

    source_path="$REPOSITORY_ROOT/$relative_path"
    destination_path="$SNAPSHOT_ROOT/$relative_path"
    if [[ ! -f "$source_path" ]]; then
        echo "Required source file is missing: $relative_path" >&2
        exit 1
    fi
    mkdir -p "$(dirname "$destination_path")"

    if [[ "$relative_path" == "DCA Script Marker — DCA State Template.xlsx" ]]; then
        "$SCRIPT_DIR/sanitize_template.sh" "$source_path" "$destination_path"
    else
        /bin/cp "$source_path" "$destination_path"
    fi
done < "$SOURCE_FILE_LIST"

THIRD_PARTY_ROOT="$SNAPSHOT_ROOT/third_party_sources"
mkdir -p "$THIRD_PARTY_ROOT"
while IFS=$'\t' read -r expected_sha filename source_url || [[ -n "$expected_sha" ]]; do
    if [[ -z "$expected_sha" || "$expected_sha" == \#* ]]; then
        continue
    fi
    cached_path="$SOURCE_CACHE/$filename"
    download_path="$SOURCE_CACHE/.$filename.download"

    if [[ -f "$cached_path" ]]; then
        actual_sha="$(shasum -a 256 "$cached_path" | awk '{print $1}')"
        if [[ "$actual_sha" != "$expected_sha" ]]; then
            echo "Cached dependency source has the wrong checksum: $filename" >&2
            exit 1
        fi
    else
        curl \
            --fail \
            --location \
            --proto '=https' \
            --retry 3 \
            --silent \
            --show-error \
            --tlsv1.2 \
            --output "$download_path" \
            "$source_url"
        actual_sha="$(shasum -a 256 "$download_path" | awk '{print $1}')"
        if [[ "$actual_sha" != "$expected_sha" ]]; then
            echo "Downloaded dependency source has the wrong checksum: $filename" >&2
            exit 1
        fi
        mv "$download_path" "$cached_path"
    fi

    /bin/cp "$cached_path" "$THIRD_PARTY_ROOT/$filename"
done < "$DEPENDENCY_LIST"

THIRD_PARTY_LICENSE_ROOT="$SNAPSHOT_ROOT/THIRD_PARTY_LICENSES"
mkdir -p "$THIRD_PARTY_LICENSE_ROOT"
/bin/cp "$SNAPSHOT_ROOT/LICENSE" "$THIRD_PARTY_LICENSE_ROOT/AGPL-3.0.txt"

extract_license() {
    local archive_name="$1"
    local member_pattern="$2"
    local output_name="$3"
    local archive_path="$THIRD_PARTY_ROOT/$archive_name"
    local member_name

    member_name="$(
        tar -tf "$archive_path" \
            | awk -v pattern="$member_pattern" \
                '$0 ~ pattern && !found { print; found = 1 }'
    )"
    if [[ -z "$member_name" ]]; then
        echo "Could not find a required licence in $archive_name." >&2
        exit 1
    fi
    tar -xOf "$archive_path" "$member_name" \
        > "$THIRD_PARTY_LICENSE_ROOT/$output_name"
}

extract_license \
    pymupdf-1.27.2.3.tar.gz \
    '^pymupdf-1[.]27[.]2[.]3/COPYING$' \
    PyMuPDF-1.27.2.3-COPYING.txt
extract_license \
    mupdf-1.27.2-source.tar.gz \
    '^mupdf-[^/]+/COPYING$' \
    MuPDF-1.27.2-COPYING.txt
extract_license \
    Python-3.11.5.tgz \
    '^Python-3[.]11[.]5/LICENSE$' \
    Python-3.11.5.txt
extract_license \
    openssl-3.0.10.tar.gz \
    '^openssl-3[.]0[.]10/LICENSE[.]txt$' \
    OpenSSL-3.0.10.txt
extract_license \
    openpyxl-3.1.5.tar.gz \
    '^openpyxl-3[.]1[.]5/LICENCE[.]rst$' \
    openpyxl-3.1.5.txt
extract_license \
    et_xmlfile-2.0.0.tar.gz \
    '^et_xmlfile-2[.]0[.]0/LICENCE[.]rst$' \
    et_xmlfile-2.0.0-MIT.txt
extract_license \
    et_xmlfile-2.0.0.tar.gz \
    '^et_xmlfile-2[.]0[.]0/LICENCE[.]python$' \
    et_xmlfile-2.0.0-Python.txt
extract_license \
    et_xmlfile-2.0.0.tar.gz \
    '^et_xmlfile-2[.]0[.]0/AUTHORS[.]txt$' \
    et_xmlfile-2.0.0-AUTHORS.txt
extract_license \
    pyinstaller-6.22.2.tar.gz \
    '/COPYING[.]txt$' \
    PyInstaller-6.22.2.txt

{
    printf 'Complete dependency sources and their nested notices are in:\n'
    printf '../third_party_sources/\n\n'
    printf 'MuPDF embedded-library, font, CMap, ICC, and hyphenation notices\n'
    printf 'are preserved inside mupdf-1.27.2-source.tar.gz.\n'
} > "$THIRD_PARTY_LICENSE_ROOT/README.txt"

(
    cd "$SNAPSHOT_ROOT"
    find . -type f ! -name SOURCE_MANIFEST.sha256 -print \
        | LC_ALL=C sort \
        | while IFS= read -r source_file; do
            shasum -a 256 "$source_file"
        done > SOURCE_MANIFEST.sha256
    shasum -a 256 -c SOURCE_MANIFEST.sha256 >/dev/null
)

(
    cd "$STAGING_ROOT"
    zip -q -X -r "$TEMP_ARCHIVE" "$SOURCE_NAME"
)
unzip -tq "$TEMP_ARCHIVE" >/dev/null
mv "$TEMP_ARCHIVE" "$OUTPUT_PATH"

echo "$OUTPUT_PATH"
