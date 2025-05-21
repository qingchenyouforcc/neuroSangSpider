// Copyright (C) 2020 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick
import QtQuick.NativeStyle as NativeStyle
import QtQuick.Controls.Windows.impl as WindowsImpl

NativeStyle.DefaultTextArea {
    id: control

    ContextMenu.menu: WindowsImpl.TextEditingContextMenu {
        control: control
    }
}
