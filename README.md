# DCA Script Marker

DCA Script Marker is a local macOS tool for theatre sound teams. It reads a
scene-by-scene DCA assignment workbook and a text-based script PDF, adds the
correct DCA number beside dialogue cues, preserves the PDF page layout, and
creates a review report for human checking.

The current build is a private beta for macOS 13 or later. One Universal app
supports both Apple Silicon and Intel Macs without requiring Python, Homebrew,
or Xcode on the tester's computer.

## Beta status

The project is not ready for production show use. Every generated script must
be checked against its review report and spot-checked by a member of the sound
team. See [BETA_TESTING.md](BETA_TESTING.md) for supported inputs, known
limitations, and the tester checklist. See [PRIVACY.md](PRIVACY.md) for local
data handling and [RELEASE_NOTES.md](RELEASE_NOTES.md) for beta readiness.

## Current capabilities

- Horizontal and supported legacy vertical DCA workbook formats
- Editable or flattened PDF markings
- Full marking, first appearance, and DCA State legend modes
- Independent DCA number, scene/state, and page header/footer appearance
- English, Simplified Chinese, and mixed-language scripts with selectable text
- Local processing with no telemetry or script upload

Scanned/image-only and password-protected PDFs are not supported in the current
beta.

## Development

The marking engine is `dca_script_marker.py`. The macOS packaging workflow and
private-beta build instructions are in
[`packaging/macos/README.md`](packaging/macos/README.md).

## Licence and source code

DCA Script Marker is free and open-source software licensed under the GNU
Affero General Public License, version 3 or later. The copyright holder may
also offer the same original code under separate terms in the future.

Every beta binary must be distributed with its matching source archive. See
[LICENSING.md](LICENSING.md), [SOURCE.md](SOURCE.md), and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for details. Coffee donations
are welcome but never required to use the software.
