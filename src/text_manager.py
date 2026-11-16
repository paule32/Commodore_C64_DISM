# -*- coding: utf-8 -*-
"""Zentrale Beschriftung / Laufzeit-Lokalisierung fuer PyQt5.

- QWidget und QAction werden ueber objectName() aufgeloest.
- QComboBox-Elemente werden ueber stabile itemData(Qt.UserRole) gefunden.
- Tabs werden ueber objectName() ihres Seiten-Widgets gefunden.
- Texte in editierbaren Eingaben werden NICHT ueberschrieben.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Any

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import (
    QAction, QAbstractButton, QComboBox, QDialog, QDockWidget,
    QGroupBox, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMenu, QMessageBox, QPlainTextEdit, QProgressBar, QTabBar,
    QTabWidget, QTableView, QTableWidget, QTableWidgetItem,
    QTextEdit, QToolBar, QToolBox, QTreeView, QTreeWidget, QTreeWidgetItem,
    QWizardPage, QWidget,
)


@dataclass
class TranslationResult:
    applied: int = 0
    missing: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _valid_index(index: int | None, count: int, what: str) -> int:
    if index is None or not 0 <= index < count:
        raise IndexError(f"{what}: Index {index!r} nicht in 0..{count - 1}")
    return index


def set_qt_text(obj: object, value: str, *, kind: str = "auto",
                index: int | None = None, column: int = 0,
                key: object = None) -> None:
    """Eine zentrale Routine fuer die gaengigen Qt5-Beschriftungsarten.

    kind='auto'    Klasse entscheidet ueber setText/setTitle/setWindowTitle ...
    kind='item'    QComboBox / QToolBox / QListWidget, Eintrag per index oder key
    kind='tab'     QTabWidget / QTabBar / QToolBox, Eintrag per index
    kind='header'  QTableWidget/QTreeWidget/QTableView/QTreeView, Spaltenindex
    kind='window'  Fenstertitel
    kind='placeholder'  Platzhalter (ohne Nutzereingaben zu aendern)
    kind='tooltip', 'status', 'whats_this', 'format'
    """
    text = str(value)

    if kind == "tooltip":
        obj.setToolTip(text)
        return
    if kind == "status":
        obj.setStatusTip(text)
        return
    if kind == "whats_this":
        obj.setWhatsThis(text)
        return
    if kind == "window":
        obj.setWindowTitle(text)
        return
    if kind == "placeholder":
        if not hasattr(obj, "setPlaceholderText"):
            raise TypeError(f"{type(obj).__name__} hat keinen Placeholder")
        obj.setPlaceholderText(text)
        return
    if kind == "format":
        if not isinstance(obj, QProgressBar):
            raise TypeError("format erfordert QProgressBar")
        obj.setFormat(text)
        return

    if kind == "item":
        if isinstance(obj, QComboBox):
            if key is not None:
                index = obj.findData(key, role=Qt.UserRole)
            idx = _valid_index(index, obj.count(), "QComboBox")
            was_blocked = obj.blockSignals(True)
            try:
                obj.setItemText(idx, text)
            finally:
                obj.blockSignals(was_blocked)
            return
        if isinstance(obj, QToolBox):
            obj.setItemText(_valid_index(index, obj.count(), "QToolBox"), text)
            return
        if isinstance(obj, QListWidget):
            obj.item(_valid_index(index, obj.count(), "QListWidget")).setText(text)
            return
        raise TypeError(f"item wird fuer {type(obj).__name__} nicht unterstuetzt")

    if kind == "tab":
        if isinstance(obj, (QTabWidget, QTabBar)):
            obj.setTabText(_valid_index(index, obj.count(), "Tab"), text)
            return
        if isinstance(obj, QToolBox):
            obj.setItemText(_valid_index(index, obj.count(), "QToolBox"), text)
            return
        raise TypeError(f"tab wird fuer {type(obj).__name__} nicht unterstuetzt")

    if kind == "header":
        if isinstance(obj, QTableWidget):
            idx = _valid_index(index, obj.columnCount(), "Tabelle")
            item = obj.horizontalHeaderItem(idx)
            if item is None:
                obj.setHorizontalHeaderItem(idx, QTableWidgetItem(text))
            else:
                item.setText(text)
            return
        if isinstance(obj, QTreeWidget):
            idx = _valid_index(index, obj.columnCount(), "Baum")
            obj.headerItem().setText(idx, text)
            return
        if isinstance(obj, (QTableView, QTreeView)):
            model = obj.model()
            if model is None or index is None or not model.setHeaderData(
                index, Qt.Horizontal, text, Qt.DisplayRole
            ):
                raise ValueError("Das View-Modell unterstuetzt setHeaderData() nicht")
            return
        raise TypeError(f"header wird fuer {type(obj).__name__} nicht unterstuetzt")

    if kind != "auto":
        raise ValueError(f"Unbekannter Beschriftungstyp: {kind}")

    # Reihenfolge ist wichtig: QMenu ist auch QWidget, QWizardPage auch QWidget.
    if isinstance(obj, QAction):
        obj.setText(text)
    elif isinstance(obj, QMenu):
        obj.setTitle(text)
    elif isinstance(obj, QTreeWidgetItem):
        obj.setText(column, text)
    elif isinstance(obj, (QTableWidgetItem, QListWidgetItem, QStandardItem)):
        obj.setText(text)
    elif isinstance(obj, (QGroupBox, QWizardPage)):
        obj.setTitle(text)
    elif isinstance(obj, QAbstractButton):
        obj.setText(text)  # QPushButton, QCheckBox, QRadioButton, QToolButton ...
    elif isinstance(obj, (QLabel, QMessageBox)):
        obj.setText(text)
    elif isinstance(obj, QProgressBar):
        obj.setFormat(text)
    elif isinstance(obj, (QLineEdit, QTextEdit, QPlainTextEdit)):
        obj.setPlaceholderText(text)  # Nutzereingaben nicht ueberschreiben!
    elif isinstance(obj, (QComboBox, QTabWidget, QTabBar, QToolBox)):
        raise ValueError("index/Eintrag benoetigt: kind='item' oder kind='tab'")
    elif isinstance(obj, (QMainWindow, QDialog, QDockWidget, QToolBar)):
        obj.setWindowTitle(text)
    elif isinstance(obj, QWidget) and obj.isWindow():
        obj.setWindowTitle(text)
    else:
        raise TypeError(
            f"Keine allgemeine Text-Eigenschaft fuer {type(obj).__name__}; "
            "verwende z.B. kind='tooltip' oder einen spezifischen Setter"
        )


def _apply_spec(obj: QObject, spec: str | Mapping[str, Any]) -> int:
    if isinstance(spec, str):
        set_qt_text(obj, spec)
        return 1
    count = 0
    for kind, value in spec.items():
        if kind in {"text", "title"}:
            set_qt_text(obj, value)
            count += 1
        elif kind in {"tooltip", "placeholder", "window", "status", "whats_this", "format"}:
            set_qt_text(obj, value, kind=kind)
            count += 1
        elif kind == "items":
            if not isinstance(obj, QComboBox):
                raise TypeError("'items' erfordert QComboBox")
            for data_key, label in value.items():
                set_qt_text(obj, label, kind="item", key=data_key)
                count += 1
        elif kind == "tabs":
            if not isinstance(obj, (QTabWidget, QToolBox)):
                raise TypeError("'tabs' erfordert QTabWidget oder QToolBox")
            for page_name, label in value.items():
                idx = next((i for i in range(obj.count())
                            if obj.widget(i).objectName() == page_name), -1)
                set_qt_text(obj, label, kind="tab", index=idx)
                count += 1
        elif kind == "headers":
            for col, label in value.items():
                set_qt_text(obj, label, kind="header", index=int(col))
                count += 1
        else:
            raise ValueError(f"Unbekannter Uebersetzungs-Schluessel: {kind}")
    return count


def translate_qt(root: QObject, texts: Mapping[str, str | Mapping[str, Any]]) -> TranslationResult:
    """Uebersetzt vorhandene Widgets UND QAction per objectName().

    Die Funktion darf nach der GUI-Erstellung und bei jedem Sprachwechsel
    erneut aufgerufen werden. QTreeWidgetItem/QTableWidgetItem sind keine
    QObject-Kinder; deren Texte bei Bedarf separat ueber set_qt_text setzen.
    """
    objects = [root, *root.findChildren(QObject)]
    named: dict[str, list[QObject]] = {}
    for obj in objects:
        name = obj.objectName()
        if name:
            named.setdefault(name, []).append(obj)

    result = TranslationResult()
    for name, spec in texts.items():
        matches = named.get(name)
        if not matches:
            result.missing.append(name)
            continue
        for obj in matches:
            try:
                result.applied += _apply_spec(obj, spec)
            except (AttributeError, TypeError, ValueError, IndexError) as exc:
                result.errors.append(f"{name} ({type(obj).__name__}): {exc}")
    return result
