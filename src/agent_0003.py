# -*- coding: utf-8 -*-
"""Agent 0003: Bild-Erkennung, deutsche Bildfragen und Bildanalyse im Qt5-Dock.

Layout: exakt wie Agent 0002 oberer 3-Spalten-Teil; der untere
Assoziations-Canvas wird durch Bildwerkzeuge plus QGraphicsView ersetzt.
QGraphicsView ist bereits eine Qt-ScrollArea mit QGraphicsScene.
"""
from __future__ import annotations

from pathlib import Path

import cv2
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPen, QPixmap, QPolygonF
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QGraphicsItem, QGraphicsPixmapItem,
    QGraphicsPolygonItem, QGraphicsRectItem, QGraphicsScene,
    QGraphicsSimpleTextItem, QGraphicsView, QGroupBox, QHBoxLayout,
    QLabel, QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget,
    QTableWidgetItem,
)

from agent_0002 import GermanAssociationWidget
from agent_0003_core import detect_figures, load_image, figures_for_overlay
from agent_0003_language import LanguageEngine, ensure_agent_databases

IMAGE_FILTERS = (
    'Zeige mir alle Figuren', 'zeige mir alle Kreise',
    'zeige mir alle Dreiecke', 'zeige mir alle Rechtecke',
    'zeige mir alle Quadrate', 'Zeige mir alle Polygone',
)
IMAGE_QUESTIONS = (
    'wo befindet sich der rote kreis',
    'welcher kreis ist rot',
    'zeige mir alle kreise',
    'zeige mir alle dreiecke',
    'zeige mir alle rechtecke',
    'wie viele kreise sind im bild',
    'wie viele rote kreise sind im bild',
    'welche farbe hat das rechteck',
)


