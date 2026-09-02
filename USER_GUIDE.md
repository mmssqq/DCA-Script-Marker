# DCA Script Marker User Guide / DCA Script Marker 使用手册

Version 2.0.0

DCA Script Marker helps theatre sound teams prepare DCA states and add DCA
numbers to dialogue cues in a script PDF. Version 2 can create and edit the
Character List and DCA States directly inside the app. A local `.dcamarker`
project remembers the script PDF, output folder, DCA data, and marking settings.
Existing Excel workbooks can still be imported, and any project can be exported
to a standard Excel workbook. Processing is local to your Mac.

> Important: DCA Script Marker automates a review task; it cannot guarantee
> correct results for every PDF layout. Before rehearsal or performance, a
> member of the sound team must compare every exported script with the original
> PDF, the completed DCA project (or exported workbook), and the review report.

DCA Script Marker 是一款为剧场音响人员提供的本地 macOS 工具。Version 2 可直接在
软件内新建和编辑 Character List 与 DCA States。本地 `.dcamarker` 项目会保存剧本
PDF、输出文件夹、DCA 数据及标注设置；已有 Excel 工作簿仍可导入，也可随时将项目导出
为标准 Excel 工作簿。软件会在对白角色旁标注正确的 DCA 编号，保留原 PDF 版式，并
生成供人工复核的报告。

> 重要：DCA Script Marker 可协助自动标注，但无法保证适用于所有 PDF 排版。排练或
> 正式演出前，音响团队成员必须将每份导出的剧本与原始 PDF、已填写的 DCA 表格及
> 复核报告进行人工核对。

## English guide

### 1. What you need

- A Mac that meets the version requirement shown on the GitHub Release page.
- A local DCA Script Marker project, created in the app or imported from Excel.
- A script PDF whose words can be selected or copied.
- A folder where the marked PDF and review report will be saved.

Microsoft Excel is optional in Version 2. It is still recommended when editing
an exported workbook because compatibility with Apple Numbers and LibreOffice
has not yet been verified.

Scanned or image-only PDFs are not supported. Password-protected and digitally
signed PDFs are also not supported. Keep an unchanged copy of the original PDF
and workbook.

### 2. Install the app and create a project

1. Open the downloaded DMG.
2. Drag **DCA Script Marker** into **Applications**.
3. Open the app from Applications. Choose **New** to create a local
   `.dcamarker` project, **Open** to continue an existing project, or **Import
   Excel** to convert a completed Version 1 workbook.
4. Save the project in your show folder. It contains the DCA data and remembers
   the linked PDF, output folder, and marking settings. It does not contain or
   upload a copy of the script PDF.
5. The **User Guide** button at the upper-left
   opens the complete bilingual PDF manual bundled inside the installed app,
   so it remains available after the DMG is ejected. The **Help** button at the
   upper-right, and the Help menu item, open a shorter guide inside the app.

The matching source archive, licence, privacy notice, release notes, and this
manual are included with or supplied beside each release.

### 3. Edit Character List and DCA States

Choose **Edit Character List and DCA States** on the main window. The editor
contains two tabs: Character List and DCA States. Choose **Save Project** or **Done** to write
changes to the local project file. The setup check reports missing state names
or cue text, duplicate DCA Names, and one DCA Name assigned to more than one DCA column in the same state. Repeated
assignments are warnings only and do not block generation.

Use **Import Excel** to convert an existing workbook into a Version 2 project.
Use **Export Excel** to create a compatible `.xlsx` copy whenever it is useful
for sharing, printing, or editing outside the app.

> Workflow tip: If your Excel workbook covers only part of the script, import
> it and continue adding or editing the remaining DCA States inside the DCA
> Project. You do not need to reopen Excel. Save the project and generate the
> marked script directly; use Export Excel only if you want an updated `.xlsx`
> copy.

Older projects may open as a new `- converted.dcamarker` copy with their saved
assignments written as ordinary DCA-cell entries. The original file stays
unchanged. Review the converted cells before generating a marked script.

