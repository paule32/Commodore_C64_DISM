# -*- coding: utf-8 -*-
"""Stage 598: Projektziel-Auswahl als Dock-unabhängiges Qt-Popup.

Die kompatible ComboBox-API hält die bestehende Projekt-/Build-Verwaltung
unverändert. Ein QMenu (Qt.Popup) liegt außerhalb des QTreeWidget-Viewports;
seine Breite folgt den Menütexten, nicht der Breite der TreeList-Zelle.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontInfo, QFontMetrics
from PyQt5.QtWidgets import QApplication, QMenu, QSizePolicy, QToolButton


class ProjectTargetMenuButton(QToolButton):
    """Auswahlknopf mit Pfeil rechts und vollbreitem Popup-Menü.

    Die kleine QComboBox-kompatible Schnittstelle wird sowohl für die aktive
    Projektwahl als auch für Datei-/Ordnerzuordnungen genutzt.
    """

    currentIndexChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._index = -1
        self._base_tooltip = ""
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Nicht im Tree-Viewport: das QMenu ist ein eigenes Popup-Fenster.
        host = parent.window() if parent is not None else self
        self._choice_menu = QMenu(host)
        self._choice_menu.setObjectName("project_target_popup")
        # TreeList setzt Item-Widgets beim Neuladen frei. Das Popup hat einen
        # Fenster-Parent, daher muss es explizit mit seinem Knopf sterben.
        self.destroyed.connect(self._choice_menu.deleteLater)
        self._choice_menu.aboutToShow.connect(self._rebuild_menu)
        self.setMenu(self._choice_menu)
        self._update_caption()

    def clear(self):
        self._items.clear()
        self._index = -1
        self._update_caption()

    def addItem(self, label, userData=""):
        self._items.append({"label": str(label), "data": userData, "tooltip": ""})
        if self._index < 0:
            self.setCurrentIndex(0)

    def setItemData(self, index, data, role=Qt.UserRole):
        if 0 <= index < len(self._items):
            if role == Qt.ToolTipRole:
                self._items[index]["tooltip"] = str(data)
            elif role == Qt.UserRole:
                self._items[index]["data"] = data

    def count(self):
        return len(self._items)

    def findData(self, data):
        return next((index for index, item in enumerate(self._items)
                     if item["data"] == data), -1)

    def itemData(self, index, role=Qt.UserRole):
        if 0 <= index < len(self._items):
            item = self._items[index]
            return item["tooltip"] if role == Qt.ToolTipRole else item["data"]
        return None

    def setCurrentIndex(self, index):
        index = int(index)
        if index < -1 or index >= len(self._items):
            index = -1
        if index == self._index:
            self._update_caption()
            return
        self._index = index
        self._update_caption()
        self.currentIndexChanged.emit(index)

    def currentIndex(self):
        return self._index

    def currentData(self, role=Qt.UserRole):
        return self.itemData(self._index, role)

    def currentText(self):
        return (self._items[self._index]["label"]
                if 0 <= self._index < len(self._items) else "")

    def setToolTip(self, text):
        self._base_tooltip = str(text)
        self._update_caption()

    def _update_caption(self):
        label = self.currentText()
        if label:
            # Nur die Schaltfläche wird gekürzt, niemals der Popup-Eintrag.
            width = max(8, self.width() - 28)
            visible = self.fontMetrics().elidedText(label, Qt.ElideRight, width)
            self.setText(visible)
            QToolButton.setToolTip(self, label)
        else:
            self.setText("Projekt auswählen")
            QToolButton.setToolTip(self, self._base_tooltip)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_caption()

    def _menu_font(self):
        font = QFont(self.font())
        points = font.pointSizeF()
        if points <= 0:
            points = QFontInfo(font).pointSizeF()
        font.setPointSizeF((points if points > 0 else 10.0) + 1.0)
        return font

    def _rebuild_menu(self):
        menu = self._choice_menu
        menu.clear()
        font = self._menu_font()
        menu.setFont(font)
        host = self.window()
        dark = bool(getattr(host, "dark_mode_enabled", False))
        if dark:
            menu.setStyleSheet(
                "QMenu#project_target_popup { background:#252d39; color:#f7f7f7; "
                "border:1px solid #65758a; padding:3px; }"
                "QMenu#project_target_popup::item {padding:5px 18px 5px 24px;}"
                "QMenu#project_target_popup::item:selected {background:#365a81;}"
                "QMenu#project_target_popup::item:disabled {color:#94a1b1;}"
            )
        else:
            menu.setStyleSheet(
                "QMenu#project_target_popup { background:#fff; color:#222a35; "
                "border:1px solid #aeb8c4; padding:3px; }"
                "QMenu#project_target_popup::item {padding:5px 18px 5px 24px;}"
                "QMenu#project_target_popup::item:selected {background:#c9e1fb;}"
                "QMenu#project_target_popup::item:disabled {color:#697583;}"
            )
        for index, item in enumerate(self._items):
            # QMenu behandelt & sonst als Hotkey und verschluckt das Zeichen.
            action = menu.addAction(item["label"].replace("&", "&&"))
            action.setCheckable(True)
            action.setChecked(index == self._index)
            if item["tooltip"]:
                action.setToolTip(item["tooltip"])
            action.triggered.connect(
                lambda _checked=False, selected=index: self.setCurrentIndex(selected))
        # Auch bei einer nur 100px breiten Zelle wird der volle Text sichtbar.
        metrics = QFontMetrics(font)
        longest = max((metrics.horizontalAdvance(item["label"])
                       for item in self._items), default=0)
        desired = max(self.width(), longest + 70)
        screen = QApplication.screenAt(self.mapToGlobal(self.rect().bottomLeft()))
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is not None:
            desired = min(desired, max(140, screen.availableGeometry().width() - 24))
        menu.setMinimumWidth(desired)
