"""Stage 416 – dockbarer 16-Farben-Bitmap-Sprite-Editor für d64_dism.

Der Editor ist unabhängig vom hardwarelimitierten VIC-II-Sprite-Format.
Die Datei .bmsprite erhält einen Farbindex 0..15 pro Pixel (255 transparent).
"""
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QScrollArea, QSpinBox, QSizePolicy,
    QFileDialog, QMessageBox,
)
from c64_bitmap_sprite import (
    TRANSPARENT, EXTENSIONS, empty_sprite, resized_sprite,
    load_bitmap_sprites, save_bitmap_sprites,
)


class C64BitmapSpriteCanvas(QWidget):
    pixelsChanged = pyqtSignal()

    def __init__(self, palette, parent=None):
        super().__init__(parent)
        self.palette = palette
        self.width_pixels = 24
        self.height_pixels = 21
        self.sprite_data = empty_sprite()
        self.brush = 1
        self.zoom = 18
        self.drawing = None
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        self._update_size()

    def _update_size(self):
        self.setFixedSize(self.width_pixels * self.zoom + 1,
                          self.height_pixels * self.zoom + 1)
        self.update()

    def set_sprite(self, pixels, width, height):
        self.width_pixels = int(width)
        self.height_pixels = int(height)
        self.sprite_data = pixels  # shared backing: update editor's current sprite directly
        self._update_size()

    def set_zoom(self, zoom):
        self.zoom = max(4, min(32, int(zoom)))
        self._update_size()

    def _draw(self, point):
        x, y = point.x() // self.zoom, point.y() // self.zoom
        if not (0 <= x < self.width_pixels and 0 <= y < self.height_pixels):
            return
        new_value = self.brush if self.drawing else TRANSPARENT
        index = y * self.width_pixels + x
        if self.sprite_data[index] != new_value:
            self.sprite_data[index] = new_value
            self.pixelsChanged.emit()
            self.update()

    def mousePressEvent(self, event):
        if event.button() not in (Qt.LeftButton, Qt.RightButton):
            return
        self.drawing = event.button() == Qt.LeftButton
        self._draw(event.pos())
        event.accept()

    def mouseMoveEvent(self, event):
        if self.drawing is not None:
            self._draw(event.pos())

    def mouseReleaseEvent(self, event):
        self.drawing = None

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#1A2134'))
        dx = self.zoom
        for y in range(self.height_pixels):
            for x in range(self.width_pixels):
                value = self.sprite_data[y * self.width_pixels + x]
                if value == TRANSPARENT:
                    color = QColor('#354259' if (x+y) % 2 else '#4B5972')
                else:
                    color = QColor(self.palette[value][1])
                painter.fillRect(x * dx + 1, y * dx + 1,
                                 max(1, dx - 1), max(1, dx - 1), color)
        painter.end()


