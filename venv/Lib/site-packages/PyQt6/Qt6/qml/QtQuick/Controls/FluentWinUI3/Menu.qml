// Copyright (C) 2024 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import QtQuick.Controls.impl
import QtQuick.Controls.FluentWinUI3.impl as Impl
import QtQuick.Effects

T.Menu {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding)

    leftPadding: 5
    topPadding: 5
    rightPadding: 5
    bottomPadding: 5
    margins: 0
    overlap: 4

    delegate: MenuItem { }

    contentItem: ListView {
        implicitHeight: contentHeight
        model: control.contentModel
        interactive: Window.window
                     ? contentHeight + control.topPadding + control.bottomPadding > control.height
                     : false
        currentIndex: control.currentIndex
        spacing: 4
        clip: true

        ScrollIndicator.vertical: ScrollIndicator {}
    }

    enter: Transition {
        NumberAnimation {
            property: "height"
            from: control.implicitHeight * 0.33
            to: control.implicitHeight
            easing.type: Easing.OutCubic
            duration: 250
        }
    }

    background: Impl.StyleImage {
        implicitWidth: 200
        implicitHeight: 30
        imageConfig: Config.controls.popup["normal"].background
    }

    T.Overlay.modal: Rectangle {
        color: "transparent"
    }

    T.Overlay.modeless: Rectangle {
        color: "transparent"
    }
}
