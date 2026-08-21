# Privacy

DCA Script Marker is designed to process rehearsal documents locally on the
Mac where it is running.

## Data the app uses

The app reads only the files selected by the user:

- a DCA State Excel workbook;
- a text-based script PDF; and
- an output folder.

It writes the marked PDF and its review report to the selected output folder.
The app has no account system, advertising, analytics, telemetry, or external
crash-reporting SDK, and it does not upload scripts or workbooks.

If a selected file or output folder is stored in iCloud Drive, Dropbox, Google
Drive, OneDrive, or another synchronized location, that service may upload the
file independently of DCA Script Marker.

## Temporary data

When a user edits a DCA State legend, the app creates a uniquely named
temporary JSON file and removes it after generation or cancellation. No script
text is intentionally stored in that temporary file.

## Reports and feedback

The review report can contain character names, DCA State names, and short text
fragments found in the script. Treat the report with the same confidentiality
as the source PDF.

Do not attach confidential scripts, workbooks, reports, or uncropped
screenshots to a public issue. Use a small sanitized example, or arrange a
private sharing method with the maintainer.

## Network access

The current beta does not make network requests. The macOS app is distributed
outside the Mac App Store and is not App-Sandboxed, so this statement describes
the app's implemented behavior rather than an operating-system-enforced network
restriction.

