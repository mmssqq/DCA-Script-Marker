// Copyright © 2026 马斯琪 Siqi Ma
// SPDX-License-Identifier: AGPL-3.0-or-later

import SwiftUI
import Foundation
import AppKit

struct DCAProjectSettings: Codable, Equatable {
    var markingStyle = "Editable Full Marking"
    var markSelectedPages = false
    var startPage = ""
    var endPage = ""
    var numberColour = "Red"
    var numberSize = "Medium"
    var numberFont = "Helvetica"
    var numberPosition = "Standard"
    var numberVerticalPosition = "Default"
    var stateColour = "Blue"
    var stateSize = "Medium"
    var stateFont = "PingFang SC"
    var statePosition = "Left Gutter"
    var legendPosition = "Left Gutter"
    var pageStateDisplay = "Header and Footer"
    var pageStateTextColour = "Blue"
    var pageStateTextSize = "Medium"
    var pageStateTextFont = "PingFang SC"
    var pageStateBorderColour = "Blue"
    var showPerformerRoleMapping = false

    enum CodingKeys: String, CodingKey {
        case markingStyle = "marking_style"
        case markSelectedPages = "mark_selected_pages"
        case startPage = "start_page"
        case endPage = "end_page"
        case numberColour = "number_colour"
        case numberSize = "number_size"
        case numberFont = "number_font"
        case numberPosition = "number_position"
        case numberVerticalPosition = "number_vertical_position"
        case stateColour = "state_colour"
        case stateSize = "state_size"
        case stateFont = "state_font"
        case statePosition = "state_position"
        case legendPosition = "legend_position"
        case pageStateDisplay = "page_state_display"
        case pageStateTextColour = "page_state_text_colour"
        case pageStateTextSize = "page_state_text_size"
        case pageStateTextFont = "page_state_text_font"
        case pageStateBorderColour = "page_state_border_colour"
        case showPerformerRoleMapping = "show_performer_role_mapping"
    }
}

struct DCAProjectCharacter: Identifiable, Codable, Equatable {
    var id = UUID().uuidString
    var dcaName = ""
    var otherCharacters = ""

    enum CodingKeys: String, CodingKey {
        case id
        case dcaName = "dca_name"
        case otherCharacters = "other_characters"
    }
}

// Decode-only compatibility data; converted once to ordinary DCA entries.
struct LegacyDCAAssignmentSet: Codable, Equatable {
    var name = ""
    var members = ""

    enum CodingKeys: String, CodingKey {
        case name
        case members
    }
}

struct DCAProjectState: Identifiable, Codable, Equatable {
    var id = UUID().uuidString
    var name = ""
    var startLineCharacter = ""
    var startLineText = ""
    var startPosition = "After"
    var pageHint = ""
    var notes = ""
    var dcaAssignments = Array(repeating: "", count: 12)

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case startLineCharacter = "start_line_character"
        case startLineText = "start_line_text"
        case startPosition = "start_position"
        case pageHint = "page_hint"
        case notes
        case dcaAssignments = "dca_assignments"
    }

    mutating func normaliseAssignments() {
        dcaAssignments = Array(dcaAssignments.prefix(12))
        if dcaAssignments.count < 12 {
            dcaAssignments += Array(
                repeating: "",
                count: 12 - dcaAssignments.count
            )
        }
    }
}

struct DCAProjectDocument: Codable, Equatable {
    var schemaVersion = 1
    var name = "Untitled DCA Project"
    var scriptPath = ""
    var outputFolder = ""
    var sourceExcelPath = ""
    var settings = DCAProjectSettings()
    var characters: [DCAProjectCharacter] = []
    // Omitted from every new/saved project after one-way conversion.
    var legacyAssignmentSets: [LegacyDCAAssignmentSet]? = nil
    var states: [DCAProjectState] = []

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case name
        case scriptPath = "script_path"
        case outputFolder = "output_folder"
        case sourceExcelPath = "source_excel_path"
        case settings
        case characters
        case legacyAssignmentSets = "shared_groups"
        case states
    }

    static func newProject() -> DCAProjectDocument {
        DCAProjectDocument(
            characters: [DCAProjectCharacter()],
            states: [DCAProjectState()]
        )
    }

    mutating func normalise() {
        for index in states.indices {
            states[index].normaliseAssignments()
        }
        if characters.isEmpty {
            characters = [DCAProjectCharacter()]
        }
        if states.isEmpty {
            states = [DCAProjectState()]
        }

        convertLegacyAssignments()
    }

    var needsAssignmentConversion: Bool {
        !(legacyAssignmentSets ?? []).isEmpty
    }

    private mutating func convertLegacyAssignments() {
        let definitions = legacyAssignmentSets ?? []
        legacyAssignmentSets = nil
        guard !definitions.isEmpty else { return }

        var definitionsByName: [String: [LegacyDCAAssignmentSet]] = [:]
        for definition in definitions {
            let key = dcaAssignmentNameKey(definition.name)
            guard !key.isEmpty else { continue }
            definitionsByName[key, default: []].append(definition)
        }
        let definitionKeys = Set(definitionsByName.keys)

        // Remove obsolete repeated labels; there are no automatic membership
        // links after conversion. Individual performer/role mappings remain.
        for index in characters.indices {
            characters[index].otherCharacters = splitLegacyAssignmentNames(
                characters[index].otherCharacters
            )
            .filter { !definitionKeys.contains(dcaAssignmentNameKey($0)) }
            .joined(separator: "\n")
        }

        var knownNames = Set(characters.map { dcaAssignmentNameKey($0.dcaName) })
        for definition in definitions {
            let names = [definition.name] + splitLegacyAssignmentNames(definition.members)
            for name in names {
                let display = name.trimmingCharacters(in: .whitespacesAndNewlines)
                let key = dcaAssignmentNameKey(display)
                if !key.isEmpty && knownNames.insert(key).inserted {
                    characters.append(DCAProjectCharacter(dcaName: display))
                }
            }
        }

        for stateIndex in states.indices {
            for dcaIndex in states[stateIndex].dcaAssignments.indices {
                var entries: [String] = []
                var seen: Set<String> = []
                for line in states[stateIndex].dcaAssignments[dcaIndex]
                    .components(separatedBy: .newlines) {
                    let display = line.trimmingCharacters(in: .whitespacesAndNewlines)
                    guard !display.isEmpty else { continue }
                    // Retain explicitly typed alias variants, while avoiding
                    // duplicate entries when several old labels overlap.
                    if seen.insert(projectNameKey(display)).inserted {
                        entries.append(display)
                    }
                    for definition in definitionsByName[dcaAssignmentNameKey(display)] ?? [] {
                        for member in splitLegacyAssignmentNames(definition.members) {
                            let name = member.trimmingCharacters(in: .whitespacesAndNewlines)
                            if !name.isEmpty && seen.insert(projectNameKey(name)).inserted {
                                entries.append(name)
                            }
                        }
                    }
                }
                states[stateIndex].dcaAssignments[dcaIndex] = entries.joined(separator: "\n")
            }
        }
    }

    func writeConvertedCopy(beside sourceURL: URL) throws -> URL {
        let folder = sourceURL.deletingLastPathComponent()
        let stem = sourceURL.deletingPathExtension().lastPathComponent
        var suffix = 1
        var destination = folder.appendingPathComponent("\(stem) - converted.dcamarker")
        while FileManager.default.fileExists(atPath: destination.path) {
            suffix += 1
            destination = folder.appendingPathComponent("\(stem) - converted \(suffix).dcamarker")
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(self)
        try data.write(to: destination, options: .withoutOverwriting)
        return destination
    }

    var validationIssues: [String] {
        validationIssues(for: .english)
    }

    func validationIssues(for language: AppLanguage) -> [String] {
        Array(
            (
                blockingValidationIssues(for: language)
                + advisoryIssues(for: language)
            ).prefix(12)
        )
    }

    func blockingValidationIssues(for language: AppLanguage) -> [String] {
        var issues: [String] = []
        let usableCharacters = characters.filter {
            !$0.dcaName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        }
        let names = usableCharacters.map {
            $0.dcaName.trimmingCharacters(in: .whitespacesAndNewlines)
                .folding(options: [.caseInsensitive, .diacriticInsensitive], locale: .current)
        }
        let duplicateNames = Dictionary(grouping: names, by: { $0 })
            .filter { !$0.key.isEmpty && $0.value.count > 1 }
            .keys
            .sorted()
        if !duplicateNames.isEmpty {
            issues.append(
                language.text(
                    "Duplicate DCA Name: \(duplicateNames.joined(separator: ", ")).",
                    "DCA Name 重复：\(duplicateNames.joined(separator: "、"))。"
                )
            )
        }

        var roleOwners: [
            String: (displayName: String, owners: Set<String>)
        ] = [:]
        for character in usableCharacters {
            let owner = character.dcaName.trimmingCharacters(
                in: .whitespacesAndNewlines
            )
            let ownerKey = projectNameKey(owner)
            for role in splitProjectDisplayNames(character.otherCharacters) {
                let roleKey = projectNameKey(role)
                guard !roleKey.isEmpty, roleKey != ownerKey else {
                    continue
                }
                var entry = roleOwners[roleKey] ?? (
                    displayName: role,
                    owners: []
                )
                entry.owners.insert(ownerKey)
                roleOwners[roleKey] = entry
            }
        }
        for entry in roleOwners.values
            .filter({ $0.owners.count > 1 })
            .sorted(by: {
                $0.displayName.localizedCaseInsensitiveCompare(
                    $1.displayName
                ) == .orderedAscending
            }) {
            issues.append(language.text(
                "Role \"\(entry.displayName)\" is assigned to multiple DCA Names. Give each mapped role one DCA Name, or enter the printed label as its own DCA Name.",
                "角色“\(entry.displayName)”对应多个 DCA Name。请为每个映射角色指定一个 DCA Name，或将剧本标签作为独立的 DCA Name 填写。"
            ))
        }

        for (index, state) in states.enumerated() {
            let label = state.name.trimmingCharacters(in: .whitespacesAndNewlines)
            let displayLabel = label.isEmpty
                ? language.text("State \(index + 1)", "状态 \(index + 1)")
                : label
            if label.isEmpty {
                issues.append(language.text(
                    "\(displayLabel) needs a DCA State name.",
                    "\(displayLabel) 需要填写 DCA State 名称。"
                ))
            }
            if state.startLineText
                .trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                issues.append(language.text(
                    "\(displayLabel) needs Start Line Text.",
                    "\(displayLabel) 需要填写 Start Line Text。"
                ))
            }
        }
        return issues
    }

    func advisorySignatures() -> Set<String> {
        Set(duplicateDCAAssignments(in: states).map(\.signature))
    }

    func advisoryIssues(
        for language: AppLanguage,
        excluding ignoredSignatures: Set<String> = []
    ) -> [String] {
        duplicateDCAAssignments(in: states)
            .filter { !ignoredSignatures.contains($0.signature) }
            .map { duplicate in
                language.text(
                    "\(duplicate.stateName): \(duplicate.displayName) is assigned to "
                        + duplicate.dcaNumbers.map { "DCA \($0)" }
                            .joined(separator: " and ")
                        + ". This may be intentional; confirm before use.",
                    "\(duplicate.stateName)：\(duplicate.displayName) 同时分配到 "
                        + duplicate.dcaNumbers.map { "DCA \($0)" }
                            .joined(separator: " 和 ")
                        + "。这可能是有意设置，请在使用前确认。"
                )
            }
    }
}

