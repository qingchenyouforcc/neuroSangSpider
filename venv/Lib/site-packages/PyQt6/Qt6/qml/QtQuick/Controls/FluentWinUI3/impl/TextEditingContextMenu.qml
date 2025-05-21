// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick.Controls.FluentWinUI3
import QtQuick.Controls.FluentWinUI3.impl as FluentWinUI3Impl

Menu {
    id: menu
    popupType: Popup.Window

    required property var control

    FluentWinUI3Impl.CutAction {
        control: menu.control
    }
    FluentWinUI3Impl.CopyAction {
        control: menu.control
    }
    FluentWinUI3Impl.PasteAction {
        control: menu.control
    }
    FluentWinUI3Impl.DeleteAction {
        control: menu.control
    }

    MenuSeparator {}

    FluentWinUI3Impl.SelectAllAction {
        control: menu.control
    }
}
