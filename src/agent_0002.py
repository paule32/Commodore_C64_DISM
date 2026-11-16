# -*- coding: utf-8 -*-
"""Agent 0002: deutscher Text im oberen Bereich, Formzeichnung darunter.

Gleiche 3-Spalten-Anordnung wie Agent 0001, innerhalb eines vertikalen
Splitters. Die Zeichnung entsteht ausschließlich durch QPainter (ohne Bilder).
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QPointF, QRectF, QSize
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QPolygonF, QBrush, QPalette
from PyQt5.QtWidgets import (
    QAbstractItemView, QComboBox, QGroupBox, QHeaderView, QHBoxLayout,
    QLabel, QPlainTextEdit, QPushButton, QSizePolicy, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from agent_0001_core import check_sentence
from agent_0002_core import DEFAULT_EXAMPLES, recognize_association
from agent_0002_logic import adjective_lemma


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


class AssociationCanvas(QWidget):
    """Responsive Qt-Vektorzeichnung, auch nach Größe-/Theme-Wechsel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("agent_0002_canvas")
        self.shape = None
        self.message = "Gib oben einen Satz mit »Kreis« oder »Dreieck« ein."
        self._dark = False
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def sizeHint(self):
        return QSize(500, 270)

    def set_association(self, association):
        self.shape = association.shape
        self.message = association.message
        self.update()

    def set_dark_mode(self, enabled):
        self._dark = bool(enabled)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing, True)
            background = QColor("#1b1f26" if self._dark else "#ffffff")
            foreground = QColor("#e7eef8" if self._dark else "#20252c")
            accent = QColor("#6fb8ff" if self._dark else "#1764ad")
            p.fillRect(self.rect(), background)
            width = max(0, self.width())
            height = max(0, self.height())
            p.setPen(QPen(foreground))
            p.setFont(QFont("Arial", 10))
            if width < 40 or height < 50:
                return
            # Text unten reservieren, damit die Grafik auch bei kleinen Größen
            # nicht von ihrer Beschreibung übermalt wird.
            text_height = 88 if self.shape is None and len(self.message) > 78 else 45
            available_height = max(0, height - text_height - 20)
            diameter = min(max(0, width - 42), max(0, available_height - 14), 230)
            center_x = width / 2.0
            center_y = 12.0 + available_height / 2.0
            p.setPen(QPen(accent, 3.0))
            p.setBrush(QBrush(QColor("#274966" if self._dark else "#dcebfa")))
            if self.shape == "kreis":
                radius = diameter / 2.0
                p.drawEllipse(QRectF(center_x - radius, center_y - radius,
                                     diameter, diameter))
                p.setBrush(accent)
                p.drawEllipse(QRectF(center_x - 3, center_y - 3, 6, 6))
            elif self.shape == "dreieck":
                half = diameter / 2.0
                p.drawPolygon(QPolygonF([
                    QPointF(center_x, center_y - half),
                    QPointF(center_x - half, center_y + half),
                    QPointF(center_x + half, center_y + half),
                ]))
            p.setPen(QPen(foreground))
            label_rect = QRectF(12, max(0, height - text_height - 8),
                                max(0, width - 24), text_height + 3)
            p.drawText(label_rect, Qt.AlignCenter | Qt.TextWordWrap, self.message)
        finally:
            p.end()


