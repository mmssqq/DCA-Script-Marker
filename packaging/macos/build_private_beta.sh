#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCHEME="DCA Script Marker"
APP_VERSION="${DCA_VERSION:-1.0.0}"
BUILD_NUMBER="${DCA_BUILD_NUMBER:-5}"
RELEASE_CHANNEL="${DCA_RELEASE_CHANNEL:-stable}"
MINIMUM_MACOS_VERSION="${DCA_MINIMUM_MACOS:-12.0}"
case "$RELEASE_CHANNEL" in
    stable)
        RELEASE_TAG="v$APP_VERSION"
        VOLUME_NAME="DCA Script Marker"
        DMG_IDENTIFIER="com.siqima.DCA-Script-Marker.dmg"
        TESTING_DOCUMENT_NAME="TESTING_AND_SAFETY.md"
        FEEDBACK_DOCUMENT_NAME="ISSUE_REPORT_TEMPLATE.md"
        ;;
    beta)
        RELEASE_TAG="v$APP_VERSION-beta.$BUILD_NUMBER"
        VOLUME_NAME="DCA Script Marker Beta"
        DMG_IDENTIFIER="com.siqima.DCA-Script-Marker.beta-dmg"
        TESTING_DOCUMENT_NAME="BETA_TESTING.md"
        FEEDBACK_DOCUMENT_NAME="BETA_FEEDBACK_TEMPLATE.md"
        ;;
    *)
        echo "DCA_RELEASE_CHANNEL must be stable or beta." >&2
        exit 2
        ;;
esac
BUILD_OUTPUT_ROOT="$REPOSITORY_ROOT/build"
mkdir -p "$BUILD_OUTPUT_ROOT"
RUN_ROOT="$(mktemp -d "$BUILD_OUTPUT_ROOT/$RELEASE_CHANNEL-release.XXXXXX")"
BUILD_WORK_ROOT="$(mktemp -d "${TMPDIR:-/private/tmp}/dca-$RELEASE_CHANNEL-release-work.XXXXXX")"
DERIVED_DATA="$BUILD_WORK_ROOT/DerivedData"
ENGINE_OUTPUT="$BUILD_WORK_ROOT/Engines"
OUTPUT_DIRECTORY="$RUN_ROOT/Output"
PACKAGE_ROOT="$RUN_ROOT/Package"
APP_PATH="$PACKAGE_ROOT/DCA Script Marker.app"
DMG_PATH="$OUTPUT_DIRECTORY/DCA-Script-Marker-$RELEASE_TAG-macOS.dmg"
ZIP_PATH="$OUTPUT_DIRECTORY/DCA-Script-Marker-$RELEASE_TAG-macOS.zip"
SOURCE_NAME="DCA-Script-Marker-$RELEASE_TAG-source"
SOURCE_ARCHIVE="$OUTPUT_DIRECTORY/$SOURCE_NAME.zip"
SOURCE_EXTRACT_ROOT="$BUILD_WORK_ROOT/SourceSnapshot"
SOURCE_REPOSITORY_ROOT="$SOURCE_EXTRACT_ROOT/$SOURCE_NAME"
PROJECT_PATH="$SOURCE_REPOSITORY_ROOT/macOS App/DCA Script Marker/DCA Script Marker.xcodeproj"
CANONICAL_TEMPLATE_PATH="$REPOSITORY_ROOT/DCA Script Marker — DCA State Template.xlsx"
TEMPLATE_PATH="$SOURCE_REPOSITORY_ROOT/DCA Script Marker — DCA State Template.xlsx"
SIGNING_IDENTITY="${DCA_CODESIGN_IDENTITY:--}"
NOTARY_PROFILE="${DCA_NOTARY_PROFILE:-}"

mkdir -p "$OUTPUT_DIRECTORY" "$PACKAGE_ROOT"

if [[ ! -f "$CANONICAL_TEMPLATE_PATH" ]]; then
    echo "The finalized DCA State template is missing: $CANONICAL_TEMPLATE_PATH" >&2
    exit 1
fi

