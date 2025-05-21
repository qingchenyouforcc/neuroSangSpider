// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick
import QtQuick.Templates as T

T.Action {
    text: qsTr("Cut")
    icon.name: "edit-cut"
    // A few styles use these values, so set them as our default
    // so that they can simply use us instead of defining their own actions.
    icon.width: 24
    icon.height: 24
    // This ensures that QIOSMenu::filterFirstResponderActions filters out any
    // duplicate actions (at least when QT_NO_SHORTCUT is not defined).
    shortcut: StandardKey.Cut
    // If the control has no cut property, Qt was built without clipboard support.
    enabled: !control.readOnly && control.selectedText.length > 0 && control.hasOwnProperty("cut")
    onTriggered: control.cut()

    // Can't be T.Control because otherwise it would fail to assign TextField/TextArea to it,
    // and we'd need TextFieldCutAction and TextAreaCutAction.
    required property var control
}
