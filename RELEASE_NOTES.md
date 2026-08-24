# Release notes

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
- Improved matching for the 《无间道》 test, including early music-state cues,
  title-case English speaker labels, and `梁科长`
- Editable page header/footer labels whose text and border move together
- Independent page header/footer text, font, size, and border colour
- Safer Save as New and Replace guidance for Apple Preview
- Finalized bilingual DCA State workbook included with the beta

### Verification completed

- 25 automated engine, template, and release-packaging tests pass
- Universal Swift Release build succeeds
- Apple Silicon and Intel frozen engines start without external dependencies
- Both frozen engines produced matching review results in a real-script smoke
  test
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
- No theatre script PDFs or private test materials are included

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
