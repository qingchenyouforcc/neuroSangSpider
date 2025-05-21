// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick.Controls.Fusion
import QtQuick.Controls.Fusion.impl as FusionImpl

Menu {
    id: menu
    popupType: Popup.Window

    required property var control

    FusionImpl.CutAction {
        control: menu.control
    }
    FusionImpl.CopyAction {
        control: menu.control
    }
    FusionImpl.PasteAction {
        control: menu.control
    }
    FusionImpl.DeleteAction {
        control: menu.control
    }

    MenuSeparator {}

    FusionImpl.SelectAllAction {
        control: menu.control
    }
}