for release_file in \
    LICENSE \
    LICENSING.md \
    THIRD_PARTY_NOTICES.md \
    SOURCE.md \
    CONTRIBUTING.md \
    USER_GUIDE.md \
    "output/pdf/START HERE - User Guide - 使用手册.pdf"; do
    if [[ ! -s "$REPOSITORY_ROOT/$release_file" ]]; then
        echo "A required release file is missing: $release_file" >&2
        exit 1
    fi
done

if [[ -n "$NOTARY_PROFILE" && "$SIGNING_IDENTITY" == "-" ]]; then
    echo "DCA_NOTARY_PROFILE requires a Developer ID Application identity." >&2
    exit 1
fi

if [[ "$SIGNING_IDENTITY" != "-" ]]; then
    if [[ -z "$NOTARY_PROFILE" ]]; then
        echo "A shareable release requires DCA_NOTARY_PROFILE for notarization." >&2
        exit 1
    fi

    IDENTITY_DETAILS="$(
        security find-identity -v -p codesigning \
            | grep -F "$SIGNING_IDENTITY" \
            | head -n 1 \
            || true
    )"
    if [[ "$IDENTITY_DETAILS" != *"Developer ID Application:"* ]]; then
        echo "The requested Developer ID Application identity is not installed." >&2
        exit 1
    fi

    if ! xcrun notarytool history \
        --keychain-profile "$NOTARY_PROFILE" \
        --output-format json >/dev/null; then
        echo "The notarytool Keychain profile could not be validated." >&2
        exit 1
    fi
fi

DCA_VERSION="$APP_VERSION" DCA_BUILD_NUMBER="$BUILD_NUMBER" \
    DCA_RELEASE_CHANNEL="$RELEASE_CHANNEL" \
    "$SCRIPT_DIR/build_source_archive.sh" "$SOURCE_ARCHIVE"
mkdir -p "$SOURCE_EXTRACT_ROOT"
unzip -q "$SOURCE_ARCHIVE" -d "$SOURCE_EXTRACT_ROOT"
if [[ ! -d "$SOURCE_REPOSITORY_ROOT" ]]; then
    echo "The source archive did not contain the expected release root." >&2
    exit 1
fi

DCA_VERSION="$APP_VERSION" DCA_BUILD_NUMBER="$BUILD_NUMBER" \
    DCA_MINIMUM_MACOS="$MINIMUM_MACOS_VERSION" \
    "$SOURCE_REPOSITORY_ROOT/packaging/macos/build_engines.sh" "$ENGINE_OUTPUT"

xcodebuild \
    -quiet \
    -project "$PROJECT_PATH" \
    -scheme "$SCHEME" \
    -configuration Release \
    -destination "generic/platform=macOS" \
    -derivedDataPath "$DERIVED_DATA" \
    ARCHS="arm64 x86_64" \
    ONLY_ACTIVE_ARCH=NO \
    MACOSX_DEPLOYMENT_TARGET="$MINIMUM_MACOS_VERSION" \
    MARKETING_VERSION="$APP_VERSION" \
    CURRENT_PROJECT_VERSION="$BUILD_NUMBER" \
    CODE_SIGNING_ALLOWED=NO \
    COMPILER_INDEX_STORE_ENABLE=NO \
    OTHER_SWIFT_FLAGS="-disable-sandbox" \
    build

ditto \
    "$DERIVED_DATA/Build/Products/Release/DCA Script Marker.app" \
    "$APP_PATH"

ditto "$TEMPLATE_PATH" \
    "$PACKAGE_ROOT/DCA Script Marker — DCA State Template.xlsx"
ditto "$SOURCE_REPOSITORY_ROOT/README.md" "$PACKAGE_ROOT/README.md"
ditto "$SOURCE_REPOSITORY_ROOT/TESTING_AND_SAFETY.md" \
    "$PACKAGE_ROOT/$TESTING_DOCUMENT_NAME"
ditto "$SOURCE_REPOSITORY_ROOT/ISSUE_REPORT_TEMPLATE.md" \
    "$PACKAGE_ROOT/$FEEDBACK_DOCUMENT_NAME"
