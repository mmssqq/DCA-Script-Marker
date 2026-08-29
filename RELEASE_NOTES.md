# Release notes

## 1.0.0 (build 7) — first stable release

DCA Script Marker 1.0.0 is the first stable GitHub release. It is a local,
Universal macOS app for theatre sound teams and supports macOS 12 Monterey or
later on Apple Silicon and 64-bit Intel Macs. Users do not need Python,
Homebrew, or Xcode.

### Highlights

- Marks dialogue cues with DCA assignments from the supplied scene/state
  workbook while preserving the script PDF layout
- Supports English, Simplified Chinese, and mixed-language scripts, including
  broader bold, centred, multi-column, cast-track, combined-speaker, and
  full-stop speaker-label layouts
- Protects stage directions from being treated as dialogue labels
- Uses strict Page Hint matching and reports the exact cue page when an
  unresolved state conflicts with its configured hint
- Clearly distinguishes printed script Page Hint values from sequential PDF
  page positions used by selected-page exports
- Adds automatic safety warnings for missing states, zero marks, incomplete
  assignments, and known speakers without an active assignment
- Shows a dedicated bilingual stop warning when no dialogue DCA numbers are
  added, with direct access to the output folder and review report
- Adds an upper-left User Guide button that opens the complete bilingual PDF
  manual bundled inside the installed app, even after the DMG is ejected
- Provides editable annotations in all three user-facing modes: full marking,
  first appearance only, and DCA State legends
- Offers Header Only, Footer Only, Header and Footer, or Off, with independent
  text and border styling and movable text-plus-border annotations
- Provides eight readable annotation colours for DCA numbers, in-script State
  labels, and page header/footer text and borders
- Includes the finalized bilingual workbook, complete bilingual manual, safe
  Save as New/Replace guidance, privacy information, and matching source code

### Verification before publication

- 82 automated engine, interface-contract, template, regression-runner, and
  release-packaging tests pass
- Regression coverage exercises thousands of dialogue cues and dozens of
  configured states across varied script layouts; source scripts and workbooks
  used for internal validation are not included in the repository or release
- The Universal build workflow verifies both host architectures and launches
  the self-contained Apple Silicon and Intel engines independently
- The public DMG is published only after Developer ID signing, Apple
  notarization, ticket stapling, Gatekeeper assessment, disk-image validation,
  source-manifest verification, and SHA-256 checksum generation
- Physical Intel macOS 12.7.6 installation and marked-PDF generation passed on
  the preceding release candidate; Apple Silicon Monterey 12.x remains
  unverified

### Important limitations

- Every exported script must be compared with the original PDF, completed DCA
  workbook, and review report before rehearsal or performance
- If no dialogue DCA numbers are added, the output must not be used; check the
  PDF text/layout, workbook names and assignments, first state cue, and Page
  Hint before regenerating
- Scanned/image-only, password-protected, and digitally signed PDFs are not
  supported
- Unusual columns, rotated text, tight margins, or nonstandard speaker layouts
  can reduce matching accuracy
- Editable annotation behaviour can vary between PDF viewers; Save as New is
  recommended when comparing styles
- There is no automatic updater

## 0.9.0 beta 2 — Monterey compatibility candidate

This build extends the public pre-release beta to macOS 12 Monterey. The
notarized DMG has passed physical installation, launch, marked-PDF generation,
and review-report generation on Intel macOS 12.7.6. Apple Silicon Monterey
12.x remains unverified, so this release should remain clearly labelled as a
pre-release.

### Changes since beta 1

- Targets macOS 12 Monterey or later on Apple Silicon and 64-bit Intel Macs;
  physical Intel Monterey 12.7.6 validation has passed
- Replaces a macOS 13-only file-path API in the Swift interface
- Aligns the host app, both embedded engines, package manifest, and verification
  checks to the same macOS 12 minimum
- Adds a packaging test that rejects a bundle or Mach-O binary requiring a
  system newer than the declared minimum

### Compatibility verification

- Completed: installed and launched the notarized DMG on the Intel macOS
  12.7.6 test Mac
- Completed: generated and reviewed a marked PDF and review report on that Mac
- Test on Apple Silicon running Monterey 12.x, using hardware or a suitable VM;
  until then, Apple Silicon Monterey compatibility remains unverified

## 0.9.0 beta 1 — public pre-release

This build was published as the first GitHub pre-release. It requires macOS 13
Ventura or later.

### Highlights

- One Universal app for Apple Silicon and 64-bit Intel Macs
- Self-contained marker engines; testers do not need Python, Homebrew, or Xcode
- macOS 13 Ventura or later
- Improved multilingual and mixed-layout matching, including early music-state
  cues, title-case English speaker labels, and Chinese role names
- Editable page header/footer labels whose text and border move together
- Independent page header/footer text, font, size, and border colour
- Safer Save as New and Replace guidance for Apple Preview
- Finalized bilingual DCA State workbook included with the beta

### Verification completed

- 25 automated engine, template, and release-packaging tests pass
- Universal Swift Release build succeeds
- Apple Silicon and Intel frozen engines start without external dependencies
- Both frozen engines produced matching review results in a representative
  script smoke test
- The Universal app and both embedded engines are signed with Developer ID and
  Hardened Runtime under one Team ID
- The DMG is accepted by Apple's notarization service, stapled, Gatekeeper
  checked, and checksum verified

### Validation still requested

- Test the notarized download on a physical Intel Mac and a clean Apple Silicon
  Mac

### Distribution and source

- The bundled beta is licensed under GNU AGPL version 3 or later
- The DMG includes the finalized template, licence, and third-party notices
- The exact matching source ZIP is supplied beside the DMG as a separate
  release file
- Dependency source archives are identified by locked SHA-256 checksums
- No theatre script PDFs or internal validation materials are included

### Known beta limitations

- Text-based PDFs with selectable text only; scanned/image-only PDFs are not
  supported
- Password-protected and digitally signed PDFs are not supported
- Unusual columns, rotated text, tight margins, or nonstandard cue layouts may
  reduce matching accuracy
- Every marked PDF and review report requires human checking
- Editable annotation behavior can vary between PDF viewers
- Replacing a PDF that remains open in Preview can temporarily show cached
  markings; Save as New is recommended
- No automatic updater