#### Excel compatibility

The workbook has three sheets. Keep their names and the existing header row
unchanged.

#### Sheet 1: How to use

This sheet contains a short bilingual reminder and field descriptions. It is
for reference; the marker reads the `DCA States` sheet.

#### Sheet 2: Character List

Character List is optional. If you do not need **Other Script Characters
Played** mapping, leave it blank and enter the script character names directly
in the DCA 1–12 cells. The app can still mark the script normally. Complete
Character List only when one DCA Name or performer needs to cover additional,
differently named individual script characters.

Starting at row 3, use one row for each stable DCA identity. In column A, enter
the name you want to select in `DCA States` and display in DCA State legends.
This can be a performer's name or a primary character name. These column A
names become dropdown choices on the `DCA States` sheet. A printed label such
as `MALE ENSEMBLE` can simply be an ordinary DCA Name in column A.

| Column A: DCA Name | Column B: Other Script Characters Played |
| --- | --- |
| `TOM` | *(blank)* |
| `JERRY` | *(blank)* |
| `APPLE` | *(blank)* |
| `ALL THREE` | *(blank)* |

This example contains four ordinary, independent DCA Names. `ALL THREE` has no
relationship to the other three names, and its **Other Script Characters
Played** cell stays blank. Select each name independently in DCA States.

Column B is **Other Script Characters Played**. It provides an optional,
workbook-wide **Performer / Role Mapping** for shows in which one performer or
radio mic covers additional, differently named script roles. Only when that
mapping is genuinely needed, enter one additional script character on each new
line in column B. Otherwise leave it blank, as in the example above.

**Find a DCA Name by its script role**

For example, enter `Jack` in DCA Name, then enter `Student` and `Teacher` on
separate lines in Other Script Characters Played. One DCA Name can have several
roles. You can then find the assignment by a role instead of checking the
Character List each time:

- **In the app:** choose `Student` under **Other Script Characters Played** for
  `Jack [Student]`, or `Teacher` for `Jack [Teacher]`. Both show a green check
  when Jack is already assigned; he is added only once.
- **In Excel:** choose `Jack [Student]` or `Jack [Teacher]` from the DCA cell
  dropdown. The cell keeps the selected label. Jack is the DCA Name and the
  bracketed text identifies the role you looked up. This works in a normal
  `.xlsx` file without macros.

Selecting either role assigns Jack and **all** his Character List roles to that
DCA in this state. For example, both Student and Teacher receive Jack's DCA
number; you do not need to select every role separately.

Keep the Character List mapping, with one other script character per line.
This is a shortcut to an existing DCA Name, not a new DCA Name.
The app's choices refresh after you edit Character List. The blank Excel
template updates its choices when Excel recalculates; an app-exported workbook
contains the choices known at export, so export it again to refresh the list
or type the name manually. After renaming a character or role, review DCA cells
that were already filled; their existing text is not automatically rewritten.

For `MALE ENSEMBLE`, enter `MALE ENSEMBLE` in column A and leave column B
blank unless it also has a genuine script-role mapping. Select it in a DCA cell
like any other name. The app does not manage or expand a membership list.

Selecting the column-A DCA Name remains recommended. For compatibility, if a
DCA State cell contains a role that maps to exactly one DCA Name, the app
automatically resolves it to that DCA Name. In a new workbook, repeating the
same column-B role under several DCA Names is reported as ambiguous. Give each
mapped role one DCA Name, or enter the printed label as its own ordinary DCA Name.

The automatic safety check also warns when a blank DCA column appears between
populated DCA columns in one state—for example, DCA 1–5 and DCA 7–9 are filled
but DCA 6 is blank. The gap may be intentional, so the app does not block the
output; confirm it in the marked PDF and review report before rehearsal.

The same DCA Name may also appear in more than one DCA column in one state.
The app shows a reminder but still allows generation. This can be intentional
when a performer sings solo lines on an individual DCA and then joins an
ensemble carried by another DCA. In that case the relevant script cue may show
both DCA numbers. Confirm the choice in the warning and review report rather
than separating the performer unnecessarily.