class GermanAssociationWidget(QWidget):
    """Kompatibles, im d64_dism-Hauptfenster andockbares Agent-0002-Widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("agent_0002_association_widget")
        self._dark = self._find_application_dark_mode()
        self._active_input = "combo"

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(7)
        heading = QLabel("Deutscher Assoziationsparser – Agent 0002", self)
        heading.setObjectName("agent_0002_heading")
        root.addWidget(heading)

        self.main_splitter = QSplitter(Qt.Vertical, self)
        self.main_splitter.setObjectName("agent_0002_vertical_splitter")
        self.main_splitter.setChildrenCollapsible(False)
        root.addWidget(self.main_splitter, 1)

        self.upper_splitter = QSplitter(Qt.Horizontal, self.main_splitter)
        self.upper_splitter.setObjectName("agent_0002_upper_splitter")
        self.upper_splitter.setChildrenCollapsible(False)

        left = QGroupBox("Text / Beispiele", self.upper_splitter)
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Text auswählen oder neu eingeben:", left))
        self.example_combo = QComboBox(left)
        self.example_combo.setObjectName("agent_0002_example_combo")
        self.example_combo.setEditable(True)
        self.example_combo.setInsertPolicy(QComboBox.NoInsert)
        self.example_combo.addItems(DEFAULT_EXAMPLES)
        left_layout.addWidget(self.example_combo)
        left_layout.addWidget(QLabel("Satz:", left))
        self.input_edit = QPlainTextEdit(left)
        self.input_edit.setObjectName("agent_0002_sentence_input")
        self.input_edit.setPlaceholderText("Was ist ein Kreis? / Zeige mir ein Dreieck")
        self.input_edit.setMaximumHeight(90)
        left_layout.addWidget(self.input_edit)
        self.analyze_button = QPushButton("Assoziation erkennen", left)
        self.analyze_button.setObjectName("agent_0002_analyze_button")
        left_layout.addWidget(self.analyze_button)
        left_layout.addStretch(1)
        self.upper_splitter.addWidget(left)

        middle = QGroupBox("Wörter / Analyse", self.upper_splitter)
        mid_layout = QVBoxLayout(middle)
        self.token_table = QTableWidget(0, 3, middle)
        self.token_table.setObjectName("agent_0002_token_table")
        self.token_table.setHorizontalHeader(_GrammarHeader(Qt.Horizontal, self.token_table))
        self.token_table.setVerticalHeader(_GrammarHeader(Qt.Vertical, self.token_table))
        self.token_table.setHorizontalHeaderLabels(["Position", "Wort", "Wortart"])
        self.token_table.verticalHeader().show()
        self.token_table.verticalHeader().setMinimumWidth(38)
        self.token_table.setAlternatingRowColors(True)
        self.token_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.token_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.token_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.token_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.token_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        mid_layout.addWidget(self.token_table)
        self.upper_splitter.addWidget(middle)

        right = QGroupBox("Prüfergebnis / Assoziation", self.upper_splitter)
        right_layout = QVBoxLayout(right)
        self.result_label = QLabel("Noch kein Text geprüft", right)
        self.result_label.setWordWrap(True)
        right_layout.addWidget(self.result_label)
        self.diagnostics = QPlainTextEdit(right)
        self.diagnostics.setReadOnly(True)
        self.diagnostics.setObjectName("agent_0002_diagnostics")
        right_layout.addWidget(self.diagnostics, 1)
        self.upper_splitter.addWidget(right)
        self.upper_splitter.setSizes([260, 390, 290])

        lower = QGroupBox("Visuelle Assoziation", self.main_splitter)
        lower_layout = QVBoxLayout(lower)
        self.canvas = AssociationCanvas(lower)
        lower_layout.addWidget(self.canvas, 1)
        self.main_splitter.addWidget(lower)
        self.main_splitter.setSizes([330, 290])
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 2)

        self.example_combo.activated.connect(self._selected_example)
        self.example_combo.lineEdit().textEdited.connect(self._combo_text_edited)
        self.example_combo.lineEdit().returnPressed.connect(self.analyze)
        self.input_edit.textChanged.connect(self._editor_text_edited)
        self.analyze_button.clicked.connect(self.analyze)

        self.set_dark_mode(self._dark)
        self._selected_example(0)

    def _find_application_dark_mode(self):
        current = self.parent()
        while current is not None:
            if hasattr(current, "dark_mode_enabled"):
                return bool(current.dark_mode_enabled)
            current = current.parent()
        return False

    def _set_input_text(self, text):
        old = self.input_edit.blockSignals(True)
        try:
            self.input_edit.setPlainText(text)
        finally:
            self.input_edit.blockSignals(old)

    def _selected_example(self, index):
        if index < 0:
            return
        self._active_input = "combo"
        text = self.example_combo.itemText(index)
        self._set_input_text(text)
        self._run_analysis(text)

    def _combo_text_edited(self, text):
        self._active_input = "combo"
        self._set_input_text(text)

    def _editor_text_edited(self):
        self._active_input = "editor"

    def analyze(self):
        text = (self.input_edit.toPlainText()
                if self._active_input == "editor"
                else self.example_combo.currentText())
        self._run_analysis(text)

    def _run_analysis(self, text):
        association = recognize_association(text)
        analysis = check_sentence(text)
        self.token_table.setRowCount(len(analysis.tokens))
        for row, token in enumerate(analysis.tokens):
            category = token.category
            if token.text.casefold() in ("kreis", "dreieck"):
                category = "Nomen (Geometrie)"
            elif token.text.casefold() in ("zeige", "zeig", "zeichne", "sieht"):
                category = "Verb"
            elif adjective_lemma(token.text):
                category = "Adjektiv (Geometrie)"
            for col, value in enumerate((str(token.index), token.text, category)):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.token_table.setItem(row, col, item)
        self.canvas.set_association(association)
        self.result_label.setText(
            "Erkannte Form: " + (association.shape.title() if association.shape else "Keine")
            + " | Absicht: " + association.intent
            + " | Prolog: " + association.logic_status
        )
        diagnostics = [association.message, "", "Logische Prüfung (d64prolog): "
                       + association.logic_status, "",
                       "Basisprüfung (Agent 0001):"]
        if analysis.diagnostics:
            diagnostics.extend(analysis.diagnostics)
        else:
            diagnostics.append("Keine Auffälligkeiten der Basisprüfung erkannt.")
        diagnostics.append("Hinweis: Die Prolog-Prüfung beweist nur Regeln der begrenzten "
                           "Geometrie-Wissensbasis; keine allgemeine logische Satzprüfung.")
        self.diagnostics.setPlainText("\n".join(diagnostics))
        return association

    def set_dark_mode(self, enabled):
        self._dark = bool(enabled)
        if self._dark:
            bg, fg, panel, field, border, alternate, selected = (
                "#191919", "#f1f1f1", "#242424", "#272727",
                "#565656", "#303030", "#375c78")
            header_bg, header_fg = "#303030", "#f5f5f5"
        else:
            bg, fg, panel, field, border, alternate, selected = (
                "#f4f4f4", "#1d1d1d", "#fafafa", "#ffffff",
                "#999999", "#f0f0f0", "#add8ff")
            header_bg, header_fg = "#e1e1e1", "#171717"
        self.setStyleSheet(f"""
            QWidget#agent_0002_association_widget {{background:{bg};color:{fg};}}
            QGroupBox {{background:{panel};color:{fg};border:1px solid {border};
                border-radius:4px;margin-top:11px;padding-top:5px;}}
            QGroupBox::title {{subcontrol-origin:margin;left:9px;padding:0 4px;}}
            QLabel {{color:{fg};}}
            QComboBox, QComboBox QAbstractItemView, QPlainTextEdit {{
                background:{field};color:{fg};border:1px solid {border};
                selection-background-color:{selected};}}
            QPushButton {{background:{field};color:{fg};border:1px solid {border};
                border-radius:3px;padding:5px 10px;}}
            QPushButton:hover {{background:{alternate};}}
            QTableWidget {{background:{field};color:{fg};
                alternate-background-color:{alternate};gridline-color:{border};
                selection-background-color:{selected};selection-color:{fg};
                border:1px solid {border};}}
            QHeaderView::section {{background:{header_bg};color:{header_fg};
                border:1px solid {border};padding:5px 8px;}}
            QTableCornerButton::section {{background:{header_bg};
                border:1px solid {border};}}
            QSplitter::handle {{background:{border};}}
        """)
        for header in (self.token_table.horizontalHeader(), self.token_table.verticalHeader()):
            header.set_dark_mode(self._dark)
        # Agent 0003 ersetzt den unteren Bereich durch eine QGraphicsScene.
        # In diesem Fall existiert kein AssociationCanvas mehr. Das Theme darf
        # nicht auf einem von Qt bereits geloeschten Canvas gesetzt werden.
        canvas = getattr(self, 'canvas', None)
        if canvas is not None:
            canvas.set_dark_mode(self._dark)
        self.token_table.viewport().update()
