"""PyQt5-Docking-Inhalt für Agent -> 0001."""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QHeaderView,
)

from .grammar import parse_sentence

EXAMPLES = (
    "Was ist heute für ein Tag?",
    "Heute ist für ein Tag?",
    "Was für ein Tag ist heute?",
    "Welcher Tag ist heute?",
    "Ist heute ein Feiertag?",
    "Wo wohnst du?",
    "Wo du wohnst?",
    "Der Mann geht nach Hause.",
    "Der Mann gehen nach Hause.",
    "Heute bin ich müde.",
    "Heute ich bin müde.",
)


class GermanGrammarWidget(QWidget):
    """Eingabe, Wortarten und Diagnosen – keine zusätzliche QApplication."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("agent_0001_grammar_widget")
        self.setFont(QFont("Arial", 10))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Agent 0001 – Deutscher Grammatikparser")
        title.setObjectName("agent_0001_title")
        font = QFont("Arial", 12)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        hint = QLabel("Regelbasierte Analyse deutscher Hauptsätze und Fragen. "
                      "Nicht erkannte Formen werden nicht automatisch als falsch bewertet.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        choose_row = QHBoxLayout()
        self.examples = QComboBox(self)
        self.examples.setObjectName("agent_0001_examples")
        self.examples.addItems(EXAMPLES)
        choose_row.addWidget(self.examples, 1)
        load_btn = QPushButton("Beispiel laden", self)
        load_btn.clicked.connect(self._load_example)
        choose_row.addWidget(load_btn)
        layout.addLayout(choose_row)

        layout.addWidget(QLabel("Satz:"))
        self.input_edit = QPlainTextEdit(self)
        self.input_edit.setObjectName("agent_0001_sentence_input")
        self.input_edit.setPlaceholderText("Deutschen Satz eingeben …")
        self.input_edit.setMaximumHeight(90)
        layout.addWidget(self.input_edit)

        buttons = QHBoxLayout()
        analyze_btn = QPushButton("Grammatik prüfen", self)
        analyze_btn.setObjectName("agent_0001_analyze_button")
        analyze_btn.clicked.connect(self.analyze)
        buttons.addWidget(analyze_btn)
        clear_btn = QPushButton("Zurücksetzen", self)
        clear_btn.clicked.connect(self._clear)
        buttons.addWidget(clear_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        splitter = QSplitter(Qt.Vertical, self)
        self.token_table = QTableWidget(0, 4, splitter)
        self.token_table.setObjectName("agent_0001_token_table")
        self.token_table.setHorizontalHeaderLabels(["Nr.", "Token", "Wortart", "Position"])
        self.token_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch)
        self.token_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.token_table.setSelectionBehavior(QTableWidget.SelectRows)

        self.result_edit = QPlainTextEdit(splitter)
        self.result_edit.setObjectName("agent_0001_result")
        self.result_edit.setReadOnly(True)
        splitter.addWidget(self.token_table)
        splitter.addWidget(self.result_edit)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        self._load_example()

    def _load_example(self):
        self.input_edit.setPlainText(self.examples.currentText())
        self.analyze()

    def _clear(self):
        self.input_edit.clear()
        self.token_table.setRowCount(0)
        self.result_edit.clear()
        self.input_edit.setFocus()

    def analyze(self):
        result = parse_sentence(self.input_edit.toPlainText().strip())
        self.token_table.setRowCount(len(result.tokens))
        for row, token in enumerate(result.tokens):
            for col, value in enumerate((str(row+1), token.text,
                                          token.part_of_speech, str(token.start+1))):
                item = QTableWidgetItem(value)
                self.token_table.setItem(row, col, item)

        status = {
            "korrekt": "ERKANNT – innerhalb der Teilgrammatik korrekt",
            "fehlerhaft": "GRAMMATIKFEHLER ERKANNT",
            "nicht_erkannt": "NICHT ERKANNT – keine sichere Aussage",
        }.get(result.status, result.status)
        lines = [f"Status: {status}",
                 f"Satzart: {result.sentence_kind}",
                 f"Intent: {result.intent or '-'}", ""]
        for issue in result.diagnostics:
            where = f" (Zeichen {issue.position+1})" if issue.position is not None else ""
            lines.append(f"{issue.code}{where}: {issue.message}")
        if result.suggestion:
            lines.extend(["", f"Korrekturvorschlag: {result.suggestion}"])
        self.result_edit.setPlainText("\n".join(lines))
