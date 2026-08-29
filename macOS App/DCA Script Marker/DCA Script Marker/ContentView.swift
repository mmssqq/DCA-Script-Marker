// Copyright © 2026 马斯琪 Siqi Ma
// SPDX-License-Identifier: AGPL-3.0-or-later

import SwiftUI
import AppKit
import UniformTypeIdentifiers
import Foundation

extension Notification.Name {
    static let openDCAScriptMarkerHelp = Notification.Name(
        "openDCAScriptMarkerHelp"
    )
}

private struct MarkerRuntime {
    let executableURL: URL
    let argumentPrefix: [String]
}

private struct MarkerSafetyWarning: Decodable {
    let code: String
    let severity: String
    let message: String
}

private struct MarkerCompletionResult: Decodable {
    let markedCount: Int
    let outputPDF: String
    let reviewReport: String
    let safetyLevel: String
    let safetyWarningCount: Int
    let safetyWarnings: [MarkerSafetyWarning]

    enum CodingKeys: String, CodingKey {
        case markedCount = "marked_count"
        case outputPDF = "output_pdf"
        case reviewReport = "review_report"
        case safetyLevel = "safety_level"
        case safetyWarningCount = "safety_warning_count"
        case safetyWarnings = "safety_warnings"
    }
}

struct ContentView: View {
    @State private var templatePath = ""
    @State private var scriptPath = ""
    @State private var outputFolder = ""
    @State private var markSelectedPages = false
    @State private var startPage = ""
    @State private var endPage = ""
    @State private var selectedStyle = "Editable Full Marking"
    @State private var message = ""
    @State private var isGenerating = false
    @State private var showAnnotationStyle = false
    @State private var numberColour = "Red"
    @State private var numberSize = "Medium"
    @State private var numberFont = "Helvetica"
    @State private var numberPosition = "Standard"
    @State private var numberVerticalPosition = "Default"
    @State private var stateColour = "Blue"
    @State private var stateSize = "Medium"
    @State private var stateFont = "PingFang SC"
    @State private var statePosition = "Left Gutter"
    @State private var legendPosition = "Left Gutter"
    @State private var pageStateDisplay = "Header and Footer"
    @State private var pageStateTextColour = "Blue"
    @State private var pageStateTextSize = "Medium"
    @State private var pageStateTextFont = "PingFang SC"
    @State private var pageStateBorderColour = "Blue"
    @State private var legendDrafts: [LegendDraft] = []
    @State private var showLegendEditor = false
    @State private var showHelp = false

    let styles = [
        "Editable Full Marking",
        "First Appearance Only",
        "DCA State Legend"
    ]

