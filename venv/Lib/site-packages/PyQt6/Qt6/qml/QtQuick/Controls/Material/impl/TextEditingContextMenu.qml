// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick.Controls.impl
import QtQuick.Controls.Material

Menu {
    id: menu
    popupType: Popup.Window

    required property var control

    CutAction {
        control: menu.control
    }
    CopyAction {
        control: menu.control
    }
    PasteAction {
        control: menu.control
    }
    DeleteAction {
        control: menu.control
    }

    MenuSeparator {}

    SelectAllAction {
        control: menu.control
    }
}