private func projectNameKey(_ value: String) -> String {
    value.trimmingCharacters(in: .whitespacesAndNewlines)
        .folding(
            options: [.caseInsensitive, .diacriticInsensitive],
            locale: .current
        )
}

private func dcaAssignmentNameKey(_ value: String) -> String {
    let primaryName = value
        .split(separator: "[", maxSplits: 1)
        .first
        .map(String.init) ?? value
    return projectNameKey(primaryName)
}

private func splitProjectDisplayNames(_ value: String) -> [String] {
    value
        .components(separatedBy: CharacterSet(charactersIn: ",，、;；|\r\n"))
        .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
        .filter { !$0.isEmpty }
}

// Older membership fields accepted delimiters, but commas within aliases
// belong to that name and must survive the one-time conversion.
private func splitLegacyAssignmentNames(_ value: String) -> [String] {
    var parts: [String] = []
    var current = ""
    var bracketDepth = 0
    let separators = CharacterSet(charactersIn: ",，、;；|\r\n")
    for character in value {
        if character == "[" { bracketDepth += 1 }
        if character == "]" { bracketDepth = max(0, bracketDepth - 1) }
        if bracketDepth == 0 && character.unicodeScalars.allSatisfy({ separators.contains($0) }) {
            let part = current.trimmingCharacters(in: .whitespacesAndNewlines)
            if !part.isEmpty { parts.append(part) }
            current = ""
        } else {
            current.append(character)
        }
    }
    let last = current.trimmingCharacters(in: .whitespacesAndNewlines)
    if !last.isEmpty { parts.append(last) }
    return parts
}

struct DCAProjectRoleChoice: Hashable {
    let key: String
    let role: String
    let dcaName: String

    var assignmentLabel: String {
        projectRoleAssignmentLabel(dcaName: dcaName, role: role)
    }
}