ditto "$SOURCE_REPOSITORY_ROOT/PRIVACY.md" "$PACKAGE_ROOT/PRIVACY.md"
ditto "$SOURCE_REPOSITORY_ROOT/RELEASE_NOTES.md" "$PACKAGE_ROOT/RELEASE_NOTES.md"
ditto "$SOURCE_REPOSITORY_ROOT/LICENSE" "$PACKAGE_ROOT/LICENSE"
ditto "$SOURCE_REPOSITORY_ROOT/LICENSING.md" "$PACKAGE_ROOT/LICENSING.md"
ditto "$SOURCE_REPOSITORY_ROOT/THIRD_PARTY_NOTICES.md" \
    "$PACKAGE_ROOT/THIRD_PARTY_NOTICES.md"
ditto "$SOURCE_REPOSITORY_ROOT/THIRD_PARTY_LICENSES" \
    "$PACKAGE_ROOT/THIRD_PARTY_LICENSES"
ditto "$SOURCE_REPOSITORY_ROOT/SOURCE.md" "$PACKAGE_ROOT/SOURCE.md"
ditto "$SOURCE_REPOSITORY_ROOT/CONTRIBUTING.md" "$PACKAGE_ROOT/CONTRIBUTING.md"
ditto "$SOURCE_REPOSITORY_ROOT/USER_GUIDE.md" "$PACKAGE_ROOT/USER_GUIDE.md"
ditto \
    "$SOURCE_REPOSITORY_ROOT/output/pdf/START HERE - User Guide - 使用手册.pdf" \
    "$PACKAGE_ROOT/START HERE - User Guide - 使用手册.pdf"
# Keep the corresponding-source archive beside the installer as a separate
# release asset. Apple recursively notarizes archives found inside a DMG; the
# upstream PyInstaller source tarball intentionally contains unsigned bootloader
# development binaries, even though none of those files are executed by the app.
ln -s /Applications "$PACKAGE_ROOT/Applications"

mkdir -p "$APP_PATH/Contents/Helpers"
ditto \
    "$ENGINE_OUTPUT/DCAEngine-arm64.app" \
    "$APP_PATH/Contents/Helpers/DCAEngine-arm64.app"
ditto \
    "$ENGINE_OUTPUT/DCAEngine-x86_64.app" \
    "$APP_PATH/Contents/Helpers/DCAEngine-x86_64.app"

APP_LICENSE_ROOT="$APP_PATH/Contents/Resources/Licenses"
mkdir -p "$APP_LICENSE_ROOT"
for license_file in LICENSE LICENSING.md THIRD_PARTY_NOTICES.md SOURCE.md; do
    ditto \
        "$SOURCE_REPOSITORY_ROOT/$license_file" \
        "$APP_LICENSE_ROOT/$license_file"
done
ditto \
    "$SOURCE_REPOSITORY_ROOT/THIRD_PARTY_LICENSES" \
    "$APP_LICENSE_ROOT/THIRD_PARTY_LICENSES"

sign_for_distribution() {
    local file_path="$1"

    codesign \
        --force \
        --options runtime \
        --timestamp \
        --sign "$SIGNING_IDENTITY" \
        "$file_path"
}

sign_disk_image() {
    codesign \
        --force \
        --timestamp \
        --identifier "$DMG_IDENTIFIER" \
        --sign "$SIGNING_IDENTITY" \
        "$1"
}

