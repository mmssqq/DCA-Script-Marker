#!/bin/bash

set -euo pipefail

APP_PATH="${1:-}"
MINIMUM_MACOS_VERSION="${DCA_MINIMUM_MACOS:-12.0}"

version_is_greater() {
    local candidate="$1"
    local maximum="$2"
    local candidate_major candidate_minor candidate_patch
    local maximum_major maximum_minor maximum_patch

    IFS=. read -r candidate_major candidate_minor candidate_patch \
        <<< "$candidate"
    IFS=. read -r maximum_major maximum_minor maximum_patch \
        <<< "$maximum"
    candidate_minor="${candidate_minor:-0}"
    candidate_patch="${candidate_patch:-0}"
    maximum_minor="${maximum_minor:-0}"
    maximum_patch="${maximum_patch:-0}"

    if [[ ! "$candidate_major" =~ ^[0-9]+$ \
        || ! "$candidate_minor" =~ ^[0-9]+$ \
        || ! "$candidate_patch" =~ ^[0-9]+$ \
        || ! "$maximum_major" =~ ^[0-9]+$ \
        || ! "$maximum_minor" =~ ^[0-9]+$ \
        || ! "$maximum_patch" =~ ^[0-9]+$ ]]; then
        return 2
    fi

    if (( candidate_major != maximum_major )); then
        (( candidate_major > maximum_major ))
        return
    fi
    if (( candidate_minor != maximum_minor )); then
        (( candidate_minor > maximum_minor ))
        return
    fi
    (( candidate_patch > maximum_patch ))
}

if [[ "$APP_PATH" == "--version-is-greater" ]]; then
    if [[ $# -ne 3 ]]; then
        echo "Usage: $0 --version-is-greater <candidate> <maximum>" >&2
        exit 2
    fi
    if version_is_greater "$2" "$3"; then
        exit 0
    else
        exit $?
    fi
fi

if [[ -z "$APP_PATH" || ! -d "$APP_PATH" ]]; then
    echo "Usage: $0 <DCA Script Marker.app>" >&2
    exit 2
fi

APP_PATH="$(realpath "$APP_PATH")"

HOST_EXECUTABLE="$APP_PATH/Contents/MacOS/DCA Script Marker"
ARM_ENGINE_APP="$APP_PATH/Contents/Helpers/DCAEngine-arm64.app"
INTEL_ENGINE_APP="$APP_PATH/Contents/Helpers/DCAEngine-x86_64.app"
ARM_ENGINE="$ARM_ENGINE_APP/Contents/MacOS/DCAEngine"
INTEL_ENGINE="$INTEL_ENGINE_APP/Contents/MacOS/DCAEngine"
LICENSE_ROOT="$APP_PATH/Contents/Resources/Licenses"
USER_GUIDE_PDF="$APP_PATH/Contents/Resources/START HERE - User Guide - 使用手册.pdf"

for bundle_path in "$APP_PATH" "$ARM_ENGINE_APP" "$INTEL_ENGINE_APP"; do
    bundle_minimum="$({
        plutil -extract LSMinimumSystemVersion raw -o - \
            "$bundle_path/Contents/Info.plist"
    } 2>/dev/null || true)"
    if [[ "$bundle_minimum" != "$MINIMUM_MACOS_VERSION" ]]; then
        echo "A bundle has the wrong minimum macOS version: $bundle_path ($bundle_minimum)" >&2
        exit 1
    fi
done

while IFS= read -r -d '' candidate; do
    if ! file "$candidate" | grep -q 'Mach-O'; then
        continue
    fi

    minimum_versions="$(
        otool -l "$candidate" | awk '
            $1 == "cmd" && $2 == "LC_BUILD_VERSION" {
                command_type = "build"
                next
            }
            $1 == "cmd" && $2 == "LC_VERSION_MIN_MACOSX" {
                command_type = "legacy"
                next
            }
            command_type == "build" && $1 == "minos" {
                print $2
                command_type = ""
            }
            command_type == "legacy" && $1 == "version" {
                print $2
                command_type = ""
            }
        '
    )"
    if [[ -z "$minimum_versions" ]]; then
        echo "Could not read the minimum macOS version from: $candidate" >&2
        exit 1
    fi

    while IFS= read -r binary_minimum; do
        comparison_status=0
        if version_is_greater "$binary_minimum" "$MINIMUM_MACOS_VERSION"; then
            comparison_status=0
        else
            comparison_status=$?
        fi
        if [[ "$comparison_status" -eq 0 ]]; then
            echo "A bundled binary requires macOS $binary_minimum: $candidate" >&2
            exit 1
        fi
        if [[ "$comparison_status" -ne 1 ]]; then
            echo "Could not compare macOS version $binary_minimum for: $candidate" >&2
            exit 1
        fi
    done <<< "$minimum_versions"
done < <(find "$APP_PATH" -type f -print0)

if [[ ! -s "$USER_GUIDE_PDF" \
    || "$(head -c 5 "$USER_GUIDE_PDF")" != "%PDF-" ]]; then
    echo "The app is missing its bundled PDF user guide." >&2
    exit 1