// Match Excel's visible shortcut while retaining the ordinary DCA identity.
// Merge existing aliases into one bracket pair instead of nesting brackets.
func projectRoleAssignmentLabel(dcaName: String, role: String) -> String {
    func display(_ value: String) -> String {
        value.precomposedStringWithCompatibilityMapping
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
    func key(_ value: String) -> String {
        display(value).lowercased().split(whereSeparator: \.isWhitespace)
            .joined(separator: " ")
    }
    func parts(_ value: String) -> (name: String, aliases: [String]) {
        let pattern = #"^(.+?)\s*\[([^\]]+)\]$"#
        let regex = try! NSRegularExpression(pattern: pattern)
        guard let match = regex.firstMatch(
            in: value, range: NSRange(value.startIndex..., in: value)
        ), let nameRange = Range(match.range(at: 1), in: value),
           let aliasRange = Range(match.range(at: 2), in: value)
        else { return (value, []) }
        return (
            display(String(value[nameRange])),
            splitProjectDisplayNames(String(value[aliasRange]))
        )
    }

    let owner = display(dcaName)
    let role = display(role)
    guard !owner.isEmpty, !role.isEmpty else { return "" }
    let ownerParts = parts(owner)
    guard key(ownerParts.name) != key(role) else { return "" }
    let roleParts = parts(role)
    var aliases = ownerParts.aliases
    var seen = Set(aliases.map(key))
    for alias in [roleParts.name] + roleParts.aliases {
        if seen.insert(key(alias)).inserted {
            aliases.append(alias)
        }
    }
    return "\(ownerParts.name) [\(aliases.joined(separator: ", "))]"
}

func projectRoleChoices(
    from characters: [DCAProjectCharacter]
) -> [DCAProjectRoleChoice] {
    var choices: [DCAProjectRoleChoice] = []
    var seen: Set<String> = []
    for character in characters {
        let owner = character.dcaName.trimmingCharacters(
            in: .whitespacesAndNewlines
        )
        let ownerKey = projectNameKey(owner)
        guard !ownerKey.isEmpty else { continue }
        for role in splitProjectDisplayNames(character.otherCharacters) {
            let roleKey = projectNameKey(role)
            guard roleKey != dcaAssignmentNameKey(owner) else { continue }
            let key = "\(ownerKey)\u{1F}\(roleKey)"
            guard seen.insert(key).inserted else { continue }
            choices.append(DCAProjectRoleChoice(
                key: key,
                role: role,
                dcaName: owner
            ))
        }
    }
    return choices
}

private struct DuplicateDCAAssignment {
    let signature: String
    let stateName: String
    let displayName: String
    let dcaNumbers: [Int]
}

private func duplicateDCAAssignments(
    in states: [DCAProjectState]
) -> [DuplicateDCAAssignment] {
    var duplicates: [DuplicateDCAAssignment] = []

    for (stateIndex, state) in states.enumerated() {
        var assignments: [
            String: (displayName: String, dcaNumbers: Set<Int>)
        ] = [:]

        for (dcaIndex, cell) in state.dcaAssignments.enumerated() {
            for entry in cell.split(whereSeparator: \.isNewline) {
                let primary = String(entry)
                    .split(separator: "[", maxSplits: 1)
                    .first
                    .map(String.init)?
                    .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                guard !primary.isEmpty else { continue }
                let key = primary.folding(
                    options: [.caseInsensitive, .diacriticInsensitive],
                    locale: .current
                )
                var assignment = assignments[key] ?? (
                    displayName: primary,
                    dcaNumbers: []
                )
                assignment.dcaNumbers.insert(dcaIndex + 1)
                assignments[key] = assignment
            }
        }

        let stateName = state.name.trimmingCharacters(
            in: .whitespacesAndNewlines
        ).isEmpty ? "State \(stateIndex + 1)" : state.name

        for (key, assignment) in assignments {
            let numbers = assignment.dcaNumbers.sorted()
            guard numbers.count > 1 else { continue }
            duplicates.append(
                DuplicateDCAAssignment(
                    signature: "\(state.id)|\(key)|\(numbers.map(String.init).joined(separator: ","))",
                    stateName: stateName,
                    displayName: assignment.displayName,
                    dcaNumbers: numbers
                )
            )
        }
    }

    return duplicates.sorted {
        if $0.stateName == $1.stateName {
            return $0.displayName.localizedCaseInsensitiveCompare(
                $1.displayName
            ) == .orderedAscending
        }
        return $0.stateName.localizedCaseInsensitiveCompare(
            $1.stateName
        ) == .orderedAscending
    }
}

private struct DuplicateDCAAssignmentWarning: Identifiable {
    let id = UUID()
    let message: String
}

private struct DCAAssignmentFocus: Hashable {
    let stateID: String
    let dcaIndex: Int
}

private final class StateRowSelectionView: NSView {
    var onSelect: (() -> Void)?
    private var mouseDownMonitor: Any?

    // Observe the click without taking it away from a text field, picker,
    // or button. A row-wide SwiftUI gesture can compete with native editors.
    override func hitTest(_ point: NSPoint) -> NSView? { nil }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        stopObserving()
        guard window != nil else { return }
        mouseDownMonitor = NSEvent.addLocalMonitorForEvents(
            matching: .leftMouseDown
        ) { [weak self] event in
            self?.observeMouseDown(event)
            return event
        }
    }

    func observeMouseDown(_ event: NSEvent) {
        guard event.type == .leftMouseDown else { return }
        selectIfClicked(at: event.locationInWindow, in: event.window)
    }

    func selectIfClicked(at pointInWindow: NSPoint, in eventWindow: NSWindow?) {
        let point = convert(pointInWindow, from: nil)
        guard let window,
              eventWindow === window,
              !isHiddenOrHasHiddenAncestor,
              bounds.contains(point),
              visibleRect.contains(point)
        else { return }
        onSelect?()
    }

    func stopObserving() {
        if let mouseDownMonitor {
            NSEvent.removeMonitor(mouseDownMonitor)
        }
        mouseDownMonitor = nil
    }

    deinit {
        stopObserving()
    }
}

private struct StateRowSelectionReader: NSViewRepresentable {
    let onSelect: () -> Void

    func makeNSView(context: Context) -> StateRowSelectionView {
        let view = StateRowSelectionView()
        view.onSelect = onSelect
        return view
    }

    func updateNSView(_ view: StateRowSelectionView, context: Context) {
        view.onSelect = onSelect
    }

    static func dismantleNSView(
        _ view: StateRowSelectionView,
        coordinator: Void
    ) {
        view.stopObserving()
        view.onSelect = nil
    }
}

private final class StateTableHorizontalOffsetView: NSView {
    var onOffsetChange: ((CGFloat) -> Void)?

    private weak var observedClipView: NSClipView?
    private var boundsObserver: NSObjectProtocol?

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        DispatchQueue.main.async { [weak self] in
            self?.connectIfNeeded()
        }
    }

    override func viewDidMoveToSuperview() {
        super.viewDidMoveToSuperview()
        DispatchQueue.main.async { [weak self] in
            self?.connectIfNeeded()
        }
    }

    func connectIfNeeded() {
        var ancestor = superview
        var horizontalScrollView: NSScrollView?

        while let view = ancestor {
            if let scrollView = view as? NSScrollView,
               scrollView.hasHorizontalScroller,
               !scrollView.hasVerticalScroller {
                horizontalScrollView = scrollView
                break
            }
            ancestor = view.superview
        }

        guard let clipView = horizontalScrollView?.contentView else {
            return
        }

        if observedClipView === clipView {
            reportOffset()
            return
        }

        stopObserving()
        observedClipView = clipView
        clipView.postsBoundsChangedNotifications = true
        boundsObserver = NotificationCenter.default.addObserver(
            forName: NSView.boundsDidChangeNotification,
            object: clipView,
            queue: .main
        ) { [weak self] _ in
            self?.reportOffset()
        }
        reportOffset()
    }

    func stopObserving() {
        if let boundsObserver {
            NotificationCenter.default.removeObserver(boundsObserver)
        }
        boundsObserver = nil
        observedClipView = nil
    }

    private func reportOffset() {
        guard let observedClipView else { return }
        onOffsetChange?(max(0, observedClipView.bounds.minX))
    }

    deinit {
        stopObserving()
    }
}

private struct StateTableHorizontalOffsetReader: NSViewRepresentable {
    @Binding var offset: CGFloat

    func makeNSView(context: Context) -> StateTableHorizontalOffsetView {
        let view = StateTableHorizontalOffsetView()
        configure(view)
        return view
    }

    func updateNSView(
        _ view: StateTableHorizontalOffsetView,
        context: Context
    ) {
        configure(view)
        DispatchQueue.main.async { [weak view] in
            view?.connectIfNeeded()
        }
    }

    static func dismantleNSView(
        _ view: StateTableHorizontalOffsetView,
        coordinator: Void
    ) {
        view.stopObserving()
    }