class GermanImageRecognitionWidget(GermanAssociationWidget):
    """Agent 0002 kompatibel; Bild und Wortabfragen statt Vektorbeispiel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('agent_0003_recognition_widget')
        self._image_bgr = None
        self._image_path = None
        self.figures = []
        # Nach dem Laden noch keine Konturen vorhanden. "Satz / Bild prüfen"
        # führt die erste Erkennung automatisch aus; explizite Erkennung
        # berechnet sie bei Bedarf erneut.
        self._recognition_done = False
        self._recognition_error = ''
        self._highlighted_figures = set()
        # Bei Bildfragen nur die passenden Treffer beschriften/umranden.
        # Der ComboBox-Filter kann jederzeit wieder alle Figuren anzeigen.
        self._show_query_only = False
        self._figures_by_item = {}
        self._overlay_items = []

        heading = self.findChild(QLabel, 'agent_0002_heading')
        if heading is not None:
            heading.setText('Deutscher Bild- und Grammatikparser – Agent 0003')
        self.analyze_button.setText('Satz / Bild prüfen')
        self.input_edit.setPlaceholderText(
            'Beispiel: wo befindet sich der rote kreis?'
        )
        self.example_combo.clear()
        self.example_combo.addItems(IMAGE_QUESTIONS)
        self.example_combo.setCurrentIndex(0)
        self._set_input_text(IMAGE_QUESTIONS[0])
        self._active_input = 'combo'

        old = self.main_splitter.widget(1)
        # Der alte AssociationCanvas gehoert dem unteren Agent-0002-Panel.
        # Wird dieses aus dem Splitter entfernt, kann Qt den C++-Canvas loeschen.
        # Deshalb die langlebige Python-Referenz vor dem Entfernen neutralisieren.
        self.canvas = None
        if old is not None:
            old.hide()
            old.setParent(None)
            old.deleteLater()

        lower = QGroupBox('Bild-Erkennung / OpenCV', self.main_splitter)
        lower.setObjectName('agent_0003_image_group')
        lower_layout = QVBoxLayout(lower)
        lower_layout.setContentsMargins(8, 10, 8, 8)
        lower_layout.setSpacing(5)
        lower_layout.addWidget(QLabel('Welche Figuren sollen markiert werden?', lower))
        self.figure_combo = QComboBox(lower)
        self.figure_combo.setObjectName('agent_0003_figure_combo')
        self.figure_combo.addItems(IMAGE_FILTERS)
        lower_layout.addWidget(self.figure_combo)

        self.image_splitter = QSplitter(Qt.Horizontal, lower)
        self.image_splitter.setObjectName('agent_0003_image_splitter')
        self.image_splitter.setChildrenCollapsible(False)
        lower_layout.addWidget(self.image_splitter, 1)

        controls = QWidget(self.image_splitter)
        controls.setObjectName('agent_0003_image_controls')
        controls.setMinimumWidth(120)
        controls.setMaximumWidth(245)
        tools = QVBoxLayout(controls)
        tools.setContentsMargins(3, 3, 3, 3)
        self.load_button = QPushButton('Bild laden ...', controls)
        self.load_button.setObjectName('agent_0003_load_button')
        self.recognize_button = QPushButton('Erkennung ...', controls)
        self.recognize_button.setObjectName('agent_0003_recognize_button')
        self.recognize_button.setEnabled(False)
        self.image_info = QLabel('Noch kein Bild geladen.', controls)
        self.image_info.setWordWrap(True)
        tools.addWidget(self.load_button)
        tools.addWidget(self.recognize_button)
        tools.addWidget(self.image_info)
        tools.addStretch(1)
        self.image_splitter.addWidget(controls)

        self.scene = QGraphicsScene(self)
        self.scene.setObjectName('agent_0003_graphics_scene')
        self.image_view = QGraphicsView(self.scene, self.image_splitter)
        self.image_view.setObjectName('agent_0003_graphics_view')
        self.image_view.setRenderHint(QPainter.Antialiasing, True)
        self.image_view.setDragMode(QGraphicsView.NoDrag)
        self.image_view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.image_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.image_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.image_splitter.addWidget(self.image_view)
        self.image_splitter.setSizes([170, 700])
        self.image_splitter.setStretchFactor(0, 0)
        self.image_splitter.setStretchFactor(1, 1)

        self.main_splitter.addWidget(lower)
        self.main_splitter.setSizes([330, 290])
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 2)

        self.load_button.clicked.connect(self.load_picture)
        self.recognize_button.clicked.connect(self.recognize)
        self.figure_combo.currentIndexChanged.connect(self._on_filter_changed)
        self.scene.selectionChanged.connect(self._selection_changed)
        self.analyze_button.clicked.connect(self._emit_answer_to_log)

        data_dir = Path(__file__).resolve().parent / 'data'
        try:
            words_path, questions_path = ensure_agent_databases(data_dir)
            self.language_engine = LanguageEngine(words_path, questions_path)
            self.language_error = ''
        except (ValueError, OSError) as exc:
            self.language_engine = None
            self.language_error = str(exc)
            self.diagnostics.setPlainText('Wort-/Fragen-Datenbank nicht verfügbar: ' + str(exc))
        self.set_dark_mode(self._dark)
        self._log('Agent 0003 initialisiert – OpenCV-Bildanalyse und deutsche Bildfragen')

    def _log(self, message: str) -> None:
        parent = self.parent()
        while parent is not None:
            logger = getattr(parent, 'log', None)
            if callable(logger):
                logger('dBASE/DOS-DEBUG [Agent 0003]: ' + str(message))
                return
            parent = parent.parent()
        print('dBASE/DOS-DEBUG [Agent 0003]:', message)

    def load_picture(self, filename=None):
        """Bild auswählen und anzeigen; keine automatische Erkennung beim Laden."""
        if not filename or isinstance(filename, bool):
            filename, _filter = QFileDialog.getOpenFileName(
                self, 'Bild für Agent 0003 laden', str(Path.home()),
                'Bilder (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;Alle Dateien (*)'
            )
        if not filename:
            return False
        try:
            image = load_image(filename)
        except (OSError, ValueError, cv2.error) as exc:
            QMessageBox.warning(self, 'Bild-Erkennung', 'Bild konnte nicht geladen werden:\n' + str(exc))
            self._log('Bild laden fehlgeschlagen: ' + str(exc))
            return False
        self._image_bgr = image
        self._image_path = Path(filename)
        self.figures = []
        self._recognition_done = False
        self._recognition_error = ''
        self._highlighted_figures.clear()
        self._show_query_only = False
        self._figures_by_item.clear()
        self._overlay_items.clear()
        height, width = image.shape[:2]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        qimage = QImage(rgb.data, width, height, int(rgb.strides[0]), QImage.Format_RGB888).copy()
        self.scene.clear()
        picture = QGraphicsPixmapItem(QPixmap.fromImage(qimage))
        picture.setZValue(-2)
        self.scene.addItem(picture)
        self.scene.setSceneRect(QRectF(0, 0, width, height))
        self.image_view.resetTransform()
        self.image_view.horizontalScrollBar().setValue(0)
        self.image_view.verticalScrollBar().setValue(0)
        self.recognize_button.setEnabled(True)
        self.image_info.setText(f'{self._image_path.name}\n{width} × {height} Pixel')
        self.result_label.setText('Bild geladen – „Erkennung ...“ startet die Figurenanalyse.')
        self._log(f'Bild geladen: {filename} ({width} x {height})')
        return True

    def _detect_current_image(self) -> bool:
        """OpenCV-Analyse ohne rekursiven Aufruf der Satzprüfung.

        Liefert True auch bei 0 erkannten Figuren; so wird bei weiteren
        Textabfragen nicht jedes Mal derselbe Bildscan ausgeführt.
        """
        if self._image_bgr is None:
            self.result_label.setText('Bitte zuerst ein Bild laden.')
            return False
        try:
            figures = detect_figures(self._image_bgr)
        except (ValueError, cv2.error) as exc:
            self._recognition_done = False
            self._recognition_error = str(exc)
            self._log('Erkennungsfehler: ' + self._recognition_error)
            self.diagnostics.setPlainText('OpenCV-Fehler: ' + self._recognition_error)
            self.result_label.setText('Bilderkennung fehlgeschlagen: ' + self._recognition_error)
            return False
        self.figures = figures
        self._recognition_done = True
        self._recognition_error = ''
        self._highlighted_figures.clear()
        self._show_query_only = False
        self.show_filtered_shapes()
        self.result_label.setText(f'Erkannt: {len(self.figures)} Figur(en) im Bild.')
        self._log(f'Erkennung abgeschlossen: {len(self.figures)} Figur(en)')
        return True

    def analyze(self):
        """Satz / Bild prüfen: bei Bedarf zunächst das geladene Bild analysieren.

        Agent 0002 verbindet bereits den Prüfen-Button und die Eingabe-Taste
        mit self.analyze; durch das Überschreiben gilt die Funktion auch
        für diese bestehenden Signalverbindungen.
        """
        if (self._image_bgr is not None
                and not self._recognition_done
                and not self._detect_current_image()):
            return None
        return super().analyze()

    def recognize(self):
        """Explizit erneut erkennen und anschließend die aktuelle Frage prüfen."""
        if not self._detect_current_image():
            return []
        super().analyze()
        return self.figures

    def _on_filter_changed(self, _index=None):
        """Explizite ComboBox-Auswahl beendet die Markierung der letzten Frage."""
        self._show_query_only = False
        self._highlighted_figures.clear()
        self.show_filtered_shapes()

    def show_filtered_shapes(self, _index=None):
        """Nur passende Frage-Treffer markieren, sonst den ComboBox-Filter.

        Figurenerkennung bleibt unverändert im Cache; die Original-Pixmap
        bleibt ebenfalls unverändert. Es werden ausschließlich die bisher
        von uns angelegten Kontur-, Label- und Hintergrund-Items entfernt.
        """
        old_items = self._overlay_items
        self._overlay_items = []
        self._figures_by_item.clear()
        for item in old_items:
            self.scene.removeItem(item)
        selected_filter = self.figure_combo.currentText()
        selected_ids = self._highlighted_figures if self._show_query_only else None
        visible_figures = figures_for_overlay(self.figures, selected_filter, selected_ids)
        for figure in visible_figures:
            poly = QGraphicsPolygonItem(QPolygonF(
                [QPointF(x, y) for x, y in figure.points]
            ))
            match = id(figure) in self._highlighted_figures
            poly.setPen(QPen(QColor('#ffad36' if match else '#10ff40'),
                            3.0 if match else 2.3))
            poly.setBrush(QBrush(Qt.NoBrush))
            poly.setFlag(QGraphicsItem.ItemIsSelectable, True)
            poly.setZValue(10)
            poly.setToolTip(f'{figure.label} – {figure.color} – {figure.center}')
            self.scene.addItem(poly)
            self._overlay_items.append(poly)
            self._figures_by_item[poly] = figure
            # Lesbare, kontrastreiche Beschriftung direkt auf der Figur.
            label = QGraphicsSimpleTextItem(figure.label)
            label.setFont(QFont('Arial', 10, QFont.Bold))
            label.setBrush(QBrush(QColor('#ffffff')))
            bounds = label.boundingRect()
            tx = max(0, figure.center[0] - bounds.width()/2)
            ty = max(0, figure.center[1] - bounds.height()/2)
            bg = QGraphicsRectItem(QRectF(tx-2, ty-1, bounds.width()+4, bounds.height()+2))
            bg.setBrush(QBrush(QColor(0, 0, 0, 175)))
            bg.setPen(QPen(Qt.NoPen))
            bg.setZValue(11)
            # Der Klick muss durch den Label-Hintergrund zur auswählbaren
            # Figurenkontur durchgehen.
            bg.setAcceptedMouseButtons(Qt.NoButton)
            self.scene.addItem(bg)
            label.setPos(tx, ty)
            label.setAcceptedMouseButtons(Qt.NoButton)
            label.setZValue(12)
            self.scene.addItem(label)
            self._overlay_items.extend((bg, label))
        if self._image_path is not None:
            status = 'markiert' if self._show_query_only else 'angezeigt'
            self.image_info.setText(f'{self._image_path.name}\n'
                                    f'{len(self.figures)} erkannt · '
                                    f'{len(visible_figures)} {status}')

    def _selection_changed(self):
        selected = [self._figures_by_item[item]
                    for item in self.scene.selectedItems()
                    if item in self._figures_by_item]
        if selected:
            figure = selected[0]
            self.result_label.setText(
                f'Ausgewählt: {figure.color} {figure.label}, '
                f'Mittelpunkt {figure.center}, Fläche ≈ {figure.area:.0f} px²'
            )
            self._log(f'Auswahl: {figure.color} {figure.label} bei {figure.center}')

    def _run_analysis(self, text):
        """Auch während super().__init__ sicher; danach DBF-Satzmuster nutzen."""
        if not hasattr(self, 'language_engine'):
            return super()._run_analysis(text)
        if self.language_engine is None:
            self.diagnostics.setPlainText('Keine DBF-Prüfung möglich: ' + self.language_error)
            return None
        analysis, tokens, question, diagnostics = self.language_engine.inspect(text)
        self.token_table.setRowCount(len(tokens))
        for row_index, (index, word, category) in enumerate(tokens):
            for column, value in enumerate((str(index), word, category)):
                cell = QTableWidgetItem(value)
                if column == 0:
                    cell.setTextAlignment(Qt.AlignCenter)
                self.token_table.setItem(row_index, column, cell)
        if question:
            intent = question.intent
            if self._image_bgr is None:
                answer = 'Bildfrage erkannt; bitte zuerst ein Bild laden und Figuren erkennen.'
                chosen = []
            else:
                height, width = self._image_bgr.shape[:2]
                answer, chosen = self.language_engine.answer(
                    text, self.figures, width, height
                )
            diagnostics.insert(0, 'Bildfrage: ' + text.strip() + '\nAntwort: ' + answer)
            # Eine Bildfrage zeigt NUR die vom Sprachparser ausgewählten
            # Figuren, unabhängig vom aktuellen ComboBox-Filter. Alle anderen
            # bleiben als Original-Bildpixel ohne Overlay oder Beschriftung.
            self._show_query_only = True
            self._highlighted_figures = {id(fig) for fig in chosen}
            if self._image_bgr is not None:
                self.show_filtered_shapes()
            # Erst nach dem Neuzeichnen: selectionChanged kann beim Entfernen
            # einer alten Kontur ausgelöst werden und sonst den Text ersetzen.
            self.result_label.setText('Absicht: ' + intent + ' | ' + answer.replace('\n', ' | '))
        else:
            # Ungültiger/normaler Text darf keine Markierungen einer alten
            # Frage stehenlassen; über die ComboBox bleiben sie abrufbar.
            self._show_query_only = True
            self._highlighted_figures.clear()
            if self._image_bgr is not None:
                self.show_filtered_shapes()
            self.result_label.setText('Keine unterstützte Bildfrage erkannt; Textbasisprüfung durchgeführt.')
        known = sum(1 for _i, word, category in tokens
                    if word.isalpha() and '(nicht im DBF)' not in category)
        diagnostics.extend((
            '', f'Wortschatz: {len(self.language_engine.words)} Einträge, '
                f'{known} erkannte Satzwörter.',
            'Hinweis: Das sind Mustersätze und Plausibilitätsregeln, '
            'keine vollständige deutsche Grammatik oder allgemeines Weltwissen.',
        ))
        self.diagnostics.setPlainText('\n'.join(diagnostics))
        return question

    def _emit_answer_to_log(self):
        self._log(self.result_label.text())

    def set_dark_mode(self, enabled):
        super().set_dark_mode(enabled)
        self.setStyleSheet(self.styleSheet().replace(
            'QWidget#agent_0002_association_widget',
            'QWidget#agent_0003_recognition_widget'))
        if not hasattr(self, 'scene'):
            return
        self.scene.setBackgroundBrush(QColor('#1a1a1a' if enabled else '#f5f5f5'))
        self.image_view.setStyleSheet(
            'QGraphicsView { background:%s; border:1px solid %s; }' %
            ('#202020' if enabled else '#ffffff', '#555' if enabled else '#999')
        )
