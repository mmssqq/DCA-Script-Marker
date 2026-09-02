// Copyright © 2026 马斯琪 Siqi Ma
// SPDX-License-Identifier: AGPL-3.0-or-later

import SwiftUI

@main
struct DCA_Script_MarkerApp: App {
    @AppStorage("appLanguage") private var appLanguageRaw = (
        AppLanguage.systemDefault.rawValue
    )

    private var appLanguage: AppLanguage {
        AppLanguage(rawValue: appLanguageRaw) ?? .english
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            CommandGroup(replacing: .help) {
                Button(appLanguage.text(
                    "DCA Script Marker Help",
                    "DCA Script Marker 帮助"
                )) {
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
