# -*- coding: utf-8 -*-
"""Stage 570: interaktive Matrix-Multiplikation im Mathematik-Dock (PyQt5)."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSpinBox,
    QPushButton, QToolBar, QLineEdit, QFrame, QGroupBox, QMessageBox,
    QSizePolicy,
)
from matrix_multiplication_logic import (
    multiply_matrices, format_matrix_value, matrix_calculation_steps,
)


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.layout() is not None:
            _clear_layout(item.layout())
        if item.widget() is not None:
            item.widget().deleteLater()


class MatrixMultiplicationPanel(QWidget):
    """Eingaben, Ergebnis und zeilenweise Erklärungen oberhalb der Fakten-Seite."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('matrix_multiplication_interactive_panel')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.entries_a = []
        self.entries_b = []
        self.current_dimensions = None
        self.last_result = None
        self._dark_mode = True

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 12)
        outer.setSpacing(8)

        self.toolbar = QToolBar('Matrizen multiplizieren', self)
        self.toolbar.setObjectName('matrix_multiplication_toolbar')
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(self.toolbar.iconSize())

        self.m1_spin = self._add_dimension('m1', 2)
        self.n1_spin = self._add_dimension('n1', 3)
        self.toolbar.addSeparator()
        self.m2_spin = self._add_dimension('m2', 3)
        self.n2_spin = self._add_dimension('n2', 2)
        self.toolbar.addSeparator()

        self.create_button = QPushButton('Erstellen', self)
        self.create_button.setObjectName('matrix_multiplication_create_button')
        self.create_button.clicked.connect(self.create_matrices)
        self.toolbar.addWidget(self.create_button)
        self.calculate_button = QPushButton('Berechnen', self)
        self.calculate_button.setObjectName('matrix_multiplication_calculate_button')
        self.calculate_button.clicked.connect(self.calculate)
        self.toolbar.addWidget(self.calculate_button)
        outer.addWidget(self.toolbar)

        self.status_label = QLabel('', self)
        self.status_label.setObjectName('matrix_multiplication_status')
        self.status_label.setWordWrap(True)
        outer.addWidget(self.status_label)

        self.matrices_frame = QFrame(self)
        self.matrices_frame.setObjectName('matrix_multiplication_canvas')
        self.matrices_layout = QVBoxLayout(self.matrices_frame)
        self.matrices_layout.setSpacing(8)
        outer.addWidget(self.matrices_frame)

        self.steps_box = QGroupBox('Rechenschritte', self)
        self.steps_box.setObjectName('matrix_multiplication_steps')
        self.steps_layout = QVBoxLayout(self.steps_box)
        self.steps_layout.setContentsMargins(8, 12, 8, 8)
        self.steps_layout.setSpacing(5)
        self.steps_box.hide()
        outer.addWidget(self.steps_box)

        self.create_matrices()
        self.set_dark_mode(True)

    def _add_dimension(self, text, initial):
        label = QLabel(text + ':', self)
        label.setObjectName('matrix_dimension_' + text + '_label')
        self.toolbar.addWidget(label)
        spin = QSpinBox(self)
        spin.setObjectName('matrix_dimension_' + text)
        spin.setAccessibleName('Dimension ' + text)
        spin.setRange(1, 12)
        spin.setValue(initial)
        spin.setFixedWidth(62)
        spin.setToolTip('Anzahl Zeilen (m) bzw. Spalten (n), 1–12')
        self.toolbar.addWidget(spin)
        return spin

    def _dimensions(self):
        return (self.m1_spin.value(), self.n1_spin.value(),
                self.m2_spin.value(), self.n2_spin.value())

    def _matrix_widget(self, label, rows, cols, prefix):
        holder = QWidget(self.matrices_frame)
        outer = QVBoxLayout(holder)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)
        heading = QLabel(f'{label} ({rows} × {cols})', holder)
        heading.setAlignment(Qt.AlignCenter)
        outer.addWidget(heading)
        frame = QFrame(holder)
        frame.setObjectName('matrix_multiplication_bracket')
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(4)
        cells = []
        for i in range(rows):
            line = []
            for j in range(cols):
                cell = QLineEdit(frame)
                cell.setObjectName(f'matrix_{prefix}_{i+1}_{j+1}')
                cell.setAlignment(Qt.AlignCenter)
                cell.setFixedWidth(62)
                cell.setMaxLength(40)
                cell.setToolTip(f'{label}: Zeile {i+1}, Spalte {j+1}')
                cell.setPlaceholderText('0')
                grid.addWidget(cell, i, j)
                line.append(cell)
            cells.append(line)
        outer.addWidget(frame)
        return holder, cells

    def create_matrices(self):
        """Eingabefelder anhand der vier SpinBox-Werte neu aufbauen."""
        m1, n1, m2, n2 = self._dimensions()
        self.current_dimensions = (m1, n1, m2, n2)
        self.last_result = None
        _clear_layout(self.matrices_layout)
        _clear_layout(self.steps_layout)
        self.steps_box.hide()
        row_holder = QWidget(self.matrices_frame)
        row = QHBoxLayout(row_holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        row.addStretch(1)
        a, self.entries_a = self._matrix_widget('Matrix A', m1, n1, 'a')
        b, self.entries_b = self._matrix_widget('Matrix B', m2, n2, 'b')
        row.addWidget(a)
        mul = QLabel('×', row_holder)
        mul.setObjectName('matrix_multiplication_symbol')
        mul.setAlignment(Qt.AlignCenter)
        mul.setStyleSheet('font-size: 24px; font-weight: bold;')
        row.addWidget(mul)
        row.addWidget(b)
        row.addStretch(1)
        self.matrices_layout.addWidget(row_holder)
        if n1 != m2:
            self.status_label.setText(
                f'Bitte Dimensionen prüfen: n1 = {n1} muss m2 = {m2} entsprechen.'
            )
        else:
            self.status_label.setText(
                f'Matrix A ({m1}×{n1}) × Matrix B ({m2}×{n2}) '
                f'ergibt eine {m1}×{n2}-Ergebnismatrix.'
            )
        self.matrices_frame.adjustSize()

    def _read_values(self, cells):
        values = []
        for row in cells:
            line = []
            for cell in row:
                text = cell.text().strip()
                if not text:
                    text = '0'
                    cell.setText(text)
                line.append(text)
            values.append(line)
        return values

    def calculate(self):
        """Leere Eingaben mit 0 füllen, multiplizieren, Ergebnis als Labels zeigen."""
        if self.current_dimensions != self._dimensions():
            QMessageBox.information(
                self, 'Matrix-Multiplikation',
                'Die Dimensionen wurden geändert. Bitte zuerst „Erstellen“ wählen.'
            )
            return
        a = self._read_values(self.entries_a)
        b = self._read_values(self.entries_b)
        try:
            result = multiply_matrices(a, b)
            steps = matrix_calculation_steps(a, b)
        except ValueError as exc:
            self.last_result = None
            self.status_label.setText(str(exc))
            QMessageBox.warning(self, 'Matrix-Multiplikation', str(exc))
            return
        self.last_result = result
        _clear_layout(self.steps_layout)
        self.steps_box.show()
        caption = QLabel('C = A × B  ·  c(i,j) = Σ a(i,k) · b(k,j)', self.steps_box)
        caption.setWordWrap(True)
        self.steps_layout.addWidget(caption)
        # Jede Zeile der Ergebnismatrix bildet eine eigene Label-Reihe.
        result_frame = QFrame(self.steps_box)
        result_frame.setObjectName('matrix_multiplication_result')
        result_grid = QGridLayout(result_frame)
        result_grid.setSpacing(6)
        result_grid.addWidget(QLabel('Ergebnis C:', result_frame), 0, 0, 1, len(result[0]))
        for i, line in enumerate(result):
            for j, value in enumerate(line):
                value_label = QLabel(format_matrix_value(value), result_frame)
                value_label.setObjectName(f'matrix_result_{i+1}_{j+1}')
                value_label.setAlignment(Qt.AlignCenter)
                value_label.setMinimumWidth(68)
                value_label.setStyleSheet('font-family: Consolas, "Courier New", monospace; font-weight: bold;')
                result_grid.addWidget(value_label, i + 1, j)
        self.steps_layout.addWidget(result_frame)
        for i, row in enumerate(steps):
            heading = QLabel(f'Ergebniszeile {i+1}:', self.steps_box)
            heading.setStyleSheet('font-weight: bold;')
            self.steps_layout.addWidget(heading)
            for expression in row:
                entry = QLabel(expression, self.steps_box)
                entry.setTextInteractionFlags(Qt.TextSelectableByMouse)
                entry.setWordWrap(True)
                self.steps_layout.addWidget(entry)
        self.status_label.setText(
            f'Berechnet: {len(result)} Zeilen × {len(result[0])} Spalten.'
        )

    def set_dark_mode(self, enabled):
        self._dark_mode = bool(enabled)
        if enabled:
            bg, fg, panel, border, input_bg = '#1e1e1e', '#eeeeee', '#282828', '#656565', '#202020'
        else:
            bg, fg, panel, border, input_bg = '#f7f7f7', '#202020', '#ffffff', '#888888', '#ffffff'
        self.setStyleSheet(f'''
            QWidget#matrix_multiplication_interactive_panel {{ background: {bg}; color: {fg}; }}
            QToolBar#matrix_multiplication_toolbar {{ background: {panel}; color: {fg};
                border: 1px solid {border}; spacing: 6px; padding: 5px; }}
            QFrame#matrix_multiplication_canvas {{ background: {panel};
                border: 1px solid {border}; border-radius: 4px; }}
            QFrame#matrix_multiplication_bracket {{ border-left: 3px solid {fg};
                border-right: 3px solid {fg}; background: {panel}; }}
            QGroupBox#matrix_multiplication_steps {{ border: 1px solid {border};
                margin-top: 10px; padding-top: 6px; }}
            QGroupBox#matrix_multiplication_steps::title {{ subcontrol-origin: margin; left: 10px; }}
            QLabel {{ color: {fg}; }}
            QLineEdit, QSpinBox {{ background: {input_bg}; color: {fg};
                border: 1px solid {border}; padding: 3px; }}
            QPushButton {{ background: {panel}; color: {fg};
                border: 1px solid {border}; padding: 5px 8px; }}
            QFrame#matrix_multiplication_result {{ border-left: 3px solid {fg};
                border-right: 3px solid {fg}; background: {panel}; }}
        ''')
