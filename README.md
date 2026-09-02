# DCA Script Marker

DCA Script Marker is a local macOS tool for building scene-by-scene DCA states
and marking dialogue cues with the correct DCA numbers while preserving the
script PDF layout and creating a review report. Version 2 includes an in-app
Character List and DCA States editor, plus Excel import and export.

**中文：** DCA Script Marker 是一款为剧场音响人员提供的本地 macOS 工具。它会读取
按场次编排的 DCA 列表和文字版剧本 PDF，在对白角色旁标注正确的 DCA 编号，保留原
PDF 版式，并生成供人工复核的报告。

Version 2.0.0 targets macOS 12 Monterey or later as one Universal app for
Apple Silicon and 64-bit Intel Macs. The previous notarized release candidate
passed installation, launch, marked-PDF generation, and review-report
generation on Intel macOS 12.7.6. Apple Silicon Monterey 12.x remains
unverified. Users do not need Python, Homebrew, or Xcode.

**中文：** 2.0.0 版本面向 macOS 12 Monterey 或更高版本，一个通用安装包同时包含
Apple 芯片和 64 位 Intel Mac 版本。此前经过公证的候选版本已在 Intel macOS 12.7.6
实体 Mac 上通过安装、启动、生成标注 PDF 和复核报告测试；运行 Monterey 12.x 的
Apple 芯片 Mac 尚未单独验证。使用者无需安装 Python、Homebrew 或 Xcode。

## Install and quick start / 安装与快速开始

1. Download the `macOS.dmg` from the GitHub Release, open it, and drag
   **DCA Script Marker** into **Applications**.
2. Choose **New** to create a local `.dcamarker` project, **Open** to continue
   one, or **Import Excel** to convert an existing DCA workbook.
3. Choose **Edit Character List and DCA States**. Character List is optional:
   leave it blank unless you need **Other Script Characters Played** mapping.
   Enter names directly in each state's DCA 1–12 assignments, then complete
   its start cue and Page Hint. When mapping is needed, enter one DCA identity
   per Character List row and put each additional script role on a new line.
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

1. 从 GitHub Release 下载 `macOS.dmg`，打开后将 **DCA Script Marker** 拖入
   **Applications（应用程序）**。
2. 选择 **New** 新建本地 `.dcamarker` 项目，选择 **Open** 继续已有项目，或选择
   **Import Excel** 转换现有 DCA 工作簿。
3. 选择 **Edit Character List and DCA States**。Character List 为可选项；如果不需要
   **Other Script Characters Played** 映射，可以留空，直接填写每个状态的开始提示、
   Page Hint 和 DCA 1–12 分配。如果需要映射，再在 Character List 中每行填写一个
   DCA 身份，并将饰演的其他剧本角色分行填写。
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