    var body: some View {
        VStack(spacing: 22) {
            ZStack {
                HStack {
                    Button {
                        openUserGuide()
                    } label: {
                        Label("User Guide", systemImage: "book.closed")
                    }
                    .buttonStyle(.bordered)
                    .help("Open the complete bilingual PDF user guide / 打开完整双语 PDF 使用手册")

                    Spacer()

                    Button {
                        showHelp = true
                    } label: {
                        Label("Help", systemImage: "questionmark.circle")
                    }
                    .buttonStyle(.bordered)
                    .help("Open the DCA Script Marker help guide")
                }

                VStack(alignment: .center) {
                    Text("DCA Script Marker")
                        .font(.system(size: 28, weight: .bold))

                    Text("Create marked rehearsal scripts from a DCA State template.")
                        .foregroundStyle(.secondary)
                }
            }

            VStack(spacing: 14) {
                FileRow(
                    title: "DCA State Template",
                    path: $templatePath,
                    buttonTitle: "Choose Excel"
                ) {
                    templatePath = chooseFile(
                        allowedTypes: ["xlsx"]
                    )
                }

                FileRow(
                    title: "Script PDF",
                    path: $scriptPath,
                    buttonTitle: "Choose PDF"
                ) {
                    scriptPath = chooseFile(
                        allowedTypes: ["pdf"]
                    )
                }

                VStack(alignment: .leading, spacing: 3) {
                    Text("Use a text-based PDF: you should be able to select or copy words from the script. Scanned or image-only PDFs are not supported.")
                    Text("请使用可选择或复制文字的文本型 PDF。扫描版或仅图片的 PDF 暂不支持。")
                }
                .font(.caption)
                .foregroundStyle(.secondary)

                FileRow(
                    title: "Output Folder",
                    path: $outputFolder,
                    buttonTitle: "Choose Folder"
                ) {
                    outputFolder = chooseFolder()
                }
            }

            VStack(alignment: .leading, spacing: 8) {
                Toggle("Mark selected pages only", isOn: $markSelectedPages)
                    .font(.headline)

                if markSelectedPages {
                    HStack {
                        Text("From page")
                        TextField("1", text: $startPage)
                            .frame(width: 60)
                        Text("to")
                        TextField("Last", text: $endPage)
                            .frame(width: 60)
                        Text("(PDF page numbers)")
                            .foregroundStyle(.secondary)
                    }
                    .textFieldStyle(.roundedBorder)
                }

                VStack(alignment: .leading, spacing: 3) {
                    Text("Important: Excel Page Hint normally uses the page number printed inside the script. A selected-page range always uses the PDF viewer's page position, counting the cover as page 1.")
                    Text("重要：Excel 的 Page Hint 通常填写剧本页面内印刷的页码；“只标注指定页码”始终使用 PDF 阅读器中的页面位置，并从封面作为第 1 页开始计算。")
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }

            VStack(alignment: .leading, spacing: 10) {
                Text("Choose Marking Style")
                    .font(.headline)

                HStack(spacing: 10) {
                    ForEach(styles, id: \.self) { style in
                        Button {
                            selectedStyle = style
                        } label: {
                            Text(style)
                                .font(.system(size: 13, weight: .semibold))
                                .multilineTextAlignment(.center)
                                .frame(maxWidth: .infinity)
                                .frame(height: 52)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(selectedStyle == style ? .blue : .gray)
                    }
                }

                Text(helpText(for: selectedStyle))
                    .font(.system(size: 14))
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, minHeight: 44, maxHeight: 44)
                    .padding(.top, 2)
            }

            Text("Selected: \(selectedStyle)")
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity)

            HStack(spacing: 16) {
                Button {
                    guard !templatePath.isEmpty,
                          !scriptPath.isEmpty,
                          !outputFolder.isEmpty else {
                        message = "Please choose a DCA template, script PDF, and output folder."
                        return
                    }
                    showAnnotationStyle = true
                } label: {
                    Text(isGenerating ? "Generating…" : "Generate Marked Script")
                        .font(.system(size: 18, weight: .bold))
                        .foregroundStyle(.white)
                        .frame(width: 300)
                        .frame(height: 54)
                }
                .buttonStyle(.plain)
                .background(Color.green, in: RoundedRectangle(cornerRadius: 16))
                .disabled(isGenerating)

                if isGenerating {
                    VStack(alignment: .leading, spacing: 6) {
                        ProgressView()
                            .progressViewStyle(.linear)
                            .frame(width: 150)
                            .tint(.green)
                        Text("Marking script…")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .transition(.opacity)
                }
            }
            .animation(.easeInOut(duration: 0.2), value: isGenerating)

            if !message.isEmpty {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
        .padding(32)
        .frame(minWidth: 760, minHeight: 500)
        .background(Color(red: 0.94, green: 0.96, blue: 0.98))
        .sheet(isPresented: $showAnnotationStyle) {
            AnnotationStyleSheet(
                numberColour: $numberColour,
                numberSize: $numberSize,
                numberFont: $numberFont,
                numberPosition: $numberPosition,
                numberVerticalPosition: $numberVerticalPosition,
                stateColour: $stateColour,
                stateSize: $stateSize,
                stateFont: $stateFont,
                statePosition: $statePosition,
                legendPosition: $legendPosition,
                selectedStyle: selectedStyle,
                pageStateDisplay: $pageStateDisplay,
                pageStateTextColour: $pageStateTextColour,
                pageStateTextSize: $pageStateTextSize,
                pageStateTextFont: $pageStateTextFont,
                pageStateBorderColour: $pageStateBorderColour,
                cancel: { showAnnotationStyle = false },
                continueAction: {
                    showAnnotationStyle = false
                    if selectedStyle == "DCA State Legend" {
                        loadLegendEditor()
                    } else {
                        generateMarkedScript()
                    }
                }
            )
        }
        .sheet(isPresented: $showLegendEditor) {
            LegendEditorSheet(
                drafts: $legendDrafts,
                cancel: { showLegendEditor = false },
                export: {
                    showLegendEditor = false
                    exportEditedLegend()
                }
            )
        }
        .sheet(isPresented: $showHelp) {
            HelpSheet(close: { showHelp = false })
        }
        .onReceive(
            NotificationCenter.default.publisher(
                for: .openDCAScriptMarkerHelp
            )
        ) { _ in
            showHelp = true
        }
    }

    func helpText(for style: String) -> String {
        switch style {
        case "Editable Full Marking":
            return "Marks every dialogue line with an editable DCA number.\n为每一句角色台词标注可编辑的 DCA 编号。"
        case "First Appearance Only":
            return "Marks each character's first appearance in every DCA State with editable annotations.\n在每个 DCA 状态中，只为每个角色第一次出现的台词创建可编辑标注。"
        default:
            return "Creates an editable DCA list; its page labels can also be moved or deleted.\n创建可编辑的 DCA 分配列表；页面标签也可以移动或删除。"
        }
    }

    func chooseFile(allowedTypes: [String]) -> String {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.allowedContentTypes = allowedTypes.compactMap {
            UTType(filenameExtension: $0)
        }

        return panel.runModal() == .OK
            ? panel.url?.path ?? ""
            : ""
    }

    func chooseFolder() -> String {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseFiles = false
        panel.canChooseDirectories = true

        return panel.runModal() == .OK
            ? panel.url?.path ?? ""
            : ""
    }

    private func openUserGuide() {
        guard let guideURL = Bundle.main.url(
            forResource: "START HERE - User Guide - 使用手册",
            withExtension: "pdf"
        ), NSWorkspace.shared.open(guideURL) else {
            let alert = NSAlert()
            alert.alertStyle = .warning
            alert.messageText = (
                "User guide unavailable / 无法打开使用手册"
            )
            alert.informativeText = """
            The complete bilingual PDF user guide could not be opened. Please reinstall DCA Script Marker from the official release DMG.

            无法打开完整的双语 PDF 使用手册。请从官方发行版 DMG 重新安装 DCA Script Marker。
            """
            alert.addButton(withTitle: "OK")
            alert.runModal()
            return
        }
    }

    func loadLegendEditor() {
        isGenerating = true
        message = "Loading the DCA State Legend…"

        DispatchQueue.global(qos: .userInitiated).async {
            guard let runtime = markerRuntime() else {
                DispatchQueue.main.async {
                    isGenerating = false
                    message = "This build is missing its bundled DCA marker engine. Please reinstall the app."
                }
                return
            }

            let process = Process()
            let output = Pipe()
            process.executableURL = runtime.executableURL
            process.arguments = runtime.argumentPrefix + [
                "--template", templatePath,
                "--list-legends",
            ]
            process.environment = markerEnvironment()
            process.standardOutput = output
            process.standardError = output

            do {
                try process.run()
                process.waitUntilExit()
                let data = output.fileHandleForReading.readDataToEndOfFile()
                let drafts = try JSONDecoder().decode([LegendDraft].self, from: data)

                DispatchQueue.main.async {
                    isGenerating = false
                    legendDrafts = drafts
                    showLegendEditor = true
                }
            } catch {
                DispatchQueue.main.async {
                    isGenerating = false
                    message = "Could not load the DCA State Legend: \(error.localizedDescription)\n\(resultText(from: output))"
                }
            }
        }
    }

    func exportEditedLegend() {
        do {
            let overrides = Dictionary(
                uniqueKeysWithValues: legendDrafts.map { ($0.id, $0.text) }
            )
            let file = FileManager.default.temporaryDirectory
                .appendingPathComponent(
                    "DCA-Script-Marker-Legend-Edits-\(UUID().uuidString).json"
                )
            let data = try JSONEncoder().encode(overrides)
            try data.write(to: file, options: .atomic)
            generateMarkedScript(legendOverridesFile: file.path)
        } catch {
            message = "Could not save the edited legend: \(error.localizedDescription)"
        }
    }

    func resultText(from output: Pipe) -> String {
        let data = output.fileHandleForReading.readDataToEndOfFile()
        return String(data: data, encoding: .utf8) ?? ""
    }

    private func showSafetyAlert(_ result: MarkerCompletionResult) {
        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = (
            "Review required before use / 使用前需要复核"
        )

        let warningLines = result.safetyWarnings.prefix(3).map {
            "• \($0.message)"
        }
        let remainingCount = max(
            0,
            result.safetyWarningCount - warningLines.count
        )
        let remainingText = remainingCount > 0
            ? "\n• \(remainingCount) more warning(s) are listed in the review report."
            : ""

        alert.informativeText = """
        The PDF was created, but the automatic safety check found possible setup or matching problems. Check the review report and marked PDF before rehearsal.

        PDF 已生成，但自动安全检查发现可能的设置或匹配问题。请在排练前核对复核报告和标注后的 PDF。

        \(warningLines.joined(separator: "\n"))\(remainingText)
        """
        alert.addButton(
            withTitle: "Show Output Folder"
        )
        alert.addButton(
            withTitle: "Open Review Report"
        )
        alert.addButton(withTitle: "Later")

        switch alert.runModal() {
        case .alertFirstButtonReturn:
            let outputFolder = URL(
                fileURLWithPath: result.outputPDF
            ).deletingLastPathComponent()
            NSWorkspace.shared.open(outputFolder)
        case .alertSecondButtonReturn:
            NSWorkspace.shared.open(
                URL(fileURLWithPath: result.reviewReport)
            )
        default:
            break
        }
    }

    private func showZeroDCANumbersAlert(_ result: MarkerCompletionResult) {
        let alert = NSAlert()
        alert.alertStyle = .critical
        alert.messageText = (
            "No DCA numbers were added / 未添加任何 DCA 编号"
        )
        alert.informativeText = """
        No dialogue DCA numbers were added. Do not use this output until you have checked the original PDF, completed workbook, and review report.

        Possible causes include a blank or incomplete workbook with no usable DCA States or assignments, a scanned/image-only PDF, an unrecognised speaker-label layout, character names or DCA assignments that do not match, or a Start Line Text/Page Hint that did not activate the intended state.

        Page numbers are not interchangeable: Excel Page Hint normally uses the number printed inside the script; use the PDF page position only when no printed page number exists. A selected-page range always uses the PDF viewer's page position, counting the cover as page 1.

        没有添加任何对白 DCA 编号。请先核对原始 PDF、已填写的工作簿和复核报告，勿直接使用此输出。

        可能原因包括：工作簿仍为空白或没有可用的 DCA 状态及分配、PDF 为扫描版或纯图片、软件尚未识别该角色标签排版、角色名称或 DCA 分配不一致，或 Start Line Text / Page Hint 未能启动正确的状态。

        两种页码不能混用：Excel 的 Page Hint 通常填写剧本页面内印刷的页码；只有没有印刷页码时才使用 PDF 页面位置。“只标注指定页码”始终使用 PDF 阅读器中的页面位置，并从封面作为第 1 页开始计算。
        """
        alert.addButton(withTitle: "Show Output Folder")
        alert.addButton(withTitle: "Open Review Report")
        alert.addButton(withTitle: "Try Another PDF")

        switch alert.runModal() {
        case .alertFirstButtonReturn:
            let outputFolder = URL(
                fileURLWithPath: result.outputPDF
            ).deletingLastPathComponent()
            NSWorkspace.shared.open(outputFolder)
        case .alertSecondButtonReturn:
            NSWorkspace.shared.open(
                URL(fileURLWithPath: result.reviewReport)
            )
        case .alertThirdButtonReturn:
            let replacementPath = chooseFile(allowedTypes: ["pdf"])
            if !replacementPath.isEmpty {
                scriptPath = replacementPath
                message = "A new script PDF is selected. Check the workbook and generate again."
            }
        default:
            break
        }
    }

    private func showSafetyUnavailableAlert() {
        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = (
            "Safety result unavailable / 无法读取安全检查结果"
        )
        alert.informativeText = """
        The PDF was created, but the app could not read the automatic safety result. Open the output folder and check the review report and marked PDF manually before rehearsal.

        PDF 已生成，但软件无法读取自动安全检查结果。请打开输出文件夹，并在排练前人工核对复核报告和标注后的 PDF。
        """
        alert.addButton(
            withTitle: "Show Output Folder"
        )
        alert.addButton(withTitle: "Later")

        if alert.runModal() == .alertFirstButtonReturn {
            NSWorkspace.shared.open(
                URL(fileURLWithPath: outputFolder)
            )
        }
    }

    private func markerRuntime() -> MarkerRuntime? {
        #if arch(arm64)
        let engineBundleName = "DCAEngine-arm64.app"
        #elseif arch(x86_64)
        let engineBundleName = "DCAEngine-x86_64.app"
        #else
        return nil
        #endif

        let bundledEngine = Bundle.main.bundleURL
            .appendingPathComponent("Contents/Helpers", isDirectory: true)
            .appendingPathComponent(engineBundleName, isDirectory: true)
            .appendingPathComponent("Contents/MacOS", isDirectory: true)
            .appendingPathComponent("DCAEngine", isDirectory: false)

        if FileManager.default.isExecutableFile(atPath: bundledEngine.path) {
            return MarkerRuntime(
                executableURL: bundledEngine,
                argumentPrefix: []
            )
        }

        #if DEBUG
        // Xcode development builds may use the source checkout before the
        // two distributable engines have been assembled. Release builds never
        // contain or depend on these development-only paths.
        let sourceFile = URL(fileURLWithPath: #filePath)
        let projectFolder = sourceFile
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        let markerFile = projectFolder.appendingPathComponent(
            "dca_script_marker.py"
        )
        let pythonCandidates = [
            projectFolder.appendingPathComponent(".venv/bin/python"),
            URL(fileURLWithPath: "/usr/local/bin/python3"),
            URL(fileURLWithPath: "/usr/bin/python3"),
        ]

        if FileManager.default.fileExists(atPath: markerFile.path),
           let python = pythonCandidates.first(where: {
               FileManager.default.isExecutableFile(atPath: $0.path)
           }) {
            return MarkerRuntime(
                executableURL: python,
                argumentPrefix: [markerFile.path]
            )
        }
        #endif

        return nil
    }

    private func markerEnvironment() -> [String: String] {
        var environment = ProcessInfo.processInfo.environment
        environment["HOME"] = FileManager.default
            .homeDirectoryForCurrentUser.path
        environment["PATH"] = "/usr/bin:/bin"
        environment["LANG"] = "en_US.UTF-8"
        environment["LC_ALL"] = "en_US.UTF-8"
        environment["PYTHONUTF8"] = "1"
        return environment
    }

    func markedOutputURL() -> URL {
        let scriptURL = URL(fileURLWithPath: scriptPath)
        let originalName = scriptURL.deletingPathExtension().lastPathComponent

        return URL(fileURLWithPath: outputFolder)
            .appendingPathComponent(
                "\(originalName)_marked_\(formattedToday()).pdf"
            )
    }

    func chooseOutputMode() -> String? {
        let outputURL = markedOutputURL()

        guard FileManager.default.fileExists(atPath: outputURL.path) else {
            return "replace"
        }

        let alert = NSAlert()
        alert.messageText = "A marked PDF already exists"
        alert.informativeText = "Save as New is recommended when adjusting the marking style. Replacing a PDF that is still open in Preview can temporarily show both versions together."
        alert.addButton(withTitle: "Save as New PDF (Recommended)")
        alert.addButton(withTitle: "Replace Existing PDF")
        alert.addButton(withTitle: "Cancel")

        switch alert.runModal() {
        case .alertFirstButtonReturn:
            return "new"
        case .alertSecondButtonReturn:
            let replacementAlert = NSAlert()
            replacementAlert.messageText = "Close the PDF before replacing it"
            replacementAlert.informativeText = "Preview keeps editable markings in memory. Close the existing marked PDF in Preview, then continue with the replacement."
            replacementAlert.addButton(withTitle: "Replace After Closing")
            replacementAlert.addButton(withTitle: "Cancel")

            return replacementAlert.runModal() == .alertFirstButtonReturn
                ? "replace"
                : nil
        default:
            return nil
        }
    }
    func generateMarkedScript(legendOverridesFile: String? = nil) {
        guard !templatePath.isEmpty,
              !scriptPath.isEmpty,
              !outputFolder.isEmpty else {
            removeLegendOverridesFile(legendOverridesFile)
            message = "Please choose a DCA template, script PDF, and output folder."
            return
        }

        if markSelectedPages {
            guard let firstPage = Int(startPage),
                  let lastPage = Int(endPage),
                  firstPage >= 1,
                  lastPage >= firstPage else {
                removeLegendOverridesFile(legendOverridesFile)
                message = "Enter a valid page range, for example 12 to 18."
                return
            }
        }
        guard let outputMode = chooseOutputMode() else {
            removeLegendOverridesFile(legendOverridesFile)
            message = "Export cancelled."
            return
        }
        let replacingExistingPDF = outputMode == "replace"
            && FileManager.default.fileExists(atPath: markedOutputURL().path)
        let generationStyle = selectedStyle
        isGenerating = true
        message = "Creating your marked script…"

        DispatchQueue.global(qos: .userInitiated).async {
            let resultFile = FileManager.default.temporaryDirectory
                .appendingPathComponent(
                    "DCA-Script-Marker-Result-\(UUID().uuidString).json"
                )
            defer {
                removeLegendOverridesFile(legendOverridesFile)
                try? FileManager.default.removeItem(at: resultFile)
            }

            guard let runtime = markerRuntime() else {
                DispatchQueue.main.async {
                    isGenerating = false
                    message = "This build is missing its bundled DCA marker engine. Please reinstall the app."
                }
                return
            }

            let process = Process()
            let output = Pipe()
            process.executableURL = runtime.executableURL
            process.environment = markerEnvironment()
            var arguments = runtime.argumentPrefix + [
                "--template", templatePath,
                "--script", scriptPath,
                "--output", outputFolder,
                "--output-mode", outputMode,
                "--result-json-file", resultFile.path,
                "--style", generationStyle,
                "--number-colour", numberColour.lowercased(),
                "--number-scale", scale(for: numberSize),
                "--number-font", numberFont,
                "--number-gap", numberGap(for: numberPosition),
                "--number-y-offset", numberVerticalOffset(for: numberVerticalPosition),
                "--state-colour", stateColour.lowercased(),
                "--state-scale", scale(for: stateSize),
                "--state-font", stateFont,
                "--state-position", statePosition,
                "--state-placement", "Beside Cue",
                "--page-state-text-colour", pageStateTextColour.lowercased(),
                "--page-state-scale", scale(for: pageStateTextSize),
                "--page-state-font", pageStateTextFont,
                "--page-state-border-colour", pageStateBorderColour.lowercased(),
                "--page-state-display", pageStateDisplayArgument(for: pageStateDisplay),
                "--legend-position", legendPosition,
            ]
            if markSelectedPages {
                arguments += [
                    "--start-page", startPage,
                    "--end-page", endPage,
                ]
            }

            if let legendOverridesFile {
                arguments += ["--legend-overrides-file", legendOverridesFile]
            }
            process.arguments = arguments
            process.standardOutput = output
            process.standardError = output

            do {
                try process.run()
                let data = output.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()
                let result = String(data: data, encoding: .utf8) ?? "No output received."
                let completionData = try? Data(contentsOf: resultFile)

                DispatchQueue.main.async {
                    let completionResult = completionData.flatMap {
                        try? JSONDecoder().decode(
                            MarkerCompletionResult.self,
                            from: $0
                        )
                    }
                    isGenerating = false
                    if process.terminationStatus == 0 {
                        NSWorkspace.shared.open(
                            URL(fileURLWithPath: outputFolder)
                        )
                        if replacingExistingPDF {
                            message = result + "\n\nReplacement complete. Close and reopen the PDF in Preview before reviewing it."
                        } else {
                            message = result
                        }
                        if let completionResult {
                            if completionResult.markedCount == 0
                                && generationStyle != "DCA State Legend" {
                                showZeroDCANumbersAlert(completionResult)
                            } else if completionResult.safetyLevel != "ok" {
                                showSafetyAlert(completionResult)
                            }
                        } else {
                            showSafetyUnavailableAlert()
                        }
                    } else {
                        message = "The marker could not finish:\n\(result)"
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    isGenerating = false
                    message = "Could not start the DCA marker engine: \(error.localizedDescription)"
                }
            }
        }
    }

    private func removeLegendOverridesFile(_ path: String?) {
        guard let path else { return }
        try? FileManager.default.removeItem(atPath: path)
    }

    func scale(for size: String) -> String {
        switch size {
        case "Small": return "0.9"
        case "Large": return "1.45"
        default: return "1.2"
        }
    }

    func formattedToday() -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: Date())
    }

    func numberGap(for position: String) -> String {
        switch position {
        case "Near Script": return "3"
        case "Far Left": return "40"
        default: return "16"
        }
    }
    func numberVerticalOffset(for position: String) -> String {
        switch position {
        case "Slightly Up": return "-3"
        case "Slightly Down": return "3"
        default: return "0"
        }
    }

    func pageStateDisplayArgument(for display: String) -> String {
        switch display {
        case "Off": return "off"
        case "Header Only": return "header"
        case "Footer Only": return "footer"
        default: return "both"
        }
    }
}

struct AnnotationStyleSheet: View {
    @Binding var numberColour: String
    @Binding var numberSize: String
    @Binding var numberFont: String
    @Binding var numberPosition: String
    @Binding var numberVerticalPosition: String
    @Binding var stateColour: String
    @Binding var stateSize: String
    @Binding var stateFont: String
    @Binding var statePosition: String
    @Binding var legendPosition: String
    let selectedStyle: String
    @Binding var pageStateDisplay: String
    @Binding var pageStateTextColour: String
    @Binding var pageStateTextSize: String
    @Binding var pageStateTextFont: String
    @Binding var pageStateBorderColour: String
    let cancel: () -> Void
    let continueAction: () -> Void

    private let colours = [
        "Red", "Blue", "Black", "Green",
        "Orange", "Purple", "Grey", "Brown"
    ]
    private let sizes = ["Small", "Medium", "Large"]
    private let numberFonts = ["Helvetica", "Times", "Courier"]
    private let stateFonts = ["PingFang SC", "Chinese System", "Helvetica", "Times", "Courier"]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 6) {
                Text("Annotation Style")
                    .font(.title2.bold())

                Text("Choose the appearance of DCA numbers and DCA State labels.")
                    .foregroundStyle(.secondary)
            }

            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    HStack(alignment: .top, spacing: 16) {
                        VStack(alignment: .leading, spacing: 10) {
                            StyleSection(
                                title: "DCA Numbers",
                                colour: $numberColour,
                                size: $numberSize,
                                font: $numberFont,
                                colours: colours,
                                sizes: sizes,
                                fonts: numberFonts
                            )

                            PickerRow(
                                title: "Horizontal Position",
                                selection: $numberPosition,
                                options: ["Near Script", "Standard", "Far Left"]
                            )
                            PickerRow(
                                title: "Vertical Position",
                                selection: $numberVerticalPosition,
                                options: [
                                    "Slightly Up",
                                    "Default",
                                    "Slightly Down"
                                ]
                            )
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)

                        Divider()

                        VStack(alignment: .leading, spacing: 10) {
                            StyleSection(
                                title: "DCA State / Snapshot / Scene",
                                colour: $stateColour,
                                size: $stateSize,
                                font: $stateFont,
                                colours: colours,
                                sizes: sizes,
                                fonts: stateFonts
                            )

                            PickerRow(
                                title: "Position",
                                selection: $statePosition,
                                options: ["Left Gutter", "Far from Script"]
                            )

                            if selectedStyle == "DCA State Legend" {
                                PickerRow(
                                    title: "Legend Position",
                                    selection: $legendPosition,
                                    options: ["Left Gutter", "Near Script"]
                                )
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    Divider()

                    VStack(alignment: .leading, spacing: 10) {
                        Text("DCA State Header & Footer")
                            .font(.headline)

                        PickerRow(
                            title: "Show Current DCA State",
                            selection: $pageStateDisplay,
                            options: [
                                "Off",
                                "Header Only",
                                "Footer Only",
                                "Header and Footer"
                            ]
                        )

                        HStack(alignment: .top, spacing: 16) {
                            VStack(alignment: .leading, spacing: 10) {
                                PickerRow(
                                    title: "Text Colour",
                                    selection: $pageStateTextColour,
                                    options: colours
                                )
                                PickerRow(
                                    title: "Text Size",
                                    selection: $pageStateTextSize,
                                    options: sizes
                                )
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)

                            Divider()

                            VStack(alignment: .leading, spacing: 10) {
                                PickerRow(
                                    title: "Text Font",
                                    selection: $pageStateTextFont,
                                    options: stateFonts
                                )
                                PickerRow(
                                    title: "Border Colour",
                                    selection: $pageStateBorderColour,
                                    options: colours
                                )
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        .disabled(pageStateDisplay == "Off")
                        .opacity(pageStateDisplay == "Off" ? 0.5 : 1)

                        Text("Chinese labels automatically use a compatible Chinese font.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.trailing, 8)
            }

            HStack {
                Spacer()
                Button("Cancel", action: cancel)
                Button("Continue", action: continueAction)
                    .buttonStyle(.borderedProminent)
            }
        }
        .padding(24)
        .frame(
            minWidth: 760,
            idealWidth: 800,
            maxWidth: 800,
            minHeight: 580,
            idealHeight: 650,
            maxHeight: 650
        )
    }
}

struct LegendDraft: Identifiable, Codable {
    let id: String
    let name: String
    var text: String

    enum CodingKeys: String, CodingKey {
        case id = "key"
        case name
        case text
    }
}

struct LegendEditorSheet: View {
    @Binding var drafts: [LegendDraft]
    let cancel: () -> Void
    let export: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Edit DCA State Legends")
                .font(.title2.bold())

            Text("Review or change each DCA membership list before creating the PDF.")
                .foregroundStyle(.secondary)

            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    ForEach($drafts) { $draft in
                        VStack(alignment: .leading, spacing: 6) {
                            Text(draft.name)
                                .font(.headline)
                            TextEditor(text: $draft.text)
                                .font(.system(size: 14))
                                .frame(minHeight: 110)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(.quaternary)
                                )
                        }
                    }
                }
            }

            HStack {
                Spacer()
                Button("Cancel", action: cancel)
                Button("Export Edited Legend", action: export)
                    .buttonStyle(.borderedProminent)
            }
        }
        .padding(28)
        .frame(width: 620, height: 620)
    }
}

struct HelpSheet: View {
    let close: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                Text("DCA Script Marker Help / 使用说明")
                    .font(.title2.bold())
                Spacer()
                Button("Done / 完成", action: close)
                    .buttonStyle(.borderedProminent)
            }

            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    HelpStep(
                        number: "1",
                        title: "Complete the DCA State template / 完成 DCA 状态表",
                        detail: "Copy the included Excel template from the DMG into your project folder. Add every dialogue character to Character List, then enter each state, start cue, start position, Page Hint, and DCA assignment in DCA States. For Page Hint, normally use the page number printed inside the script; use the PDF page position only when no printed page number exists. Save the completed copy before choosing it in the app.\n先把 DMG 内附带的 Excel 模板复制到项目文件夹。在 Character List 填写所有对白角色，再在 DCA States 填写状态、起始提示、开始位置、Page Hint 和 DCA 分配。Page Hint 通常填写剧本页面内印刷的页码；只有没有印刷页码时，才使用 PDF 页面位置。保存完成的副本后再在软件中选择。"
                    )
                    HelpStep(
                        number: "2",
                        title: "Choose your files / 选择文件",
                        detail: "Choose the Excel DCA State template, the original script PDF, and the folder where you want the marked PDF saved.\n选择 DCA 状态表 Excel、原始剧本 PDF，以及标注后 PDF 的保存文件夹。"
                    )
                    HelpStep(
                        number: "3",
                        title: "Choose a marking style / 选择标注方式",
                        detail: "All three styles create movable PDF annotations. Editable Full Marking marks every dialogue line. First Appearance Only marks each character's first cue in every DCA State. DCA State Legend creates an editable membership list. Page header/footer text and its border move or delete together.\n三种标注方式都会创建可移动的 PDF 标注。可编辑完整标注会标注每一句角色台词；仅首次出现会在每个 DCA 状态中标注每个角色的第一句台词；DCA 状态图例会创建可编辑的分配列表。页眉或页脚文字与边框会一起移动或删除。"
                    )
                    HelpStep(
                        number: "4",
                        title: "Optional: mark only selected pages / 可选：只标注指定页码",
                        detail: "Turn on Mark selected pages only when preparing only part of a script. This range always uses the PDF viewer's page position, counting the cover as page 1. It may differ from the page number printed inside the script.\n当只需要处理剧本的一部分时，打开此选项。这里始终使用 PDF 阅读器中的页面位置，并从封面作为第 1 页开始计算；它可能与剧本页面内印刷的页码不同。"
                    )
                    HelpStep(
                        number: "5",
                        title: "Generate and review / 生成并检查",
                        detail: "Choose annotation colours, fonts, sizes, and positions. Page DCA States can be Off, Header Only, Footer Only, or Header and Footer. Then generate the PDF and check the review report before rehearsal. If no DCA numbers are added, do not use the output; check the PDF text, layout, workbook names, state cue, and Page Hint.\n选择标注颜色、字体、大小和位置。页面 DCA 状态可以关闭、仅显示在页眉、仅显示在页脚，或同时显示在页眉和页脚。然后生成 PDF，并在排练前检查复核报告。如果没有添加任何 DCA 编号，请勿使用该输出，并检查 PDF 文字与排版、工作簿角色名称、状态提示和 Page Hint。"
                    )

