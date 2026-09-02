// Copyright © 2026 马斯琪 Siqi Ma
// SPDX-License-Identifier: AGPL-3.0-or-later

import SwiftUI
import AppKit
import UniformTypeIdentifiers
import Foundation
import Combine

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

private struct RoleMappingRow: Identifiable, Decodable {
    let dca: String
    let performer: String
    let roles: [String]

    var id: String {
        "\(dca)|\(performer)|\(roles.joined(separator: "|"))"
    }
}

private struct RoleMappingState: Identifiable, Decodable {
    let id: String
    let key: String
    let name: String
    let pageHint: String
    let rows: [RoleMappingRow]

    private enum CodingKeys: String, CodingKey {
        case id
        case key
        case name
        case pageHint = "page_hint"
        case rows
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        key = try container.decode(String.self, forKey: .key)
        name = try container.decode(String.self, forKey: .name)
        pageHint = try container.decodeIfPresent(
            String.self,
            forKey: .pageHint
        ) ?? ""
        rows = try container.decode([RoleMappingRow].self, forKey: .rows)
    }
}

private struct RoleMappingSearchAppearance: Identifiable, Equatable {
    let stateID: String
    let stateName: String
    let dca: String

    var id: String {
        "\(stateID)|\(dca)"
    }
}

private struct RoleMappingSearchResult: Identifiable {
    let performer: String
    let roles: [String]
    var appearances: [RoleMappingSearchAppearance]

    var id: String {
        performer.folding(
            options: [.caseInsensitive, .diacriticInsensitive],
            locale: .current
        )
    }
}

@MainActor
private final class RoleMappingPanelModel: ObservableObject {
    @Published var states: [RoleMappingState] = []
    @Published var selectedStateID = ""
    @Published var searchText = ""
    @Published var staysOnTop = true
    @Published var workbookName = ""
    @Published var language = AppLanguage.systemDefault

    func load(
        states: [RoleMappingState],
        workbookName: String,
        language: AppLanguage
    ) {
        self.states = states
        self.workbookName = workbookName
        self.language = language
        selectedStateID = (
            states.first(where: { !$0.rows.isEmpty }) ?? states.first
        )?.id ?? ""
        searchText = ""
    }
}

@MainActor
private final class RoleMappingPanelController: NSObject, ObservableObject {
    let model = RoleMappingPanelModel()
    private var panel: NSPanel?

    func show(
        states: [RoleMappingState],
        workbookName: String,
        language: AppLanguage
    ) {
        model.load(
            states: states,
            workbookName: workbookName,
            language: language
        )

        if panel == nil {
            let rootView = RoleMappingPanelView(
                model: model,
                close: { [weak self] in self?.close() },
                setStaysOnTop: { [weak self] enabled in
                    self?.setStaysOnTop(enabled)
                }
            )
            let hostingController = NSHostingController(rootView: rootView)
            let newPanel = NSPanel(
                contentRect: NSRect(x: 0, y: 0, width: 600, height: 520),
                styleMask: [
                    .titled,
                    .closable,
                    .miniaturizable,
                    .resizable,
                    .utilityWindow,
                ],
                backing: .buffered,
                defer: false
            )
            newPanel.title = language.label("DCA States Inspector")
            newPanel.contentViewController = hostingController
            newPanel.isFloatingPanel = true
            newPanel.hidesOnDeactivate = false
            newPanel.isReleasedWhenClosed = false
            newPanel.level = .floating
            newPanel.collectionBehavior = [
                .canJoinAllSpaces,
                .fullScreenAuxiliary,
            ]
            newPanel.minSize = NSSize(width: 480, height: 360)
            newPanel.setFrameAutosaveName(
                "DCA Script Marker DCA States Inspector"
            )
            panel = newPanel
        }

        panel?.title = language.label("DCA States Inspector")

        setStaysOnTop(model.staysOnTop)
        panel?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func close() {
        panel?.orderOut(nil)
    }

    func updateLanguage(_ language: AppLanguage) {
        model.language = language
        panel?.title = language.label("DCA States Inspector")
    }

    private func setStaysOnTop(_ enabled: Bool) {
        model.staysOnTop = enabled
        panel?.level = enabled ? .floating : .normal
    }
}

private struct RoleMappingPanelView: View {
    @ObservedObject var model: RoleMappingPanelModel
    let close: () -> Void
    let setStaysOnTop: (Bool) -> Void

    private func t(_ english: String, _ chinese: String) -> String {
        model.language.text(english, chinese)
    }

    private var selectedState: RoleMappingState? {
        model.states.first { $0.id == model.selectedStateID }
    }

    private var selectedPageHint: String {
        let value = selectedState?.pageHint.trimmingCharacters(
            in: .whitespacesAndNewlines
        ) ?? ""
        return value.isEmpty ? "—" : value
    }

    private var searchQuery: String {
        model.searchText
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .folding(options: [.caseInsensitive, .diacriticInsensitive], locale: .current)
    }

    private var isSearchingAllStates: Bool {
        !searchQuery.isEmpty
    }

    private var selectedStateRows: [RoleMappingRow] {
        selectedState?.rows ?? []
    }

    private var selectedStateIndex: Int? {
        model.states.firstIndex { $0.id == model.selectedStateID }
    }

    private var canSelectPreviousState: Bool {
        guard let selectedStateIndex else { return false }
        return selectedStateIndex > model.states.startIndex
    }

    private var canSelectNextState: Bool {
        guard let selectedStateIndex else { return false }
        return selectedStateIndex < model.states.index(before: model.states.endIndex)
    }

    private func selectState(offset: Int) {
        guard let selectedStateIndex else { return }
        let newIndex = selectedStateIndex + offset
        guard model.states.indices.contains(newIndex) else { return }
        model.selectedStateID = model.states[newIndex].id
    }

    private var globalSearchResults: [RoleMappingSearchResult] {
        guard isSearchingAllStates else { return [] }

        var resultIndexes: [String: Int] = [:]
        var results: [RoleMappingSearchResult] = []

        for state in model.states {
            for row in state.rows {
                let performerKey = row.performer.folding(
                    options: [.caseInsensitive, .diacriticInsensitive],
                    locale: .current
                )
                let searchableText = (
                    "\(row.performer) \(row.roles.joined(separator: " "))"
                ).folding(
                    options: [.caseInsensitive, .diacriticInsensitive],
                    locale: .current
                )

                guard searchableText.contains(searchQuery) else { continue }

                let appearance = RoleMappingSearchAppearance(
                    stateID: state.id,
                    stateName: state.name,
                    dca: row.dca
                )
                if let resultIndex = resultIndexes[performerKey] {
                    if !results[resultIndex].appearances.contains(appearance) {
                        results[resultIndex].appearances.append(appearance)
                    }
                } else {
                    resultIndexes[performerKey] = results.count
                    results.append(
                        RoleMappingSearchResult(
                            performer: row.performer,
                            roles: row.roles,
                            appearances: [appearance]
                        )
                    )
                }
            }
        }

        return results
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 4) {
                Text(model.language.label("DCA States Inspector"))
                    .font(.title2.bold())
                Text(t(
                    "Keep this window beside Preview to check every active DCA Name and any other script characters played.",
                    "将此窗口放在 Preview 旁边，查看所有启用的 DCA Name 及其饰演的其他剧本角色。"
                ))
                    .font(.callout)
                    .foregroundStyle(.secondary)
                Text(model.workbookName)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .truncationMode(.middle)
            }

            HStack(alignment: .bottom, spacing: 14) {
                Button {
                    selectState(offset: -1)
                } label: {
                    Label(
                        model.language.label("Previous"),
                        systemImage: "chevron.left"
                    )
                        .frame(width: 92)
                }
                .disabled(!canSelectPreviousState)
                .help(t("Show the previous DCA State", "显示上一个 DCA 状态"))

                VStack(spacing: 4) {
                    Text(model.language.label("DCA State"))
                        .font(.caption.bold())
                        .foregroundStyle(.secondary)

                    Picker("", selection: $model.selectedStateID) {
                        ForEach(model.states) { state in
                            Text(state.name).tag(state.id)
                        }
                    }
                    .labelsHidden()
                    .pickerStyle(.menu)
                    .frame(maxWidth: .infinity)
                }
                .frame(maxWidth: .infinity)

                VStack(spacing: 4) {
                    Text(model.language.label("Page Hint"))
                        .font(.caption.bold())
                        .foregroundStyle(.secondary)

                    Text(selectedPageHint)
                        .font(.body.weight(.semibold))
                        .lineLimit(1)
                        .textSelection(.enabled)
                        .frame(width: 82, height: 22)
                        .background(
                            Color.secondary.opacity(0.08),
                            in: RoundedRectangle(cornerRadius: 5)
                        )
                }

                Button {
                    selectState(offset: 1)
                } label: {
                    Label(
                        model.language.label("Next"),
                        systemImage: "chevron.right"
                    )
                        .labelStyle(.titleAndIcon)
                        .frame(width: 92)
                }
                .disabled(!canSelectNextState)
                .help(t("Show the next DCA State", "显示下一个 DCA 状态"))
            }

            TextField(
                t(
                    "Search all states by DCA Name or other character",
                    "按 DCA Name 或其他剧本角色搜索全部状态"
                ),
                text: $model.searchText
            )
            .textFieldStyle(.roundedBorder)

