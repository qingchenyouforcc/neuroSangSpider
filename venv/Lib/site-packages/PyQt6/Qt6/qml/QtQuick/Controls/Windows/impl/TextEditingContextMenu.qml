// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick.Controls.Windows
import QtQuick.Controls.Windows.impl as WindowsImpl

Menu {
    id: menu
    popupType: Popup.Window

    required property var control

    WindowsImpl.CutAction {
        control: menu.control
    }
    WindowsImpl.CopyAction {
        control: menu.control
    }
    WindowsImpl.PasteAction {
        control: menu.control
    }
    WindowsImpl.DeleteAction {
        control: menu.control
    }

    MenuSeparator {}

    WindowsImpl.SelectAllAction {
        control: menu.control
    }
}
