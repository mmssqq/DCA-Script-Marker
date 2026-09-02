#!/bin/bash

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DESTINATION="${1:-}"
PYTHON_BIN="${DCA_BUILD_PYTHON:-/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11}"
APP_VERSION="${DCA_VERSION:-2.0.0}"
BUILD_NUMBER="${DCA_BUILD_NUMBER:-8}"
MINIMUM_MACOS_VERSION="${DCA_MINIMUM_MACOS:-12.0}"

if [[ -z "$DESTINATION" ]]; then
    echo "Usage: $0 <engine-output-directory>" >&2
    exit 2
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "A universal Python 3.11 build is required at: $PYTHON_BIN" >&2
    exit 1
fi

PYTHON_ARCHITECTURES="$(lipo -archs "$PYTHON_BIN")"
if [[ "$PYTHON_ARCHITECTURES" != *"arm64"* || "$PYTHON_ARCHITECTURES" != *"x86_64"* ]]; then
    echo "The build Python must contain both arm64 and x86_64." >&2
    exit 1
fi

BUILD_ROOT="$(mktemp -d "${TMPDIR:-/private/tmp}/dca-engine-build.XXXXXX")"
SOURCE_ROOT="$BUILD_ROOT/source"
PIP_CACHE_DIR="${DCA_PIP_CACHE_DIR:-$REPOSITORY_ROOT/build/pip-cache}"

mkdir -p "$SOURCE_ROOT" "$DESTINATION" "$PIP_CACHE_DIR"
cp "$REPOSITORY_ROOT/dca_script_marker.py" "$SOURCE_ROOT/dca_script_marker.py"

run_for_architecture() {
    local architecture="$1"
    shift

    if [[ "$architecture" == "x86_64" ]]; then
        arch -x86_64 "$@"
    else
        arch -arm64 "$@"
    fi
}

build_engine() {
    local architecture="$1"
    local engine_name="DCAEngine"
    local engine_bundle_name="DCAEngine-$architecture.app"
    local bundle_architecture="$architecture"
    if [[ "$architecture" == "x86_64" ]]; then
        bundle_architecture="x86-64"
    fi
    local bundle_identifier="com.siqima.DCA-Script-Marker.engine.$bundle_architecture"
    local environment="$BUILD_ROOT/venv-$architecture"
    local architecture_root="$BUILD_ROOT/$architecture"
    local bundle_root="$DESTINATION/$engine_bundle_name"

    "$PYTHON_BIN" -m venv "$environment"

    PIP_CACHE_DIR="$PIP_CACHE_DIR" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    run_for_architecture "$architecture" \
        "$environment/bin/python" -m pip install \
        --only-binary=:all: \
        --requirement "$REPOSITORY_ROOT/requirements.txt" \
        --requirement "$SCRIPT_DIR/build-requirements.txt"

    run_for_architecture "$architecture" \
        "$environment/bin/python" -m pip check
    run_for_architecture "$architecture" \
        "$environment/bin/python" -c \
        'from importlib.metadata import version; expected={"PyMuPDF":"1.27.2.3","openpyxl":"3.1.5","et_xmlfile":"2.0.0","PyInstaller":"6.22.2","altgraph":"0.17.5","macholib":"1.16.4","packaging":"26.3","pyinstaller-hooks-contrib":"2026.6"}; actual={name:version(name) for name in expected}; assert actual == expected, f"Dependency mismatch: {actual!r}"; print(actual)'

    run_for_architecture "$architecture" \
        "$environment/bin/python" -m unittest discover \
        -s "$REPOSITORY_ROOT/tests" -v

    mkdir -p "$architecture_root/cache" "$architecture_root/spec"
    PYINSTALLER_CONFIG_DIR="$architecture_root/cache" \
    run_for_architecture "$architecture" \
        "$environment/bin/python" -m PyInstaller \
        --noconfirm \
        --clean \
        --onedir \
        --windowed \
        --target-architecture "$architecture" \
        --osx-bundle-identifier "$bundle_identifier" \
        --name "$engine_name" \
        --distpath "$architecture_root/dist" \
        --workpath "$architecture_root/work" \
        --specpath "$architecture_root/spec" \
        "$SOURCE_ROOT/dca_script_marker.py"

    ditto \
        "$architecture_root/dist/$engine_name.app" \
        "$bundle_root"
    plutil -replace CFBundleShortVersionString -string "$APP_VERSION" \
        "$bundle_root/Contents/Info.plist"
    plutil -replace CFBundleVersion -string "$BUILD_NUMBER" \
        "$bundle_root/Contents/Info.plist"
    plutil -replace LSBackgroundOnly -bool true \
        "$bundle_root/Contents/Info.plist"
    plutil -replace LSMinimumSystemVersion -string "$MINIMUM_MACOS_VERSION" \
        "$bundle_root/Contents/Info.plist"
}

build_engine arm64
build_engine x86_64

echo "$DESTINATION"
