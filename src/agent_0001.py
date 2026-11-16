# -*- coding: utf-8 -*-
"""Agent 0001: Deutscher Grammatikparser mit JSON-Beispielsatzverwaltung.

Für Stage 571 ergänzt, da die Stage-570-Datei auf dieses Modul verweist,
es aber nicht mitliefert. Der Prüfer ist bewusst eine Basisprüfung.
"""
from __future__ import annotations

import ctypes
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette, QPen
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSplitter, QLabel,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QPlainTextEdit, QMessageBox, QSizePolicy, QAbstractItemView,
)

from agent_0001_data import ExampleStore, ExampleStoreError, normalize_text
from agent_0001_core import check_sentence


class _GrammarHeader(QHeaderView):
    """Eigenständig gezeichneter Header, unabhängig vom nativen Windows-Stil.

    Ein lokales Qt-Stylesheet allein reicht nicht in jeder Kombination aus
    QApplication-Stylesheet, Windows-QStyle und Dark-/Light-Mode-Umschaltung.
    Diese paintSection-Implementierung setzt Hintergrund und Text für jede
    horizontale und vertikale Header-Zelle ausdrücklich.
    """

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._header_background = QColor('#e1e1e1')
        self._header_foreground = QColor('#171717')
        self._header_border = QColor('#999999')
        self.setHighlightSections(False)
        self.setSectionsClickable(False)

    def set_dark_mode(self, enabled):
        if enabled:
            bg, fg, border = '#303030', '#f5f5f5', '#565656'
        else:
            bg, fg, border = '#e1e1e1', '#171717', '#999999'
        self._header_background = QColor(bg)
        self._header_foreground = QColor(fg)
        self._header_border = QColor(border)
        pal = self.palette()
        for role in (QPalette.Window, QPalette.Base, QPalette.Button):
            pal.setColor(role, QColor(bg))
        for role in (QPalette.WindowText, QPalette.ButtonText, QPalette.Text):
            pal.setColor(role, QColor(fg))
        self.setPalette(pal)
        self.viewport().setPalette(pal)
        self.setAutoFillBackground(True)
        self.viewport().setAutoFillBackground(True)
        # Auch das Stylesheet bleibt für nicht übermalte Header-Flächen aktiv.
        self.setStyleSheet(
            'QHeaderView {background-color:%s;color:%s;}'
            'QHeaderView::section {background-color:%s;color:%s;'
            'border:1px solid %s;padding:5px 8px;}'
            % (bg, fg, bg, fg, border)
        )
        self.viewport().update()
        self.update()

    def paintSection(self, painter, rect, logical_index):
        if not rect.isValid():
            return
        painter.save()
        try:
            painter.fillRect(rect, self._header_background)
            painter.setPen(QPen(self._header_border))
            painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())
            painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
            model = self.model()
            caption = (model.headerData(logical_index, self.orientation(), Qt.DisplayRole)
                       if model is not None else None)
            if caption is not None:
                painter.setPen(QPen(self._header_foreground))
                align = Qt.AlignVCenter | (Qt.AlignHCenter if self.orientation() == Qt.Vertical
                                          else Qt.AlignLeft)
                painter.drawText(rect.adjusted(8, 0, -6, -1), align, str(caption))
        finally:
            painter.restore()