    private func configure(_ view: StateTableHorizontalOffsetView) {
        let binding = _offset
        view.onOffsetChange = { newOffset in
            guard abs(binding.wrappedValue - newOffset) > 0.5 else {
                return
            }
            DispatchQueue.main.async {
                binding.wrappedValue = newOffset
            }
        }
    }
}

private final class DCAAssignmentNSTextView: NSTextView {
    var moveWithTab: ((Int) -> Void)?

    override func insertTab(_ sender: Any?) {
        moveWithTab?(1)
    }

    override func insertBacktab(_ sender: Any?) {
        moveWithTab?(-1)
    }
}

private struct DCAAssignmentTextEditor: NSViewRepresentable {
    @Binding var text: String
    let focus: DCAAssignmentFocus
    @Binding var requestedFocus: DCAAssignmentFocus?
    let transformBeforeCommit: (String) -> String
    let moveFocus: (DCAAssignmentFocus, Int) -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSScrollView()
        scrollView.borderType = .noBorder
        scrollView.drawsBackground = false
        scrollView.hasVerticalScroller = true
        scrollView.autohidesScrollers = true

        let textView = DCAAssignmentNSTextView()
        textView.delegate = context.coordinator
        textView.string = text
        textView.font = NSFont.systemFont(ofSize: NSFont.systemFontSize)
        textView.isRichText = false
        textView.importsGraphics = false
        textView.allowsUndo = true
        textView.drawsBackground = false
        textView.isHorizontallyResizable = false
        textView.isVerticallyResizable = true
        textView.autoresizingMask = [.width]
        textView.textContainerInset = NSSize(width: 1, height: 3)
        textView.textContainer?.widthTracksTextView = true
        textView.textContainer?.containerSize = NSSize(
            width: 0,
            height: CGFloat.greatestFiniteMagnitude
        )
        textView.moveWithTab = { [weak coordinator = context.coordinator] offset in
            coordinator?.moveFocus(offset: offset)
        }
        scrollView.documentView = textView
        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        context.coordinator.parent = self
        guard let textView = scrollView.documentView as? NSTextView else {
            return
        }
        if textView.string != text {
            textView.string = text
        }
        guard requestedFocus == focus else { return }
        let focusRequest = focus
        let focusBinding = _requestedFocus
        DispatchQueue.main.async {
            if scrollView.window?.firstResponder !== textView {
                scrollView.window?.makeFirstResponder(textView)
            }
            if focusBinding.wrappedValue == focusRequest {
                focusBinding.wrappedValue = nil
            }
        }
    }

    final class Coordinator: NSObject, NSTextViewDelegate {
        var parent: DCAAssignmentTextEditor

        init(parent: DCAAssignmentTextEditor) {
            self.parent = parent
        }

        func textDidChange(_ notification: Notification) {
            guard let textView = notification.object as? NSTextView else {
                return
            }
            let value = textView.string.hasSuffix("\n")
                ? parent.transformBeforeCommit(textView.string)
                : textView.string
            parent.text = value
            if textView.string != value {
                textView.string = value
                textView.setSelectedRange(
                    NSRange(location: (value as NSString).length, length: 0)
                )
            }
        }

        func textDidEndEditing(_ notification: Notification) {
            if parent.requestedFocus == parent.focus {
                parent.requestedFocus = nil
            }
            parent.text = parent.transformBeforeCommit(parent.text)
        }

        func moveFocus(offset: Int) {
            parent.text = parent.transformBeforeCommit(parent.text)
            parent.moveFocus(parent.focus, offset)
        }
    }
}

private struct CharacterRolesTextEditor: NSViewRepresentable {
    @Binding var text: String
    let moveFocus: (Int) -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSScrollView()
        scrollView.borderType = .noBorder
        scrollView.drawsBackground = false
        scrollView.hasVerticalScroller = true
        scrollView.autohidesScrollers = true

        let textView = DCAAssignmentNSTextView()
        textView.delegate = context.coordinator
        textView.string = text
        textView.font = NSFont.systemFont(ofSize: NSFont.systemFontSize)
        textView.isRichText = false
        textView.importsGraphics = false
        textView.allowsUndo = true
        textView.drawsBackground = false
        textView.isHorizontallyResizable = false
        textView.isVerticallyResizable = true
        textView.autoresizingMask = [.width]
        textView.textContainerInset = NSSize(width: 1, height: 3)
        textView.textContainer?.widthTracksTextView = true
        textView.textContainer?.containerSize = NSSize(
            width: 0,
            height: CGFloat.greatestFiniteMagnitude
        )
        textView.moveWithTab = { [weak coordinator = context.coordinator] offset in
            coordinator?.parent.moveFocus(offset)
        }
        scrollView.documentView = textView
        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        context.coordinator.parent = self
        guard let textView = scrollView.documentView as? NSTextView else {
            return
        }
        if textView.string != text {
            textView.string = text
        }
    }

    final class Coordinator: NSObject, NSTextViewDelegate {
        var parent: CharacterRolesTextEditor

        init(parent: CharacterRolesTextEditor) {
            self.parent = parent
        }

        func textDidChange(_ notification: Notification) {
            guard let textView = notification.object as? NSTextView else {
                return
            }
            parent.text = textView.string
        }
    }
}

private enum DCAProjectEditorTab: String, CaseIterable, Identifiable {
    case characters = "Character List"
    case states = "DCA States"

    var id: String { rawValue }
}

private final class ProjectEditorWindowView: NSView {
    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        guard let window else { return }
        window.styleMask.insert(.resizable)
        window.contentMinSize = NSSize(width: 820, height: 540)
    }
}

private struct ProjectEditorWindowConfigurator: NSViewRepresentable {
    func makeNSView(context: Context) -> NSView {
        ProjectEditorWindowView()
    }

    func updateNSView(_ nsView: NSView, context: Context) {}
}

private struct PrimaryAddButtonLabel: View {
    let title: String

    var body: some View {
        Label(title, systemImage: "plus")
            .font(.system(size: 15, weight: .semibold))
            .frame(minWidth: 200, minHeight: 34)
            .padding(.horizontal, 12)
            .padding(.vertical, 4)
            .contentShape(Rectangle())
    }
}

struct DCAProjectEditor: View {
    @Environment(\.appLanguage) private var language
    @Binding var project: DCAProjectDocument
    @Binding var ignoredAdvisorySignatures: Set<String>
    let projectPath: String
    let save: () -> Void
    let exportExcel: () -> Void
    let close: () -> Void

    @State private var selectedTab = DCAProjectEditorTab.characters
    @State private var selectedStateID = ""
    @State private var focusedDCAAssignment: DCAAssignmentFocus?
    @State private var activeDCANamePicker: DCAAssignmentFocus?
    @FocusState private var focusedCharacterNameID: String?
    @State private var showValidation = false
    @State private var autosaveWorkItem: DispatchWorkItem?
    @State private var duplicateAssignmentWarning: (
        DuplicateDCAAssignmentWarning?
    )
    @State private var warnedDuplicateAssignments: Set<String> = []
    @State private var stateTableHorizontalOffset: CGFloat = 0

    private var selectedStateIndex: Int? {
        project.states.firstIndex { $0.id == selectedStateID }
    }

    private var blockingValidationIssues: [String] {
        project.blockingValidationIssues(for: language)
    }

    private var visibleAdvisoryIssues: [String] {
        project.advisoryIssues(
            for: language,
            excluding: ignoredAdvisorySignatures
        )
    }

    private var validationIssues: [String] {
        Array(
            (blockingValidationIssues + visibleAdvisoryIssues).prefix(12)
        )
    }

    private func t(_ english: String, _ chinese: String) -> String {
        language.text(english, chinese)
    }