class C64BitmapSpriteEditorDialog(QWidget):
    """Mehrfach-Sprite-Editor mit frei wählbaren C64-Palettenfarben je Pixel."""

    def __init__(self, parent, *, initial_directory, initial_path=None, palette=None):
        super().__init__(parent)
        self.setObjectName('c64_bitmap_sprite_editor')
        self.setWindowTitle('C64 Bitmap Sprite Editor')
        self.initial_directory = Path(initial_directory)
        self.current_path = None
        self.project_owner = None
        self._c64_sprite_tree_item = None
        self.palette = list(palette or [])
        if len(self.palette) != 16:
            raise ValueError('Bitmap-Sprite-Editor benötigt genau 16 C64-Farben')
        self.width_pixels = 24
        self.height_pixels = 21
        self.sprites = [empty_sprite()]
        self.modified = False
        self._updating = False
        self._build_ui()
        self._switch_sprite(1)
        if initial_path is not None:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.load_file(initial_path))

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        file_row = QHBoxLayout()
        self.new_button = QPushButton('Neu', self)
        self.load_button = QPushButton('Öffnen …', self)
        self.save_button = QPushButton('Speichern', self)
        self.save_as_button = QPushButton('Speichern unter …', self)
        for button in (self.new_button, self.load_button, self.save_button, self.save_as_button):
            file_row.addWidget(button)
        file_row.addStretch(1)
        outer.addLayout(file_row)
        self.path_label = QLabel('Neues Bitmap Sprite (.bmsprite) – noch nicht gespeichert', self)
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        outer.addWidget(self.path_label)

        content = QHBoxLayout()
        outer.addLayout(content, 1)
        scroll = QScrollArea(self)
        scroll.setObjectName('c64_bitmap_sprite_canvas_scroll')
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setMinimumSize(220, 190)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas = C64BitmapSpriteCanvas(self.palette, scroll)
        scroll.setWidget(self.canvas)
        content.addWidget(scroll, 1)

        panel = QWidget(self)
        panel.setMinimumWidth(255)
        panel.setMaximumWidth(345)
        side = QVBoxLayout(panel)
        side.setContentsMargins(4, 0, 4, 0)
        content.addWidget(panel)
        settings = QGroupBox('Bitmap-Sprite-Einstellungen', panel)
        form = QFormLayout(settings)
        self.sprite_number = QSpinBox(settings)
        self.sprite_number.setRange(1, 1)
        form.addRow('Sprite-Nr.:', self.sprite_number)
        self.width_spin = QSpinBox(settings)
        self.width_spin.setRange(1, 128)
        self.width_spin.setValue(24)
        self.height_spin = QSpinBox(settings)
        self.height_spin.setRange(1, 128)
        self.height_spin.setValue(21)
        form.addRow('Rasterbreite:', self.width_spin)
        form.addRow('Rasterhöhe:', self.height_spin)
        self.zoom_spin = QSpinBox(settings)
        self.zoom_spin.setRange(4, 32)
        self.zoom_spin.setValue(18)
        self.zoom_spin.setSuffix(' px')
        form.addRow('Editor-Zoom:', self.zoom_spin)
        side.addWidget(settings)

        palette_group = QGroupBox('Alle 16 C64-Farben pro Pixel', panel)
        palette_layout = QVBoxLayout(palette_group)
        palette_grid = QGridLayout()
        self.palette_buttons = []
        for index, (name, color) in enumerate(self.palette):
            button = QPushButton(f'{index:02d}', palette_group)
            button.setCheckable(True)
            button.setToolTip(f'{index}: {name}')
            pix = QPixmap(24, 24)
            pix.fill(QColor(color))
            button.setIcon(QIcon(pix))
            button.clicked.connect(lambda _checked=False, n=index: self._choose_color(n))
            palette_grid.addWidget(button, index // 4, index % 4)
            self.palette_buttons.append(button)
        palette_layout.addLayout(palette_grid)
        transparent_button = QPushButton('Transparent (Rechtsklick)', palette_group)
        transparent_button.clicked.connect(lambda: self._choose_color(TRANSPARENT))
        palette_layout.addWidget(transparent_button)
        side.addWidget(palette_group)

        operations = QGroupBox('Bearbeiten', panel)
        operations_grid = QGridLayout(operations)
        self.add_button = QPushButton('Sprite hinzufügen', operations)
        self.duplicate_button = QPushButton('Duplizieren', operations)
        self.delete_button = QPushButton('Sprite entfernen', operations)
        self.clear_button = QPushButton('Sprite leeren', operations)
        self.fill_button = QPushButton('Mit Farbe füllen', operations)
        operations_grid.addWidget(self.add_button, 0, 0)
        operations_grid.addWidget(self.duplicate_button, 0, 1)
        operations_grid.addWidget(self.delete_button, 1, 0)
        operations_grid.addWidget(self.clear_button, 1, 1)
        operations_grid.addWidget(self.fill_button, 2, 0, 1, 2)
        side.addWidget(operations)
        self.info_label = QLabel(
            'Links zeichnen, rechts transparent löschen.\n'
            'Das eigene .bmsprite-Format enthält 16 Farben/Pixel; '
            'es ist kein direktes VIC-II-Hardware-Sprite.', panel)
        self.info_label.setWordWrap(True)
        side.addWidget(self.info_label)
        side.addStretch(1)

        self.new_button.clicked.connect(self._new_clicked)
        self.load_button.clicked.connect(self.load_dialog)
        self.save_button.clicked.connect(self.save)
        self.save_as_button.clicked.connect(self.save_as)
        self.sprite_number.valueChanged.connect(self._switch_sprite)
        self.width_spin.valueChanged.connect(self._resize_document)
        self.height_spin.valueChanged.connect(self._resize_document)
        self.zoom_spin.valueChanged.connect(self.canvas.set_zoom)
        self.add_button.clicked.connect(self.add_sprite)
        self.duplicate_button.clicked.connect(self.duplicate_sprite)
        self.delete_button.clicked.connect(self.delete_sprite)
        self.clear_button.clicked.connect(lambda: self._fill(TRANSPARENT))
        self.fill_button.clicked.connect(lambda: self._fill(self.canvas.brush))
        self.canvas.pixelsChanged.connect(self._mark_modified)
        self._choose_color(1)

    def _choose_color(self, index):
        self.canvas.brush = index
        for i, button in enumerate(self.palette_buttons):
            button.setChecked(i == index)

    def _mark_modified(self, changed=True):
        self.modified = bool(changed)
        self.setWindowTitle('C64 Bitmap Sprite Editor' + (' *' if self.modified else ''))

    def _switch_sprite(self, number):
        index = max(0, min(len(self.sprites) - 1, int(number) - 1))
        self.canvas.set_sprite(self.sprites[index], self.width_pixels, self.height_pixels)
        self.delete_button.setEnabled(len(self.sprites) > 1)

    def _resize_document(self, _value=None):
        if self._updating:
            return
        new_width, new_height = self.width_spin.value(), self.height_spin.value()
        if (new_width, new_height) != (self.width_pixels, self.height_pixels):
            self.sprites = [resized_sprite(data, self.width_pixels, self.height_pixels,
                                           new_width, new_height) for data in self.sprites]
            self.width_pixels, self.height_pixels = new_width, new_height
            self._switch_sprite(self.sprite_number.value())
            self._mark_modified()

    def _fill(self, color):
        sprite = self.sprites[self.sprite_number.value() - 1]
        if any(value != color for value in sprite):
            sprite[:] = bytes([color]) * len(sprite)
            self.canvas.update()
            self._mark_modified()

    def add_sprite(self):
        if len(self.sprites) >= 256:
            QMessageBox.warning(self, 'Bitmap-Sprites', 'Maximal 256 Sprites pro Datei')
            return
        self.sprites.append(empty_sprite(self.width_pixels, self.height_pixels))
        self.sprite_number.setMaximum(len(self.sprites))
        self.sprite_number.setValue(len(self.sprites))
        self._mark_modified()

    def duplicate_sprite(self):
        if len(self.sprites) >= 256:
            QMessageBox.warning(self, 'Bitmap-Sprites', 'Maximal 256 Sprites pro Datei')
            return
        self.sprites.append(bytearray(self.sprites[self.sprite_number.value() - 1]))
        self.sprite_number.setMaximum(len(self.sprites))
        self.sprite_number.setValue(len(self.sprites))
        self._mark_modified()

    def delete_sprite(self):
        if len(self.sprites) <= 1:
            return
        self.sprites.pop(self.sprite_number.value() - 1)
        self.sprite_number.setMaximum(len(self.sprites))
        self.sprite_number.setValue(min(self.sprite_number.value(), len(self.sprites)))
        self._switch_sprite(self.sprite_number.value())
        self._mark_modified()

    def _confirm_discard(self):
        if not self.modified:
            return True
        response = QMessageBox.question(
            self, 'Ungespeichertes Bitmap Sprite', 'Änderungen speichern?',
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save)
        if response == QMessageBox.Cancel:
            return False
        return response != QMessageBox.Save or self.save()

    def _new_clicked(self):
        if self.project_owner is not None:
            self.project_owner.new_c64_bitmap_sprite_project()
        elif self._confirm_discard():
            self.new_sprite_document()

    def new_sprite_document(self):
        self._updating = True
        try:
            self.width_pixels = 24
            self.height_pixels = 21
            self.sprites = [empty_sprite()]
            self.sprite_number.setMaximum(1)
            self.sprite_number.setValue(1)
            self.width_spin.setValue(24)
            self.height_spin.setValue(21)
        finally:
            self._updating = False
        self.current_path = None
        self._c64_sprite_tree_item = None
        self._switch_sprite(1)
        self.path_label.setText('Neues Bitmap Sprite (.bmsprite) – noch nicht gespeichert')
        self._mark_modified(False)

    def load_dialog(self):
        if not self._confirm_discard():
            return
        start = str(self.current_path.parent if self.current_path else self.initial_directory)
        filename, _filter = QFileDialog.getOpenFileName(
            self, 'Bitmap-Sprites laden', start,
            'C64 Bitmap-Sprites (*.bmsprite *.bmspr)')
        if filename:
            self.load_file(Path(filename), already_confirmed=True)

    def load_file(self, path, already_confirmed=False):
        if not already_confirmed and not self._confirm_discard():
            return False
        try:
            path = Path(path).expanduser().resolve()
            if path.suffix.casefold() not in EXTENSIONS:
                raise ValueError('Bitmap-Sprites müssen die Endung .bmsprite oder .bmspr besitzen')
            sprites, width, height = load_bitmap_sprites(path)
        except (OSError, ValueError, TypeError) as exc:
            QMessageBox.critical(self, 'Bitmap-Sprite laden', str(exc))
            return False
        self._updating = True
        try:
            self.sprites = sprites
            self.width_pixels, self.height_pixels = width, height
            self.sprite_number.setMaximum(len(sprites))
            self.sprite_number.setValue(1)
            self.width_spin.setValue(width)
            self.height_spin.setValue(height)
        finally:
            self._updating = False
        self.current_path = path
        self.initial_directory = path.parent
        self.path_label.setText(f'{path} – {len(sprites)} Bitmap Sprite(s), {width}×{height}')
        self._switch_sprite(1)
        self._mark_modified(False)
        if self.project_owner is not None:
            self.project_owner._register_c64_sprite_editor_file(self, path)
        return True

    def save(self):
        if self.current_path is None:
            return self.save_as()
        try:
            if self.current_path.suffix.casefold() not in EXTENSIONS:
                raise ValueError('Nur das Binärformat .bmsprite/.bmspr kann gespeichert werden')
            save_bitmap_sprites(self.current_path, self.sprites,
                                self.width_pixels, self.height_pixels)
        except (OSError, ValueError, TypeError) as exc:
            QMessageBox.critical(self, 'Bitmap-Sprite speichern', str(exc))
            return False
        self.path_label.setText(
            f'{self.current_path} – {len(self.sprites)} Bitmap Sprite(s), '
            f'{self.width_pixels}×{self.height_pixels}, 16 C64-Farben')
        self._mark_modified(False)
        if self.project_owner is not None:
            self.project_owner._register_c64_sprite_editor_file(self, self.current_path)
        return True

    def save_as(self):
        initial = self.current_path or self.initial_directory / 'Bitmap_Sprite_1.bmsprite'
        filename, selected_filter = QFileDialog.getSaveFileName(
            self, 'Bitmap-Sprites binär speichern', str(initial),
            'C64 Bitmap-Sprites (*.bmsprite);;C64 Bitmap-Sprites kompakt (*.bmspr)')
        if not filename:
            return False
        path = Path(filename)
        if not path.suffix:
            path = path.with_suffix('.bmspr' if '*.bmspr' in selected_filter else '.bmsprite')
        if path.suffix.casefold() not in EXTENSIONS:
            QMessageBox.warning(self, 'Bitmap-Sprite', 'Bitte .bmsprite oder .bmspr verwenden')
            return False
        old = self.current_path
        self.current_path = path.expanduser().resolve()
        if not self.save():
            self.current_path = old
            return False
        return True

    def closeEvent(self, event):
        event.accept() if self._confirm_discard() else event.ignore()