class _GrammarMessageBox(QMessageBox):
    """Dark-/Light-Mode-Meldungen des Grammatikparsers.

    Ein eigener QMessageBox-Dialog statt der statischen Convenience-Methoden
    erlaubt explizite Paletten und Styles auch für den Windows-QStyle.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("agent_0001_message_box")
        self.setTextFormat(Qt.PlainText)
        self._dark_mode = False

    def set_dark_mode(self, enabled):
        self._dark_mode = bool(enabled)
        if self._dark_mode:
            background, field, foreground, border, button, hover, pressed, accent = (
                "#202630", "#171c24", "#ffffff", "#596779",
                "#343e4d", "#414d5f", "#27313e", "#4f91cf",
            )
        else:
            background, field, foreground, border, button, hover, pressed, accent = (
                "#f0f0f0", "#ffffff", "#000000", "#9b9b9b",
                "#f5f5f5", "#e4f1fb", "#d5e8f6", "#2a69aa",
            )

        palette = QPalette(self.palette())
        for role in (QPalette.Window, QPalette.Button):
            palette.setColor(role, QColor(background if role == QPalette.Window else button))
        for role in (QPalette.Base, QPalette.AlternateBase):
            palette.setColor(role, QColor(field))
        for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
            palette.setColor(role, QColor(foreground))
        palette.setColor(QPalette.Highlight, QColor(accent))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.setStyleSheet(f"""
            QMessageBox#agent_0001_message_box {{
                background-color: {background}; color: {foreground};
            }}
            QMessageBox#agent_0001_message_box QLabel {{
                color: {foreground}; background-color: transparent;
            }}
            QMessageBox#agent_0001_message_box QPushButton {{
                min-width: 78px; background-color: {button}; color: {foreground};
                border: 1px solid {border}; border-radius: 3px;
                padding: 5px 10px;
            }}
            QMessageBox#agent_0001_message_box QPushButton:hover {{
                background-color: {hover};
            }}
            QMessageBox#agent_0001_message_box QPushButton:pressed {{
                background-color: {pressed};
            }}
            QMessageBox#agent_0001_message_box QPushButton:default {{
                border: 2px solid {accent};
            }}
            QMessageBox#agent_0001_message_box QTextEdit,
            QMessageBox#agent_0001_message_box QPlainTextEdit {{
                background-color: {field}; color: {foreground};
                border: 1px solid {border};
            }}
        """)
        for child in self.findChildren(QWidget):
            child.setPalette(palette)
        if self.isVisible():
            self._apply_native_title_theme()
        self.update()

    def _apply_native_title_theme(self):
        """Windows 10/11: DWM-Dunkeltitelleiste; auf anderen OS ohne Effekt."""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            value = ctypes.c_int(1 if self._dark_mode else 0)
            dwm = ctypes.windll.dwmapi.DwmSetWindowAttribute
            for attribute in (20, 19):
                if dwm(hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                    break
        except (AttributeError, OSError, ValueError, TypeError):
            # Alte Windows-Versionen / fehlender DWM: Qt-Dialog bleibt bedienbar.
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_native_title_theme()


class GermanGrammarWidget(QWidget):
    """Das kompatible Widget für `Agent -> 0001` in d64_dism.py."""

    def __init__(self, parent=None, store=None):
        super().__init__(parent)
        self.setObjectName("agent_0001_german_grammar_widget")
        self.store = store if store is not None else ExampleStore()
        self._stored_texts = []
        self._updating_examples = False
        self._dark = self._find_application_dark_mode()
        self._active_input = "combo"  # neue Texte können im Textfeld oder in der ComboBox stehen
        self._last_edited_combo_text = None  # bleibt auch bei Fokusverlust erhalten
        self._check_in_progress = False

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(7)

        heading = QLabel("Deutscher Grammatikparser – Agent 0001", self)
        heading.setObjectName("agent_0001_heading")
        root.addWidget(heading)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setObjectName("agent_0001_splitter")
        root.addWidget(splitter, 1)

        left = QGroupBox("Beispieltexte", splitter)
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Text auswählen oder neu eingeben:"))
        self.example_combo = QComboBox(left)
        self.example_combo.setObjectName("agent_0001_example_combo")
        self.example_combo.setEditable(True)
        self.example_combo.setInsertPolicy(QComboBox.NoInsert)
        self.example_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.example_combo.setMinimumWidth(160)
        self.combo = self.example_combo  # praktische Aliasbezeichnung
        left_layout.addWidget(self.example_combo)

        # Das ursprüngliche separate Satz-Eingabefeld bleibt als zweiter
        # Eingabeweg erhalten. Beide Wege laufen durch check_current_text().
        left_layout.addWidget(QLabel("Satz:"))
        self.input_edit = QPlainTextEdit(left)
        self.input_edit.setObjectName("agent_0001_sentence_input")
        self.input_edit.setPlaceholderText("Neuen deutschen Satz hier eingeben …")
        self.input_edit.setMaximumHeight(85)
        left_layout.addWidget(self.input_edit)

        self.check_button = QPushButton("Prüfen", left)
        self.check_button.setToolTip(
            "Satz grammatisch prüfen und bei neuen Texten das Speichern in JSON anbieten"
        )
        self.check_button.setObjectName("agent_0001_check_button")
        left_layout.addWidget(self.check_button)
        self.example_hint = QLabel(
            "Neue Texte werden analysiert und erst nach deiner Bestätigung "
            "in der JSON-Datei gespeichert.", left
        )
        self.example_hint.setWordWrap(True)
        left_layout.addWidget(self.example_hint)
        left_layout.addStretch(1)
        splitter.addWidget(left)

        middle = QGroupBox("Wörter / Analyse", splitter)
        mid_layout = QVBoxLayout(middle)
        self.token_table = QTableWidget(0, 3, middle)
        self.token_table.setObjectName("agent_0001_token_table")
        # Eigene Header-Painter verhindern weiße System-Header im Dark-Mode.
        self.token_table.setHorizontalHeader(_GrammarHeader(Qt.Horizontal, self.token_table))
        self.token_table.setVerticalHeader(_GrammarHeader(Qt.Vertical, self.token_table))
        self.token_table.setHorizontalHeaderLabels(["Position", "Wort", "Wortart"])
        # Stage 572: auch der vertikale Header ist sichtbar und wird explizit
        # im Dark-Mode gestaltet (bisher war er versteckt).
        self.token_table.verticalHeader().show()
        self.token_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.token_table.verticalHeader().setMinimumWidth(38)
        self.token_table.setAlternatingRowColors(True)
        self.token_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.token_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.token_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.token_table.horizontalHeader().setSectionsMovable(False)
        self.token_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.token_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Interactive
        )
        self.token_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.token_table.horizontalHeader().setMinimumSectionSize(52)
        self.table = self.token_table
        mid_layout.addWidget(self.token_table)
        splitter.addWidget(middle)

        right = QGroupBox("Prüfergebnis", splitter)
        right_layout = QVBoxLayout(right)
        self.result_label = QLabel("Noch kein Text geprüft", right)
        self.result_label.setObjectName("agent_0001_result_label")
        right_layout.addWidget(self.result_label)
        self.diagnostics = QPlainTextEdit(right)
        self.diagnostics.setObjectName("agent_0001_diagnostics")
        self.diagnostics.setReadOnly(True)
        right_layout.addWidget(self.diagnostics, 1)
        splitter.addWidget(right)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([240, 430, 300])

        self.example_combo.activated.connect(self._selected_example)
        self.example_combo.lineEdit().textEdited.connect(self._combo_text_edited)
        self.example_combo.lineEdit().returnPressed.connect(self.check_current_text)
        self.input_edit.textChanged.connect(self._editor_text_edited)
        self.check_button.clicked.connect(self.check_current_text)

        # Auch beim initialen JSON-Ladefehler muss der Fehlerdialog das
        # aktuell aktive Anwendungstheme erhalten.
        self.set_dark_mode(self._dark)
        self._reload_examples()
        if self._stored_texts:
            self.example_combo.setCurrentIndex(0)
            self._set_input_text(self._stored_texts[0])
            self._run_check(self._stored_texts[0])

    def _find_application_dark_mode(self):
        current = self.parent()
        while current is not None:
            if hasattr(current, "dark_mode_enabled"):
                return bool(current.dark_mode_enabled)
            current = current.parent()
        return False

    def _set_input_text(self, text):
        """Programmatische Feldänderungen dürfen die Eingabequelle nicht umstellen."""
        previous = self.input_edit.blockSignals(True)
        try:
            self.input_edit.setPlainText(text)
        finally:
            self.input_edit.blockSignals(previous)

    def _combo_text_edited(self, text):
        self._active_input = "combo"
        self._last_edited_combo_text = text
        self._set_input_text(text)

    def _editor_text_edited(self):
        self._active_input = "editor"
        self._last_edited_combo_text = None

    def _show_grammar_dialog(self, icon, title, message, *,
                             buttons=QMessageBox.Ok,
                             default_button=QMessageBox.NoButton):
        """Eine einheitlich gestaltete modale Meldung mit unverändertem Rückgabewert."""
        dialog = _GrammarMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setIcon(icon)
        dialog.setText(message)
        dialog.setStandardButtons(buttons)
        if default_button != QMessageBox.NoButton:
            dialog.setDefaultButton(default_button)
        if buttons & QMessageBox.No:
            dialog.setEscapeButton(QMessageBox.No)
        dialog.set_dark_mode(self._dark)
        return dialog.exec_()

    def _reload_examples(self, preserve=None):
        """Lädt die JSON-Daten und wählt den gerade gespeicherten Satz wirklich aus."""
        try:
            examples = self.store.load()
        except ExampleStoreError as exc:
            self._show_grammar_dialog(
                QMessageBox.Warning, "Grammatikparser – JSON-Fehler", str(exc)
            )
            return False  # beschädigte JSON-Datei nie durch eine leere Liste ersetzen

        self._updating_examples = True
        try:
            old_block = self.example_combo.blockSignals(True)
            try:
                self.example_combo.clear()
                self.example_combo.addItems(examples)
                if preserve is not None:
                    wanted = normalize_text(preserve)
                    index = next(
                        (i for i, item in enumerate(examples)
                         if item.casefold() == wanted.casefold()), -1
                    )
                    if index >= 0:
                        self.example_combo.setCurrentIndex(index)
                    else:
                        self.example_combo.setEditText(wanted)
                elif examples:
                    self.example_combo.setCurrentIndex(0)
            finally:
                self.example_combo.blockSignals(old_block)
        finally:
            self._updating_examples = False
        self._stored_texts = examples
        self._last_edited_combo_text = None
        self.example_combo.update()
        self.example_combo.view().viewport().update()
        return True

    def _selected_example(self, index):
        if self._updating_examples or index < 0:
            return
        selected = self.example_combo.itemText(index)
        self._active_input = "combo"
        self._last_edited_combo_text = None
        self._set_input_text(selected)
        self._run_check(selected)

    def _run_check(self, text):
        result = check_sentence(text)
        self.token_table.setRowCount(len(result.tokens))
        for i, token in enumerate(result.tokens):
            for column, content in enumerate((str(token.index), token.text, token.category)):
                item = QTableWidgetItem(content)
                if column == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.token_table.setItem(i, column, item)
        self.result_label.setText(
            f"Intent: {result.intent} – "
            + ("Keine Auffälligkeiten der Basisprüfung" if result.valid else "Auffälligkeiten erkannt")
        )
        if result.diagnostics:
            self.diagnostics.setPlainText("\n".join("• " + s for s in result.diagnostics))
        else:
            self.diagnostics.setPlainText(
                "Keine der hinterlegten Basisregeln hat einen Fehler erkannt. "
                "Dies ist keine vollständige grammatische Validierung."
            )
        return result

    def check_current_text(self):
        """Prüft den zuletzt aktiv bearbeiteten Satz, fragt vor neuer JSON-Aufnahme."""
        if self._check_in_progress:
            return
        self._check_in_progress = True
        try:
            self._check_and_offer_save()
        finally:
            self._check_in_progress = False

    def _check_and_offer_save(self):
        raw_text = (
            self.input_edit.toPlainText() if self._active_input == "editor"
            else self._last_edited_combo_text if self._last_edited_combo_text is not None
            else self.example_combo.currentText()
        )
        try:
            text = normalize_text(raw_text)
        except ExampleStoreError as exc:
            self._show_grammar_dialog(
                QMessageBox.Information, "Grammatikparser", str(exc)
            )
            return

        # Erst analysieren, danach die Speichernachfrage anbieten – auch wenn
        # die begrenzte Teilgrammatik einen Fehler gefunden hat.
        result = self._run_check(text)
        try:
            exists = self.store.contains(text)
        except ExampleStoreError as exc:
            self._show_grammar_dialog(
                QMessageBox.Warning, "Grammatikparser – JSON-Fehler", str(exc)
            )
            return
        if exists:
            # Die ComboBox kann seit dem letzten Laden durch eine andere Instanz
            # ergänzt worden sein: Anzeige auch für bereits gespeicherte Texte
            # mit der JSON-Datei synchronisieren.
            self._reload_examples(preserve=text)
            self._set_input_text(text)
            return

        hint = (
            "Der neue Text wurde geprüft.\n\n"
            + ("Keine Auffälligkeiten der Basisprüfung."
               if result.valid else "Es wurden folgende Auffälligkeiten erkannt:\n"
               + "\n".join(result.diagnostics))
            + "\n\nDiesen Text dauerhaft in der JSON-Beispielsliste speichern?"
        )
        choice = self._show_grammar_dialog(
            QMessageBox.Question, "Neuen Grammatiktext speichern?", hint,
            buttons=QMessageBox.Yes | QMessageBox.No,
            default_button=QMessageBox.No,
        )
        if choice != QMessageBox.Yes:
            return
        try:
            added = self.store.add(text)
        except ExampleStoreError as exc:
            self._show_grammar_dialog(
                QMessageBox.Warning, "Grammatikparser – Speichern fehlgeschlagen", str(exc)
            )
            return

        # Die ComboBox wird nach jeder erfolgreichen Übernahme aus dem JSON
        # neu geladen, und der neue Eintrag wird selektiert (currentIndex >= 0).
        if self._reload_examples(preserve=text):
            self._active_input = "combo"
            self._set_input_text(text)
            if added:
                self._show_grammar_dialog(
                    QMessageBox.Information, "Grammatikparser",
                    "Der geprüfte Text wurde gespeichert.\n\n"
                    f"JSON-Datei: {self.store.path}"
                )

    def set_dark_mode(self, enabled):
        self._dark = bool(enabled)
        if self._dark:
            fg, bg, panel, field, border, alternate, selected = (
                "#f1f1f1", "#191919", "#242424", "#272727",
                "#565656", "#303030", "#375c78",
            )
            header_bg, header_fg = "#303030", "#f5f5f5"
        else:
            fg, bg, panel, field, border, alternate, selected = (
                "#1d1d1d", "#f4f4f4", "#fafafa", "#ffffff",
                "#999999", "#f0f0f0", "#add8ff",
            )
            header_bg, header_fg = "#e1e1e1", "#171717"

        self.setStyleSheet(f"""
        QWidget#agent_0001_german_grammar_widget {{background:{bg};color:{fg};}}
        QGroupBox {{background:{panel};color:{fg};border:1px solid {border};
                   border-radius:4px;margin-top:11px;padding-top:5px;}}
        QGroupBox::title {{subcontrol-origin:margin;left:9px;padding:0 4px;}}
        QLabel {{color:{fg};}}
        QComboBox, QComboBox QAbstractItemView, QPlainTextEdit {{
            background:{field};color:{fg};border:1px solid {border};
            selection-background-color:{selected};
        }}
        QPushButton {{background:{field};color:{fg};border:1px solid {border};
                     border-radius:3px;padding:5px 10px;}}
        QPushButton:hover {{background:{alternate};}}
        QTableWidget {{background:{field};color:{fg};
            alternate-background-color:{alternate};gridline-color:{border};
            selection-background-color:{selected};selection-color:{fg};
            border:1px solid {border};}}
        QHeaderView {{background:{header_bg};color:{header_fg};}}
        QHeaderView::section {{background:{header_bg};color:{header_fg};
            border:0;border-right:1px solid {border};
            border-bottom:1px solid {border};padding:5px 8px;}}
        QTableCornerButton::section {{background:{header_bg};
            border:1px solid {border};}}
        """)
        # Windows/Qt kann reine QSS-Header-Hintergründe hell übermalen.
        # Beide Header zeichnen daher jede Sektion selbst (paintSection).
        for header in (self.token_table.horizontalHeader(),
                       self.token_table.verticalHeader()):
            if isinstance(header, _GrammarHeader):
                header.set_dark_mode(self._dark)
            else:
                # Kompatibilität, falls ein anderer Code den Header ersetzt hat.
                palette = header.palette()
                palette.setColor(QPalette.Window, QColor(header_bg))
                palette.setColor(QPalette.Button, QColor(header_bg))
                palette.setColor(QPalette.ButtonText, QColor(header_fg))
                palette.setColor(QPalette.WindowText, QColor(header_fg))
                header.setPalette(palette)
                header.setStyleSheet(
                    f'QHeaderView::section {{background-color:{header_bg};'
                    f'color:{header_fg};border:1px solid {border};}}'
                )
            header.viewport().update()
        # Falls während eines Modal-Dialogs das Theme umgeschaltet wird,
        # bleiben auch bereits geöffnete Meldungsfenster synchron.
        for dialog in self.findChildren(_GrammarMessageBox):
            dialog.set_dark_mode(self._dark)
        self.token_table.viewport().update()
        self.token_table.update()