    private var characterListDCANames: [String] {
        var seen: Set<String> = []
        return project.characters.compactMap { character in
            let name = character.dcaName.trimmingCharacters(
                in: .whitespacesAndNewlines
            )
            guard !name.isEmpty else { return nil }
            let key = name.folding(
                options: [.caseInsensitive, .diacriticInsensitive],
                locale: .current
            )
            guard seen.insert(key).inserted else { return nil }
            return name
        }
    }

    private var characterListPickerIdentity: String {
        let roleIdentity = characterListRoleChoices.map {
            "\($0.key):\($0.role):\($0.dcaName)"
        }
        return (characterListDCANames + roleIdentity)
            .joined(separator: "\u{1F}")
    }

    private var characterListRoleChoices: [DCAProjectRoleChoice] {
        projectRoleChoices(from: project.characters)
    }

    var body: some View {
        VStack(spacing: 0) {
            editorHeader
            Divider()

            HStack(spacing: 0) {
                VStack(alignment: .leading, spacing: 10) {
                    ForEach(DCAProjectEditorTab.allCases) { tab in
                        Button {
                            switchEditorTab(to: tab)
                        } label: {
                            Label(
                                language.label(tab.rawValue),
                                systemImage: tab == .characters
                                    ? "person.2"
                                    : "list.number"
                            )
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.vertical, 7)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(selectedTab == tab ? .blue : .gray)
                    }
                    Spacer()
                }
                .padding(14)
                .frame(width: 190)
                .background(Color.secondary.opacity(0.06))

                Divider()

                Group {
                    if selectedTab == .characters {
                        characterListEditor
                    } else {
                        stateEditor
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }

            Divider()
            editorFooter
        }
        .frame(
            minWidth: 820,
            idealWidth: 1180,
            minHeight: 540,
            idealHeight: 760
        )
        .background(Color(red: 0.94, green: 0.96, blue: 0.98))
        .background(ProjectEditorWindowConfigurator())
        .onAppear {
            project.normalise()
            selectedStateID = project.states.first?.id ?? ""
            DispatchQueue.main.async {
                checkForDuplicateAssignments(in: project.states)
            }
        }
        .onChange(of: project.states) { states in
            if !states.contains(where: { $0.id == selectedStateID }) {
                selectedStateID = states.first?.id ?? ""
            }
            checkForDuplicateAssignments(in: states)
        }
        .onChange(of: project) { _ in
            autosaveWorkItem?.cancel()
            let workItem = DispatchWorkItem { save() }
            autosaveWorkItem = workItem
            DispatchQueue.main.asyncAfter(
                deadline: .now() + 0.7,
                execute: workItem
            )
        }
        .onDisappear {
            autosaveWorkItem?.cancel()
            save()
        }
        .alert(item: $duplicateAssignmentWarning) { warning in
            Alert(
                title: Text(
                    t(
                        "Duplicate DCA Assignment",
                        "重复的 DCA 分配"
                    )
                ),
                message: Text(warning.message),
                primaryButton: .default(Text(t("Review", "检查"))),
                secondaryButton: .default(Text(t("Ignore", "忽略"))) {
                    ignoreCurrentDuplicateAdvisories()
                }
            )
        }
    }

    private var editorHeader: some View {
        HStack(spacing: 14) {
            VStack(alignment: .leading, spacing: 3) {
                TextField(t("Project name", "项目名称"), text: $project.name)
                    .font(.title2.bold())
                    .textFieldStyle(.plain)
                Text(projectPath)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .truncationMode(.middle)
            }

            Spacer()

            Button(language.label("Export Excel"), action: exportExcel)
                .help(t(
                    "Create a standard Excel workbook from this project",
                    "从当前项目创建标准 Excel 工作簿"
                ))
            Button {
                enlargeEditorWindow()
            } label: {
                Label(
                    language.label("Enlarge"),
                    systemImage: "arrow.up.left.and.arrow.down.right"
                )
            }
            .help(t("Enlarge the project editor", "放大项目编辑窗口"))
            Button(language.label("Save Project"), action: save)
                .buttonStyle(.borderedProminent)
                .keyboardShortcut("s", modifiers: [.command])
        }
        .padding(18)
    }

    private func enlargeEditorWindow() {
        guard let window = NSApp.keyWindow ?? NSApp.mainWindow,
              let screen = window.screen ?? NSScreen.main else {
            return
        }

        // Use nearly the complete visible display. The former 1,240-point
        // target left much of a large screen unused and exposed only about
        // seven DCA assignment columns at once.
        let available = screen.visibleFrame.insetBy(dx: 12, dy: 12)
        let frameDecorationWidth = max(
            0,
            window.frame.width - window.contentLayoutRect.width
        )
        let frameDecorationHeight = max(
            0,
            window.frame.height - window.contentLayoutRect.height
        )
        let targetWidth = max(
            820,
            available.width - frameDecorationWidth
        )
        let targetHeight = max(
            540,
            available.height - frameDecorationHeight
        )

        window.setContentSize(
            NSSize(width: targetWidth, height: targetHeight)
        )
        if window.sheetParent == nil {
            window.setFrameOrigin(
                NSPoint(x: available.minX, y: available.minY)
            )
        }
    }

    private var characterListEditor: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 12) {
                VStack(alignment: .leading, spacing: 3) {
                    Text(language.label("Character List"))
                        .font(.title3.bold())
                    Text(t(
                        "Character List is optional. Put each ordinary DCA Name on its own row. Fill Other Script Characters Played only when that DCA Name performs an additional, differently named script character. If you do not need to track a group's members, enter its printed group label here as an ordinary DCA Name and leave column B blank.",
                        "Character List 为可选项。每个普通 DCA Name 单独填写一行。只有当该 DCA Name 还扮演另一个名称不同的剧本角色时，才填写 Other Script Characters Played。如果不需要记录群组成员，可把剧本中的群组标签作为普通 DCA Name 填在这里，并将 B 列留空。"
                    ))
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Label(
                        t(
                            "DCA Name example: TOM • JERRY • APPLE • ALL THREE — column B blank • Tab: next row",
                            "DCA Name 示例：TOM • JERRY • APPLE • ALL THREE — B 列留空 • Tab：下一行"
                        ),
                        systemImage: "keyboard"
                    )
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.blue.opacity(0.78))
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                Button {
                    project.characters.append(DCAProjectCharacter())
                } label: {
                    PrimaryAddButtonLabel(
                        title: language.label("Add DCA Name")
                    )
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .fixedSize()

                Color.clear
                    .frame(maxWidth: .infinity, minHeight: 1)
            }
            .fixedSize(horizontal: false, vertical: true)

            HStack(spacing: 10) {
                Text(language.label("DCA Name"))
                    .font(.system(size: 14, weight: .bold))
                    .foregroundStyle(.blue)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 9)
                    .frame(width: 220, alignment: .leading)
                    .background(
                        Color.blue.opacity(0.16),
                        in: RoundedRectangle(cornerRadius: 7)
                    )
                Text(language.label(
                    "Other Script Characters Played — one per line"
                ))
                    .font(.system(size: 14, weight: .bold))
                    .foregroundStyle(.orange)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 9)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(
                        Color.yellow.opacity(0.22),
                        in: RoundedRectangle(cornerRadius: 7)
                    )
                Color.clear.frame(width: 34)
            }
            .padding(.horizontal, 10)
            .fixedSize(horizontal: false, vertical: true)

            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(project.characters.indices, id: \.self) { index in
                        HStack(alignment: .top, spacing: 10) {
                            TextField(
                                language.label("DCA Name"),
                                text: $project.characters[index].dcaName
                            )
                            .textFieldStyle(.roundedBorder)
                            .focused(
                                $focusedCharacterNameID,
                                equals: project.characters[index].id
                            )
                            .padding(8)
                            .frame(width: 220)
                            .background(
                                Color.blue.opacity(0.09),
                                in: RoundedRectangle(cornerRadius: 8)
                            )

                            CharacterRolesTextEditor(
                                text: $project.characters[index].otherCharacters,
                                moveFocus: { offset in
                                    moveCharacterRolesFocus(
                                        from: project.characters[index].id,
                                        offset: offset
                                    )
                                }
                            )
                            .frame(height: 68)
                            .padding(4)
                            .background(.background)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(Color.secondary.opacity(0.25))
                            )
                            .padding(8)
                            .background(
                                Color.yellow.opacity(0.13),
                                in: RoundedRectangle(cornerRadius: 8)
                            )

                            Button(role: .destructive) {
                                project.characters.remove(at: index)
                                if project.characters.isEmpty {
                                    project.characters.append(DCAProjectCharacter())
                                }
                            } label: {
                                Image(systemName: "trash")
                            }
                            .buttonStyle(.borderless)
                            .frame(width: 34, height: 32)
                            .help(t(
                                "Remove this DCA Name",
                                "删除此 DCA Name"
                            ))
                        }
                        .padding(10)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .topLeading)
            }
            .frame(
                maxWidth: .infinity,
                maxHeight: .infinity,
                alignment: .topLeading
            )
            .layoutPriority(1)
        }
        .padding(18)
    }

    private var stateEditor: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top, spacing: 12) {
                VStack(alignment: .leading, spacing: 3) {
                    Text(language.label("DCA States"))
                        .font(.title3.bold())
                    Text(
                        t(
                            "One row per state; scroll right for all fields.",
                            "每个状态一行；向右滚动查看并编辑全部栏目。"
                        )
                    )
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)

                    Label(
                        t(
                            "Tab: next DCA cell • Return: new line",
                            "Tab：下一个 DCA 单元格 • Return（回车）：换行"
                        ),
                        systemImage: "keyboard"
                    )
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.blue.opacity(0.78))
                    .lineLimit(1)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                Button {
                    addState()
                } label: {
                    PrimaryAddButtonLabel(
                        title: language.label("Add DCA State")
                    )
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .fixedSize()

                VStack(alignment: .trailing, spacing: 7) {
                    Color.clear.frame(height: 26)

                    HStack(spacing: 8) {
                        Button {
                            duplicateSelectedState()
                        } label: {
                            Label(
                                language.label("Duplicate Row"),
                                systemImage: "plus.square.on.square"
                            )
                        }
                        .disabled(selectedStateIndex == nil)

                        Button(role: .destructive) {
                            deleteSelectedState()
                        } label: {
                            Label(
                                language.label("Delete Row"),
                                systemImage: "trash"
                            )
                        }
                        .disabled(
                            selectedStateIndex == nil || project.states.count <= 1
                        )
                    }
                }
                .frame(maxWidth: .infinity, alignment: .trailing)
            }

            ScrollView(.horizontal) {
                VStack(spacing: 0) {
                    stateTableHeader
                    Divider()

                    ScrollView(.vertical) {
                        LazyVStack(spacing: 0) {
                            ForEach(project.states.indices, id: \.self) { index in
                                stateTableRow(index: index)
                                Divider()
                            }
                        }
                    }
                }
                .background(
                    StateTableHorizontalOffsetReader(
                        offset: $stateTableHorizontalOffset
                    )
                )
            }
            .background(.background)
            .clipShape(RoundedRectangle(cornerRadius: 9))
            .overlay(
                RoundedRectangle(cornerRadius: 9)
                    .stroke(Color.secondary.opacity(0.22))
            )
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 14)
    }

    private var stateTableHeader: some View {
        HStack(spacing: 0) {
            HStack(spacing: 0) {
                stateHeaderCell(
                    language.label("No."),
                    width: 48,
                    colour: .blue
                )
                stateHeaderCell(
                    language.label("DCA State"),
                    width: 150,
                    colour: .blue
                )
            }
            .background(Color(nsColor: .controlBackgroundColor))
            .overlay(alignment: .trailing) {
                Rectangle()
                    .fill(Color.secondary.opacity(0.28))
                    .frame(width: 1)
            }
            .offset(x: frozenStateIdentityOffset)
            .zIndex(2)

            stateHeaderCell(language.label("Start Line Character"), width: 180, colour: .blue)
            stateHeaderCell(language.label("Start Line Text"), width: 310, colour: .blue)
            stateHeaderCell(language.label("State Start Position"), width: 140, colour: .blue)
            stateHeaderCell(language.label("Page Hint"), width: 100, colour: .blue)
            ForEach(0..<12, id: \.self) { dcaIndex in
                stateHeaderCell(
                    "DCA \(dcaIndex + 1)",
                    width: 150,
                    colour: .orange,
                    alignment: .center
                )
            }
            stateHeaderCell(language.label("Notes"), width: 190, colour: .blue)
            stateHeaderCell("", width: 42, colour: .blue)
        }
    }

    private func stateHeaderCell(
        _ title: String,
        width: CGFloat,
        colour: Color,
        alignment: Alignment = .leading
    ) -> some View {
        Text(title)
            .font(.caption.bold())
            .foregroundStyle(colour)
            .padding(.horizontal, 7)
            .frame(width: width, alignment: alignment)
            .padding(.vertical, 9)
            .background(colour.opacity(0.11))
    }

    private func stateTableRow(index: Int) -> some View {
        let stateID = project.states[index].id
        let isSelected = stateID == selectedStateID

        return HStack(alignment: .top, spacing: 0) {
            HStack(alignment: .top, spacing: 0) {
                Button {
                    selectedStateID = stateID
                } label: {
                    Text("\(index + 1)")
                        .frame(width: 48, height: 76)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.borderless)
                .foregroundStyle(
                    isSelected ? Color.white : Color.blue
                )
                .background(
                    isSelected ? Color.blue : Color.clear
                )
                .help(t("Select this DCA State row", "选择此 DCA 状态行"))

                stateTextField(
                    language.label("DCA State"),
                    text: $project.states[index].name,
                    width: 150
                )
            }
            .background(
                Color.blue.opacity(0.055)
            )
            .background(Color(nsColor: .controlBackgroundColor))
            .overlay(alignment: .trailing) {
                Rectangle()
                    .fill(Color.secondary.opacity(0.22))
                    .frame(width: 1)
            }
            .offset(x: frozenStateIdentityOffset)
            .zIndex(2)

            stateTextField(
                t("Character", "角色"),
                text: $project.states[index].startLineCharacter,
                width: 180
            )
            stateTextEditor(
                text: $project.states[index].startLineText,
                width: 310
            )

            Picker(
                language.label("State Start Position"),
                selection: $project.states[index].startPosition
            ) {
                Text(language.label("Before")).tag("Before")
                Text(language.label("After")).tag("After")
            }
            .labelsHidden()
            .padding(.horizontal, 7)
            .frame(width: 140, height: 76)

            stateTextField(
                t("Page", "页码"),
                text: $project.states[index].pageHint,
                width: 100,
                verticalAlignment: .center
            )

            ForEach(0..<12, id: \.self) { dcaIndex in
                stateDCAAssignmentEditor(
                    text: $project.states[index]
                        .dcaAssignments[dcaIndex],
                    focus: DCAAssignmentFocus(
                        stateID: project.states[index].id,
                        dcaIndex: dcaIndex
                    ),
                    width: 150,
                    background: Color.yellow.opacity(0.075)
                )
            }

            stateTextEditor(
                text: $project.states[index].notes,
                width: 190
            )

            Button(role: .destructive) {
                deleteState(at: index)
            } label: {
                Image(systemName: "trash")
            }
            .buttonStyle(.borderless)
            .disabled(project.states.count <= 1)
            .frame(width: 42, height: 76)
            .help(t("Delete this DCA State row", "删除此 DCA 状态行"))
        }
        .background(Color.blue.opacity(0.055))
        .background(StateRowSelectionReader {
            guard selectedStateID != stateID else { return }
            selectedStateID = stateID
        })
        .overlay {
            Rectangle()
                .strokeBorder(
                    Color.blue.opacity(isSelected ? 0.45 : 0),
                    lineWidth: 1
                )
                .allowsHitTesting(false)
        }
    }

    private var frozenStateIdentityOffset: CGFloat {
        stateTableHorizontalOffset
    }

    private func stateTextField(
        _ placeholder: String,
        text: Binding<String>,
        width: CGFloat,
        verticalAlignment: Alignment = .top
    ) -> some View {
        TextField(placeholder, text: text)
            .textFieldStyle(.roundedBorder)
            .padding(.horizontal, 7)
            .frame(
                width: width,
                height: 76,
                alignment: verticalAlignment
            )
    }

    private func stateTextEditor(
        text: Binding<String>,
        width: CGFloat,
        background: Color = Color.clear
    ) -> some View {
        let outerInset: CGFloat = 7
        let editorInset: CGFloat = 4

        return TextEditor(text: text)
            .font(.body)
            .frame(
                width: width - (outerInset * 2) - (editorInset * 2),
                height: 54
            )
            .padding(editorInset)
            .background(background)
            .overlay(
                RoundedRectangle(cornerRadius: 5)
                    .stroke(Color.secondary.opacity(0.22))
            )
            .padding(.horizontal, outerInset)
            .padding(.vertical, outerInset)
    }

    private func stateDCAAssignmentEditor(
        text: Binding<String>,
        focus: DCAAssignmentFocus,
        width: CGFloat,
        background: Color
    ) -> some View {
        let outerInset: CGFloat = 7
        let editorInset: CGFloat = 4
        let pickerIsPresented = Binding<Bool>(
            get: { activeDCANamePicker == focus },
            set: { isPresented in
                if !isPresented && activeDCANamePicker == focus {
                    activeDCANamePicker = nil
                }
            }
        )

        return ZStack(alignment: .topTrailing) {
            DCAAssignmentTextEditor(
                text: text,
                focus: focus,
                requestedFocus: $focusedDCAAssignment,
                transformBeforeCommit: { $0 },
                moveFocus: moveDCAAssignmentFocus
            )
            .frame(
                width: width - (outerInset * 2) - (editorInset * 2),
                height: 54
            )
            .padding(editorInset)
            .background(background)
            .overlay(
                RoundedRectangle(cornerRadius: 5)
                    .stroke(Color.secondary.opacity(0.22))
            )
            .padding(.horizontal, outerInset)
            .padding(.vertical, outerInset)

            Button {
                activeDCANamePicker = focus
                focusedDCAAssignment = focus
            } label: {
                Image(systemName: "person.crop.circle.badge.plus")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(
                        characterListDCANames.isEmpty
                            ? Color.secondary
                            : Color.blue
                    )
                    .frame(width: 24, height: 22)
                    .background(
                        Color(nsColor: .controlBackgroundColor).opacity(0.92),
                        in: RoundedRectangle(cornerRadius: 5)
                    )
            }
            .buttonStyle(.plain)
            .id(
                "\(focus.stateID)|\(focus.dcaIndex)|"
                + characterListPickerIdentity
            )
            .fixedSize()
            .padding(.top, 9)
            .padding(.trailing, 9)
            .disabled(characterListDCANames.isEmpty)
            .help(
                characterListDCANames.isEmpty
                    ? t(
                        "Add DCA Names to Character List first",
                        "请先在 Character List 中添加 DCA Name"
                    )
                    : t(
                        "Choose a DCA Name from Character List",
                        "从 Character List 选择 DCA Name"
                    )
            )
            .popover(
                isPresented: pickerIsPresented,
                arrowEdge: .trailing
            ) {
                VStack(alignment: .leading, spacing: 12) {
                    Text(t("Add DCA Names", "添加 DCA Name"))
                        .font(.headline)

                    Text(t(
                        "Choose a DCA Name, or a script role to keep DCA Name [Role] in the cell, like Excel.",
                        "请选择 DCA Name，或选择剧本角色，在单元格中保留 DCA Name [角色]，与 Excel 一致。"
                    ))
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    ScrollView {
                        LazyVStack(spacing: 3) {
                            Text(t("DCA Names", "DCA Name"))
                                .font(.caption.bold())
                                .foregroundStyle(.secondary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, 8)

                            ForEach(characterListDCANames, id: \.self) { name in
                                let isSelected = dcaCellContains(
                                    name,
                                    in: text.wrappedValue
                                )
                                Button {
                                    addDCAName(name, to: text)
                                    focusedDCAAssignment = focus
                                } label: {
                                    HStack(spacing: 9) {
                                        Image(systemName: isSelected
                                            ? "checkmark.circle.fill"
                                            : "plus.circle"
                                        )
                                        .foregroundStyle(
                                            isSelected ? .green : .blue
                                        )
                                        Text(name)
                                            .foregroundStyle(
                                                isSelected
                                                    ? Color.secondary
                                                    : Color.primary
                                            )
                                        Spacer()
                                    }
                                    .contentShape(Rectangle())
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 6)
                                }
                                .buttonStyle(.plain)
                                .disabled(isSelected)
                            }

                            if !characterListRoleChoices.isEmpty {
                                Divider()
                                    .padding(.vertical, 3)

                                Text(t(
                                    "Other Script Characters Played",
                                    "饰演的其他剧本角色"
                                ))
                                    .font(.caption.bold())
                                    .foregroundStyle(.secondary)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .padding(.horizontal, 8)

                                ForEach(characterListRoleChoices, id: \.key) { choice in
                                    let isSelected = dcaCellContains(
                                        choice.dcaName,
                                        in: text.wrappedValue
                                    )
                                    Button {
                                        addDCAName(choice.assignmentLabel, to: text)
                                        focusedDCAAssignment = focus
                                    } label: {
                                        HStack(spacing: 9) {
                                            Image(systemName: isSelected
                                                ? "checkmark.circle.fill"
                                                : "plus.circle"
                                            )
                                            .foregroundStyle(
                                                isSelected ? .green : .blue
                                            )
                                            VStack(alignment: .leading, spacing: 2) {
                                                Text(choice.role)
                                                    .foregroundStyle(
                                                        isSelected
                                                            ? Color.secondary
                                                            : Color.primary
                                                    )
                                                Text(t(
                                                    "Adds \(choice.assignmentLabel)",
                                                    "填入 \(choice.assignmentLabel)"
                                                ))
                                                    .font(.caption2)
                                                    .foregroundStyle(.secondary)
                                            }
                                            Spacer()
                                        }
                                        .contentShape(Rectangle())
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 6)
                                    }
                                    .buttonStyle(.plain)
                                    .disabled(isSelected)
                                }
                            }

                        }
                    }
                    .frame(maxHeight: 300)

                    Divider()

                    HStack {
                        Spacer()
                        Button(language.label("Done")) {
                            activeDCANamePicker = nil
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .padding(16)
                .frame(width: 285)
            }
        }
        .frame(width: width, height: 76)
        .background(background)
    }

    private func addDCAName(_ name: String, to text: Binding<String>) {
        let current = text.wrappedValue.trimmingCharacters(
            in: .whitespacesAndNewlines
        )
        let newKey = dcaAssignmentNameKey(name)
        let existingKeys = current
            .split(whereSeparator: \.isNewline)
            .map { dcaAssignmentNameKey(String($0)) }

        guard !existingKeys.contains(newKey) else { return }
        text.wrappedValue = current.isEmpty ? name : "\(current)\n\(name)"
    }

    private func dcaCellContains(_ name: String, in text: String) -> Bool {
        let nameKey = dcaAssignmentNameKey(name)
        return text
            .split(whereSeparator: \.isNewline)
            .contains { dcaAssignmentNameKey(String($0)) == nameKey }
    }

    private var editorFooter: some View {
        VStack(spacing: 8) {
            if showValidation && !validationIssues.isEmpty {
                VStack(alignment: .leading, spacing: 3) {
                    HStack {
                        Label(
                            t(
                                "Please review these setup items:",
                                "请检查以下设置项目："
                            ),
                            systemImage: "exclamationmark.triangle.fill"
                        )
                        .font(.caption.bold())
                        .foregroundStyle(.orange)

                        Spacer()

                        if !visibleAdvisoryIssues.isEmpty {
                            Button {
                                ignoreCurrentDuplicateAdvisories()
                            } label: {
                                Image(systemName: "xmark.circle.fill")
                            }
                            .buttonStyle(.plain)
                            .foregroundStyle(.secondary)
                            .help(t(
                                "Ignore repeated-assignment reminders for this project session",
                                "在本次项目会话中忽略重复分配提醒"
                            ))
                            .accessibilityLabel(t(
                                "Ignore repeated-assignment reminders",
                                "忽略重复分配提醒"
                            ))
                        }
                    }
                    ForEach(validationIssues, id: \.self) { issue in
                        Text("• \(issue)")
                            .font(.caption)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }

            HStack {
                Button {
                    showValidation.toggle()
                } label: {
                    Label(
                        validationIssues.isEmpty
                            ? t("Setup check passed", "设置检查通过")
                            : t(
                                "\(validationIssues.count) setup item(s)",
                                "\(validationIssues.count) 个设置问题"
                            ),
                        systemImage: validationIssues.isEmpty
                            ? "checkmark.circle.fill"
                            : "exclamationmark.triangle.fill"
                    )
                }
                .buttonStyle(.borderless)
                .foregroundStyle(
                    validationIssues.isEmpty ? .green : .orange
                )

                Spacer()

                Text(t(
                    "Changes autosave to the local project file.",
                    "修改会自动保存到本地项目文件。"
                ))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Button(language.label("Done")) {
                    save()
                    close()
                }
                .buttonStyle(.borderedProminent)
                .keyboardShortcut(.defaultAction)
            }
        }
        .padding(14)
    }

    private func checkForDuplicateAssignments(
        in states: [DCAProjectState]
    ) {
        let duplicates = duplicateDCAAssignments(in: states)
        let activeSignatures = Set(duplicates.map(\.signature))
        warnedDuplicateAssignments.formIntersection(activeSignatures)

        guard duplicateAssignmentWarning == nil,
              let duplicate = duplicates.first(where: {
                  !warnedDuplicateAssignments.contains($0.signature)
                      && !ignoredAdvisorySignatures.contains($0.signature)
              }) else {
            return
        }

        warnedDuplicateAssignments.insert(duplicate.signature)
        let dcaList = duplicate.dcaNumbers
            .map { "DCA \($0)" }
            .joined(separator: ", ")
        duplicateAssignmentWarning = DuplicateDCAAssignmentWarning(
            message: t(
                "“\(duplicate.displayName)” appears in \(dcaList) for \(duplicate.stateName). This may be intentional, so it will not stop generation. Please confirm it before using the marked script.",
                "在 \(duplicate.stateName) 中，“\(duplicate.displayName)” 同时出现在 \(dcaList)。这可能是有意设置，因此不会阻止生成；请在使用标注剧本前确认。"
            )
        )
    }

    private func ignoreCurrentDuplicateAdvisories() {
        let signatures = project.advisorySignatures()
        ignoredAdvisorySignatures.formUnion(signatures)
        warnedDuplicateAssignments.formUnion(signatures)
        duplicateAssignmentWarning = nil
        if blockingValidationIssues.isEmpty {
            showValidation = false
        }
    }

    private func switchEditorTab(to tab: DCAProjectEditorTab) {
        guard tab != selectedTab else { return }
        NSApp.keyWindow?.makeFirstResponder(nil)
        DispatchQueue.main.async {
            selectedTab = tab
        }
    }

    private func addState() {
        let state = DCAProjectState()
        project.states.append(state)
        selectedStateID = state.id
    }

    private func duplicateSelectedState() {
        guard let index = selectedStateIndex else { return }
        var copy = project.states[index]
        copy.id = UUID().uuidString
        copy.name = copy.name.isEmpty ? "" : "\(copy.name) Copy"
        project.states.insert(copy, at: index + 1)
        selectedStateID = copy.id
    }

    private func deleteSelectedState() {
        guard let index = selectedStateIndex,
              project.states.count > 1 else { return }
        deleteState(at: index)
    }

    private func deleteState(at index: Int) {
        guard project.states.indices.contains(index),
              project.states.count > 1 else { return }
        let removedID = project.states[index].id
        project.states.remove(at: index)
        if selectedStateID == removedID {
            selectedStateID = project.states[
                min(index, project.states.count - 1)
            ].id
        }
    }

    private func moveCharacterRolesFocus(
        from characterID: String,
        offset: Int
    ) {
        guard let currentIndex = project.characters.firstIndex(
            where: { $0.id == characterID }
        ) else {
            return
        }

        var targetIndex = currentIndex
        if offset > 0 {
            targetIndex = currentIndex + 1
            if targetIndex >= project.characters.count {
                let current = project.characters[currentIndex]
                let hasContent = !current.dcaName.trimmingCharacters(
                    in: .whitespacesAndNewlines
                ).isEmpty || !current.otherCharacters.trimmingCharacters(
                    in: .whitespacesAndNewlines
                ).isEmpty

                if hasContent {
                    project.characters.append(DCAProjectCharacter())
                } else {
                    targetIndex = currentIndex
                }
            }
        }

        guard project.characters.indices.contains(targetIndex) else { return }
        let targetID = project.characters[targetIndex].id
        DispatchQueue.main.async {
            focusedCharacterNameID = targetID
        }
    }

    private func moveDCAAssignmentFocus(
        from focus: DCAAssignmentFocus,
        offset: Int
    ) {
        guard let stateIndex = project.states.firstIndex(
            where: { $0.id == focus.stateID }
        ) else {
            return
        }
        let target = stateIndex * 12 + focus.dcaIndex + offset
        guard target >= 0, target < project.states.count * 12 else {
            return
        }
        let targetStateIndex = target / 12
        focusedDCAAssignment = DCAAssignmentFocus(
            stateID: project.states[targetStateIndex].id,
            dcaIndex: target % 12
        )
    }
}
