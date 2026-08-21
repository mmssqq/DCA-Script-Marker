# DCA Script Marker private beta

Thank you for testing DCA Script Marker. This beta is intended for rehearsal
preparation and must still be checked by a human before it is used in a show.

## Supported Macs

- Apple Silicon and Intel Macs
- macOS 13 Ventura or later
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

The shareable beta will be signed and notarized by Apple. If macOS says the app
cannot be verified, stop and report the exact message rather than bypassing the
warning.

The DMG also contains the GNU AGPL licence, third-party notices, and the exact
matching source archive. Keep these files together when sharing the beta.

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

During the private beta, please send feedback rather than code or pull
requests. A contributor policy will be added before outside code contributions
are accepted.