Special DCA-cell example: `ALL THREE` is an ordinary DCA Name with no
**Other Script Characters Played** mapping. In one DCA State, enter:

| DCA column | Names in the cell, one per line |
| --- | --- |
| `DCA 1` | `TOM` + new line + `ALL THREE` |
| `DCA 2` | `JERRY` + new line + `ALL THREE` |
| `DCA 3` | `APPLE` + new line + `ALL THREE` |

The individual script cues receive `1`, `2`, and `3`, while the script cue
labelled `ALL THREE` receives `1/2/3`. Because `ALL THREE` is intentionally
assigned to three DCA columns, the app may show a duplicate-assignment reminder;
confirm or ignore that reminder when this setup is correct.

If the repeated assignment is intentional, choose **Ignore** in its reminder
or click the **X** beside the expanded setup list. The app suppresses those
exact duplicate-assignment reminders for the current project session, including
the confirmation before generation. A new or changed duplicate still receives
a reminder. Required setup errors—such as a missing DCA State name or Start
Line Text—cannot be ignored and remain visible.

This mapping is different from an inline alias. Use Performer / Role Mapping
for genuinely different roles played by one person, and use square-bracket
aliases for alternate printed forms, spellings, or short names of the same
role. Performer / Role Mapping applies throughout the workbook; an inline
alias applies only to the DCA assignment cell/state where it is written.

Column B is optional. Leave it blank when no performer/role mapping is needed.

When generating a script, **Show DCA Name / Other Script Characters** adds a
movable card to the first active PDF page. It lists active Character List
mappings, not state-local `[alias]` names. Empty cards are not added.

After opening a project, click **DCA States** beside **Generate
Marked Script** to open the **DCA States Inspector**. This separate window can
stay above Preview while you scroll through the PDF. The **DCA State** label is
above the scene/state menu; use **Previous** and **Next** on either side to move
through the states with one click, or choose a state directly from the menu.
When the search box is empty, the table shows every active DCA number and DCA
Name in that state, even when **Other Script Characters Played** is blank, so it
can also be used as a complete state check. When you type a DCA Name or other
script character, the inspector searches the entire
project. Each matching DCA Name appears once, together with every DCA State
where it is active and the applicable DCA number. For example, searching
`AMERICAN SOLDIER` can show that it belongs to `M4` and list the states where
`M4` is active. Clear the search box to return to the selected-state view. The
window is movable and resizable. Because the PDF is being viewed in a separate app, the inspector cannot
automatically know which page Preview is showing; use Previous, Next, or the
state menu as you move through the script.

If you later change a DCA Name in `Character List`, the template's dropdown
choices refresh automatically after Excel recalculates.
Existing DCA assignment cells remain ordinary saved text, so re-select any
already assigned cell that should adopt the renamed value.

#### Sheet 3: DCA States

Start entering states on row 5. Use one row for each DCA State, scene, snapshot,
or song. Do not rename the columns.

| Column | What to enter |
| --- | --- |
| DCA State | A unique state label, for example `S1`, `Act 1 Scene 3`, or `Snapshot 20`. |
| Start Line Character | The speaker of the start cue. Optional, but strongly recommended when the same cue text is used by more than one character. |
| Start Line Text | The exact phrase that activates this state. Copy it directly from the selectable script text when possible, including punctuation. |
| State Start Position | Enter exactly `Before` if the new state applies before the cue, or `After` if it applies after the cue. |
| Page Hint | Optional. Normally use the number printed inside the script. If that page has no printed number, use its sequential PDF page position, counting the first file page or cover as PDF page 1. This strict hint helps when cue text repeats. |
| DCA 1 to DCA 12 | Assign the characters carried by each DCA in this state. |
| Notes | Optional notes for your own reference. This is the final column, and the marker does not use it. |