verify_distribution_signatures() {
    local signature_details
    local expected_team_id
    local candidate
    local candidate_details
    local candidate_team_id
    local entitlements

    signature_details="$(codesign -d --verbose=4 "$APP_PATH" 2>&1)"
    expected_team_id="$(
        printf '%s\n' "$signature_details" \
            | sed -n 's/^TeamIdentifier=//p' \
            | head -n 1
    )"

    if [[ -z "$expected_team_id" || "$expected_team_id" == "not set" ]]; then
        echo "The signed app has no Developer Team ID." >&2
        exit 1
    fi
    if [[ "$signature_details" != *"Authority=Developer ID Application:"* ]]; then
        echo "The app is not signed with Developer ID Application." >&2
        exit 1
    fi
    if [[ "$signature_details" != *"flags=0x10000(runtime)"* ]]; then
        echo "The app is missing Hardened Runtime." >&2
        exit 1
    fi
    if ! printf '%s\n' "$signature_details" | grep -q '^Timestamp='; then
        echo "The app signature has no secure timestamp." >&2
        exit 1
    fi

    while IFS= read -r -d '' candidate; do
        if ! file "$candidate" | grep -q 'Mach-O'; then
            continue
        fi
        candidate_details="$(codesign -d --verbose=4 "$candidate" 2>&1)"
        candidate_team_id="$(
            printf '%s\n' "$candidate_details" \
                | sed -n 's/^TeamIdentifier=//p' \
                | head -n 1
        )"
        if [[ "$candidate_team_id" != "$expected_team_id" ]]; then
            echo "A nested binary has a mismatched Team ID: $candidate" >&2
            exit 1
        fi
        if [[ "$candidate_details" != *"flags=0x10000(runtime)"* ]]; then
            echo "A nested binary is missing Hardened Runtime: $candidate" >&2
            exit 1
        fi
        if ! printf '%s\n' "$candidate_details" | grep -q '^Timestamp='; then
            echo "A nested binary has no secure timestamp: $candidate" >&2
            exit 1
        fi
    done < <(find "$APP_PATH" -type f -print0)

    entitlements="$(codesign -d --entitlements :- "$APP_PATH" 2>/dev/null || true)"
    if [[ "$entitlements" == *"com.apple.security.get-task-allow"* ]]; then
        echo "The Release app contains the development get-task-allow entitlement." >&2
        exit 1
    fi
}

if [[ "$SIGNING_IDENTITY" == "-" ]]; then
    # Ad-hoc signatures have no Team ID. Applying Hardened Runtime library
    # validation to each nested binary separately prevents the frozen Python
    # helpers from loading their bundled frameworks. Deep ad-hoc signing is
    # appropriate for local verification; shared builds use the Developer ID
    # branch below so every nested component has the same Team ID.
    codesign --force --deep --sign - \
        "$APP_PATH/Contents/Helpers/DCAEngine-arm64.app"
    codesign --force --deep --sign - \
        "$APP_PATH/Contents/Helpers/DCAEngine-x86_64.app"
    codesign --force --deep --sign - "$APP_PATH"
else
    while IFS= read -r -d '' candidate; do
        if file "$candidate" | grep -q 'Mach-O'; then
            sign_for_distribution "$candidate"
        fi
    done < <(find "$APP_PATH/Contents/Helpers" -type f -print0)

    sign_for_distribution "$APP_PATH/Contents/Helpers/DCAEngine-arm64.app"
    sign_for_distribution "$APP_PATH/Contents/Helpers/DCAEngine-x86_64.app"
    sign_for_distribution "$APP_PATH"
    verify_distribution_signatures
fi
DCA_MINIMUM_MACOS="$MINIMUM_MACOS_VERSION" \
    "$SCRIPT_DIR/verify_beta_app.sh" "$APP_PATH"

GIT_COMMIT="$(git -C "$REPOSITORY_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
SOURCE_PROVENANCE="commit $GIT_COMMIT"
if [[ -n "$(git -C "$REPOSITORY_ROOT" status --porcelain 2>/dev/null || true)" ]]; then
    SOURCE_PROVENANCE="working source snapshot based on $GIT_COMMIT"
fi
SOURCE_SHA="$(shasum -a 256 "$SOURCE_ARCHIVE" | awk '{print $1}')"
SIGNATURE_DESCRIPTION="Ad-hoc signature; local verification only"
if [[ "$SIGNING_IDENTITY" != "-" ]]; then
    SIGNATURE_DESCRIPTION="$SIGNING_IDENTITY"
fi
{
    printf 'DCA Script Marker %s\n' "$APP_VERSION"
    printf 'Build number: %s\n' "$BUILD_NUMBER"
    printf 'Release channel: %s\n' "$RELEASE_CHANNEL"
    printf 'Minimum macOS: %s\n' "$MINIMUM_MACOS_VERSION"
    printf 'Architectures: arm64, x86_64\n'
    printf 'Signing: %s\n' "$SIGNATURE_DESCRIPTION"
    printf 'Source archive: %s\n' "$(basename "$SOURCE_ARCHIVE")"
    printf 'Source SHA-256: %s\n' "$SOURCE_SHA"
    printf 'Source provenance: %s\n' "$SOURCE_PROVENANCE"
    printf 'Licence: GNU AGPL-3.0-or-later\n'
} > "$PACKAGE_ROOT/RELEASE_MANIFEST.txt"

