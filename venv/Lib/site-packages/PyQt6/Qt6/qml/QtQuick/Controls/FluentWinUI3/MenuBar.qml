// Copyright (C) 2024 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import QtQuick.Controls.impl
import QtQuick.Controls.FluentWinUI3.impl as Impl

T.MenuBar {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding)

    spacing: config.spacing || 0

    topPadding: SafeArea.margins.top + (config.topPadding || 0)
    bottomPadding: SafeArea.margins.bottom + (config.bottomPadding || 0)
    leftPadding: SafeArea.margins.left + (config.leftPadding || 0)
    rightPadding: SafeArea.margins.right + (config.rightPadding || 0)

    readonly property var config: Config.controls.toolbar["normal"] || {}

    delegate: MenuBarItem { }

    contentItem: Row {
        spacing: control.spacing
        Repeater {
            model: control.contentModel
        }
    }

    background: Impl.StyleImage {
        imageConfig: control.config.background
    }
}
