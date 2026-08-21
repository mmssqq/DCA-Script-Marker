# Release notes

## 0.9.0 beta 1 — preparation build

This build is being prepared for a small friends-and-colleagues beta. It is not
yet approved for distribution.

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

- 24 automated engine, template, and release-packaging tests pass
- Universal Swift Release build succeeds
- Apple Silicon and Intel frozen engines start without external dependencies
- Both frozen engines produced matching review results in a real-script smoke
  test
- Hardened-runtime nested-signing layout was rehearsed with one Team ID

### Required before testers receive it

- Install a Developer ID Application certificate
- Create and validate a `notarytool` Keychain profile
- Produce, notarize, staple, and Gatekeeper-check the DMG
- Test the notarized download on a physical Intel Mac and a clean Apple Silicon
  Mac

### Distribution and source

- The bundled beta is licensed under GNU AGPL version 3 or later
- Each binary package includes the finalized template, licence and third-party
  notices, and the exact matching source archive
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