In a DCA cell, choose a character from the dropdown or type it manually. Put
each character on a separate line when one DCA carries several people. To add
an alternate printed form of that same role for this state, put it in square
brackets after the main name, for example `Lin Feifei [Feifei]` or
`林菲菲 [菲菲]`. Separate multiple aliases inside the brackets with commas.
For different roles played by one performer, define the global mapping in
column B of `Character List`. The `Jack [Student]` dropdown shortcut described
above uses that mapping; it is not a replacement for the Character List.

> Important page-number rule: the app uses two different page numbers. Excel
> Page Hint normally means the number printed inside the script. **Mark
> selected pages only** always means the sequential PDF page position shown by
> the viewer, counting from the file's first page. For example, if printed
> script page 1 is PDF page 7 because of a cover and contents, enter Page Hint
> `1`; to select only that page in the app, enter PDF page `7`. Confusing the
> numbers can prevent a state from activating, activate a repeated cue on the
> wrong page, leave early pages unmarked, or continue the previous state's DCA
> assignments.

For the first pages to receive assignments, make the first state cue an early,
unique phrase at or before the first relevant dialogue. Use `Before` when the
state is already active as that cue begins. Add a character and page hint when
the phrase could be ambiguous.

Choose **Save Project** or **Done** after editing. Exporting Excel is optional.

### 4. Open a project and choose files

1. Choose **New**, **Open**, or **Import Excel**, then use **Edit Character List
   and DCA States** to review the project data.
2. Next to **Script PDF**, choose the unchanged original script PDF.
3. Next to **Output Folder**, choose where the marked PDF and review report
   should be created.
4. Optional: turn on **Mark selected pages only** and enter the first and last
   sequential PDF page positions shown by the viewer. Count from the first
   file page, including covers and contents; never enter the page number
   printed inside the script here.

Use the Language selector at the top of the main window to choose English or
Chinese for the app's labels, explanations, and reminders.

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
- Under **DCA State Header, Footer & Mapping**, choose **Off**, **Header Only**,
  **Footer Only**, or **Header and Footer**. You can choose the visible label's
  text colour, size, font, and border colour independently.
- Turn on **Show DCA Name / Other Script Characters** to place one movable
  reference card on the first selected page where each DCA State is active.
  The card inherits the header/footer text and border appearance, searches for
  clear page space, and contains only genuine Character List column-B mappings.

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

If no dialogue DCA numbers are added, the app shows a dedicated warning with
**Show Output Folder**, **Open Review Report**, and **Try Another PDF**. Do not
use that output. Check that PDF text can be selected, the speaker-label layout
is recognised, script names, aliases, and Performer / Role Mappings match the
project assignments, and the first state cue and Page Hint are correct.

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
- **No DCA numbers appear**: do not use the output. Confirm that the project
  contains usable DCA States and assignments; confirm the PDF has selectable
  text; check whether its speaker-label layout is recognised; make
  script names, aliases, and Performer / Role Mappings match the assignments;
  then check the first state cue, Page Hint, and review report.
- **A state starts in the wrong place**: copy a more unique Start Line Text,
  choose the correct Before/After value, and add Start Line Character and Page
  Hint.
- **A character is not marked**: make the name entered in the DCA assignment
  match the dialogue label. If Character List mapping is being used, check that
  spelling too. For another spelling of the same role, add an inline alias; for
  a different role played by the same performer, add it to that performer's
  column B role mapping.
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
- 在软件中新建或从 Excel 导入的本地 DCA Script Marker 项目。
- 一份可以选择或复制文字的剧本 PDF。
- 一个用于保存标注 PDF 和复核报告的文件夹。

Version 2 中 Microsoft Excel 为可选。若需要编辑导出的工作簿，仍建议使用 Microsoft
Excel；目前尚未验证 Apple Numbers 或 LibreOffice 的兼容性。

当前不支持扫描版或纯图片 PDF，也不支持密码保护或带数字签名的 PDF。请始终保留
未经修改的原始 PDF 以及 DCA 项目或导出表格备份。

### 2. 安装软件并新建项目

