# DCA Script Marker User Guide / DCA Script Marker 使用手册

Version 1.0.0

DCA Script Marker helps theatre sound teams add DCA numbers to dialogue cues
in a script PDF. It reads the DCA assignments from the supplied Excel template,
keeps the original PDF page layout, and creates a review report for human
checking. Processing is local to your Mac.

> Important: DCA Script Marker automates a review task; it cannot guarantee
> correct results for every PDF layout. Before rehearsal or performance, a
> member of the sound team must compare every exported script with the original
> PDF, the completed DCA workbook, and the review report.

DCA Script Marker 是一款为剧场音响人员提供的本地 macOS 工具。它会读取
按场次编排的 DCA 列表和文字版剧本 PDF，在对白角色旁标注正确的 DCA 编号，保留原
PDF 版式，并生成供人工复核的报告。

> 重要：DCA Script Marker 可协助自动标注，但无法保证适用于所有 PDF 排版。排练或
> 正式演出前，音响团队成员必须将每份导出的剧本与原始 PDF、已填写的 DCA 表格及
> 复核报告进行人工核对。

## English guide

### 1. What you need

- A Mac that meets the version requirement shown on the GitHub Release page.
- The included `DCA Script Marker - DCA State Template.xlsx` workbook.
- A script PDF whose words can be selected or copied.
- A folder where the marked PDF and review report will be saved.

Microsoft Excel is recommended for preserving the template dropdowns. Template
compatibility with Apple Numbers and LibreOffice has not yet been verified.

Scanned or image-only PDFs are not supported. Password-protected and digitally
signed PDFs are also not supported. Keep an unchanged copy of the original PDF
and workbook.

### 2. Install the app and copy the template

1. Open the downloaded DMG.
2. Drag **DCA Script Marker** into **Applications**.
3. Copy the included Excel template from the DMG into your own show or project
   folder. Do not fill in the copy inside the mounted DMG because a DMG is
   normally read-only.
4. Rename your copied workbook if useful, for example
   `My Show - DCA States.xlsx`.
5. Open the app from Applications. The menu item **Help** opens a short guide
   inside the app.

The matching source archive, licence, privacy notice, release notes, and this
manual are included with or supplied beside each release.

### 3. Complete the Excel template

The workbook has three sheets. Keep their names and the existing header row
unchanged.

#### Sheet 1: How to use

This sheet contains a short bilingual reminder and field descriptions. It is
for reference; the marker reads the `DCA States` sheet.

#### Sheet 2: Character List

Starting at cell A3, enter every dialogue character name once, one character
per row. Use the name as it appears beside dialogue in the script. These names
become the dropdown choices on the `DCA States` sheet.

If you later change a name in `Character List`, re-select that character in
every DCA assignment cell where it is used. This refreshes the dropdown value
stored by Excel.

#### Sheet 3: DCA States

Start entering states on row 5. Use one row for each DCA State, scene, snapshot,
or song. Do not rename the columns.

| Column | What to enter |
| --- | --- |
| DCA State | A unique state label, for example `S1`, `Act 1 Scene 3`, or `Snapshot 20`. |
| Start Line Character | The speaker of the start cue. Optional, but strongly recommended when the same cue text is used by more than one character. |
| Start Line Text | The exact phrase that activates this state. Copy it directly from the selectable script text when possible, including punctuation. |
| State Start position | Enter exactly `Before` if the new state applies before the cue, or `After` if it applies after the cue. |
| Page Hint | Optional. Use the page number printed on the script page. If there is no printed page number, use the PDF page number. This helps when cue text repeats. |
| Notes | For your own notes. The marker does not use this column. |
| DCA 1 to DCA 12 | Assign the characters carried by each DCA in this state. |

In a DCA cell, choose a character from the dropdown or type it manually. Put
each character on a separate line when one DCA carries several people. To add
a script alias, put it in square brackets after the main name, for example
`Lin Feifei [Feifei]` or `林菲菲 [菲菲]`. Separate multiple aliases inside the
brackets with commas.

For the first pages to receive assignments, make the first state cue an early,
unique phrase at or before the first relevant dialogue. Use `Before` when the
state is already active as that cue begins. Add a character and page hint when
the phrase could be ambiguous.

Save the completed workbook as an `.xlsx` file before opening the marker.

### 4. Choose files in DCA Script Marker

1. Next to **DCA State Template**, choose your completed Excel copy. Do not
   choose the blank template unless you have filled and saved it.
2. Next to **Script PDF**, choose the unchanged original script PDF.
3. Next to **Output Folder**, choose where the marked PDF and review report
   should be created.
