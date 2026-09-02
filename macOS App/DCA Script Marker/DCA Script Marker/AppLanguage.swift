// Copyright © 2026 马斯琪 Siqi Ma
// SPDX-License-Identifier: AGPL-3.0-or-later

import SwiftUI

enum AppLanguage: String, CaseIterable, Identifiable {
    case english = "en"
    case simplifiedChinese = "zh-Hans"

    var id: String { rawValue }

    static var systemDefault: AppLanguage {
        let preferred = Locale.preferredLanguages.first?.lowercased() ?? ""
        return preferred.hasPrefix("zh") ? .simplifiedChinese : .english
    }

    var menuTitle: String {
        switch self {
        case .english: return "English"
        case .simplifiedChinese: return "简体中文"
        }
    }

    var locale: Locale {
        Locale(identifier: rawValue)
    }

    func text(_ english: String, _ chinese: String) -> String {
        self == .simplifiedChinese ? chinese : english
    }

    func label(_ storedValue: String) -> String {
        guard self == .simplifiedChinese else { return storedValue }
        switch storedValue {
        case "User Guide": return "使用手册"
        case "Help": return "帮助"
        case "DCA Project": return "DCA 项目"
        case "New": return "新建"
        case "Open": return "打开"
        case "Import Excel": return "导入 Excel"
        case "Export Excel": return "导出 Excel"
        case "Script PDF": return "剧本 PDF"
        case "Choose PDF": return "选择 PDF"
        case "Output Folder": return "输出文件夹"
        case "Choose Folder": return "选择文件夹"
        case "Choose Marking Style": return "选择标注方式"
        case "Editable Full Marking": return "可编辑完整标注"
        case "First Appearance Only": return "仅首次出现"
        case "DCA State Legend": return "DCA 状态图例"
        case "DCA States": return "DCA 状态"
        case "Character List": return "角色列表"
        case "DCA States Inspector": return "DCA 状态对照窗口"
        case "DCA State": return "DCA 状态"
        case "Previous": return "上一个"
        case "Next": return "下一个"
        case "Close": return "关闭"
        case "Done": return "完成"
        case "Cancel": return "取消"
        case "Continue": return "继续"
        case "Save Project": return "保存项目"
        case "Enlarge": return "放大"
        case "Add DCA Name": return "添加 DCA Name"
        case "Add DCA State": return "添加 DCA 状态"
        case "Duplicate Row": return "复制本行"
        case "Delete Row": return "删除本行"
        case "DCA Name": return "DCA Name"
        case "Other Script Characters Played — one per line":
            return "饰演的其他剧本角色 — 每行一个"
        case "No.": return "序号"
        case "Start Line Character": return "开始台词角色"
        case "Start Line Text": return "开始台词文字"
        case "State Start Position": return "状态开始位置"
        case "Page Hint": return "页码提示"
        case "Notes": return "备注"
        case "Before": return "之前"
        case "After": return "之后"
        case "Annotation Style": return "标注样式"
        case "DCA Numbers": return "DCA 编号"
        case "DCA State / Snapshot / Scene": return "DCA 状态 / Snapshot / 场景"
        case "Horizontal Position": return "水平位置"
        case "Vertical Position": return "垂直位置"
        case "Position": return "位置"
        case "Legend Position": return "图例位置"
        case "DCA State Header, Footer & Mapping": return "DCA 状态页眉、页脚与角色映射"
        case "Show Current DCA State": return "显示当前 DCA 状态"
        case "Text Colour": return "文字颜色"
        case "Text Size": return "文字大小"
        case "Text Font": return "文字字体"
        case "Border Colour": return "边框颜色"
        case "Show DCA Name / Other Script Characters":
            return "显示 DCA Name / 其他剧本角色"
        case "Colour": return "颜色"
        case "Size": return "大小"
        case "Font": return "字体"
        case "Red": return "红色"
        case "Blue": return "蓝色"
        case "Black": return "黑色"
        case "Green": return "绿色"
        case "Orange": return "橙色"
        case "Purple": return "紫色"
        case "Grey": return "灰色"
        case "Brown": return "棕色"
        case "Small": return "小"
        case "Medium": return "中"
        case "Large": return "大"
        case "Near Script": return "靠近剧本"
        case "Standard": return "标准"
        case "Far Left": return "最左侧"
        case "Slightly Up": return "稍微向上"
        case "Default": return "默认"
        case "Slightly Down": return "稍微向下"
        case "Left Gutter": return "左侧页边"
        case "Far from Script": return "远离剧本"
        case "Off": return "关闭"
        case "Header Only": return "仅页眉"
        case "Footer Only": return "仅页脚"
        case "Header and Footer": return "页眉和页脚"
        case "Edit DCA State Legends": return "编辑 DCA 状态图例"
        case "Export Edited Legend": return "导出已编辑图例"
        default: return storedValue
        }
    }
}

private struct AppLanguageEnvironmentKey: EnvironmentKey {
    static let defaultValue = AppLanguage.systemDefault
}

extension EnvironmentValues {
    var appLanguage: AppLanguage {
        get { self[AppLanguageEnvironmentKey.self] }
        set { self[AppLanguageEnvironmentKey.self] = newValue }
    }
}