1. 打开下载的 DMG。
2. 将 **DCA Script Marker** 拖入 **Applications（应用程序）**。
3. 从 Applications 打开软件。选择 **New** 新建本地 `.dcamarker` 项目，选择
   **Open** 继续已有项目，或选择 **Import Excel** 将已经完成的 Version 1 工作簿
   转换为 Version 2 项目。
4. 将项目文件保存在自己的演出文件夹。项目会保存 DCA 数据，并记住关联的剧本 PDF、
   输出文件夹和标注设置；项目不会复制或上传剧本 PDF。
5. 左上角的 **User Guide** 按钮会打开已内置在软件中的完整
   双语 PDF 使用手册，因此推出 DMG 后仍然可以使用。右上角的 **Help** 按钮及菜单中的
   Help 项目会打开软件内的简短说明。

每个发行版本都会同时提供对应的源代码压缩包、许可证、隐私说明、发行说明和本手册。

### 3. 编辑 Character List 和 DCA States

在主窗口选择 **Edit Character List and DCA States**。软件内编辑器包含与 Excel
工作簿对应的两个页面：Character List 和 DCA States。
选择 **Save Project** 或 **Done**，即可将修改写入本地项目文件。设置检查会提示缺少
状态名称或开始台词、重复的 DCA Name，以及同一状态中一个 DCA Name
被分配到多个 DCA 栏目。重复分配只会显示提醒，不会阻止生成。

使用 **Import Excel** 可将已有工作簿转换为 Version 2 项目；需要在软件外分享、打印
或编辑时，可使用 **Export Excel** 随时生成兼容的 `.xlsx` 副本。

> 工作流程提示：如果 Excel 工作簿只完成了部分剧本，可以先导入，然后直接在 DCA 项目
> 中继续添加或编辑其余 DCA States，无需重新打开 Excel。保存项目后即可直接生成标注
> 剧本；只有需要新版 `.xlsx` 副本时，才使用 Export Excel。

较早版本的项目可能会以新的 `- converted.dcamarker` 副本打开，原有分配会转换为普通
DCA 单元格条目。原文件保持不变；请在生成标注剧本前检查转换后的单元格。

#### Excel 兼容说明

模板包含三个工作表。请勿修改工作表名称，也不要修改已有的表头行。

#### 工作表 1：How to use

这里包含中英文简要步骤和各字段说明，供填写时参考。软件实际读取的是
`DCA States` 工作表。

#### 工作表 2：Character List

Character List 为可选项。如果不需要 **Other Script Characters Played（饰演的其他剧本
角色）** 映射，可以将其留空，直接在 DCA 1–12 单元格中填写剧本角色名，软件仍可正常
标注。只有当同一个 DCA Name 或演员需要对应其他名称不同的单独剧本角色时，才需要填写
Character List。`MALE ENSEMBLE` 等剧本标签可直接作为普通 DCA Name 填入 A 列。

从第 3 行开始，每个稳定的 DCA 身份使用一行。在 A 列填写您希望在 `DCA States`
中选择、并在 DCA 状态图例中显示的名称；这可以是演员名，也可以是主要角色名。A 列中的
名称会成为 `DCA States` 工作表中的下拉选项。

| A 列：DCA Name | B 列：Other Script Characters Played（饰演的其他剧本角色） |
| --- | --- |
| `TOM` | *留空* |
| `JERRY` | *留空* |
| `APPLE` | *留空* |
| `ALL THREE` | *留空* |

此示例包含四个普通、互相独立的 DCA Name。`ALL THREE` 与另外三个名称没有映射关系，
它的 **Other Script Characters Played** 单元格保持为空；请在 DCA States 中分别选择。

B 列名称为 **Other Script Characters Played（饰演的其他剧本角色）**，可选填写整个
工作簿通用的 **Performer / Role Mapping（演员 / 角色对应）**。只有当同一位演员或同一支
无线麦确实还覆盖其他名称不同的剧本角色时，才在对应 B 列单元格中每行填写一个额外角色；
否则请像上面的示例一样保持为空。

**按剧本角色选择 DCA Name**

