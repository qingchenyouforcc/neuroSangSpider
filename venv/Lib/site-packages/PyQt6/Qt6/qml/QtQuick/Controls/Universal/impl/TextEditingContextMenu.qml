// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick.Controls.Universal
import QtQuick.Controls.Universal.impl as UniversalImpl

Menu {
    id: menu
    popupType: Popup.Window

    required property var control

    UniversalImpl.CutAction {
        control: menu.control
    }
    UniversalImpl.CopyAction {
        control: menu.control
    }
    UniversalImpl.PasteAction {
        control: menu.control
    }
    UniversalImpl.DeleteAction {
        control: menu.control
    }

    MenuSeparator {}

    UniversalImpl.SelectAllAction {
        control: menu.control
    }
}
