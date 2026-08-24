# DCA Script Marker public beta

Thank you for testing DCA Script Marker. This beta is intended for rehearsal
preparation and must still be checked by a human before it is used in a show.
The complete workflow is available in the bilingual
[User Guide / 使用手册](USER_GUIDE.md).

## Supported Macs

- Apple Silicon and Intel Macs
- Beta 2 targets macOS 12 Monterey or later. Its notarized DMG passed physical
  installation, launch, marked-PDF generation, and review-report generation on
  Intel macOS 12.7.6. Apple Silicon Monterey 12.x remains unverified. The
  published beta 1 requires macOS 13 Ventura or later.
- Text-based script PDFs with selectable text
- DCA State workbooks in the supplied horizontal format or the supported
  legacy vertical format

Scanned/image-only PDFs, password-protected PDFs, and digitally signed PDFs
are not supported in this beta. Do not overwrite a production copy of a
script; keep the original PDF and workbook unchanged.

## Install the beta

1. Open the supplied DMG.
2. Drag **DCA Script Marker** to **Applications**.
3. Open the app from Applications.
4. Confirm that **About DCA Script Marker** shows the expected beta version.

This beta is signed and notarized by Apple. If macOS says the app
cannot be verified, stop and report the exact message rather than bypassing the
warning.

The DMG contains the GNU AGPL licence and third-party notices. The exact
matching source ZIP is supplied beside the DMG as a separate release file.
Keep the DMG, source ZIP, release manifest, and checksums together when sharing
the beta.

## Suggested test

1. Choose a DCA State workbook, the original script PDF, and a new output
   folder.
2. Generate **Editable Full Marking** with page header/footer labels enabled.
3. Check several scene transitions, the first pages, and speakers mentioned in
   stage directions.
4. In Preview, move a DCA number, an in-script DCA State label, a header/footer
   label, and a legend. Text and border should move as one object.
5. Close and reopen the marked PDF. Confirm that edits remain and no duplicate
   labels appear.
6. Try **Full Marking**, **First Appearance Only**, and **DCA State Legend**.
7. Check the review report for missing states and unexpected speaker names.

When changing annotation settings, **Save as New PDF** is recommended. If you
choose Replace, close the existing marked PDF in Preview before replacing it;
Preview can otherwise display an old in-memory copy over the new file.

## Privacy

DCA Script Marker processes the PDF and workbook locally. The beta has no
telemetry and does not upload scripts. The generated review report may contain
short fragments from the script, so treat it with the same confidentiality as
the source material. Never attach a confidential script to a public GitHub
issue; use a small sanitized example instead.

## What to report

Please include:

- DCA Script Marker version and build number
- Mac model, Intel or Apple Silicon, and macOS version
- Marking style and relevant appearance settings
- PDF page number and DCA State where the issue appears
- What you expected and what happened
- Whether closing and reopening the PDF changed the result
- The review report, only if it contains no confidential material
- A cropped screenshot or sanitized sample files when possible

Crashes, damaged output, loss of an existing file, or an app that cannot launch
are release-blocking issues and should be reported immediately.

During the public beta, please send feedback rather than code or pull requests.
Users may fork and modify the AGPL source now; upstream pull requests are
temporarily paused while a long-term contributor-licensing policy is prepared.