例如，在 DCA Name 中填写 `Jack`，在 Other Script Characters Played 中分两行填写
`Student` 和 `Teacher`。一个 DCA Name 可以对应多个角色。之后可以直接按角色选择，
不必每次返回 Character List 查找：

- **软件内：**打开 DCA 单元格的选择菜单，在**饰演的其他剧本角色**下选择 `Student`
  会填入 `Jack [Student]`；选择 `Teacher` 会填入 `Jack [Teacher]`，与 Excel 一致。
  Jack 只会加入一次；当前单元格已有 Jack 时，两个角色选项均显示绿色勾选。
- **Excel：**在 DCA 单元格的下拉列表中选择 `Jack [Student]` 或 `Jack [Teacher]`，
  单元格保留所选文字。Jack 是 DCA Name，方括号内标明您查找的角色。普通 `.xlsx`
  文件即可使用，无需宏。

选择任一角色，即会将 Jack 及其在 Character List 中对应的**全部角色**分配至当前状态的
该 DCA。例如 Student 和 Teacher 都使用 Jack 的 DCA 编号，不需要逐个选择这些角色。

请保留 Character List 中的角色对应关系，每行填写一个其他剧本角色。这只是选择现有
DCA Name 的快捷方式，不会新增 DCA Name。在软件中修改 Character List
后，选择菜单会更新；空白 Excel 模板在 Excel 重新计算后更新选项。软件导出的工作簿包含
导出时已有的选项，请重新导出以更新列表，也可以手动填写名称。更改角色或 DCA Name
后，请检查已填写的 DCA 单元格；其中原有的文字不会自动改写。

例如，将 `MALE ENSEMBLE` 填入 A 列；没有真实的演员 / 角色映射时，B 列留空。
在 DCA 单元格中像其他名称一样选择即可。软件不管理或自动展开成员名单。

仍然建议在 DCA 状态单元格中选择 A 列的 DCA 名称。为了兼容旧工作簿，如果单元格中填写的
角色只对应唯一一个 DCA 名称，软件会自动转换为该 DCA 名称。对于新工作簿，如果同一个 B 列
角色重复填写在多个 DCA Name 下，软件会报告“映射不明确”。请为每个映射角色指定一个
DCA Name，或将剧本标签作为独立的普通 DCA Name 填写。

同一个 DCA Name 也可以在同一状态中出现在多个 DCA 栏目。软件会显示提醒，但仍允许继续
生成。例如，一位演员先使用个人 DCA 演唱独唱台词，随后又加入由另一个 DCA 承载的群唱，
这种重复分配可能正是需要的；相关剧本提示可能会同时显示两个 DCA 编号。请在提醒和复核报告
中确认设置，无需为了消除提醒而强行拆分该演员。

特别 DCA 单元格示例：`ALL THREE` 是普通 DCA Name，
没有 **Other Script Characters Played** 映射。在同一个 DCA 状态中填写：

| DCA 栏 | 单元格内的名称（每行一个） |
| --- | --- |
| `DCA 1` | `TOM`（换行）`ALL THREE` |
| `DCA 2` | `JERRY`（换行）`ALL THREE` |
| `DCA 3` | `APPLE`（换行）`ALL THREE` |

三个单独角色的剧本提示分别获得 `1`、`2` 和 `3`，而剧本中标为 `ALL THREE` 的提示会获得
`1/2/3`。由于 `ALL THREE` 被有意分配到三个 DCA 栏，软件可能会显示重复分配提醒；如果这项
设置正确，请确认或忽略该提醒。

如果重复分配是有意设置的，可在提醒窗口中选择 **Ignore（忽略）**，或点击展开的设置检查
列表中该提醒旁边的 **X**。软件会在当前项目会话中隐藏完全相同的重复分配提醒，生成前也不再
重复确认；如果重复分配内容后来发生变化，软件会再次提醒。缺少 DCA State 名称或 Start Line
Text 等必填设置错误不能忽略，仍会继续显示。

