# macOS private beta packaging

The beta is one Universal macOS app. Its Swift interface contains both Intel
and Apple Silicon code. Internally it contains one self-contained marker engine
for each processor and automatically launches the correct engine.

## Local verification build

Run:

```sh
./packaging/macos/build_private_beta.sh
```

Without additional settings, the result is ad-hoc signed and is suitable only
for local testing.

The local build normally creates a DMG. If disk-image services are unavailable
in a protected build environment, it falls back to a ZIP for local verification.
Shareable Developer ID builds deliberately require the DMG workflow.
The app, helper engines, package filename, and checksum all use the same beta
version and build number. Override them with `DCA_VERSION` and
`DCA_BUILD_NUMBER` when preparing a later beta.

## Shareable private beta

In Xcode, open **Settings → Accounts**, select the paid team, choose
**Manage Certificates**, and add a `Developer ID Application` certificate.
Then create the notarization profile. Omit `--password` so `notarytool` prompts
securely instead of placing a secret in shell history:

```sh
xcrun notarytool store-credentials "DCA Script Marker Notary" \
  --apple-id "YOUR_APPLE_ID" \
  --team-id "YOUR_TEAM_ID"
```

After both items are available in Keychain, run:

```sh
DCA_CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
DCA_NOTARY_PROFILE="DCA Script Marker Notary" \
./packaging/macos/build_private_beta.sh
```

`DCA_NOTARY_PROFILE` is the Keychain profile created for `notarytool`. The
script builds both engines from the pinned requirements, runs the Python tests
under both processor architectures, builds the Universal Swift app, signs the
nested code, verifies portability, creates a DMG, submits it for notarization,
and staples the accepted ticket. It then runs a Gatekeeper assessment and
creates basename-only SHA-256 checksums.

The DMG includes the app, the finalized bilingual DCA State template, private
beta instructions, privacy information, release notes, feedback template, and
licence files. The exact matching corresponding-source ZIP is published beside
the DMG as a separate GitHub Release asset. Keeping it outside the DMG prevents
Apple's notarization service from treating development binaries preserved in
upstream source tarballs as executable app content. The source ZIP is built
from an explicit allowlist, contains a checksum manifest, and includes
checksum-locked upstream source archives for the bundled runtime and
dependencies. Private test scripts and generated files are never copied into
it.

The output directory contains four release artifacts:

- the notarized and stapled macOS DMG;
- the matching `-source.zip` archive;
- `RELEASE_MANIFEST.txt`; and
- `SHA256SUMS.txt` covering the other three files.

The binary and matching source archive must always be distributed together.
See the repository's `LICENSING.md`, `SOURCE.md`, and
`THIRD_PARTY_NOTICES.md` before sharing a build.

The finalized template is never edited in place. The release workflow removes
only Excel's optional developer-machine absolute-path metadata from its staged
copy; workbook content and formatting remain unchanged.

The initial private beta supports macOS 13 Ventura or later.
