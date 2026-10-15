# -*- coding: utf-8 -*-
"""Stage 386: interaktiver Chemie-Lernbaukasten fuer d64_dism/PyQt5."""
from PyQt5.QtCore import QByteArray, QMimeData, Qt
from PyQt5.QtGui import QDrag, QFont
from PyQt5.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QPushButton, QScrollArea, QSizePolicy, QSplitter,
    QVBoxLayout, QWidget,
)

from chemistry_model import ELEMENTS, BY_SYMBOL, find_reaction, pretty_equation, pretty_formula

MIME_ELEMENT = 'application/x-d64-chemistry-element'


class ChemistryElementButton(QPushButton):
    """Anklicken oder per Drag & Drop zur Reaktionsflaeche ziehen."""

    def __init__(self, element, parent=None):
        super().__init__(f'{element.number}\n{element.symbol}\n{element.name}', parent)
        self.symbol = element.symbol
        self.setObjectName('chemistry_element_tile')
        self.setToolTip(f'{element.number} – {element.name} ({element.symbol}) | {element.family}')
        self.setMinimumSize(64, 70)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._press_pos = None

    def mousePressEvent(self, event):
        self._press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (self._press_pos is not None and (event.buttons() & Qt.LeftButton)
                and (event.pos() - self._press_pos).manhattanLength() >= 10):
            self._press_pos = None
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData(MIME_ELEMENT, QByteArray(self.symbol.encode('ascii')))
            drag.setMimeData(mime)
            drag.exec_(Qt.CopyAction)
            return
        super().mouseMoveEvent(event)


class ChemistryElementDropArea(QFrame):
    """Akzeptiert ausschliesslich die im Baukasten bekannten Elementsymbole."""

    def __init__(self, workbench, parent=None):
        super().__init__(parent)
        self.workbench = workbench
        self.setObjectName('chemistry_drop_area')
        self.setAcceptDrops(True)
        self.setMinimumHeight(185)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME_ELEMENT):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(MIME_ELEMENT):
            event.ignore()
            return
        symbol = bytes(event.mimeData().data(MIME_ELEMENT)).decode('ascii', errors='ignore')
        if symbol in BY_SYMBOL:
            self.workbench.add_element(symbol)
            event.acceptProposedAction()
        else:
            event.ignore()


