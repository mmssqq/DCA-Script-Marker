#!/bin/bash

set -euo pipefail

APP_PATH="${1:-}"

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
