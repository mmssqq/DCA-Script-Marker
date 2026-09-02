# Testing and safety

Thank you for using and testing DCA Script Marker. The app is intended for
rehearsal preparation and every result must be checked by a human before it is
used in a show. The complete workflow is available in the bilingual
[User Guide / 使用手册](USER_GUIDE.md).

## Supported Macs

- Apple Silicon and Intel Macs
- Version 2.0.0 targets macOS 12 Monterey or later. The previous notarized
  release candidate passed physical installation, launch, marked-PDF
  generation, and review-report generation on Intel macOS 12.7.6. Apple
  Silicon Monterey 12.x remains unverified.
- Text-based script PDFs with selectable text
- DCA State workbooks in the supplied horizontal format or the supported
  legacy vertical format
- Optional Performer / Role Mapping in the supplied workbook, while older
  workbooks without mappings remain supported

Scanned/image-only PDFs, password-protected PDFs, and digitally signed PDFs
are not supported in this release. Do not overwrite a production copy of a
script; keep the original PDF and workbook unchanged.

## Important page-number rule

Excel **Page Hint** normally means the page number printed inside the script.
If that page has no printed number, use the sequential PDF page position shown
by the viewer, counting the cover as PDF page 1. **Mark selected pages only**
always uses the sequential PDF page position, never the printed script page.
Confusing these numbers can prevent a state from activating, activate a
repeated cue on the wrong page, leave early pages unmarked, or continue the
previous state's assignments.

Excel 的 **Page Hint** 通常填写剧本页面内印刷的页码；如果该页没有印刷页码，再填写
PDF 阅读器显示的顺序页码，并从封面作为 PDF 第 1 页开始计算。**Mark selected pages
only** 始终使用 PDF 顺序页码，不要填写剧本内印刷页码。混淆两种页码可能导致状态
无法启动、重复提示在错误页面启动、前面页面没有标注，或继续使用上一状态的分配。

## Performer / Role Mapping safety / 演员与角色对应安全检查

Performer / Role Mapping is for different script roles played by one person or
carried by one DCA identity. It is not a replacement for inline square-bracket
aliases, which describe alternate printed forms of the same role in one DCA
assignment cell/state. For example, enter `Ben` in `Character List` column A
and `Barber, Butcher, Coach` in column B, then select only `Ben` in `DCA States`.
The three script role labels should receive Ben's DCA number. The app rejects
conflicting mappings instead of choosing an identity silently. Existing
workbooks with column B blank continue to work as before.

演员 / 角色对应用于“同一位演员或同一 DCA 身份对应多个不同剧本角色”，不会取代方括号内联
别名；内联别名仅表示同一角色在某个 DCA 分配单元格 / 状态中的不同印刷形式。例如，
在 `Character List` A 列填写 `Ben`，B 列填写 `Barber, Butcher, Coach`，再在 `DCA States`
中只选择 `Ben`；三个剧本角色标签都应获得 Ben 的 DCA 编号。如果对应关系冲突，软件会拒绝该
工作簿，而不会默默猜测。B 列留空的旧工作簿会保持原有行为。

## Install the release

1. Open the supplied DMG.
2. Drag **DCA Script Marker** to **Applications**.
3. Open the app from Applications.
4. Eject the DMG, select **User Guide** at the upper-left, and confirm that the
   complete bilingual PDF manual opens from the installed app.
5. Confirm that **About DCA Script Marker** shows the expected version.

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
7. Test Performer / Role Mapping with a small sanitized case: put `Ben` in
   `Character List` column A and `Barber, Butcher, Coach` in column B; select Ben
   in the active DCA State and confirm all three printed role labels receive
   Ben's DCA number while the legend shows only Ben. Also confirm an inline
   alias still affects only the DCA cell/state where it is written.
8. Check the review report for missing states and unexpected speaker names.
9. Generate a short sample with **Header Only**, **Footer Only**, and **Off**;
   confirm that no label appears in a location you disabled.
10. Confirm the first relevant page and every state transition use the intended
   DCA assignment. If no DCA numbers are added, do not use the output; open the
   review report and check selectable text, speaker-label layout, names,
   assignments, the first state cue, and Page Hint.

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
- Sequential PDF page position, printed script page number, and DCA State where
  the issue appears
- Whether Performer / Role Mapping or an inline alias was used, including a
  sanitized example of the relevant names
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