            if isSearchingAllStates {
                Label(
                    t(
                        "Whole-project search • \(globalSearchResults.count) DCA Name(s)",
                        "整个项目搜索 • \(globalSearchResults.count) 个 DCA Name"
                    ),
                    systemImage: "magnifyingglass"
                )
                .font(.caption)
                .foregroundStyle(.secondary)
            }

            VStack(spacing: 0) {
                HStack(spacing: 12) {
                    if isSearchingAllStates {
                        Text(t(
                            "DCA Name",
                            "DCA Name"
                        ))
                            .fixedSize(horizontal: false, vertical: true)
                            .frame(width: 100, alignment: .leading)
                        Text(t(
                            "Other Script Characters Played",
                            "饰演的其他剧本角色"
                        ))
                            .fixedSize(horizontal: false, vertical: true)
                            .frame(width: 180, alignment: .leading)
                        Text(model.language.label("DCA States"))
                            .frame(maxWidth: .infinity, alignment: .leading)
                    } else {
                        Text("DCA")
                            .frame(width: 48, alignment: .leading)
                        Text(t(
                            "DCA Name",
                            "DCA Name"
                        ))
                            .fixedSize(horizontal: false, vertical: true)
                            .frame(width: 140, alignment: .leading)
                        Text(t(
                            "Other Script Characters Played",
                            "饰演的其他剧本角色"
                        ))
                            .fixedSize(horizontal: false, vertical: true)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .font(.caption.bold())
                .foregroundStyle(.secondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 9)
                .background(Color.secondary.opacity(0.08))

                Divider()

                if model.states.isEmpty {
                    emptyMessage(
                        t(
                            "No usable DCA States were found in this project.",
                            "此项目中没有可用的 DCA 状态。"
                        )
                    )
                } else if isSearchingAllStates && globalSearchResults.isEmpty {
                    emptyMessage(t(
                        "No mapping matches this project search.",
                        "项目中没有符合搜索条件的映射。"
                    ))
                } else if isSearchingAllStates {
                    ScrollView {
                        LazyVStack(spacing: 0) {
                            ForEach(globalSearchResults) { result in
                                HStack(alignment: .top, spacing: 12) {
                                    Text(result.performer)
                                        .fontWeight(.semibold)
                                        .foregroundStyle(.blue)
                                        .frame(width: 100, alignment: .leading)
                                    VStack(alignment: .leading, spacing: 3) {
                                        ForEach(result.roles, id: \.self) { role in
                                            Text(role)
                                                .frame(
                                                    maxWidth: .infinity,
                                                    alignment: .leading
                                                )
                                                .textSelection(.enabled)
                                        }
                                    }
                                    .frame(
                                        width: 180,
                                        alignment: .leading
                                    )
                                    VStack(alignment: .leading, spacing: 3) {
                                        ForEach(result.appearances) { appearance in
                                            Text(
                                                "\(appearance.stateName) · DCA \(appearance.dca)"
                                            )
                                            .frame(
                                                maxWidth: .infinity,
                                                alignment: .leading
                                            )
                                            .textSelection(.enabled)
                                        }
                                    }
                                    .frame(
                                        maxWidth: .infinity,
                                        alignment: .leading
                                    )
                                }
                                .padding(.horizontal, 12)
                                .padding(.vertical, 10)

                                Divider()
                            }
                        }
                    }
                } else if selectedState?.rows.isEmpty != false {
                    emptyMessage(
                        t(
                            "This DCA State has no active DCA assignments.",
                            "此 DCA 状态没有启用的 DCA 分配。"
                        )
                    )
                } else {
                    ScrollView {
                        LazyVStack(spacing: 0) {
                            ForEach(selectedStateRows) { row in
                                HStack(alignment: .top, spacing: 12) {
                                    Text(row.dca)
                                        .font(.system(.body, design: .monospaced).bold())
                                        .foregroundStyle(.blue)
                                        .frame(width: 48, alignment: .leading)
                                    Text(row.performer)
                                        .fontWeight(.semibold)
                                        .frame(width: 140, alignment: .leading)
                                    VStack(alignment: .leading, spacing: 3) {
                                        ForEach(row.roles, id: \.self) { role in
                                            Text(role)
                                                .frame(
                                                    maxWidth: .infinity,
                                                    alignment: .leading
                                                )
                                                .textSelection(.enabled)
                                        }
                                    }
                                    .frame(
                                        maxWidth: .infinity,
                                        alignment: .leading
                                    )
                                }
                                .padding(.horizontal, 12)
                                .padding(.vertical, 10)

                                Divider()
                            }
                        }
                    }
                }
            }
            .background(.background)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.secondary.opacity(0.25))
            )

            HStack {
                Toggle(
                    t("Stay above PDF windows", "保持在 PDF 窗口上方"),
                    isOn: Binding(
                        get: { model.staysOnTop },
                        set: { setStaysOnTop($0) }
                    )
                )
                .toggleStyle(.checkbox)

                Spacer()

                Text(
                    isSearchingAllStates
                        ? t(
                            "Each matching DCA Name is shown once. Clear the search to return to the selected state.",
                            "每个匹配的 DCA Name 只显示一次。清空搜索即可返回当前状态。"
                        )
                        : t(
                            "Use Previous, Next, or the state menu as you move through the PDF.",
                            "翻阅 PDF 时，请使用上一个、下一个或状态菜单切换。"
                        )
                )
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Button(model.language.label("Close"), action: close)
                    .keyboardShortcut(.cancelAction)
            }
        }
        .padding(20)
        .frame(minWidth: 480, minHeight: 360)
        .background(Color(red: 0.94, green: 0.96, blue: 0.98))
    }

    @ViewBuilder
    private func emptyMessage(_ text: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: "person.2")
                .font(.title2)
                .foregroundStyle(.secondary)
            Text(text)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(24)
    }
}

struct ContentView: View {
    @AppStorage("appLanguage") private var appLanguageRaw = (
        AppLanguage.systemDefault.rawValue
    )
    @State private var templatePath = ""
    @State private var project = DCAProjectDocument.newProject()
    @State private var projectPath = ""
    @State private var ignoredProjectAdvisorySignatures: Set<String> = []
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
    @State private var showPerformerRoleMapping = false
    @State private var legendDrafts: [LegendDraft] = []
    @State private var showLegendEditor = false
    @State private var showHelp = false
    @State private var isLoadingRoleMapping = false
    @State private var isImportingProject = false
    @State private var isExportingProject = false
    @State private var showProjectEditor = false
    @StateObject private var roleMappingPanelController = (
        RoleMappingPanelController()
    )

    let styles = [
        "Editable Full Marking",
        "First Appearance Only",
        "DCA State Legend"
    ]

    private var appLanguage: AppLanguage {
        AppLanguage(rawValue: appLanguageRaw) ?? .english
    }

    private func t(_ english: String, _ chinese: String) -> String {
        appLanguage.text(english, chinese)
    }

    private var missingEngineMessage: String {
        t(
            "This build is missing its bundled DCA marker engine. Please reinstall the app.",
            "此版本缺少内置的 DCA 标注引擎。请重新安装软件。"
        )
    }