这项功能与方括号内联别名不同。“演员 / 角色对应”用于“同一位演员饰演的多个真正不同
角色”；方括号别名用于“同一角色的不同印刷形式、拼法或简称”。演员 / 角色对应在整个工作簿中
生效；内联别名只在填写它的那个 DCA 分配单元格 / 状态中生效。

B 列为可选项；不需要演员 / 角色对应时，可以留空。

生成剧本时，可以打开 **Show DCA Name / Other Script Characters**。软件会在每个
DCA 状态首次启用的所选 PDF 页面添加一份可移动的对照卡。卡片会显示当前状态中的真实
Character List 映射，不会混入状态内 `[别名]`；没有映射的状态不会生成空卡片。

打开项目后，点击 **Generate Marked Script** 旁边的 **DCA States**，即可打开
独立的 **DCA States Inspector（DCA 状态对照窗口）**。阅读 PDF 时，这个窗口可以保持在
Preview 上方。**DCA State** 标题位于场次 / 状态菜单上方；点击左右两侧的
**Previous** 和 **Next** 即可单击切换状态，也可以直接从菜单中选择。搜索框为空时，
表格会显示该状态中所有启用的 DCA 编号和 DCA Name，即使
**Other Script Characters Played** 为空也会显示，因此也可以用来完整复核该状态。输入 DCA Name
或其他剧本角色后，软件会搜索整个项目。
每个匹配的 DCA Name 只显示一次，并列出其启用的所有 DCA State 及对应的 DCA 编号。
例如，搜索 `AMERICAN SOLDIER` 可以显示它属于 `M4`，并列出 `M4` 启用的所有状态。
清空搜索框即可返回当前所选状态。
窗口可以移动和调整大小。由于 PDF 是在另一个软件中查看，
对照窗口无法自动知道 Preview 当前显示哪一页，因此翻阅剧本时请使用 Previous、Next
或状态菜单切换 DCA 状态。

如果之后在 `Character List` 中修改 DCA Name，
请在所有已经分配该名称的 DCA 单元格中重新选择一次，以刷新 Excel 保存的下拉选项值。

#### 工作表 3：DCA States

从第 5 行开始填写。每个 DCA 状态、场次、Snapshot 或歌曲使用一行。请勿修改列名。

| 列名 | 填写内容 |
| --- | --- |
| DCA State | 唯一的状态名称，例如 `S1`、`Act 1 Scene 3` 或 `Snapshot 20`。 |
| Start Line Character | 开始提示文字的说话角色。此项可选；如果同一句提示文字由多个角色说出，强烈建议填写。 |
| Start Line Text | 激活该状态的准确文字。尽量直接从可选中文字的剧本中复制，并保留标点。 |
| State Start Position | 如果新状态在提示文字之前生效，请准确填写 `Before`；如果在提示文字之后生效，请填写 `After`。 |
| Page Hint | 可选。通常填写剧本页面内印刷的页码；如果该页没有印刷页码，再填写该页在 PDF 阅读器中的顺序位置，并从文件第一页或封面作为 PDF 第 1 页开始计算。提示文字重复时，此严格页码提示很有帮助。 |
| DCA 1 到 DCA 12 | 填写当前状态中每个 DCA 所包含的角色。 |
| Notes | 可选，仅供人工备注。Notes 位于最后一列，软件不会读取此列。 |

在 DCA 单元格中，可以从下拉列表选择角色，也可以手动输入。如果一个 DCA 包含多个
角色，请在同一个单元格内每行填写一个角色。如果要为当前状态添加“同一角色的另一个印刷
形式”，请在主要名称后用方括号填写，例如 `Lin Feifei [Feifei]` 或 `林菲菲 [菲菲]`。
多个别名可在方括号内用逗号分隔。同一位演员饰演的不同角色，应先在 `Character List`
的 B 列建立全局对应关系。上文的 `Jack [Student]` 下拉快捷选项使用该对应关系，不能替代
Character List 中的设置。

