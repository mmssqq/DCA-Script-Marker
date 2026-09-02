import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EDITOR = ROOT / "macOS App/DCA Script Marker/DCA Script Marker/DCAProjectEditor.swift"


class StateRowSelectionTests(unittest.TestCase):
    def test_row_selection_does_not_request_editing_focus(self):
        source = EDITOR.read_text(encoding="utf-8")
        row = source.split("private func stateTableRow(index: Int)", 1)[1].split(
            "private var frozenStateIdentityOffset", 1
        )[0]
        self.assertIn(".background(StateRowSelectionReader {", row)
        self.assertIn("guard selectedStateID != stateID else { return }", row)
        self.assertIn("selectedStateID = stateID", row)
        self.assertNotIn("focusedDCAAssignment =", row)
        self.assertNotIn(".onTapGesture", row)
        self.assertIn(".allowsHitTesting(false)", row)
        observer = source.split("private final class StateRowSelectionView", 1)[1].split(
            "private final class StateTableHorizontalOffsetView", 1
        )[0]
        self.assertIn("self?.observeMouseDown(event)\n            return event", observer)
        self.assertIn("view.stopObserving()", observer)
        self.assertNotIn("makeFirstResponder", observer)

    @unittest.skipUnless(
        sys.platform == "darwin" and shutil.which("swiftc"),
        "macOS Swift compiler required",
    )
    def test_native_click_selection_respects_clipping_and_preserves_typing(self):
        source = EDITOR.read_text(encoding="utf-8")
        observer = "private final class StateRowSelectionView" + source.split(
            "private final class StateRowSelectionView", 1
        )[1].split("private struct StateRowSelectionReader", 1)[0]
        harness = r'''
import AppKit

@main struct RowSelectionChecks {
    static func main() {
        _ = NSApplication.shared
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 800, height: 320),
            styleMask: [.borderless], backing: .buffered, defer: false
        )
        let root = NSView(frame: NSRect(x: 0, y: 0, width: 800, height: 320))
        window.contentView = root
        let clip = NSClipView(frame: NSRect(x: 20, y: 20, width: 500, height: 240))
        root.addSubview(clip)
        let document = NSView(frame: NSRect(x: 0, y: 0, width: 1000, height: 600))
        clip.documentView = document
        let rowA = StateRowSelectionView(frame: NSRect(x: 0, y: 20, width: 1000, height: 76))
        let rowB = StateRowSelectionView(frame: NSRect(x: 0, y: 100, width: 1000, height: 76))
        let rowC = StateRowSelectionView(frame: NSRect(x: 0, y: 180, width: 1000, height: 76))
        let rows = [rowA, rowB, rowC]
        var selected = ""
        var selections = 0
        for (row, name) in zip(rows, ["A", "B", "C"]) {
            document.addSubview(row)
            row.onSelect = { selected = name; selections += 1 }
            precondition(row.hitTest(NSPoint(x: 10, y: 10)) == nil)
        }
        let editor = NSTextView(frame: NSRect(x: 220, y: 105, width: 180, height: 65))
        editor.isRichText = false
        document.addSubview(editor)
        precondition(window.makeFirstResponder(editor))

        func click(_ x: CGFloat, _ y: CGFloat, in eventWindow: NSWindow? = nil,
                   type: NSEvent.EventType = .leftMouseDown) {
            let point = document.convert(NSPoint(x: x, y: y), to: nil)
            if type == .leftMouseDown {
                // Unshown test windows have no system window number. Pass
                // their identity directly without showing a window on screen.
                rows.forEach { $0.selectIfClicked(at: point, in: eventWindow ?? window) }
                return
            }
            let event = NSEvent.mouseEvent(
                with: type, location: point, modifierFlags: [], timestamp: 0,
                windowNumber: (eventWindow ?? window).windowNumber,
                context: nil, eventNumber: 1, clickCount: 1, pressure: 1
            )!
            rows.forEach { $0.observeMouseDown(event) }
        }
        // Number, state-name region, empty padding, and native text editor.
        for point in [NSPoint(x: 12, y: 50), NSPoint(x: 130, y: 50),
                      NSPoint(x: 420, y: 50)] {
            selected = ""
            click(point.x, point.y)
            precondition(selected == "A", "Expected A; got \(selected); visible=\(rowA.visibleRect); window=\(window.windowNumber)")
        }
        click(260, 130)
        precondition(selected == "B")
        precondition(window.firstResponder === editor)
        editor.insertText("S115", replacementRange: NSRange(location: NSNotFound, length: 0))
        precondition(editor.string == "S115")
        precondition(window.firstResponder === editor)

        // Horizontal scrolling still selects DCA cells, not hidden columns.
        clip.scroll(to: NSPoint(x: 500, y: 0))
        selected = ""
        click(750, 130)
        precondition(selected == "B")
        selected = ""
        click(250, 130)
        precondition(selected.isEmpty)

        // A clipped row must not react to clicks over the header/footer.
        clip.scroll(to: NSPoint(x: 500, y: 100))
        click(750, 50)
        precondition(selected.isEmpty)
        click(750, 205)
        precondition(selected == "C")
        let beforeIgnoredClicks = selections
        click(750, 205, type: .rightMouseDown)
        rowC.isHidden = true
        click(750, 205)
        rowC.isHidden = false
        let otherWindow = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 800, height: 320),
            styleMask: [.borderless], backing: .buffered, defer: false
        )
        click(750, 205, in: otherWindow)
        precondition(selections == beforeIgnoredClicks)

        // Row reuse replaces the callback; removing it releases the monitor.
        rowC.onSelect = { selected = "replacement" }
        click(750, 205)
        precondition(selected == "replacement")
        weak var releasedRow: StateRowSelectionView?
        autoreleasepool {
            let temporaryRow = StateRowSelectionView(frame: .zero)
            document.addSubview(temporaryRow)
            releasedRow = temporaryRow
            temporaryRow.removeFromSuperview()
        }
        precondition(releasedRow == nil)
        rows.forEach { $0.stopObserving(); $0.stopObserving() }
        print("Row selection checks passed")
    }
}
'''
        with tempfile.TemporaryDirectory(prefix="dca-row-selection-") as directory:
            directory = Path(directory)
            swift = directory / "RowSelectionChecks.swift"
            swift.write_text("import AppKit\n" + observer + harness, encoding="utf-8")
            executable = directory / "RowSelectionChecks"
            environment = dict(os.environ)
            environment["CLANG_MODULE_CACHE_PATH"] = str(directory / "clang-cache")
            compiled = subprocess.run(
                [shutil.which("swiftc"), "-parse-as-library", "-module-cache-path",
                 str(directory / "swift-cache"), str(swift), "-o", str(executable)],
                capture_output=True, text=True, timeout=180, env=environment,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            result = subprocess.run(
                [str(executable)], capture_output=True, text=True, timeout=30
            )
            numbered_source = "\n".join(
                f"{index}: {line}" for index, line in enumerate(
                    swift.read_text(encoding="utf-8").splitlines(), 1
                )
            )
            self.assertEqual(
                result.returncode, 0,
                result.stdout + result.stderr + "\n" + numbered_source,
            )
            self.assertIn("Row selection checks passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
