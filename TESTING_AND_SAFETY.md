# Testing and safety

Thank you for using and testing DCA Script Marker. The app is intended for
rehearsal preparation and every result must be checked by a human before it is
used in a show. The complete workflow is available in the bilingual
[User Guide / 使用手册](USER_GUIDE.md).

## Supported Macs

- Apple Silicon and Intel Macs
- Version 1.0.0 targets macOS 12 Monterey or later. The previous notarized
  release candidate passed physical installation, launch, marked-PDF
  generation, and review-report generation on Intel macOS 12.7.6. Apple
  Silicon Monterey 12.x remains unverified.
- Text-based script PDFs with selectable text
- DCA State workbooks in the supplied horizontal format or the supported
  legacy vertical format

Scanned/image-only PDFs, password-protected PDFs, and digitally signed PDFs
are not supported in this release. Do not overwrite a production copy of a
script; keep the original PDF and workbook unchanged.

## Install the release

1. Open the supplied DMG.
2. Drag **DCA Script Marker** to **Applications**.
3. Open the app from Applications.
4. Confirm that **About DCA Script Marker** shows the expected version.

The public DMG is signed and notarized by Apple. If macOS says the app
cannot be verified, stop and report the exact message rather than bypassing the
warning.

The DMG contains the GNU AGPL licence and third-party notices. The exact
matching source ZIP is supplied beside the DMG as a separate release file.
Keep the DMG, source ZIP, release manifest, and checksums together when sharing
the release.

## Suggested test

1. Choose a DCA State workbook, the original script PDF, and a new output
   folder.
2. Generate **Editable Full Marking** with **Header and Footer** selected.
3. Check several scene transitions, the first pages, and speakers mentioned in
   stage directions.
4. In Preview, move a DCA number, an in-script DCA State label, a header/footer
   label, and a legend. Text and border should move as one object.
5. Close and reopen the marked PDF. Confirm that edits remain and no duplicate
   labels appear.
6. Repeat the test with **First Appearance Only** and **DCA State Legend**.
   Confirm their visible DCA numbers or legend, plus page header/footer labels,
   can be moved or deleted.
7. Check the review report for missing states and unexpected speaker names.
8. Generate a short sample with **Header Only**, **Footer Only**, and **Off**;
   confirm that no label appears in a location you disabled.

When changing annotation settings, **Save as New PDF** is recommended. If you
choose Replace, close the existing marked PDF in Preview before replacing it;
Preview can otherwise display an old in-memory copy over the new file.

## Privacy

DCA Script Marker processes the PDF and workbook locally. The app has no
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

## Automatic real-script regression check

Maintainers can run a private golden regression pack before building a release.
The public repository contains only the runner and a synthetic manifest
example. Copyrighted scripts, workbooks, their paths, file hashes, generated
PDFs, and approved baselines must remain in a separate private folder.

The runner accepts only explicitly listed clean source PDFs and a strict set of
non-path engine options. It rejects marked PDFs and path traversal, hashes every
original PDF/workbook before and after use, and runs the engine against locked
isolated copies. It reopens the output PDF, checks that page geometry is
preserved, and compares stable state, page, speaker/DCA identity, safety, and
configuration measurements. It never compares dated filenames, absolute
paths, PDF bytes, warning prose, or runtime duration.

Configure a private pack by copying
`tests/real_script_regressions.example.json`, then set:

```sh
export DCA_REGRESSION_ASSETS_ROOT="/path/to/private/Test"
export DCA_REGRESSION_MANIFEST="/path/to/private/real_script_regressions.json"
export DCA_REGRESSION_BASELINE="/path/to/private/approved_baseline.json"
```

Run the short pre-change check:

```sh
.venv/bin/python tools/run_real_script_regressions.py --suite smoke
```

Run every configured real-script case before a release build:

```sh
.venv/bin/python tools/run_real_script_regressions.py --suite full
```

Exit status `0` means every selected case matches its approved snapshot. Status
`1` means a valid output changed and needs review. Status `2` means the private
pack, an input, the engine, or an output PDF was invalid or unavailable.

Baseline changes are deliberately separate from ordinary runs. First inspect
the field-by-field differences and visually check representative output pages.
Then approve only named cases, or deliberately approve the complete manifest:

```sh
.venv/bin/python tools/run_real_script_regressions.py \
  --case example_chinese_colon \
  --accept-current
```

```sh
.venv/bin/python tools/run_real_script_regressions.py \
  --all \
  --accept-current
```

An existing baseline is backed up before an approved update. If a source PDF,
workbook, OCR file, engine-option list, or targeted assertion changed, approval
also requires `--allow-input-changes` after the new input/configuration has been
checked. The older spelling `--allow-source-changes` remains an alias. A
critical safety result and a failed targeted assertion can never be silently
accepted.

Please send bug reports and usability feedback rather than code or pull requests.
Users may fork and modify the AGPL source now; upstream pull requests are
temporarily paused while a long-term contributor-licensing policy is prepared.
