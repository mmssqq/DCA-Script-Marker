# DCA Script Marker

DCA Script Marker is a local macOS tool for building scene-by-scene DCA states
and marking dialogue cues with the correct DCA numbers while preserving the
script PDF layout and creating a review report. Version 2 includes an in-app
Character List and DCA States editor, plus Excel import and export.

**中文：** DCA Script Marker 是一款为剧场音响人员提供的本地 macOS 工具。它根据
按场次编排的 DCA 状态，在文字版剧本的对白角色旁标注正确的 DCA 编号，保留原 PDF
版式，并生成供人工复核的报告。Version 2 新增软件内的角色列表与 DCA 状态编辑器，
并支持 Excel 导入与导出。

**[Download Version 2 for Mac / 下载 Mac 版 Version 2](https://github.com/mmssqq/DCA-Script-Marker/releases/download/v2.0.0/DCA-Script-Marker-v2.0.0-macOS.dmg)**
· [Release notes and source / 更新记录与源码](https://github.com/mmssqq/DCA-Script-Marker/releases/tag/v2.0.0)
· [User Guide / 使用手册](USER_GUIDE.md)

Version 2.0.0 (build 8) is Developer ID signed and Apple-notarized. One Universal
app supports Apple Silicon and 64-bit Intel Macs running macOS 12 Monterey or
later. No Python, Homebrew, or Xcode is needed to use the app.

**中文：** Version 2.0.0（构建版本 8）已完成 Developer ID 签名和 Apple 公证。
一个通用安装包支持运行 macOS 12 Monterey 或更高版本的 Apple 芯片及 64 位 Intel Mac。
使用软件无需安装 Python、Homebrew 或 Xcode。

## New in Version 2 / Version 2 新功能

- **Edit directly in the app.** Create or open a local `.dcamarker` project and
  edit Character List and all 12 DCA assignment columns without needing Excel.
  Edits autosave; the project remembers the linked PDF, output folder, and
  marking settings.
  **直接在软件内编辑。** 新建或打开本地 `.dcamarker` 项目，无需 Excel 即可编辑角色
  列表和全部 12 个 DCA 分配列。修改会自动保存，项目会记住关联 PDF、输出文件夹及
  标注设置。
- **Keep your Excel workflow.** Import a compatible DCA workbook, continue
  editing in the app, and export a standard `.xlsx` copy when needed. The
  included blank template updates its dropdown choices when names or mapped
  roles change within its prepared Character List rows.
  **保留 Excel 工作流程。** 导入兼容的 DCA 工作簿，在软件内继续编辑，并按需导出
  标准 `.xlsx` 副本。内附空白模板会根据预设角色输入行内的名称及兼演角色变化，更新
  下拉选项。
- **Choose a DCA Name through its script roles.** If `Jack` also plays `Student`
  and `Teacher`, put those roles on separate lines under **Other Script
  Characters Played**. Choose `Jack [Student]` or `Jack [Teacher]` in Excel, or
  the corresponding role shortcut in the app. The selected role label stays
  visible, while all of Jack's mapped roles use his active DCA assignment; the
  app adds Jack only once per cell. An ensemble label such as `MALE ENSEMBLE`
  can simply be an ordinary DCA Name with no role mapping.
  **通过剧本角色选择 DCA Name。** 如果 `Jack` 同时饰演 `Student` 和 `Teacher`，
  将两个角色分行填入 **Other Script Characters Played（饰演的其他剧本角色）**。
  可在 Excel 中选择 `Jack [Student]` 或 `Jack [Teacher]`，或在软件内选择对应的
  角色快捷选项。所选角色标签保持可见，Jack 的全部对应角色均使用他当前的 DCA 分配；
  软件在同一单元格内只添加一次 Jack。`MALE ENSEMBLE` 等合唱名称也可直接作为普通
  DCA Name 使用，无需填写角色映射。
- **Work faster in DCA States.** State numbers stay visible when scrolling
  horizontally. Select a state from its row, use larger Add buttons, and see
  more states with compact rows. In DCA assignment cells, **Tab** moves to the
  next cell and **Return/Enter** starts a new line.
  **更方便地编辑 DCA 状态。** 横向滚动时仍可看见状态序号；可通过点击所在行选择状态，
  使用更大的添加按钮，并通过紧凑行高查看更多状态。在 DCA 分配单元格中，**Tab**
  切换至下一个单元格，**Return/Enter** 换行。
- **Check assignments beside your PDF.** The floating **DCA States Inspector**
  shows the active DCA Names and their other script roles. Move between states
  or search across them while reviewing the script.
  **在 PDF 旁核对分配。** 独立的 **DCA States Inspector（DCA 状态对照窗口）** 显示
  当前状态的 DCA Name 及其饰演的其他角色，方便阅读剧本时切换状态或跨状态搜索。
- **Keep intentional repeated assignments.** Assigning a name to more than
  one DCA produces a reminder, not an export block. Use **Ignore** or the
  reminder's **X** to dismiss confirmed duplicate-assignment reminders for the
  current project session. Required setup errors still need attention.
  **保留有意设置的重复分配。** 同一名称分配至多个 DCA 时会提醒，但不阻止导出。
  确认属于有意安排后，可使用 **Ignore（忽略）** 或提醒的 **X**，在当前项目会话内
  忽略相关重复分配提醒；必需的设置错误仍需处理。
- **Updated bilingual help.** English and Chinese interface guidance, keyboard
  hints, the bundled User Guide, and Excel's How to use sheet explain the
  project and role-mapping workflows.
  **更新双语帮助。** 中英文界面说明、键盘提示、内附使用手册及 Excel 的 How to use
  工作表，提供项目编辑与兼演角色设置的操作指引。

**Excel dropdown note:** the blank template has live choices within its prepared
input rows. An app-exported workbook's choices reflect the project at export
time; after changing the project's Character List, export again to refresh them.
Import and export create copies; they do not keep Excel and the app automatically
synchronized.

**Excel 下拉选项说明：** 空白模板在预设输入行内提供动态选项。软件导出的工作簿，
其选项以导出时的项目为准；修改项目角色列表后，请重新导出以刷新选项。导入与导出
会生成副本，不会使 Excel 与软件项目自动同步。

## Install and quick start / 安装与快速开始

1. Download the [Version 2 installer](https://github.com/mmssqq/DCA-Script-Marker/releases/download/v2.0.0/DCA-Script-Marker-v2.0.0-macOS.dmg),
   open it, and drag **DCA Script Marker** into **Applications**. Keep a backup
   of your existing projects and workbooks.
2. Choose **New** to create a local `.dcamarker` project, **Open** to continue
   one, or **Import Excel** to convert an existing DCA workbook.
3. Choose **Edit Character List and DCA States**. Character List is optional:
   add DCA Names there for picker choices and optional **Other Script Characters
   Played** mapping, or type names directly in each state's DCA 1–12 cells.
   Complete the state's start cue and Page Hint. When mapping is needed, enter
   one DCA identity per Character List row and each additional script role on
   a new line.
4. Choose the original text-based script PDF and an output folder. The project
   remembers these paths and the marking settings. Use **Export Excel** whenever
   a standard workbook copy is needed.
5. Choose a marking style, select **Generate Marked Script**, and review both
   the marked PDF and the generated review report.

**Important page-number rule:** Excel **Page Hint** normally uses the page
number printed inside the script. If that page has no printed number, use the
sequential PDF page position shown by the viewer, counting the cover as PDF
page 1. **Mark selected pages only** always uses the sequential PDF page
position. Confusing these numbers can leave pages unmarked or activate a DCA
State on the wrong page.

1. 下载 [Version 2 安装包](https://github.com/mmssqq/DCA-Script-Marker/releases/download/v2.0.0/DCA-Script-Marker-v2.0.0-macOS.dmg)，
   打开后将 **DCA Script Marker** 拖入 **Applications（应用程序）**。请保留现有
   项目和工作簿的备份。
2. 选择 **New** 新建本地 `.dcamarker` 项目，选择 **Open** 继续已有项目，或选择
   **Import Excel** 转换现有 DCA 工作簿。
3. 选择 **Edit Character List and DCA States**。Character List 为可选项；可以在其中
   添加 DCA Name，供选择菜单使用，并按需填写 **Other Script Characters Played**
   映射；也可以直接在每个状态的 DCA 1–12 单元格中输入名称。填写开始提示和 Page Hint。
   如需映射，在 Character List 中每行填写一个 DCA 身份，并将饰演的其他剧本角色分行填写。
4. 选择原始文字版剧本 PDF 和输出文件夹。项目会记住这些路径及标注设置；需要标准
   工作簿副本时，可随时选择 **Export Excel**。
5. 选择标注方式，点击 **Generate Marked Script**，并同时检查标注 PDF 和复核报告。

**重要页码规则：** Excel 的 **Page Hint** 通常填写剧本页面内印刷的页码；如果该页
没有印刷页码，再填写 PDF 阅读器显示的顺序页码，并从封面作为 PDF 第 1 页开始计算。
**Mark selected pages only** 始终使用 PDF 顺序页码。混淆两种页码可能造成页面没有
标注，或 DCA 状态在错误页面启动。

Use the **User Guide** button at the upper-left of the installed app to open
the complete bilingual PDF manual at any time, even after the DMG is ejected.
A second printable copy is also placed prominently inside every release DMG.
The Markdown [User Guide / 使用手册](USER_GUIDE.md) is available in the source.

使用已安装软件左上角的 **User Guide** 按钮，可随时打开完整的双语 PDF 使用手册，即使
DMG 已经推出也可以使用。每个发行版 DMG 内还会放置一份便于复制或打印的手册；源代码
中同时提供 Markdown 格式的 [User Guide / 使用手册](USER_GUIDE.md)。

## Safety and limitations / 安全说明与限制

Use a short, exact **Start Line Text** from **one printed PDF line**. A cue that
wraps across multiple printed lines is not supported; shorten it to a distinctive
single-line phrase and check the Page Hint.

**开始台词文字（Start Line Text）** 应取自 **PDF 同一印刷行内** 的简短、准确片段。
不支持跨印刷行的提示；请缩短为具有辨识度的单行片段，并核对 Page Hint。

DCA Script Marker automates a review task; it cannot guarantee correct results
for every PDF layout. Before rehearsal or performance, a member of the sound
team must compare every exported script with the original PDF, the completed
DCA workbook, and the review report. See
[Testing and safety](TESTING_AND_SAFETY.md) for supported inputs, limitations,
and the verification checklist. See [PRIVACY.md](PRIVACY.md) for local data
handling and [RELEASE_NOTES.md](RELEASE_NOTES.md) for release details.

**重要：** DCA Script Marker 可协助自动标注，但无法保证适用于所有 PDF 排版。
排练或正式演出前，音响团队成员必须将每份导出的剧本与原始 PDF、已填写的 DCA 表格
及复核报告进行人工核对。支持范围、限制和检查步骤请参阅
[Testing and safety](TESTING_AND_SAFETY.md)。所有剧本和表格均在本机处理，不会上传。

If the app reports that **no DCA numbers were added**, do not use that output.
The PDF may be image-only, its speaker-label layout may not yet be recognised,
the workbook names or assignments may not match, or a state cue/Page Hint may
be wrong. Open the review report and correct the setup before trying again.

如果软件提示**未添加任何 DCA 编号**，请勿直接使用该输出。原因可能是 PDF 为纯图片、
软件尚未识别该角色标签排版、工作簿名称或分配不一致，或状态提示/Page Hint 填写错误。
请打开复核报告并修正设置后再重新生成。

**Compatibility testing:** the previous notarized release candidate passed
installation, launch, marked-PDF generation, and review-report generation on
Intel macOS 12.7.6. Version 2 has not been physically tested on every supported
Mac/OS combination; Apple Silicon Monterey 12.x remains unverified.

**兼容性测试：** 此前经过公证的候选版本已在 Intel macOS 12.7.6 实体 Mac 上通过
安装、启动、生成标注 PDF 和复核报告测试。Version 2 尚未覆盖所有支持的设备与系统
组合；运行 Monterey 12.x 的 Apple 芯片 Mac 仍未单独验证。

## Current capabilities / 主要功能

- Local Version 2 project files that remember DCA data, the linked PDF, output
  folder, and marking settings / 本地 Version 2 项目文件可保存 DCA 数据、关联 PDF、
  输出文件夹及标注设置
- In-app Character List and DCA States editor with setup validation, plus Excel
  import and export / 软件内置 Character List 与 DCA States 编辑器及设置检查，并支持
  Excel 导入与导出
- Horizontal and supported legacy vertical DCA workbook formats / 支持横向及旧版纵向 DCA 状态表
- Optional workbook-wide Performer / Role Mapping: assign one DCA identity to
  several differently named script roles / 可在整个工作簿中设置“演员 / 角色对应”，
  让多个不同剧本角色共用同一个 DCA 身份
- Optional movable mapping card on the first selected page where each DCA State
  is active, so column-B performer/role mappings can be checked without opening
  Excel / 可在每个 DCA 状态首次启用的所选页面添加可移动对照卡，无需打开 Excel 即可
  查看 B 列演员 / 角色映射
- Editable PDF annotations in every user-facing marking mode / 所有用户可选标注方式均使用可编辑 PDF 标注
- Editable full marking, first appearance, and DCA State legend modes / 可编辑完整标注、首次出现及 DCA 状态图例模式
- Independent DCA number and scene/state appearance, with header-only, footer-only, both, or off / 可分别设置 DCA 编号及场次样式，并可选择仅页眉、仅页脚、同时显示或关闭
- English, Simplified Chinese, and mixed-language scripts with selectable text / 支持英文、简体中文及中英混排的可选中文字剧本
- Local processing with no telemetry or script upload / 完全本地处理，无遥测，不上传剧本

**Current limitations / 当前限制：** Scanned/image-only, password-protected,
and digitally signed PDFs are not supported. Unusual columns, rotated text,
tight margins, or nonstandard speaker layouts may reduce matching accuracy.
当前不支持扫描件或纯图片、密码保护及带数字签名的 PDF；特殊分栏、旋转文字、过窄页边距
或非标准角色排版可能降低匹配准确度。

## Report a bug / 报告问题

Use the bilingual [Bug Report / 问题报告](https://github.com/mmssqq/DCA-Script-Marker/issues/new?template=bug_report.yml)
form. Include the app build, macOS version, Mac processor, marking style, exact
page or scene, expected result, and actual result. Never upload a complete or
confidential production script, completed workbook, marked PDF, or unredacted
review report; use cropped screenshots and sanitized samples only.

请使用双语 [Bug Report / 问题报告](https://github.com/mmssqq/DCA-Script-Marker/issues/new?template=bug_report.yml)
表单，并填写软件 Build、macOS 版本、Mac 处理器、标注方式、准确页面或场次、预期结果和
实际结果。请勿上传完整或保密的演出剧本、已填写的 DCA 表格、完整标注 PDF 或未经处理的
复核报告；请只使用局部截图和已移除敏感信息的测试资料。

## Development

The marking engine is `dca_script_marker.py`. The macOS packaging workflow and
release build instructions are in
[`packaging/macos/README.md`](packaging/macos/README.md).

## Licence and source code

DCA Script Marker is free and open-source software licensed under the GNU
Affero General Public License, version 3 or later. The copyright holder may
also offer the same original code under separate terms in the future.

Every release binary must be distributed with its matching source archive. See
[LICENSING.md](LICENSING.md), [SOURCE.md](SOURCE.md), and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for details. Coffee donations
are welcome but never required to use the software.