class ChemistryWorkbenchWidget(QWidget):
    """40 Elemente mit Auswahl-/Drag-Fläche und bekannten Verbindungen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('chemistry_baukasten')
        self.selected_symbols = []
        self.element_buttons = []
        self._dark_mode = True
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(9)

        title = QLabel('Chemie-Baukasten · 40 Elemente', self)
        title.setObjectName('chemistry_title')
        font = QFont(title.font())
        font.setPointSize(17)
        font.setBold(True)
        title.setFont(font)
        root.addWidget(title)
        subtitle = QLabel(
            'Elemente anklicken oder auf die Arbeitsfläche ziehen. '
            'Der Baukasten zeigt bekannte Verbindungen und ausgeglichene Modellreaktionen.', self)
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        left = QWidget(splitter)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_label = QLabel('Elemente (Ordnungszahlen 1–40)', left)
        left_layout.addWidget(left_label)
        self.search_box = QLineEdit(left)
        self.search_box.setObjectName('chemistry_search')
        self.search_box.setPlaceholderText('Element, Symbol oder Gruppe suchen …')
        left_layout.addWidget(self.search_box)
        scroll = QScrollArea(left)
        scroll.setObjectName('chemistry_elements_scroll')
        scroll.setWidgetResizable(True)
        self.element_container = QWidget(scroll)
        grid = QGridLayout(self.element_container)
        grid.setContentsMargins(4, 5, 4, 5)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        for index, element in enumerate(ELEMENTS):
            button = ChemistryElementButton(element, self.element_container)
            button.clicked.connect(lambda _checked=False, sym=element.symbol: self.add_element(sym))
            button.setProperty('chemistryFamily', element.family)
            grid.addWidget(button, index // 5, index % 5)
            self.element_buttons.append(button)
        for column in range(5):
            grid.setColumnStretch(column, 1)
        grid.setRowStretch(8, 1)
        scroll.setWidget(self.element_container)
        left_layout.addWidget(scroll, 1)
        self.search_box.textChanged.connect(self.filter_elements)

        right = QWidget(splitter)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(9)
        right_layout.addWidget(QLabel('Reaktions-Arbeitsfläche', right))
        self.drop_area = ChemistryElementDropArea(self, right)
        drop_layout = QVBoxLayout(self.drop_area)
        self.drop_hint = QLabel('Zwei verschiedene Elemente hier ablegen oder links anklicken.', self.drop_area)
        self.drop_hint.setWordWrap(True)
        drop_layout.addWidget(self.drop_hint)
        self.selected_list = QListWidget(self.drop_area)
        self.selected_list.setObjectName('chemistry_selected_elements')
        self.selected_list.setMinimumHeight(80)
        drop_layout.addWidget(self.selected_list, 1)
        right_layout.addWidget(self.drop_area)
        actions = QHBoxLayout()
        self.combine_button = QPushButton('Kombinieren', right)
        self.combine_button.setObjectName('chemistry_combine')
        self.combine_button.clicked.connect(self.combine_elements)
        actions.addWidget(self.combine_button)
        self.remove_button = QPushButton('Letztes entfernen', right)
        self.remove_button.clicked.connect(self.remove_last)
        actions.addWidget(self.remove_button)
        self.clear_button = QPushButton('Leeren', right)
        self.clear_button.clicked.connect(self.clear_selection)
        actions.addWidget(self.clear_button)
        right_layout.addLayout(actions)

        examples_line = QHBoxLayout()
        examples_line.addWidget(QLabel('Beispiel laden:', right))
        self.example_combo = QComboBox(right)
        self.example_combo.addItem('Auswählen …', None)
        for label, symbols in (
            ('Wasser (H + O)', ('H', 'O')),
            ('Kochsalz (Na + Cl)', ('Na', 'Cl')),
            ('Kohlenstoffdioxid (C + O)', ('C', 'O')),
            ('Magnesiumoxid (Mg + O)', ('Mg', 'O')),
            ('Eisensulfid (Fe + S)', ('Fe', 'S')),
        ):
            self.example_combo.addItem(label, symbols)
        self.example_combo.currentIndexChanged.connect(self.load_example)
        examples_line.addWidget(self.example_combo, 1)
        right_layout.addLayout(examples_line)

        self.result_card = QFrame(right)
        self.result_card.setObjectName('chemistry_result_card')
        result_layout = QVBoxLayout(self.result_card)
        result_layout.addWidget(QLabel('Ergebnis', self.result_card))
        self.result_name = QLabel('Noch keine Verbindung gewählt', self.result_card)
        self.result_name.setObjectName('chemistry_result_name')
        self.result_name.setWordWrap(True)
        result_layout.addWidget(self.result_name)
        self.result_formula = QLabel('–', self.result_card)
        self.result_formula.setObjectName('chemistry_result_formula')
        self.result_formula.setTextInteractionFlags(Qt.TextSelectableByMouse)
        result_layout.addWidget(self.result_formula)
        self.result_equation = QLabel('', self.result_card)
        self.result_equation.setObjectName('chemistry_result_equation')
        self.result_equation.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.result_equation.setWordWrap(True)
        result_layout.addWidget(self.result_equation)
        self.result_note = QLabel('Dies ist ein Lernmodell und keine reale Versuchsanleitung.', self.result_card)
        self.result_note.setWordWrap(True)
        result_layout.addWidget(self.result_note)
        right_layout.addWidget(self.result_card, 1)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([560, 480])
        disclaimer = QLabel(
            'Hinweis: Chemische Elemente werden bei chemischen Reaktionen nicht in andere '
            'Elemente umgewandelt. Die Simulation beschreibt Verbindungen, keine Laborversuche.',
            self)
        disclaimer.setWordWrap(True)
        root.addWidget(disclaimer)
        self.set_dark_mode(True)
        self._update_selection()

    def filter_elements(self, query):
        query = str(query).strip().casefold()
        for element, button in zip(ELEMENTS, self.element_buttons):
            match = (not query or any(query in text.casefold()
                                      for text in (element.name, element.symbol, element.family, str(element.number))))
            button.setVisible(match)

    def focus_first(self):
        self.search_box.setFocus(Qt.OtherFocusReason)

    def add_element(self, symbol):
        if symbol not in BY_SYMBOL:
            return
        if symbol in self.selected_symbols:
            self.result_note.setText('Das Element ist bereits ausgewählt. Bitte ein anderes hinzufügen.')
            return
        if len(self.selected_symbols) >= 2:
            self.result_note.setText('Für dieses Lernmodell bitte höchstens zwei verschiedene Elemente wählen.')
            return
        self.selected_symbols.append(symbol)
        self._update_selection()

    def _update_selection(self):
        self.selected_list.clear()
        for symbol in self.selected_symbols:
            element = BY_SYMBOL[symbol]
            self.selected_list.addItem(f'{element.number:02d}   {element.symbol} · {element.name}')
        self.combine_button.setEnabled(len(self.selected_symbols) == 2)
        self.drop_hint.setText(f'{len(self.selected_symbols)} von 2 Elementen ausgewählt · Elemente hier ablegen')
        self.result_name.setText('Bereit zum Kombinieren' if len(self.selected_symbols) == 2
                                 else 'Elemente auswählen')
        self.result_formula.setText('–')
        self.result_equation.clear()
        self.result_note.setText('Dies ist ein Lernmodell und keine reale Versuchsanleitung.')

    def clear_selection(self):
        self.selected_symbols.clear()
        self._update_selection()

    def remove_last(self):
        if self.selected_symbols:
            self.selected_symbols.pop()
        self._update_selection()

    def load_example(self, index):
        selection = self.example_combo.itemData(index)
        if selection:
            self.selected_symbols = list(selection)
            self._update_selection()
            self.combine_elements()

    def combine_elements(self):
        if len(self.selected_symbols) != 2:
            self.result_note.setText('Bitte genau zwei verschiedene Elemente auswählen.')
            return
        reaction = find_reaction(self.selected_symbols)
        if reaction is None:
            self.result_name.setText('Keine einfache Beispielreaktion hinterlegt')
            self.result_formula.setText('–')
            self.result_equation.setText('Für diese Kombination ist kein Ergebnis im Lernkatalog gespeichert.')
            self.result_note.setText('Ein fehlender Katalogeintrag bedeutet nicht, dass es keine chemische Verbindung geben kann.')
            return
        self.result_name.setText(reaction.name)
        self.result_formula.setText(pretty_formula(reaction.formula))
        self.result_equation.setText(pretty_equation(reaction.equation))
        self.result_note.setText(reaction.note)

    def set_dark_mode(self, enabled):
        self._dark_mode = bool(enabled)
        background = '#101927' if enabled else '#f5f8fd'
        fg = '#ecf5ff' if enabled else '#192b41'
        tile = '#22354a' if enabled else '#e9f2fe'
        border = '#54738f' if enabled else '#b8cbde'
        accent = '#ffe68b' if enabled else '#165e9a'
        self.setStyleSheet('''
            QWidget#chemistry_baukasten { background: %s; color: %s; }
            QWidget#chemistry_baukasten QLabel { color: %s; background: transparent; }
            QPushButton#chemistry_element_tile {
                background: %s; color: %s; border: 1px solid %s;
                border-radius: 8px; font-size: 12px; font-weight: 600;
            }
            QPushButton#chemistry_element_tile:hover { border: 2px solid %s; }
            QFrame#chemistry_drop_area, QFrame#chemistry_result_card {
                background: %s; border: 1px solid %s; border-radius: 10px;
            }
            QLabel#chemistry_result_name, QLabel#chemistry_result_formula,
            QLabel#chemistry_result_equation { color: %s; font-size: 17px; font-weight: bold; }
            QLabel#chemistry_title { color: %s; }
        ''' % (background, fg, fg, tile, fg, border, accent, tile, border, accent, fg))