4. Optional: turn on **Mark selected pages only** and enter the first and last
   PDF page numbers. These are PDF page numbers, which may differ from the
   numbers printed inside the script.

The current control labels are in English. The Chinese text in this guide is an
explanatory translation of those controls.

### 5. Choose a marking style

- **Editable Full Marking**: marks every matched dialogue cue with editable PDF
  annotations. This is the recommended starting style for review.
- **First Appearance Only**: marks only the first matched appearance of each
  character in each DCA State, using editable annotations.
- **DCA State Legend**: creates an editable DCA membership list for every state.
  The app lets you review and edit the legend text before export, and its page
  labels remain movable and deletable afterward.

All three styles create movable and deletable PDF annotations for their visible
output. DCA numbers are editable wherever that style displays them. A page
header/footer label and its surrounding border are one annotation, so they move
or delete together.

### 6. Choose annotation appearance

Select **Generate Marked Script** to open **Annotation Style**.

- For DCA numbers, choose colour, size, font, horizontal position, and vertical
  position.
- For DCA State labels, choose colour, size, font, and gutter position.
- For a DCA State Legend, choose its position.
- Under **DCA State Header & Footer**, choose **Off**, **Header Only**, **Footer
  Only**, or **Header and Footer**. You can choose the visible label's text
  colour, size, font, and border colour independently.

Chinese labels automatically use a compatible Chinese font. Select
**Continue** to generate. Large scripts can take time; keep the app open until
the completion message appears.

### 7. Check the results

The output folder opens when generation finishes. It contains:

- `<original name>_marked_YYYY-MM-DD.pdf`
- `<original name>_review_YYYY-MM-DD.txt`

The review report lists the number of marked cues, DCA States whose start cue
was not found, and possible speaker names without a DCA assignment. A clean
report is helpful but does not replace human checking.

The report now begins with an **Automatic safety check**. The app also shows a
warning dialog when it detects a high-confidence risk, such as no usable DCA
States, no state activation, zero dialogue marks, a missing first state, a
DCA assignment row without a usable start cue, or a positioned known speaker
with no assignment in the active state. The PDF is still created so you can
inspect it. Use **Open Review Report** in the warning dialog and resolve every
warning before rehearsal. The report also identifies an exact Start Cue Text
found on a page that conflicts with its configured Page Hint when that state
never activates. These checks deliberately avoid guessing from the number of
marks per page, so a valid sparse script is not treated as a failure.

Check at least:

1. The first relevant pages and every state transition.
2. A selection of English, Chinese, and mixed-language speaker labels.
3. Speakers mentioned only inside stage directions, which must not receive a
   dialogue DCA number.
4. Repeated cue text and any state that uses a Page Hint.
5. Page header/footer labels and page boundaries.
6. Every item named in the review report.

In an editable PDF, click an annotation in Preview until its selection handles
appear, then drag it. A label and its border should move together. PDF editor
behaviour varies, so close and reopen the file once to confirm that edits remain
and duplicate labels have not appeared.

### 8. Generate again safely

If an output with the same dated name already exists, the app offers:

- **Save as New PDF (Recommended)**: creates a numbered copy without touching
  the earlier output.
- **Replace Existing PDF**: replaces the existing output. Close that PDF in
  Preview first. Preview can keep old editable annotations in memory and make
  old and new markings appear together until the file is closed and reopened.

Keep **Save as New PDF** as the normal choice while comparing styles or
positions.

### 9. Troubleshooting and reporting

- **The app icon is crossed out**: check the minimum macOS version on the
  release page and download the correct release.
- **No DCA numbers appear**: confirm that the completed workbook, not the blank
  template, was selected; confirm the PDF has selectable text; then check the
  review report for missing start cues.
- **A state starts in the wrong place**: copy a more unique Start Line Text,
  choose the correct Before/After value, and add Start Line Character and Page
  Hint.
- **A character is not marked**: make the `Character List` spelling and the DCA
  assignment match the dialogue label, or add the script name as an alias.
- **Old and new labels appear together**: close the PDF in Preview and reopen
  it. Generate with Save as New when comparing results.
- **The app cannot be verified**: stop and report the exact macOS message. Do
  not bypass a warning for a release that should be signed and notarized.

Report issues at <https://github.com/mmssqq/DCA-Script-Marker/issues> using only
sanitized examples. Never upload a confidential script, workbook, marked PDF,
or review report to a public issue.

## 中文使用手册

### 1. 使用前准备

- 一台符合 GitHub Release 页面所列系统要求的 Mac。
- DMG 内附带的 `DCA Script Marker - DCA State Template.xlsx` 模板。
- 一份可以选择或复制文字的剧本 PDF。
- 一个用于保存标注 PDF 和复核报告的文件夹。