fi

for license_file in LICENSE LICENSING.md THIRD_PARTY_NOTICES.md SOURCE.md; do
    if [[ ! -s "$LICENSE_ROOT/$license_file" ]]; then
        echo "The app is missing its bundled licence notice: $license_file" >&2
        exit 1
    fi
done
if ! grep -q 'GNU AFFERO GENERAL PUBLIC LICENSE' "$LICENSE_ROOT/LICENSE"; then
    echo "The bundled LICENSE is not the approved GNU AGPL text." >&2
    exit 1
fi
for third_party_license in \
    AGPL-3.0.txt \
    PyMuPDF-1.27.2.3-COPYING.txt \
    MuPDF-1.27.2-COPYING.txt \
    Python-3.11.5.txt \
    OpenSSL-3.0.10.txt \
    openpyxl-3.1.5.txt \
    et_xmlfile-2.0.0-MIT.txt \
    et_xmlfile-2.0.0-Python.txt \
    PyInstaller-6.22.2.txt; do
    if [[ ! -s "$LICENSE_ROOT/THIRD_PARTY_LICENSES/$third_party_license" ]]; then
        echo "The app is missing a third-party licence: $third_party_license" >&2
        exit 1
    fi
done

lipo "$HOST_EXECUTABLE" -verify_arch arm64 x86_64
lipo "$ARM_ENGINE" -verify_arch arm64
lipo "$INTEL_ENGINE" -verify_arch x86_64

if lipo -archs "$ARM_ENGINE" | grep -q x86_64; then
    echo "The Apple Silicon engine unexpectedly contains Intel code." >&2
    exit 1
fi

if lipo -archs "$INTEL_ENGINE" | grep -q arm64; then
    echo "The Intel engine unexpectedly contains Apple Silicon code." >&2
    exit 1
fi

CLEAN_HOME="$(mktemp -d "${TMPDIR:-/private/tmp}/dca-engine-home.XXXXXX")"
ARM_RESULT="$(
    env -i HOME="$CLEAN_HOME" PATH=/usr/bin:/bin LANG=en_US.UTF-8 \
        arch -arm64 "$ARM_ENGINE" --self-test
)"
INTEL_RESULT="$(
    env -i HOME="$CLEAN_HOME" PATH=/usr/bin:/bin LANG=en_US.UTF-8 \
        arch -x86_64 "$INTEL_ENGINE" --self-test
)"

if [[ "$ARM_RESULT" != *'"architecture": "arm64"'* || "$ARM_RESULT" != *'"frozen": true'* ]]; then
    echo "The Apple Silicon engine self-test failed: $ARM_RESULT" >&2
    exit 1
fi

if [[ "$INTEL_RESULT" != *'"architecture": "x86_64"'* || "$INTEL_RESULT" != *'"frozen": true'* ]]; then
    echo "The Intel engine self-test failed: $INTEL_RESULT" >&2
    exit 1
fi

while IFS= read -r -d '' link_path; do
    resolved_path="$(realpath "$link_path")"
    if [[ "$resolved_path" != "$APP_PATH"/* ]]; then
        echo "A bundled link escapes the app: $link_path -> $resolved_path" >&2
        exit 1
    fi
done < <(find "$APP_PATH" -type l -print0)

while IFS= read -r -d '' candidate; do
    if ! file "$candidate" | grep -q 'Mach-O'; then
        continue
    fi

    # Header lines contain the inspected file's own path (one per architecture)
    # and naturally point into this checkout. Linked-library lines are indented.
    if otool -L "$candidate" | grep -E '^[[:space:]]+' | grep -E '/Users/|/opt/|/usr/local/|/Library/Frameworks/Python.framework' >/dev/null; then
        echo "A bundled executable has a developer-machine dependency: $candidate" >&2
        otool -L "$candidate" >&2
        exit 1
    fi
done < <(find "$APP_PATH" -type f -print0)

# Swift embeds source/build locations as compiler metadata even in Release
# binaries. Those strings are not runtime dependencies. Reject the old paths
# the app previously attempted to execute instead.
if rg -a -l '\.venv/bin/python|anaconda3/bin/python|DCA-Script-Marker/dca_script_marker\.py' "$APP_PATH" >/dev/null; then
    echo "The Release app contains a development-only engine or Python path." >&2
    exit 1
fi

if [[ -n "${HOME:-}" ]] && rg -a -F -l "$HOME/" "$APP_PATH" >/dev/null; then
    echo "The Release app contains a private developer-home path." >&2
    exit 1
fi

codesign --verify --deep --strict "$APP_PATH"
codesign --verify --deep --strict "$ARM_ENGINE_APP"
codesign --verify --deep --strict "$INTEL_ENGINE_APP"

echo "Verified Universal app: $APP_PATH"
echo "Apple Silicon engine: $ARM_RESULT"
echo "Intel engine: $INTEL_RESULT"
