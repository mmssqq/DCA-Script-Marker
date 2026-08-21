// Copyright © 2026 马斯琪 Siqi Ma
// SPDX-License-Identifier: AGPL-3.0-or-later

import SwiftUI

@main
struct DCA_Script_MarkerApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            CommandGroup(replacing: .help) {
                Button("DCA Script Marker Help") {
                    NotificationCenter.default.post(
                        name: .openDCAScriptMarkerHelp,
                        object: nil
                    )
                }
                .keyboardShortcut("?", modifiers: [.command])
            }
        }
    }
}