    var body: some View {
        VStack(spacing: 22) {
            ZStack(alignment: .top) {
                HStack(alignment: .top) {
                    Button {
                        openUserGuide()
                    } label: {
                        Label(
                            appLanguage.label("User Guide"),
                            systemImage: "book.closed"
                        )
                    }
                    .buttonStyle(.bordered)
                    .tint(.blue)
                    .help(t(
                        "Open the complete bilingual PDF user guide",
                        "打开完整的双语 PDF 使用手册"
                    ))

                    Spacer()

                    Picker(
                        t("Language", "语言"),
                        selection: $appLanguageRaw
                    ) {
                        ForEach(AppLanguage.allCases) { language in
                            Text(language.menuTitle).tag(language.rawValue)
                        }
                    }
                    .labelsHidden()
                    .pickerStyle(.menu)
                    .frame(width: 112)
                    .help(t(
                        "Choose the app language",
                        "选择软件界面语言"
                    ))

                    Button {
                        showHelp = true
                    } label: {
                        Label(
                            appLanguage.label("Help"),
                            systemImage: "questionmark.circle"
                        )
                    }
                    .buttonStyle(.bordered)
                    .tint(.blue)
                    .help(t(
                        "Open the DCA Script Marker help guide",
                        "打开 DCA Script Marker 帮助"
                    ))
                }

                VStack(alignment: .center) {
                    Text("DCA Script Marker")
                        .font(.system(size: 28, weight: .bold))

                    Text(t(
                        "Build, edit, and mark a complete DCA project on your Mac.",
                        "在 Mac 上创建、编辑并标注完整的 DCA 项目。"
                    ))
                        .foregroundStyle(.secondary)
                }
            }
            .frame(minHeight: 50)

            VStack(spacing: 14) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(alignment: .top, spacing: 8) {
                        Text(appLanguage.label("DCA Project"))
                            .font(.system(size: 16, weight: .bold))
                            .frame(width: 135, alignment: .leading)

                        VStack(alignment: .leading, spacing: 8) {
                            HStack(spacing: 8) {
                                Text(
                                    projectPath.isEmpty
                                        ? t(
                                            "Create a project or import an existing Excel workbook",
                                            "新建项目或导入已有的 Excel 工作簿"
                                        )
                                        : projectPath
                                )
                                .foregroundStyle(
                                    projectPath.isEmpty ? .secondary : .primary
                                )
                                .lineLimit(1)
                                .truncationMode(.middle)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, 10)
                                .frame(height: 30)
                                .background(
                                    Color.secondary.opacity(0.08),
                                    in: RoundedRectangle(cornerRadius: 6)
                                )

                                Button(action: createNewProject) {
                                    Text(appLanguage.label("New"))
                                        .frame(width: 78)
                                }
                                .buttonStyle(.bordered)

                                Button(action: openProject) {
                                    Text(appLanguage.label("Open"))
                                        .frame(width: 78)
                                }
                                .buttonStyle(.bordered)

                                Button {
                                    importExcelProject()
                                } label: {
                                    Text(
                                        isImportingProject
                                            ? t("Importing…", "正在导入…")
                                            : appLanguage.label("Import Excel")
                                    )
                                    .frame(width: 78)
                                }
                                .buttonStyle(.bordered)
                                .disabled(isImportingProject)
                            }

                            HStack(spacing: 10) {
                                Button {
                                    showProjectEditor = true
                                } label: {
                                    HStack(spacing: 10) {
                                        Image(systemName: "square.and.pencil")

                                        VStack(alignment: .leading, spacing: 2) {
                                            Text(t(
                                                "Edit Character List and DCA States",
                                                "编辑 Character List 和 DCA States"
                                            ))
                                                .font(.system(size: 15, weight: .bold))
                                            Text(t(
                                                "Main project setup",
                                                "主要项目设置"
                                            ))
                                                .font(.system(size: 11, weight: .semibold))
                                                .opacity(0.88)
                                        }

                                        Spacer()
                                        Image(systemName: "chevron.right")
                                    }
                                    .foregroundStyle(.white)
                                    .padding(.horizontal, 14)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 46)
                                }
                                .buttonStyle(.plain)
                                .background {
                                    RoundedRectangle(cornerRadius: 12)
                                        .fill(
                                            LinearGradient(
                                                colors: [.blue, .cyan],
                                                startPoint: .leading,
                                                endPoint: .trailing
                                            )
                                        )
                                }
                                .overlay {
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(.white.opacity(0.18), lineWidth: 1)
                                }
                                .shadow(color: .blue.opacity(0.24), radius: 6, y: 2)
                                .opacity(projectPath.isEmpty ? 0.52 : 1)
                                .disabled(projectPath.isEmpty)

                                if !projectPath.isEmpty {
                                    Text(project.name)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                        .lineLimit(1)
                                        .truncationMode(.tail)
                                        .frame(maxWidth: 145, alignment: .trailing)
                                }

                                Button {
                                    exportProjectExcel()
                                } label: {
                                    Text(
                                        isExportingProject
                                            ? t("Exporting…", "正在导出…")
                                            : appLanguage.label("Export Excel")
                                    )
                                    .frame(width: 78)
                                }
                                .buttonStyle(.bordered)
                                .disabled(
                                    projectPath.isEmpty || isExportingProject
                                )
                                .help(
                                    t(
                                        "Export the current DCA project as an Excel workbook",
                                        "将当前 DCA 项目导出为 Excel 工作簿"
                                    )
                                )
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }

                FileRow(
                    title: "Script PDF",
                    path: $scriptPath,
                    buttonTitle: "Choose PDF"
                ) {
                    scriptPath = chooseFile(
                        allowedTypes: ["pdf"]
                    )
                    if !scriptPath.isEmpty && !projectPath.isEmpty {
                        project.scriptPath = scriptPath
                        saveCurrentProject()
                    }
                }

                VStack(alignment: .leading, spacing: 3) {
                    Text(t(
                        "Use a text-based PDF: you should be able to select or copy words from the script. Scanned or image-only PDFs are not supported.",
                        "请使用可选择或复制文字的文本型 PDF。扫描版或仅图片的 PDF 暂不支持。"
                    ))
                }
                .font(.caption)
                .foregroundStyle(.secondary)

                FileRow(
                    title: "Output Folder",
                    path: $outputFolder,
                    buttonTitle: "Choose Folder"
                ) {
                    outputFolder = chooseFolder()
                    if !outputFolder.isEmpty && !projectPath.isEmpty {
                        project.outputFolder = outputFolder
                        saveCurrentProject()
                    }
                }
            }

            VStack(alignment: .leading, spacing: 8) {
                Toggle(
                    t("Mark selected pages only", "仅标注指定页码"),
                    isOn: $markSelectedPages
                )
                    .font(.headline)

                if markSelectedPages {
                    HStack {
                        Text(t("From page", "从第"))
                        TextField("1", text: $startPage)
                            .frame(width: 60)
                        Text(t("to", "页到第"))
                        TextField("Last", text: $endPage)
                            .frame(width: 60)
                        Text(t("(PDF page numbers)", "页（PDF 页码）"))
                            .foregroundStyle(.secondary)
                    }
                    .textFieldStyle(.roundedBorder)
                }

                VStack(alignment: .leading, spacing: 3) {
                    Text(t(
                        "Important: Excel Page Hint normally uses the page number printed inside the script. A selected-page range always uses the PDF viewer's page position, counting the cover as page 1.",
                        "重要：Excel 的 Page Hint 通常填写剧本页面内印刷的页码；“仅标注指定页码”始终使用 PDF 阅读器中的页面位置，并从封面作为第 1 页开始计算。"
                    ))
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }

            HStack(alignment: .top, spacing: 28) {
                VStack(alignment: .leading, spacing: 12) {
                    Text(appLanguage.label("Choose Marking Style"))
                        .font(.system(size: 16, weight: .bold))

                    ForEach(styles, id: \.self) { style in
                        VStack(alignment: .leading, spacing: 5) {
                            Button {
                                selectedStyle = style
                            } label: {
                                HStack {
                                    Text(appLanguage.label(style))
                                        .font(.system(size: 15, weight: .semibold))
                                    Spacer()
                                    if selectedStyle == style {
                                        Image(systemName: "checkmark.circle.fill")
                                    }
                                }
                                .foregroundStyle(
                                    markingStyleTextColour(for: style)
                                )
                                .frame(maxWidth: .infinity)
                                .frame(height: 44)
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(markingStyleColour(for: style))
                            .shadow(
                                color: selectedStyle == style
                                    ? markingStyleColour(for: style).opacity(0.16)
                                    : .clear,
                                radius: 5,
                                y: 2
                            )

                            Text(helpText(for: style))
                                .font(.system(size: 12.5))
                                .foregroundStyle(.secondary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .frame(width: 500, alignment: .leading)

                Spacer(minLength: 12)

                VStack(spacing: 12) {
                    Button {
                        guard !projectPath.isEmpty,
                              !scriptPath.isEmpty,
                              !outputFolder.isEmpty else {
                            message = t(
                                "Please create or open a DCA project, then choose a script PDF and output folder.",
                                "请先新建或打开 DCA 项目，然后选择剧本 PDF 和输出文件夹。"
                            )
                            return
                        }
                        saveCurrentProject()
                        guard project.blockingValidationIssues(
                            for: appLanguage
                        ).isEmpty else {
                            showProjectValidationAlert()
                            return
                        }
                        guard confirmProjectAdvisories() else { return }
                        showAnnotationStyle = true
                    } label: {
                        VStack(spacing: 10) {
                            ZStack {
                                Image(systemName: "lightbulb.max.fill")
                                    .font(.system(size: 38, weight: .semibold))
                                    .foregroundStyle(.yellow)
                                    .shadow(
                                        color: .yellow.opacity(0.9),
                                        radius: 7
                                    )

                                Image(systemName: "sparkles")
                                    .font(.system(size: 16, weight: .bold))
                                    .foregroundStyle(.white)
                                    .offset(x: 30, y: -21)
                            }
                            .frame(height: 44)
                            Text(
                                isGenerating
                                    ? t("Generating…", "正在生成…")
                                    : t(
                                        "Generate\nMarked Script",
                                        "生成标注剧本"
                                    )
                            )
                                .font(.system(size: 18, weight: .bold))
                                .multilineTextAlignment(.center)
                        }
                        .foregroundStyle(.white)
                        .frame(width: 168, height: 168)
                    }
                    .buttonStyle(.plain)
                    .background(
                        Color.green,
                        in: RoundedRectangle(cornerRadius: 22)
                    )
                    .shadow(color: .green.opacity(0.25), radius: 7, y: 3)
                    .disabled(isGenerating)

                    if isGenerating {
                        HStack(spacing: 8) {
                            ProgressView()
                                .progressViewStyle(.linear)
                                .frame(width: 130)
                                .tint(.green)
                            Text(t("Marking…", "正在标注…"))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .transition(.opacity)
                    }

                    Divider()

                    Text(
                        t(
                            "Open the floating DCA reference while reviewing the PDF.",
                            "阅读 PDF 时打开可悬浮的 DCA 对照窗口。"
                        )
                    )
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)

                    Button {
                        loadRoleMappingInspector()
                    } label: {
                        Label(
                            isLoadingRoleMapping
                                ? t("Loading…", "正在载入…")
                                : appLanguage.label("DCA States"),
                            systemImage: "list.number"
                        )
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 48)
                    }
                    .buttonStyle(.plain)
                    .background(
                        Color.indigo,
                        in: RoundedRectangle(cornerRadius: 16)
                    )
                    .overlay {
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(.white.opacity(0.16), lineWidth: 1)
                    }
                    .shadow(color: .indigo.opacity(0.24), radius: 6, y: 2)
                    .opacity(isLoadingRoleMapping ? 0.68 : 1)
                    .disabled(isLoadingRoleMapping)
                    .help(
                        t(
                            "Keep every active DCA Name and its other script characters visible beside the PDF",
                            "在 PDF 旁持续显示当前启用的 DCA Name 及其其他剧本角色"
                        )
                    )
                }
                .frame(width: 235)
                .animation(.easeInOut(duration: 0.2), value: isGenerating)
            }
            .padding(.top, 10)

            if !message.isEmpty {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
        .padding(32)
        .frame(
            minWidth: 980,
            idealWidth: 1040,
            minHeight: 680,
            idealHeight: 740
        )
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
                showPerformerRoleMapping: $showPerformerRoleMapping,
                cancel: { showAnnotationStyle = false },
                continueAction: {
                    showAnnotationStyle = false
                    saveCurrentProject()
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
        .sheet(isPresented: $showProjectEditor) {
            DCAProjectEditor(
                project: $project,
                ignoredAdvisorySignatures: $ignoredProjectAdvisorySignatures,
                projectPath: projectPath,
                save: {
                    saveCurrentProject(capturingInterface: false)
                },
                exportExcel: { exportProjectExcel() },
                close: { showProjectEditor = false }
            )
        }
        .onReceive(
            NotificationCenter.default.publisher(
                for: .openDCAScriptMarkerHelp
            )
        ) { _ in
            showHelp = true
        }
        .onChange(of: appLanguageRaw) { _ in
            roleMappingPanelController.updateLanguage(appLanguage)
        }
        .onChange(of: projectPath) { _ in
            ignoredProjectAdvisorySignatures.removeAll()
        }
        .environment(\.appLanguage, appLanguage)
        .environment(\.locale, appLanguage.locale)
    }

    func helpText(for style: String) -> String {
        switch style {
        case "Editable Full Marking":
            return t(
                "Mark every dialogue line with an editable DCA number.",
                "为每句对白添加可编辑的 DCA 编号。"
            )
        case "First Appearance Only":
            return t(
                "Mark each character's first cue in every DCA State.",
                "仅标注每个 DCA 状态中角色的首次台词。"
            )
        default:
            return t(
                "Create an editable DCA membership list for each state.",
                "为每个状态创建可编辑的 DCA 分配列表。"
            )
        }
    }

    private func markingStyleColour(for style: String) -> Color {
        switch style {
        case "Editable Full Marking":
            return Color(red: 0.58, green: 0.75, blue: 0.88)
        case "First Appearance Only":
            return Color(red: 0.94, green: 0.84, blue: 0.58)
        default:
            return Color(red: 0.90, green: 0.70, blue: 0.75)
        }
    }

    private func markingStyleTextColour(for style: String) -> Color {
        .black.opacity(0.76)
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

    private func projectSaveURL(suggestedName: String) -> URL? {
        let panel = NSSavePanel()
        panel.title = t(
            "Save DCA Script Marker Project",
            "保存 DCA Script Marker 项目"
        )
        panel.prompt = appLanguage.label("Save Project")
        panel.canCreateDirectories = true
        panel.nameFieldStringValue = suggestedName.hasSuffix(".dcamarker")
            ? suggestedName
            : "\(suggestedName).dcamarker"
        if let projectType = UTType(filenameExtension: "dcamarker") {
            panel.allowedContentTypes = [projectType]
        }
        return panel.runModal() == .OK ? panel.url : nil
    }

    private func automaticImportedProjectURL(excelPath: String) -> URL {
        let excelURL = URL(fileURLWithPath: excelPath)
        let folderURL = excelURL.deletingLastPathComponent()
        let baseName = excelURL.deletingPathExtension().lastPathComponent
        var copyNumber = 1

        while true {
            let filename = copyNumber == 1
                ? "\(baseName).dcamarker"
                : "\(baseName) \(copyNumber).dcamarker"
            let candidate = folderURL.appendingPathComponent(filename)
            if !FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            copyNumber += 1
        }
    }

    private func createNewProject() {
        guard let url = projectSaveURL(
            suggestedName: "Untitled DCA Project"
        ) else {
            return
        }

        var newProject = DCAProjectDocument.newProject()
        newProject.name = url.deletingPathExtension().lastPathComponent
        newProject.scriptPath = scriptPath
        newProject.outputFolder = outputFolder
        project = newProject
        projectPath = url.path
        templatePath = ""
        applyProjectToInterface()
        saveCurrentProject()
        roleMappingPanelController.close()
        showProjectEditor = true
        message = t(
            "New Version 2 project created.",
            "已新建 Version 2 项目。"
        )
    }

    private func openProject() {
        let panel = NSOpenPanel()
        panel.title = t(
            "Open DCA Script Marker Project",
            "打开 DCA Script Marker 项目"
        )
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        if let projectType = UTType(filenameExtension: "dcamarker") {
            panel.allowedContentTypes = [projectType]
        }
        guard panel.runModal() == .OK, let url = panel.url else { return }

        do {
            let data = try Data(contentsOf: url)
            var openedProject = try JSONDecoder().decode(
                DCAProjectDocument.self,
                from: data
            )
            let needsConversion = openedProject.needsAssignmentConversion
            openedProject.normalise()
            let openedURL = needsConversion
                ? try openedProject.writeConvertedCopy(beside: url)
                : url
            project = openedProject
            projectPath = openedURL.path
            templatePath = openedProject.sourceExcelPath
            applyProjectToInterface()
            roleMappingPanelController.close()
            message = needsConversion
                ? t(
                    "Opened converted copy: \(openedURL.lastPathComponent). Original unchanged; review the DCA cells before generating.",
                    "已打开转换副本：\(openedURL.lastPathComponent)。原文件保持不变；请在生成前检查 DCA 单元格。"
                )
                : t(
                    "Project opened: \(openedProject.name)",
                    "已打开项目：\(openedProject.name)"
                )
        } catch {
            showProjectFileError(
                title: t("Could not open project", "无法打开项目"),
                error: error
            )
        }
    }

    private func importExcelProject() {
        let excelPath = chooseFile(allowedTypes: ["xlsx"])
        guard !excelPath.isEmpty else { return }
        guard let runtime = markerRuntime() else {
            message = missingEngineMessage
            return
        }

        isImportingProject = true
        message = t(
            "Importing the Excel workbook…",
            "正在导入 Excel 工作簿…"
        )
        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            let output = Pipe()
            process.executableURL = runtime.executableURL
            process.arguments = runtime.argumentPrefix + [
                "--template", excelPath,
                "--import-excel",
            ]
            process.environment = markerEnvironment()
            process.standardOutput = output
            process.standardError = output

            do {
                try process.run()
                let data = output.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()
                guard process.terminationStatus == 0 else {
                    let result = String(data: data, encoding: .utf8)
                        ?? "No output received."
                    throw NSError(
                        domain: "DCAScriptMarker.ProjectImport",
                        code: Int(process.terminationStatus),
                        userInfo: [NSLocalizedDescriptionKey: result]
                    )
                }

                DispatchQueue.main.async {
                    do {
                        var importedProject = try JSONDecoder().decode(
                            DCAProjectDocument.self,
                            from: data
                        )
                        importedProject.normalise()
                        importedProject.scriptPath = scriptPath
                        importedProject.outputFolder = outputFolder
                        importedProject.sourceExcelPath = excelPath
                        isImportingProject = false
                        let url = automaticImportedProjectURL(
                            excelPath: excelPath
                        )
                        project = importedProject
                        projectPath = url.path
                        templatePath = excelPath
                        applyProjectToInterface()
                        guard saveCurrentProject() else { return }
                        roleMappingPanelController.close()
                        showProjectEditor = true
                        message = (
                            t(
                                "Excel imported. Project saved beside the workbook as ",
                                "Excel 已导入。项目已保存在工作簿旁，文件名为 "
                            )
                            + url.lastPathComponent
                            + "."
                        )
                    } catch {
                        isImportingProject = false
                        showProjectFileError(
                            title: t(
                                "Could not import Excel",
                                "无法导入 Excel"
                            ),
                            error: error
                        )
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    isImportingProject = false
                    showProjectFileError(
                        title: t(
                            "Could not import Excel",
                            "无法导入 Excel"
                        ),
                        error: error
                    )
                }
            }
        }
    }

    private func exportProjectExcel() {
        guard !projectPath.isEmpty else {
            message = t(
                "Create or open a DCA project first.",
                "请先新建或打开 DCA 项目。"
            )
            return
        }
        saveCurrentProject()

        let panel = NSSavePanel()
        panel.title = t(
            "Export DCA States to Excel",
            "将 DCA 状态导出到 Excel"
        )
        panel.prompt = appLanguage.label("Export Excel")
        panel.canCreateDirectories = true
        panel.nameFieldStringValue = "\(project.name).xlsx"
        if let excelType = UTType(filenameExtension: "xlsx") {
            panel.allowedContentTypes = [excelType]
        }
        guard panel.runModal() == .OK, let outputURL = panel.url else { return }
        guard let runtime = markerRuntime() else {
            message = missingEngineMessage
            return
        }

        isExportingProject = true
        message = t(
            "Exporting the Excel workbook…",
            "正在导出 Excel 工作簿…"
        )
        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            let output = Pipe()
            process.executableURL = runtime.executableURL
            process.arguments = runtime.argumentPrefix + [
                "--project", projectPath,
                "--export-excel", outputURL.path,
            ]
            process.environment = markerEnvironment()
            process.standardOutput = output
            process.standardError = output

            do {
                try process.run()
                let data = output.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()
                let result = String(data: data, encoding: .utf8)
                    ?? "Excel export completed."
                guard process.terminationStatus == 0 else {
                    throw NSError(
                        domain: "DCAScriptMarker.ProjectExport",
                        code: Int(process.terminationStatus),
                        userInfo: [NSLocalizedDescriptionKey: result]
                    )
                }
                DispatchQueue.main.async {
                    isExportingProject = false
                    message = t(
                        "Excel exported: \(outputURL.lastPathComponent)",
                        "Excel 已导出：\(outputURL.lastPathComponent)"
                    )
                    NSWorkspace.shared.activateFileViewerSelecting([outputURL])
                }
            } catch {
                DispatchQueue.main.async {
                    isExportingProject = false
                    showProjectFileError(
                        title: t(
                            "Could not export Excel",
                            "无法导出 Excel"
                        ),
                        error: error
                    )
                }
            }
        }
    }

    @discardableResult
    private func saveCurrentProject(
        capturingInterface: Bool = true
    ) -> Bool {
        guard !projectPath.isEmpty else { return false }
        if capturingInterface {
            captureInterfaceInProject()
        }
        do {
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
            let data = try encoder.encode(project)
            try data.write(
                to: URL(fileURLWithPath: projectPath),
                options: .atomic
            )
            return true
        } catch {
            showProjectFileError(
                title: t("Could not save project", "无法保存项目"),
                error: error
            )
            return false
        }
    }

    private func captureInterfaceInProject() {
        project.scriptPath = scriptPath
        project.outputFolder = outputFolder
        project.settings.markingStyle = selectedStyle
        project.settings.markSelectedPages = markSelectedPages
        project.settings.startPage = startPage
        project.settings.endPage = endPage
        project.settings.numberColour = numberColour
        project.settings.numberSize = numberSize
        project.settings.numberFont = numberFont
        project.settings.numberPosition = numberPosition
        project.settings.numberVerticalPosition = numberVerticalPosition
        project.settings.stateColour = stateColour
        project.settings.stateSize = stateSize
        project.settings.stateFont = stateFont
        project.settings.statePosition = statePosition
        project.settings.legendPosition = legendPosition
        project.settings.pageStateDisplay = pageStateDisplay
        project.settings.pageStateTextColour = pageStateTextColour
        project.settings.pageStateTextSize = pageStateTextSize
        project.settings.pageStateTextFont = pageStateTextFont
        project.settings.pageStateBorderColour = pageStateBorderColour
        project.settings.showPerformerRoleMapping = showPerformerRoleMapping
    }

    private func applyProjectToInterface() {
        scriptPath = project.scriptPath
        outputFolder = project.outputFolder
        selectedStyle = project.settings.markingStyle
        markSelectedPages = project.settings.markSelectedPages
        startPage = project.settings.startPage
        endPage = project.settings.endPage
        numberColour = project.settings.numberColour
        numberSize = project.settings.numberSize
        numberFont = project.settings.numberFont
        numberPosition = project.settings.numberPosition
        numberVerticalPosition = project.settings.numberVerticalPosition
        stateColour = project.settings.stateColour
        stateSize = project.settings.stateSize
        stateFont = project.settings.stateFont
        statePosition = project.settings.statePosition
        legendPosition = project.settings.legendPosition
        pageStateDisplay = project.settings.pageStateDisplay
        pageStateTextColour = project.settings.pageStateTextColour
        pageStateTextSize = project.settings.pageStateTextSize
        pageStateTextFont = project.settings.pageStateTextFont
        pageStateBorderColour = project.settings.pageStateBorderColour
        showPerformerRoleMapping = project.settings.showPerformerRoleMapping
    }

    private func showProjectFileError(title: String, error: Error) {
        let alert = NSAlert()
        alert.alertStyle = .critical
        alert.messageText = title
        alert.informativeText = conciseRoleMappingError(error)
        alert.addButton(withTitle: t("OK", "确定"))
        alert.runModal()
        message = "\(title): \(conciseRoleMappingError(error))"
    }

    private func showProjectValidationAlert() {
        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = t(
            "Check DCA project setup",
            "请检查 DCA 项目设置"
        )
        alert.informativeText = project.blockingValidationIssues(
            for: appLanguage
        )
            .map { "• \($0)" }
            .joined(separator: "\n")
        alert.addButton(withTitle: t("Edit DCA Project", "编辑 DCA 项目"))
        alert.addButton(withTitle: appLanguage.label("Cancel"))
        if alert.runModal() == .alertFirstButtonReturn {
            showProjectEditor = true
        }
        message = t(
            "Please correct the highlighted project setup items before generating.",
            "请先修正项目设置中标出的项目，再重新生成。"
        )
    }

    private func confirmProjectAdvisories() -> Bool {
        let advisories = project.advisoryIssues(
            for: appLanguage,
            excluding: ignoredProjectAdvisorySignatures
        )
        guard !advisories.isEmpty else { return true }

        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = t(
            "Please confirm repeated DCA assignments",
            "请确认重复的 DCA 分配"
        )
        alert.informativeText = advisories
            .map { "• \($0)" }
            .joined(separator: "\n")
            + t(
                "\n\nThis can be valid when a performer has solo lines and then joins an ensemble. It will not stop generation.",
                "\n\n当演员先有独唱台词、之后加入群唱时，这种设置可能是正确的，因此不会阻止生成。"
            )
        alert.addButton(withTitle: t(
            "Ignore and Continue",
            "忽略并继续"
        ))
        alert.addButton(withTitle: t(
            "Edit DCA Project",
            "编辑 DCA 项目"
        ))
        alert.addButton(withTitle: appLanguage.label("Cancel"))

        switch alert.runModal() {
        case .alertFirstButtonReturn:
            ignoredProjectAdvisorySignatures.formUnion(
                project.advisorySignatures()
            )
            return true
        case .alertSecondButtonReturn:
            showProjectEditor = true
            return false
        default:
            return false
        }
    }

    private func openUserGuide() {
        guard let guideURL = Bundle.main.url(
            forResource: "START HERE - User Guide - 使用手册",
            withExtension: "pdf"
        ), NSWorkspace.shared.open(guideURL) else {
            let alert = NSAlert()
            alert.alertStyle = .warning
            alert.messageText = t(
                "User guide unavailable",
                "无法打开使用手册"
            )
            alert.informativeText = t(
                "The complete bilingual PDF user guide could not be opened. Please reinstall DCA Script Marker from the official release DMG.",
                "无法打开完整的双语 PDF 使用手册。请从官方发行版 DMG 重新安装 DCA Script Marker。"
            )
            alert.addButton(withTitle: t("OK", "确定"))
            alert.runModal()
            return
        }
    }

    func loadLegendEditor() {
        guard !projectPath.isEmpty else {
            message = t(
                "Create or open a DCA project first.",
                "请先新建或打开 DCA 项目。"
            )
            return
        }
        saveCurrentProject()
        isGenerating = true
        message = t(
            "Loading the DCA State Legend…",
            "正在载入 DCA 状态图例…"
        )

        DispatchQueue.global(qos: .userInitiated).async {
            guard let runtime = markerRuntime() else {
                DispatchQueue.main.async {
                    isGenerating = false
                    message = missingEngineMessage
                }
                return
            }

            let process = Process()
            let output = Pipe()
            process.executableURL = runtime.executableURL
            process.arguments = runtime.argumentPrefix + [
                "--project", projectPath,
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
                    message = t(
                        "Could not load the DCA State Legend: ",
                        "无法载入 DCA 状态图例："
                    ) + "\(error.localizedDescription)\n\(resultText(from: output))"
                }
            }
        }
    }

    func loadRoleMappingInspector() {
        guard !projectPath.isEmpty else {
            message = t(
                "Create or open a DCA project first.",
                "请先新建或打开 DCA 项目。"
            )
            return
        }
        saveCurrentProject()

        isLoadingRoleMapping = true
        message = t(
            "Loading the DCA States Inspector…",
            "正在载入 DCA 状态对照窗口…"
        )

        DispatchQueue.global(qos: .userInitiated).async {
            guard let runtime = markerRuntime() else {
                DispatchQueue.main.async {
                    isLoadingRoleMapping = false
                    message = missingEngineMessage
                }
                return
            }

            let process = Process()
            let output = Pipe()
            process.executableURL = runtime.executableURL
            process.arguments = runtime.argumentPrefix + [
                "--project", projectPath,
                "--list-role-mappings",
            ]
            process.environment = markerEnvironment()
            process.standardOutput = output
            process.standardError = output

            do {
                try process.run()
                let data = output.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()

                guard process.terminationStatus == 0 else {
                    let result = String(data: data, encoding: .utf8)
                        ?? "No output received."
                    throw NSError(
                        domain: "DCAScriptMarker.RoleMapping",
                        code: Int(process.terminationStatus),
                        userInfo: [NSLocalizedDescriptionKey: result]
                    )
                }

                let states = try JSONDecoder().decode(
                    [RoleMappingState].self,
                    from: data
                )
                let workbookName = URL(fileURLWithPath: projectPath)
                    .lastPathComponent

                DispatchQueue.main.async {
                    isLoadingRoleMapping = false
                    roleMappingPanelController.show(
                        states: states,
                        workbookName: workbookName,
                        language: appLanguage
                    )
                    message = t(
                        "DCA States Inspector opened. It can stay visible beside Preview.",
                        "DCA 状态对照窗口已打开，可保持显示在 Preview 旁边。"
                    )
                }
            } catch {
                DispatchQueue.main.async {
                    isLoadingRoleMapping = false
                    let errorMessage = conciseRoleMappingError(error)
                    message = t(
                        "Could not load the DCA States Inspector: ",
                        "无法载入 DCA 状态对照窗口："
                    ) + errorMessage
                    showRoleMappingLoadError(errorMessage)
                }
            }
        }
    }

    private func conciseRoleMappingError(_ error: Error) -> String {
        let lines = error.localizedDescription
            .split(whereSeparator: \.isNewline)
            .map { String($0).trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
        let finalLine = lines.last ?? error.localizedDescription
        return finalLine.replacingOccurrences(
            of: "ValueError: ",
            with: ""
        )
    }

    private func showRoleMappingLoadError(_ errorMessage: String) {
        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = t(
            "Could not load DCA States",
            "无法载入 DCA 状态"
        )
        alert.informativeText = t(
            "\(errorMessage)\n\nCheck the Character List names and mappings, then try again.",
            "\(errorMessage)\n\n请检查 Character List 中的名称和映射，然后重试。"
        )
        alert.addButton(withTitle: t("OK", "确定"))
        alert.runModal()
    }

    private func conciseMarkerFailure(_ output: String) -> String {
        let lines = output
            .split(whereSeparator: \.isNewline)
            .map { String($0).trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
        let finalLine = lines.last ?? output
        return finalLine.replacingOccurrences(
            of: "ValueError: ",
            with: ""
        )
    }

    private func showMarkerFailureAlert(_ errorMessage: String) {
        let alert = NSAlert()
        alert.alertStyle = .critical
        alert.messageText = t(
            "Check DCA project setup",
            "请检查 DCA 项目设置"
        )
        alert.informativeText = t(
            "The marker stopped before creating a PDF because the DCA project contains a setup conflict.\n\n\(errorMessage)\n\nOpen the project editor, correct the named DCA State or Character List mapping, then generate again. A repeated DCA Name in multiple DCA columns is allowed and is reported only as a review warning.",
            "软件在生成 PDF 前发现 DCA 项目设置冲突，因此已停止。\n\n\(errorMessage)\n\n请打开项目编辑器，修正提示中的 DCA 状态或 Character List 映射后重新生成。同一个 DCA Name 出现在多个 DCA 栏目是允许的，只会作为复核提醒。"
        )
        alert.addButton(withTitle: t("Edit DCA Project", "编辑 DCA 项目"))
        alert.addButton(withTitle: t("OK", "确定"))

        if alert.runModal() == .alertFirstButtonReturn {
            showProjectEditor = true
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
            message = t(
                "Could not save the edited legend: ",
                "无法保存已编辑的图例："
            ) + error.localizedDescription
        }
    }

    func resultText(from output: Pipe) -> String {
        let data = output.fileHandleForReading.readDataToEndOfFile()
        return String(data: data, encoding: .utf8) ?? ""
    }

    private func localizedSafetyWarning(
        _ warning: MarkerSafetyWarning
    ) -> String {
        guard appLanguage == .simplifiedChinese else {
            return warning.message
        }

        switch warning.code {
        case "NO_STATES_CONFIGURED":
            return "模板中没有可用的 DCA 状态。使用此 PDF 前，请添加状态名称和 Start Line Text。"
        case "NO_STATES_ACTIVATED":
            return "所选剧本页面中没有找到 DCA 状态的开始提示。请确认 PDF 文字可选择，并检查 Start Line Text、Start Line Character 和 Page Hint。"
        case "FIRST_STATE_NOT_ACTIVATED":
            return "第一个 DCA 状态没有启用，前面的页面可能没有标注。请检查 Page Hint 使用的页码类型。"
        case "MISSING_STATE_CUES":
            return "一个或多个后续 DCA 状态的开始提示未找到。请查看复核报告中的状态列表。"
        case "ZERO_CUES_MARKED":
            return "DCA 状态已启用，但没有添加对白 DCA 编号。请检查角色标签排版、角色名称、映射和 DCA 分配。"
        case "START_CUES_WITHOUT_STATE_NAMES":
            return "部分项目行填写了 Start Line Text，但没有 DCA 状态名称，因此未被使用。"
        case "ASSIGNMENTS_WITHOUT_START_CUES":
            return "部分状态行包含 DCA 分配，但没有可用的开始提示。"
        case "DCA_ASSIGNMENT_GAPS":
            return "部分 DCA 状态在已填写的 DCA 列之间存在空白列。请确认这不是遗漏的分配。"
        case "PAGE_HINT_MISMATCH":
            return "Start Line Text 出现在其他 PDF 页面位置。请检查 Page Hint 使用的是剧本内印刷页码还是 PDF 页面位置。"
        case "POSSIBLE_INCOMPLETE_FINAL_STATE":
            return "最后一个状态开始后发现了没有 DCA 分配的已知角色标签。请确认项目包含所有后续状态。"
        case "KNOWN_SPEAKERS_UNASSIGNED":
            return "发现已识别但在当前状态中没有 DCA 分配的角色标签。请查看复核报告中的示例。"
        default:
            return "发现需要检查的设置或匹配问题。详细信息请查看复核报告。"
        }
    }

    private func showSafetyAlert(_ result: MarkerCompletionResult) {
        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = t(
            "Review required before use",
            "使用前需要复核"
        )

        let warningLines = result.safetyWarnings.prefix(3).map {
            "• \(localizedSafetyWarning($0))"
        }
        let remainingCount = max(
            0,
            result.safetyWarningCount - warningLines.count
        )
        let remainingText = remainingCount > 0
            ? t(
                "\n• \(remainingCount) more warning(s) are listed in the review report.",
                "\n• 复核报告中还有 \(remainingCount) 条警告。"
            )
            : ""

        alert.informativeText = t(
            "The PDF was created, but the automatic safety check found possible setup or matching problems. Check the review report and marked PDF before rehearsal.\n\n\(warningLines.joined(separator: "\n"))\(remainingText)",
            "PDF 已生成，但自动安全检查发现可能的设置或匹配问题。请在排练前核对复核报告和标注后的 PDF。\n\n\(warningLines.joined(separator: "\n"))\(remainingText)"
        )
        alert.addButton(
            withTitle: t("Show Output Folder", "显示输出文件夹")
        )
        alert.addButton(
            withTitle: t("Open Review Report", "打开复核报告")
        )
        alert.addButton(withTitle: t("Later", "稍后"))

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
        alert.messageText = t(
            "No DCA numbers were added",
            "未添加任何 DCA 编号"
        )
        alert.informativeText = t(
            "No dialogue DCA numbers were added. Do not use this output until you have checked the original PDF, DCA project, and review report.\n\nPossible causes include a blank or incomplete project with no usable DCA States or assignments, a scanned/image-only PDF, an unrecognised speaker-label layout, character names or DCA assignments that do not match, or a Start Line Text/Page Hint that did not activate the intended state.\n\nPage numbers are not interchangeable: Excel Page Hint normally uses the number printed inside the script; use the PDF page position only when no printed page number exists. A selected-page range always uses the PDF viewer's page position, counting the cover as page 1.",
            "没有添加任何对白 DCA 编号。请先核对原始 PDF、DCA 项目和复核报告，勿直接使用此输出。\n\n可能原因包括：项目仍为空白或没有可用的 DCA 状态及分配、PDF 为扫描版或纯图片、软件尚未识别该角色标签排版、角色名称或 DCA 分配不一致，或 Start Line Text / Page Hint 未能启动正确的状态。\n\n两种页码不能混用：Excel 的 Page Hint 通常填写剧本页面内印刷的页码；只有没有印刷页码时才使用 PDF 页面位置。“仅标注指定页码”始终使用 PDF 阅读器中的页面位置，并从封面作为第 1 页开始计算。"
        )
        alert.addButton(withTitle: t("Show Output Folder", "显示输出文件夹"))
        alert.addButton(withTitle: t("Open Review Report", "打开复核报告"))
        alert.addButton(withTitle: t("Try Another PDF", "选择其他 PDF"))

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
                message = t(
                    "A new script PDF is selected. Check the DCA project and generate again.",
                    "已选择新的剧本 PDF。请检查 DCA 项目后重新生成。"
                )
            }
        default:
            break
        }
    }

    private func showSafetyUnavailableAlert() {
        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = t(
            "Safety result unavailable",
            "无法读取安全检查结果"
        )
        alert.informativeText = t(
            "The PDF was created, but the app could not read the automatic safety result. Open the output folder and check the review report and marked PDF manually before rehearsal.",
            "PDF 已生成，但软件无法读取自动安全检查结果。请打开输出文件夹，并在排练前人工核对复核报告和标注后的 PDF。"
        )
        alert.addButton(
            withTitle: t("Show Output Folder", "显示输出文件夹")
        )
        alert.addButton(withTitle: t("Later", "稍后"))

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
        let homeFolder = FileManager.default.homeDirectoryForCurrentUser
        let environment = ProcessInfo.processInfo.environment
        var pythonCandidates: [URL] = []

        if let overridePath = environment["DCA_MARKER_PYTHON"],
           !overridePath.isEmpty {
            pythonCandidates.append(URL(fileURLWithPath: overridePath))
        }
        if let condaPrefix = environment["CONDA_PREFIX"],
           !condaPrefix.isEmpty {
            pythonCandidates.append(
                URL(fileURLWithPath: condaPrefix)
                    .appendingPathComponent("bin/python")
            )
        }

        pythonCandidates += [
            projectFolder.appendingPathComponent(".venv/bin/python"),
            homeFolder.appendingPathComponent("opt/anaconda3/bin/python3"),
            homeFolder.appendingPathComponent("anaconda3/bin/python3"),
            homeFolder.appendingPathComponent("miniconda3/bin/python3"),
            URL(fileURLWithPath: "/opt/homebrew/bin/python3"),
            URL(fileURLWithPath: "/usr/local/bin/python3"),
            URL(fileURLWithPath: "/usr/bin/python3"),
        ]
        var seenPythonPaths = Set<String>()

        if FileManager.default.fileExists(atPath: markerFile.path),
           let python = pythonCandidates.first(where: {
               let candidatePath = $0.standardizedFileURL.path
               return seenPythonPaths.insert(candidatePath).inserted
                   && FileManager.default.isExecutableFile(
                       atPath: candidatePath
                   )
                   && pythonSupportsMarkerDependencies($0)
           }) {
            return MarkerRuntime(
                executableURL: python,
                argumentPrefix: [markerFile.path]
            )
        }
        #endif

        return nil
    }

    #if DEBUG
    private func pythonSupportsMarkerDependencies(_ python: URL) -> Bool {
        let process = Process()
        let output = Pipe()
        process.executableURL = python
        process.arguments = ["-c", "import fitz, openpyxl"]
        process.standardOutput = output
        process.standardError = output

        do {
            try process.run()
            _ = output.fileHandleForReading.readDataToEndOfFile()
            process.waitUntilExit()
            return process.terminationStatus == 0
        } catch {
            return false
        }
    }
    #endif

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
        alert.messageText = t(
            "A marked PDF already exists",
            "标注后的 PDF 已存在"
        )
        alert.informativeText = t(
            "Save as New is recommended when adjusting the marking style. Replacing a PDF that is still open in Preview can temporarily show both versions together.",
            "调整标注样式时建议另存为新 PDF。如果现有 PDF 仍在 Preview 中打开，替换时可能暂时同时显示两个版本。"
        )
        alert.addButton(withTitle: t(
            "Save as New PDF (Recommended)",
            "另存为新 PDF（建议）"
        ))
        alert.addButton(withTitle: t(
            "Replace Existing PDF",
            "替换现有 PDF"
        ))
        alert.addButton(withTitle: appLanguage.label("Cancel"))

        switch alert.runModal() {
        case .alertFirstButtonReturn:
            return "new"
        case .alertSecondButtonReturn:
            let replacementAlert = NSAlert()
            replacementAlert.messageText = t(
                "Close the PDF before replacing it",
                "替换前请关闭 PDF"
            )
            replacementAlert.informativeText = t(
                "Preview keeps editable markings in memory. Close the existing marked PDF in Preview, then continue with the replacement.",
                "Preview 会将可编辑标注保留在内存中。请先在 Preview 中关闭现有的标注 PDF，再继续替换。"
            )
            replacementAlert.addButton(withTitle: t(
                "Replace After Closing",
                "关闭后替换"
            ))
            replacementAlert.addButton(withTitle: appLanguage.label("Cancel"))

            return replacementAlert.runModal() == .alertFirstButtonReturn
                ? "replace"
                : nil
        default:
            return nil
        }
    }
    func generateMarkedScript(legendOverridesFile: String? = nil) {
        guard !projectPath.isEmpty,
              !scriptPath.isEmpty,
              !outputFolder.isEmpty else {
            removeLegendOverridesFile(legendOverridesFile)
            message = t(
                "Please create or open a DCA project, then choose a script PDF and output folder.",
                "请先新建或打开 DCA 项目，然后选择剧本 PDF 和输出文件夹。"
            )
            return
        }
        saveCurrentProject()

        if markSelectedPages {
            guard let firstPage = Int(startPage),
                  let lastPage = Int(endPage),
                  firstPage >= 1,
                  lastPage >= firstPage else {
                removeLegendOverridesFile(legendOverridesFile)
                message = t(
                    "Enter a valid page range, for example 12 to 18.",
                    "请输入有效的页码范围，例如第 12 页到第 18 页。"
                )
                return
            }
        }
        guard let outputMode = chooseOutputMode() else {
            removeLegendOverridesFile(legendOverridesFile)
            message = t("Export cancelled.", "已取消导出。")
            return
        }
        let replacingExistingPDF = outputMode == "replace"
            && FileManager.default.fileExists(atPath: markedOutputURL().path)
        let generationStyle = selectedStyle
        isGenerating = true
        message = t(
            "Creating your marked script…",
            "正在生成标注剧本…"
        )

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
                    message = missingEngineMessage
                }
                return
            }

            let process = Process()
            let output = Pipe()
            process.executableURL = runtime.executableURL
            process.environment = markerEnvironment()
            var arguments = runtime.argumentPrefix + [
                "--project", projectPath,
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

            if showPerformerRoleMapping {
                arguments.append("--show-performer-role-mapping")
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
                        let completionMessage: String
                        if appLanguage == .simplifiedChinese {
                            if let completionResult {
                                completionMessage = (
                                    "标注完成！共标注 \(completionResult.markedCount) 条提示。\n"
                                    + "PDF：\(completionResult.outputPDF)\n"
                                    + "复核报告：\(completionResult.reviewReport)"
                                )
                            } else {
                                completionMessage = "标注剧本已生成。请在输出文件夹中查看 PDF 和复核报告。"
                            }
                        } else {
                            completionMessage = result
                        }
                        if replacingExistingPDF {
                            message = completionMessage + t(
                                "\n\nReplacement complete. Close and reopen the PDF in Preview before reviewing it.",
                                "\n\n替换已完成。请在 Preview 中关闭并重新打开 PDF 后再检查。"
                            )
                        } else {
                            message = completionMessage
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
                        let errorMessage = conciseMarkerFailure(result)
                        message = t(
                            "The marker could not finish:\n",
                            "标注程序未能完成：\n"
                        ) + errorMessage
                        showMarkerFailureAlert(errorMessage)
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    isGenerating = false
                    message = t(
                        "Could not start the DCA marker engine: ",
                        "无法启动 DCA 标注引擎："
                    ) + error.localizedDescription
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
    @Environment(\.appLanguage) private var language
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
    @Binding var showPerformerRoleMapping: Bool
    let cancel: () -> Void
    let continueAction: () -> Void

    private let colours = [
        "Red", "Blue", "Black", "Green",
        "Orange", "Purple", "Grey", "Brown"
    ]
    private let sizes = ["Small", "Medium", "Large"]
    private let numberFonts = ["Helvetica", "Times", "Courier"]
    private let stateFonts = ["PingFang SC", "Chinese System", "Helvetica", "Times", "Courier"]

    private func t(_ english: String, _ chinese: String) -> String {
        language.text(english, chinese)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 6) {
                Text(language.label("Annotation Style"))
                    .font(.title2.bold())

                Text(t(
                    "Choose the appearance of DCA numbers and DCA State labels.",
                    "选择 DCA 编号和 DCA 状态标签的外观。"
                ))
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
                        Text(language.label("DCA State Header, Footer & Mapping"))
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
                        .disabled(
                            pageStateDisplay == "Off"
                                && !showPerformerRoleMapping
                        )
                        .opacity(
                            pageStateDisplay == "Off"
                                && !showPerformerRoleMapping
                                ? 0.5 : 1
                        )

                        Divider().padding(.vertical, 2)

                        Toggle(
                            language.label("Show DCA Name / Other Script Characters"),
                            isOn: $showPerformerRoleMapping
                        )
                        .toggleStyle(.checkbox)

                        Text(t(
                            "Adds one movable reference card to the first PDF page where each DCA State is active. Includes the performer and script-role mappings from Character List.",
                            "在每个 DCA 状态首次启用的 PDF 页面添加一份可移动的 DCA Name / 剧本标签对照卡；显示 Character List 中的演员与剧本角色对应关系。"
                        ))
                        .font(.caption)
                        .foregroundStyle(.secondary)

                        Text(t(
                            "Chinese labels automatically use a compatible Chinese font.",
                            "中文标签会自动使用兼容的中文字体。"
                        ))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.trailing, 8)
            }

            HStack {
                Spacer()
                Button(language.label("Cancel"), action: cancel)
                Button(language.label("Continue"), action: continueAction)
                    .buttonStyle(.borderedProminent)
            }
        }
        .padding(24)
        .frame(
            minWidth: 760,
            idealWidth: 800,
            maxWidth: 800,
            minHeight: 650,
            idealHeight: 720,
            maxHeight: 760
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
    @Environment(\.appLanguage) private var language
    @Binding var drafts: [LegendDraft]
    let cancel: () -> Void
    let export: () -> Void

    private func t(_ english: String, _ chinese: String) -> String {
        language.text(english, chinese)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(language.label("Edit DCA State Legends"))
                .font(.title2.bold())

            Text(t(
                "Review or change each DCA membership list before creating the PDF.",
                "生成 PDF 前，请检查或修改每个 DCA 状态的成员列表。"
            ))
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
                Button(language.label("Cancel"), action: cancel)
                Button(language.label("Export Edited Legend"), action: export)
                    .buttonStyle(.borderedProminent)
            }
        }
        .padding(28)
        .frame(width: 620, height: 620)
    }
}

struct HelpSheet: View {
    @Environment(\.appLanguage) private var language
    let close: () -> Void

    private func t(_ english: String, _ chinese: String) -> String {
        language.text(english, chinese)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                Text(t("DCA Script Marker Help", "DCA Script Marker 使用说明"))
                    .font(.title2.bold())
                Spacer()
                Button(language.label("Done"), action: close)
                    .buttonStyle(.borderedProminent)
            }

            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    HelpStep(
                        number: "1",
                        title: t(
                            "Create, open, or import a project",
                            "新建、打开或导入项目"
                        ),
                        detail: t(
                            "Choose New to create a local .dcamarker project, Open to continue one, or Import Excel to convert an existing workbook. The project remembers the script PDF, output folder, Character List, DCA States, and marking settings. You can export a standard Excel workbook whenever needed.",
                            "选择“新建”创建本地 .dcamarker 项目，选择“打开”继续已有项目，或选择“导入 Excel”转换现有工作簿。项目会记住剧本 PDF、输出文件夹、Character List、DCA 状态和标注设置；需要时仍可导出标准 Excel 工作簿。"
                        )
                    )
                    HelpStep(
                        number: "2",
                        title: t(
                            "Edit DCA data and choose files",
                            "编辑 DCA 数据并选择文件"
                        ),
                        detail: t(
                            "Open the project editor. Character List is optional: leave it blank when you do not need Other Script Characters Played mapping, and enter names directly in DCA 1–12. TOM, JERRY, APPLE, and ALL THREE can be four ordinary DCA Names with blank mapping cells. Special DCA-cell example: put TOM and ALL THREE in DCA 1, JERRY and ALL THREE in DCA 2, and APPLE and ALL THREE in DCA 3. The printed ALL THREE cue then receives 1/2/3. This intentional repeated assignment may show a reminder, but generation remains available; use Ignore or the X when the setup is correct. A printed label such as MALE ENSEMBLE can simply be an ordinary DCA Name. Select it like any other name; the app does not maintain a membership list. Required setup errors remain visible. Complete each state's Start Line Text, position, Page Hint, and assignments, then choose the original script PDF and output folder.",
                            "打开项目编辑器。Character List 为可选项：如果不需要 Other Script Characters Played 映射，可以留空，直接在 DCA 1–12 中填写名称。TOM、JERRY、APPLE 和 ALL THREE 可以是四个普通 DCA Name，映射单元格保持为空。特别 DCA 单元格示例：在 DCA 1 中填写 TOM 和 ALL THREE，在 DCA 2 中填写 JERRY 和 ALL THREE，在 DCA 3 中填写 APPLE 和 ALL THREE；剧本中标为 ALL THREE 的提示便会获得 1/2/3。这项有意设置的重复分配可能会触发提醒，但仍可继续生成；设置正确时可使用“忽略”或 X。MALE ENSEMBLE 等剧本标签可以直接作为普通 DCA Name，像其他名称一样选择；软件不管理成员名单。必须修正的设置错误仍会显示。再完成每个状态的 Start Line Text、位置、Page Hint 和分配，然后选择原始剧本 PDF 与输出文件夹。"
                        )
                    )
                    HelpStep(
                        number: "3",
                        title: t(
                            "Find a DCA Name by its script role",
                            "按剧本角色选择 DCA Name"
                        ),
                        detail: t(
                            """
                            In Character List, enter Jack as the DCA Name and put Student and Teacher on separate lines under Other Script Characters Played.

                            In a DCA States cell, open the name picker. Under Other Script Characters Played, choose Student to insert Jack [Student], or Teacher to insert Jack [Teacher], just like Excel. Choosing Jack under DCA Names inserts only Jack. These are the same DCA Name, so Jack is added only once and both role choices show a green check when he is already in that cell.

                            All Jack's mapped roles use that DCA number in the current state. This is a shortcut to an existing DCA Name, not a new DCA Name.
                            """,
                            """
                            在 Character List 中，将 Jack 填入 DCA Name，并在“饰演的其他剧本角色”下分两行填写 Student 和 Teacher。

                            打开 DCA States 单元格的名称选择菜单，在“饰演的其他剧本角色”下选择 Student，会填入 Jack [Student]；选择 Teacher，会填入 Jack [Teacher]，与 Excel 一致。在 DCA Names 下选择 Jack，则只填入 Jack。这些选项对应同一个 DCA Name，因此 Jack 只会加入一次；当前单元格已有 Jack 时，两个角色选项均显示绿色勾选。

                            在当前状态中，Jack 的全部对应角色均使用该 DCA 编号。这只是选择现有 DCA Name 的快捷方式，不会新增 DCA Name。
                            """
                        )
                    )
                    HelpStep(
                        number: "4",
                        title: t(
                            "Choose a marking style",
                            "选择标注方式"
                        ),
                        detail: t(
                            "All three styles create movable PDF annotations. Editable Full Marking marks every dialogue line. First Appearance Only marks each character's first cue in every DCA State. DCA State Legend creates an editable membership list. Page header/footer text and its border move or delete together.",
                            "三种标注方式都会创建可移动的 PDF 标注。“可编辑完整标注”会标注每一句角色台词；“仅首次出现”会在每个 DCA 状态中标注每个角色的第一句台词；“DCA 状态图例”会创建可编辑的分配列表。页眉或页脚文字与边框会一起移动或删除。"
                        )
                    )
                    HelpStep(
                        number: "5",
                        title: t(
                            "Optional: mark only selected pages",
                            "可选：仅标注指定页码"
                        ),
                        detail: t(
                            "Turn on Mark selected pages only when preparing only part of a script. This range always uses the PDF viewer's page position, counting the cover as page 1. It may differ from the page number printed inside the script.",
                            "只需要处理剧本的一部分时，请打开“仅标注指定页码”。这里始终使用 PDF 阅读器中的页面位置，并从封面作为第 1 页开始计算；它可能与剧本页面内印刷的页码不同。"
                        )
                    )
                    HelpStep(
                        number: "6",
                        title: t("Generate and review", "生成并检查"),
                        detail: t(
                            "Choose annotation colours, fonts, sizes, and positions. Page DCA States can be Off, Header Only, Footer Only, or Header and Footer. You can also add one movable DCA Name / mapped-script-label card on the first selected page where each state is active; it includes the performer and script-role mappings from Character List. Then generate the PDF and check the review report before rehearsal. If no DCA numbers are added, do not use the output; check the PDF text, layout, project names, state cue, and Page Hint.",
                            "选择标注颜色、字体、大小和位置。页面 DCA 状态可以关闭、仅显示在页眉、仅显示在页脚，或同时显示在页眉和页脚。还可以在每个状态首次启用的所选页面添加一份可移动的 DCA Name / 剧本标签对照卡；卡片显示 Character List 中的演员与剧本角色对应关系。然后生成 PDF，并在排练前检查复核报告。如果没有添加任何 DCA 编号，请勿使用该输出，并检查 PDF 文字与排版、项目角色名称、状态提示和 Page Hint。"
                        )
                    )
                    HelpStep(
                        number: "7",
                        title: t(
                            "Optional: keep DCA States visible",
                            "可选：保持 DCA 状态可见"
                        ),
                        detail: t(
                            "Click DCA States beside Generate Marked Script. The movable, resizable Inspector can stay above Preview while you read the PDF. Use Previous and Next to move through states. Search by DCA Name or other script character across the complete project; each result lists every state where that DCA Name is active.",
                            "点击“生成标注剧本”旁边的“DCA 状态”。可移动、可调整大小的对照窗口可以在阅读 PDF 时保持在 Preview 上方。使用“上一个”和“下一个”切换状态；也可按 DCA Name 或其他剧本角色搜索整个项目，并查看该 DCA Name 启用的所有状态。"
                        )
                    )

                    Divider()

                    VStack(alignment: .leading, spacing: 4) {
                        Text(t(
                            "Copyright © 2026 Siqi Ma",
                            "Copyright © 2026 马斯琪 Siqi Ma"
                        ))
                            .font(.footnote.weight(.semibold))
                        Text(t(
                            "Licensed under GNU AGPL v3 or later",
                            "使用 GNU AGPL v3 或更高版本许可"
                        ))
                            .font(.footnote)
                        Text(t(
                            "The exact source code and licences are included with every release package.",
                            "每个发行版本均附带对应的完整源代码与许可文件。"
                        ))
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
    @Environment(\.appLanguage) private var language
    let title: String
    @Binding var colour: String
    @Binding var size: String
    @Binding var font: String
    let colours: [String]
    let sizes: [String]
    let fonts: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(language.label(title)).font(.headline)

            PickerRow(title: "Colour", selection: $colour, options: colours)
            PickerRow(title: "Size", selection: $size, options: sizes)
            PickerRow(title: "Font", selection: $font, options: fonts)
        }
    }
}

struct PickerRow: View {
    @Environment(\.appLanguage) private var language
    let title: String
    @Binding var selection: String
    let options: [String]

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text(language.label(title))
                .font(.body)
                .lineLimit(2)
                .frame(width: 155, alignment: .leading)
            Picker(language.label(title), selection: $selection) {
                ForEach(options, id: \.self) { option in
                    Text(language.label(option)).tag(option)
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
    @Environment(\.appLanguage) private var language
    let title: String
    @Binding var path: String
    let buttonTitle: String
    let action: () -> Void

    var body: some View {
        HStack {
            Text(language.label(title))
                .font(.system(size: 16, weight: .bold))
                .frame(width: 145, alignment: .leading)

            TextField(
                language.text("No file selected", "未选择文件"),
                text: $path
            )
                .textFieldStyle(.roundedBorder)

            Button(language.label(buttonTitle), action: action)
                .buttonStyle(.bordered)
        }
    }
}

#if DEBUG
#Preview {
    ContentView()
}
#endif