建议使用 Microsoft Excel，以保留模板中的下拉选项。目前尚未验证 Apple Numbers 或
LibreOffice 对该模板的兼容性。

当前不支持扫描版或纯图片 PDF，也不支持密码保护或带数字签名的 PDF。请始终保留
未经修改的原始 PDF 和 Excel 表格备份。

### 2. 安装软件并复制模板

1. 打开下载的 DMG。
2. 将 **DCA Script Marker** 拖入 **Applications（应用程序）**。
3. 将 DMG 内附带的 Excel 模板复制到您自己的演出或项目文件夹。不要直接编辑挂载在
   DMG 里的模板，因为 DMG 通常是只读的。
4. 可以将复制出的文件改名，例如 `我的演出 - DCA States.xlsx`。
5. 从 Applications 打开软件。菜单中的 **Help** 可以打开软件内的简短说明。

每个发行版本都会同时提供对应的源代码压缩包、许可证、隐私说明、发行说明和本手册。

### 3. 完成 Excel 模板

模板包含三个工作表。请勿修改工作表名称，也不要修改已有的表头行。

#### 工作表 1：How to use

这里包含中英文简要步骤和各字段说明，供填写时参考。软件实际读取的是
`DCA States` 工作表。

#### 工作表 2：Character List

从 A3 单元格开始，将剧本中每个说台词的角色输入一次，每行一个角色。尽量使用角色
在剧本对白标签中出现的名称。这里输入的名称会成为 `DCA States` 工作表中的下拉选项。

如果之后在 `Character List` 中修改角色名称，请在所有已经分配该角色的 DCA 单元格中
重新选择一次该角色，以刷新 Excel 保存的下拉选项值。

#### 工作表 3：DCA States

从第 5 行开始填写。每个 DCA 状态、场次、Snapshot 或歌曲使用一行。请勿修改列名。

| 列名 | 填写内容 |
| --- | --- |
| DCA State | 唯一的状态名称，例如 `S1`、`Act 1 Scene 3` 或 `Snapshot 20`。 |
| Start Line Character | 开始提示文字的说话角色。此项可选；如果同一句提示文字由多个角色说出，强烈建议填写。 |
| Start Line Text | 激活该状态的准确文字。尽量直接从可选中文字的剧本中复制，并保留标点。 |
| State Start position | 如果新状态在提示文字之前生效，请准确填写 `Before`；如果在提示文字之后生效，请填写 `After`。 |
| Page Hint | 可选。优先填写剧本页面内印刷的页码；如果剧本没有内部页码，再填写 PDF 页码。提示文字重复时此项很有帮助。 |
| Notes | 仅供人工备注，软件不会读取此列。 |
| DCA 1 到 DCA 12 | 填写当前状态中每个 DCA 所包含的角色。 |

在 DCA 单元格中，可以从下拉列表选择角色，也可以手动输入。如果一个 DCA 包含多个
角色，请在同一个单元格内每行填写一个角色。若剧本使用了别名，请在主要名称后用方括号
填写，例如 `Lin Feifei [Feifei]` 或 `林菲菲 [菲菲]`。多个别名可在方括号内用逗号分隔。

为了让最开始的相关页面也能获得正确分配，请让第一条状态提示尽量位于第一段相关对白
之前或附近，并使用一段较早且唯一的文字。如果该状态在提示文字开始时已经生效，请选择
`Before`。如果文字可能重复，请同时填写角色和页码提示。

完成后，请将表格保存为 `.xlsx` 文件，再打开 DCA Script Marker。

### 4. 在软件中选择文件

1. 在 **DCA State Template** 旁选择您已经填写并保存的 Excel 副本。不要选择尚未填写
   的空白模板。
2. 在 **Script PDF** 旁选择未经修改的原始剧本 PDF。
3. 在 **Output Folder** 旁选择标注 PDF 和复核报告的保存位置。
4. 可选：打开 **Mark selected pages only**，输入要处理的第一个和最后一个 PDF 页码。
   这里使用的是 PDF 页码，可能与剧本页面内印刷的页码不同。

当前软件按钮和选项名称以英文显示，本手册中的中文为对应操作说明。

### 5. 选择标注方式

- **Editable Full Marking**：为每一句匹配到的角色台词创建可编辑 PDF 标注。建议第一次
  检查时使用此模式。
- **First Appearance Only**：在每个 DCA 状态中，只为每个角色第一次匹配到的台词创建
  可编辑标注。
- **DCA State Legend**：为每个状态生成可编辑的 DCA 角色分配列表；导出前可以在软件
  中检查和修改图例文字，导出后的页面标签仍可移动或删除。