> 重要页码规则：软件会使用两种不同的页码。Excel 的 Page Hint 通常是剧本页面内印刷
> 的页码；**Mark selected pages only** 始终使用 PDF 阅读器显示的顺序页码，并从文件
> 第一页开始计算。例如：封面和目录使剧本内印刷的第 1 页成为 PDF 第 7 页时，Page
> Hint 填 `1`；如只标注该页，软件中填写 PDF 第 `7` 页。混淆两种页码可能导致状态
> 无法启动、重复提示在错误页面启动、前面页面没有标注，或后续页面继续使用上一状态的
> DCA 分配。

为了让最开始的相关页面也能获得正确分配，请让第一条状态提示尽量位于第一段相关对白
之前或附近，并使用一段较早且唯一的文字。如果该状态在提示文字开始时已经生效，请选择
`Before`。如果文字可能重复，请同时填写角色和页码提示。

编辑完成后，请选择 **Save Project** 或 **Done**。导出 Excel 为可选操作。

### 4. 打开项目并选择文件

1. 选择 **New**、**Open** 或 **Import Excel**，再使用 **Edit Character List and
   DCA States** 检查项目数据。
2. 在 **Script PDF** 旁选择未经修改的原始剧本 PDF。
3. 在 **Output Folder** 旁选择标注 PDF 和复核报告的保存位置。
4. 可选：打开 **Mark selected pages only**，输入要处理的第一个和最后一个 PDF 页码。
   这里必须填写 PDF 阅读器显示的顺序页码，并将封面和目录计算在内；不要填写剧本页面
   内印刷的页码。

在主窗口顶部的 Language（语言）选项中选择 English 或中文，软件的按钮、说明和提醒将使用所选语言。

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
- 在 **DCA State Header, Footer & Mapping** 中，可以选择 **Off**、
  **Header Only**、**Footer Only** 或 **Header and Footer**，并设置所显示标签的
  文字颜色、大小、字体和边框颜色。
- 打开 **Show DCA Name / Other Script Characters**，可在每个 DCA 状态首次启用的
  所选页面添加一份可移动的对照卡。卡片会继承页眉 / 页脚的文字和边框样式，优先寻找页面
  空白位置，并且只显示 Character List B 列中真实的演员 / 角色映射。

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

如果没有添加任何对白 DCA 编号，软件会显示专门警告，并提供 **Show Output Folder**、
**Open Review Report** 和 **Try Another PDF**。请勿直接使用该输出。请确认 PDF 文字
可以选择、软件能够识别角色标签排版、剧本名称或别名与表格分配一致，并确认演员 / 角色对应也与
剧本一致，再检查第一个状态提示及 Page Hint 是否正确。

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
- **没有出现 DCA 编号**：请勿使用该输出。确认项目中包含可用的 DCA 状态和分配；
  确认 PDF 可以选中文字；检查软件是否能识别角色标签排版；让剧本名称或别名与
  表格分配一致，并确认演员 / 角色对应没有填错；再检查第一个状态提示、Page Hint 和复核报告。
- **状态从错误位置开始**：复制一段更独特的 Start Line Text，确认 Before/After，
  并填写 Start Line Character 和 Page Hint。
- **某个角色没有被标注**：让 DCA 单元格中填写的名称与对白标签一致。如果使用了
  Character List 映射，也请检查其中的拼写。如果是同一角色的另一种拼法，添加内联
  别名；如果是同一演员饰演的另一个不同角色，请将它加入该演员在 B 列的角色对应中。
- **同时看到新旧两套标签**：关闭 Preview 中的 PDF，再重新打开。比较结果时请选择
  Save as New。
- **macOS 提示无法验证软件**：请停止并记录完整提示。对于应当签名和公证的版本，
  不要绕过系统警告。

请前往 <https://github.com/mmssqq/DCA-Script-Marker/issues> 反馈问题，并且只使用经过
脱敏的示例。绝对不要把保密剧本、DCA 表格、标注 PDF 或复核报告上传到公开 Issue。
Copyright 2026 马斯琪 Siqi Ma. Licensed under GNU AGPL v3 or later.
