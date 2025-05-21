// Copyright (C) 2024 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick
import QtQuick.Controls.impl
import QtQuick.Controls.FluentWinUI3.impl as Impl
import QtQuick.Templates as T

T.Frame {
    id: control

    implicitWidth: Math.max((background.minimumWidth || implicitBackgroundWidth)
                            + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max((background.minimumHeight || implicitBackgroundHeight)
                            + topInset + bottomInset,
                            implicitContentHeight + topPadding + bottomPadding)

    topPadding: config.topPadding || 0
    bottomPadding: config.bottomPadding || 0
    leftPadding: config.leftPadding || 0
    rightPadding: config.rightPadding || 0

    topInset: -config.topInset || 0
    bottomInset: -config.bottomInset || 0
    leftInset: -config.leftInset || 0
    rightInset: -config.rightInset || 0

    readonly property string __currentState: !control.enabled ? "disabled" : "normal";
    readonly property var config: Config.controls.frame[__currentState] || {}

    background: Impl.StyleImage {
        imageConfig: control.config.background
    }
}