三种方式中所有可见的输出均为可移动、可删除的 PDF 标注。显示 DCA 编号的方式会创建
可编辑编号。页眉或页脚标签的文字与外围边框属于同一个标注，因此会一起移动或删除。

### 6. 设置标注外观

点击 **Generate Marked Script** 后会打开 **Annotation Style**。

- DCA 编号可以分别设置颜色、大小、字体、水平位置和垂直位置。
- DCA 状态标签可以分别设置颜色、大小、字体和页边位置。
- 使用 DCA State Legend 时，可以选择图例位置。
- 在 **DCA State Header & Footer** 中，可以选择 **Off**、**Header Only**、
  **Footer Only** 或 **Header and Footer**，并设置所显示标签的文字颜色、大小、字体和
  边框颜色。

中文标签会自动使用兼容的中文字体。点击 **Continue** 开始生成。较长的剧本可能需要
一些时间，请保持软件开启，直到出现完成信息。

### 7. 检查生成结果

生成完成后，软件会打开输出文件夹，其中包括：

- `<原文件名>_marked_YYYY-MM-DD.pdf`
- `<原文件名>_review_YYYY-MM-DD.txt`

复核报告会列出已标注台词数量、未找到开始提示的 DCA 状态，以及可能没有 DCA 分配的
角色名称。即使报告看起来没有问题，也仍然必须人工检查。

复核报告现在会先显示 **Automatic safety check（自动安全检查）**。如果软件发现
较高风险的问题，例如：没有可用的 DCA 状态、没有任何状态被启动、没有标注任何对白、
第一个状态未启动、已填写 DCA 分配但缺少可用的 Start Line Text，或识别到真实角色标签但
当前状态没有分配 DCA，软件会弹出中英文警告。PDF 仍会生成，以便人工检查。请点击
**Open Review Report / 打开复核报告**，并在排练前处理每一条警告。如果某个状态从未
启动，但软件在其他页面找到完全相同的 Start Cue Text，复核报告也会明确指出实际页码与
Page Hint 的冲突。这项检查不会用“每页标注数量”来猜测对错，因此不会仅因为一份合法
剧本的标注较少就将其判定为失败。

请至少检查：

1. 最开始的相关页面以及每一次状态切换。
2. 一部分英文、中文和中英混排的角色标签。
3. 只在舞台说明中出现的角色名称，不能被误认为对白角色。
4. 重复出现的提示文字以及所有使用 Page Hint 的状态。
5. 每页页眉、页脚和跨页位置。
6. 复核报告中列出的每一个项目。

对于可编辑 PDF，请在 Preview（预览）中点击标注，直到出现选择控制点，再进行拖动。
文字和边框应当一起移动。不同 PDF 编辑器的表现可能不同，因此请关闭并重新打开文件，
确认修改仍然存在，并且没有出现重复标签。

### 8. 安全地重新生成

如果相同日期和文件名的输出已经存在，软件会提供：

- **Save as New PDF (Recommended)**：创建带编号的新副本，不修改之前的输出。
- **Replace Existing PDF**：替换原输出。替换前请先在 Preview 中关闭该 PDF。Preview
  可能把旧的可编辑标注保留在内存中，在关闭并重新打开文件前，看起来像新旧标注同时存在。

在比较不同样式或位置时，建议始终使用 **Save as New PDF**。

### 9. 故障排查与问题反馈

- **软件图标带有禁止符号**：请查看 Release 页面上的最低 macOS 要求，并下载适合的
  发行版本。
- **没有出现 DCA 编号**：确认选择的是填写完成的 Excel，而不是空白模板；确认 PDF
  可以选中文字；再检查复核报告中是否有未找到的状态提示。
- **状态从错误位置开始**：复制一段更独特的 Start Line Text，确认 Before/After，
  并填写 Start Line Character 和 Page Hint。
- **某个角色没有被标注**：让 `Character List` 和 DCA 单元格中的名称与对白标签一致，
  或将剧本中的名称添加为方括号别名。
- **同时看到新旧两套标签**：关闭 Preview 中的 PDF，再重新打开。比较结果时请选择
  Save as New。
- **macOS 提示无法验证软件**：请停止并记录完整提示。对于应当签名和公证的版本，
  不要绕过系统警告。

请前往 <https://github.com/mmssqq/DCA-Script-Marker/issues> 反馈问题，并且只使用经过
脱敏的示例。绝对不要把保密剧本、DCA 表格、标注 PDF 或复核报告上传到公开 Issue。
Copyright 2026 马斯琪 Siqi Ma. Licensed under GNU AGPL v3 or later.