                    Divider()

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Copyright © 2026 马斯琪 Siqi Ma")
                            .font(.footnote.weight(.semibold))
                        Text("Licensed under GNU AGPL v3 or later / 使用 GNU AGPL v3 或更高版本许可")
                            .font(.footnote)
                        Text("The exact source code and licences are included with every release package. / 每个发行版本均附带对应的完整源代码与许可文件。")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 4)
            }
        }
        .padding(30)
        .frame(width: 660, height: 560)
        .background(Color(red: 0.94, green: 0.96, blue: 0.98))
    }
}

struct HelpStep: View {
    let number: String
    let title: String
    let detail: String

    var body: some View {
        HStack(alignment: .top, spacing: 14) {
            Text(number)
                .font(.title3.bold())
                .foregroundStyle(.white)
                .frame(width: 30, height: 30)
                .background(.blue, in: Circle())

            VStack(alignment: .leading, spacing: 4) {
                Text(title).font(.headline)
                Text(detail).foregroundStyle(.secondary)
            }
        }
    }
}

struct StyleSection: View {
    let title: String
    @Binding var colour: String
    @Binding var size: String
    @Binding var font: String
    let colours: [String]
    let sizes: [String]
    let fonts: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title).font(.headline)

            PickerRow(title: "Colour", selection: $colour, options: colours)
            PickerRow(title: "Size", selection: $size, options: sizes)
            PickerRow(title: "Font", selection: $font, options: fonts)
        }
    }
}

struct PickerRow: View {
    let title: String
    @Binding var selection: String
    let options: [String]

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text(title)
                .font(.body)
                .lineLimit(2)
                .frame(width: 155, alignment: .leading)
            Picker(title, selection: $selection) {
                ForEach(options, id: \.self) { option in
                    Text(option).tag(option)
                }
            }
            .labelsHidden()
            .fixedSize(horizontal: true, vertical: false)
            .frame(width: 155, alignment: .leading)
            Spacer(minLength: 0)
        }
    }
}

struct FileRow: View {
    let title: String
    @Binding var path: String
    let buttonTitle: String
    let action: () -> Void

    var body: some View {
        HStack {
            Text(title)
                .fontWeight(.semibold)
                .frame(width: 145, alignment: .leading)

            TextField("No file selected", text: $path)
                .textFieldStyle(.roundedBorder)

            Button(buttonTitle, action: action)
                .buttonStyle(.bordered)
        }
    }
}

#if DEBUG
#Preview {
    ContentView()
}
#endif