if [[ -e "$PACKAGE_ROOT/$(basename "$SOURCE_ARCHIVE")" ]]; then
    echo "The matching source archive must be released beside, not inside, the DMG." >&2
    exit 1
fi

if hdiutil create \
    -volname "$VOLUME_NAME" \
    -srcfolder "$PACKAGE_ROOT" \
    -format UDZO \
    -ov \
    "$DMG_PATH"; then
    PACKAGE_PATH="$DMG_PATH"
else
    if [[ "$SIGNING_IDENTITY" != "-" || -n "$NOTARY_PROFILE" ]]; then
        echo "Could not create the DMG required for the signed release." >&2
        exit 1
    fi

    echo "DMG creation is unavailable; creating a local-verification ZIP instead." >&2
    ditto -c -k --sequesterRsrc "$PACKAGE_ROOT" "$ZIP_PATH"
    PACKAGE_PATH="$ZIP_PATH"
fi

if [[ "$SIGNING_IDENTITY" != "-" ]]; then
    sign_disk_image "$PACKAGE_PATH"
fi

if [[ -n "$NOTARY_PROFILE" ]]; then
    NOTARY_RESULT="$RUN_ROOT/notarization-result.json"
    xcrun notarytool submit \
        "$PACKAGE_PATH" \
        --keychain-profile "$NOTARY_PROFILE" \
        --wait \
        --output-format json > "$NOTARY_RESULT"
    NOTARY_STATUS="$(plutil -extract status raw -o - "$NOTARY_RESULT")"
    NOTARY_SUBMISSION_ID="$(plutil -extract id raw -o - "$NOTARY_RESULT")"
    if [[ "$NOTARY_STATUS" != "Accepted" ]]; then
        NOTARY_LOG="$RUN_ROOT/notarization-log.json"
        xcrun notarytool log \
            "$NOTARY_SUBMISSION_ID" \
            "$NOTARY_LOG" \
            --keychain-profile "$NOTARY_PROFILE" \
            || true
        echo "Notarization was not accepted. See: $NOTARY_LOG" >&2
        exit 1
    fi
    xcrun stapler staple "$PACKAGE_PATH"
    xcrun stapler validate "$PACKAGE_PATH"
    spctl --assess \
        --type open \
        --context context:primary-signature \
        --verbose \
        "$PACKAGE_PATH"
fi

if [[ "$PACKAGE_PATH" == *.dmg ]]; then
    hdiutil verify "$PACKAGE_PATH"
else
    unzip -tq "$PACKAGE_PATH"
fi

OUTPUT_MANIFEST="$OUTPUT_DIRECTORY/RELEASE_MANIFEST.txt"
ditto "$PACKAGE_ROOT/RELEASE_MANIFEST.txt" "$OUTPUT_MANIFEST"
CHECKSUM_PATH="$OUTPUT_DIRECTORY/SHA256SUMS.txt"
(
    cd "$OUTPUT_DIRECTORY"
    shasum -a 256 \
        "$(basename "$PACKAGE_PATH")" \
        "$(basename "$SOURCE_ARCHIVE")" \
        "$(basename "$OUTPUT_MANIFEST")" \
        > "$(basename "$CHECKSUM_PATH")"
)

echo "Release app: $APP_PATH"
echo "Release package: $PACKAGE_PATH"
echo "Matching source archive: $SOURCE_ARCHIVE"
echo "Release manifest: $OUTPUT_MANIFEST"
echo "SHA-256 checksums: $CHECKSUM_PATH"

if [[ "$SIGNING_IDENTITY" == "-" ]]; then
    echo "This build is ad-hoc signed for local verification only."
    echo "Set DCA_CODESIGN_IDENTITY to your Developer ID Application identity before sharing it."
fi

rm -r "$BUILD_WORK_ROOT"
