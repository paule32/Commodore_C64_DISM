"""Stage 329: pixelgenauer dBase-Brush-Editor (PyQt5)."""
import json
from pathlib import Path
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal, QMimeData
from PyQt5.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QScrollArea, QFileDialog, QColorDialog,
                             QMessageBox, QDialogButtonBox, QLabel, QSpinBox, QApplication)

DEFAULT_PALETTE = [
    '#000000','#FFFFFF','#808080','#C0C0C0','#800000','#FF0000','#808000','#FFFF00',
    '#008000','#00FF00','#008080','#00FFFF','#000080','#0000FF','#800080','#FF00FF',
    '#202020','#404040','#606060','#A0A0A0','#FF8000','#FFC080','#804000','#C08040',
    '#004080','#0080FF','#80C0FF','#400080','#8040C0','#C080FF','#408040','#80FF80'
]


def empty_pattern(width, height):
    w, h = max(1, min(128, int(width))), max(1, min(128, int(height)))
    return {'format':'d64-custom-brush-v1', 'width':w, 'height':h,
            'palette':DEFAULT_PALETTE[:], 'pixels':[[1 for _ in range(w)] for _ in range(h)]}


def validated_pattern(data):
    if not isinstance(data, dict) or data.get('format') != 'd64-custom-brush-v1':
        raise ValueError('Unbekanntes Custom-Brush-Format')
    w, h = int(data['width']), int(data['height'])
    if not (1 <= w <= 128 and 1 <= h <= 128):
        raise ValueError('Mustergröße muss zwischen 1 und 128 Pixel liegen')
    palette = data['palette']
    if not isinstance(palette, list) or len(palette) != 32 or any(not QColor(str(c)).isValid() for c in palette):
        raise ValueError('Die Palette muss genau 32 gültige Farben enthalten')
    pixels = data['pixels']
    if len(pixels) != h or any(len(row) != w for row in pixels):
        raise ValueError('Pixelgeometrie stimmt nicht mit Width/Height überein')
    if any(type(index) is not int or not 0 <= index < 32 for row in pixels for index in row):
        raise ValueError('Ungültiger Farbindex')
    return {'format':'d64-custom-brush-v1', 'width':w, 'height':h,
            'palette':[QColor(c).name().upper() for c in palette],
            'pixels':[list(row) for row in pixels]}


def pattern_pixmap(data):
    data = validated_pattern(data)
    image = QImage(data['width'], data['height'], QImage.Format_ARGB32)
    palette = [QColor(v) for v in data['palette']]
    for y, row in enumerate(data['pixels']):
        for x, index in enumerate(row):
            image.setPixelColor(x, y, palette[index])
    return QPixmap.fromImage(image)


class _PixelGrid(QWidget):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.cell = 14  # 12 Pixel Vorschau + 2 Pixel Gitternetz
        self.setMouseTracking(True)
        self.setObjectName('d64CustomBrushPixelGrid')
        self.resize_grid()

    def resize_grid(self):
        self.setFixedSize(self.owner.data['width'] * self.cell + 2,
                          self.owner.data['height'] * self.cell + 2)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#303030'))
        palette = [QColor(v) for v in self.owner.data['palette']]
        for y, row in enumerate(self.owner.data['pixels']):
            for x, index in enumerate(row):
                p.fillRect(QRect(x * self.cell + 1, y * self.cell + 1,
                                 self.cell - 2, self.cell - 2), palette[index])
        p.setPen(QPen(QColor('#505050'), 2))
        for x in range(self.owner.data['width'] + 1):
            xx = x * self.cell
            p.drawLine(xx, 0, xx, self.height())
        for y in range(self.owner.data['height'] + 1):
            yy = y * self.cell
            p.drawLine(0, yy, self.width(), yy)
        p.end()

    def _paint_cell(self, event):
        x, y = event.pos().x() // self.cell, event.pos().y() // self.cell
        if 0 <= x < self.owner.data['width'] and 0 <= y < self.owner.data['height']:
            if self.owner.data['pixels'][y][x] != self.owner.color_index:
                self.owner.data['pixels'][y][x] = self.owner.color_index
                self.update(QRect(x * self.cell, y * self.cell, self.cell + 2, self.cell + 2))
                self.owner.repeat_preview.refresh_pattern()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._paint_cell(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._paint_cell(event)


class _PatternRepeatPreview(QWidget):
    """128x128 echte Pixel, mit nahtloser Wiederholung der Brush-Kachel."""
    PREVIEW_SIZE = 128

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setObjectName('d64CustomBrushRepeatPreview')
        self.setFixedSize(self.PREVIEW_SIZE, self.PREVIEW_SIZE)
        self._image = None
        self.refresh_pattern()

    def refresh_pattern(self):
        data = self.owner.data
        width, height = data['width'], data['height']
        palette = [QColor(color).rgba() for color in data['palette']]
        source = data['pixels']
        image = QImage(self.PREVIEW_SIZE, self.PREVIEW_SIZE, QImage.Format_ARGB32)
        for y in range(self.PREVIEW_SIZE):
            row = source[y % height]
            for x in range(self.PREVIEW_SIZE):
                image.setPixel(x, y, palette[row[x % width]])
        self._image = image
        self.update()

    def paintEvent(self, event):
        if self._image is not None:
            painter = QPainter(self)
            painter.drawImage(0, 0, self._image)
            painter.end()


class _PaletteButton(QPushButton):
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class D64CustomBrushDialog(QDialog):
    def __init__(self, width=16, height=16, data=None, path='', parent=None):
        super().__init__(parent)
        self.setObjectName('d64CustomBrushDialog')
        self.setWindowTitle('Custom Brush – Pixelmuster')
        self.data = validated_pattern(data) if data is not None else empty_pattern(width, height)
        self.file_path = str(path or '')
        self.color_index = 0
        self.resize(920, 710)
        self.setStyleSheet('QDialog { background:#242424; color:#eee; } QLabel { color:#eee; } '
                           'QPushButton { min-height:24px; background:#343434; color:#fff; border:1px solid #666; padding:4px; } '
                           'QPushButton:hover { border:1px solid #f0c600; } '
                           'QSpinBox { background:#343434; color:#fff; border:1px solid #666; padding:3px; }')
        outer = QVBoxLayout(self)
        middle = QHBoxLayout()
        outer.addLayout(middle, 1)
        actions = QVBoxLayout()
        middle.addLayout(actions)
        for text, callback, name in (
            ('Speichern', self.save, 'd64CustomBrushSave'),
            ('Speichern unter...', self.save_as, 'd64CustomBrushSaveAs'),
            ('Laden', self.load, 'd64CustomBrushLoad')):
            button = QPushButton(text, self)
            button.setObjectName(name)
            button.clicked.connect(callback)
            actions.addWidget(button)

        for label, attribute, name, initial in (
            ('Width', 'width_spin', 'd64CustomBrushWidth', self.data['width']),
            ('Height', 'height_spin', 'd64CustomBrushHeight', self.data['height'])):
            actions.addWidget(QLabel(label))
            spin = QSpinBox(self)
            spin.setObjectName(name)
            spin.setRange(1, 128)
            spin.setValue(initial)
            spin.valueChanged.connect(self._resize_from_spinboxes)
            setattr(self, attribute, spin)
            actions.addWidget(spin)

        for text, callback, name in (
            ('Kopieren', self.copy_pattern, 'd64CustomBrushCopy'),
            ('Einfügen', self.paste_pattern, 'd64CustomBrushPaste'),
            ('Bereinigen', self.clear_pattern, 'd64CustomBrushClear')):
            button = QPushButton(text, self)
            button.setObjectName(name)
            button.clicked.connect(callback)
            actions.addWidget(button)

        move = QGridLayout()
        actions.addLayout(move)
        for text, row, col, dx, dy, name in (
            ('↑', 0, 1, 0, -1, 'd64CustomBrushMoveUp'),
            ('←', 1, 0, -1, 0, 'd64CustomBrushMoveLeft'),
            ('↓', 1, 1, 0, 1, 'd64CustomBrushMoveDown'),
            ('→', 1, 2, 1, 0, 'd64CustomBrushMoveRight')):
            button = QPushButton(text, self)
            button.setObjectName(name)
            button.setToolTip({'↑':'Hoch', '↓':'Runter', '←':'Links', '→':'Rechts'}[text])
            button.clicked.connect(lambda _checked=False, x=dx, y=dy: self.shift_pattern(x, y))
            move.addWidget(button, row, col)

        for text, direction, name in (
            ('Vertikal spiegeln', 'vertical', 'd64CustomBrushFlipVertical'),
            ('Horizontal spiegeln', 'horizontal', 'd64CustomBrushFlipHorizontal')):
            button = QPushButton(text, self)
            button.setObjectName(name)
            button.clicked.connect(lambda _checked=False, d=direction: self.flip_pattern(d))
            actions.addWidget(button)
        actions.addStretch(1)

        editor_col = QVBoxLayout()
        middle.addLayout(editor_col, 1)
        scroll = QScrollArea(self)
        scroll.setObjectName('d64CustomBrushDrawingScroll')
        scroll.setWidgetResizable(False)
        self.grid = _PixelGrid(self)
        scroll.setWidget(self.grid)
        editor_col.addWidget(scroll, 1)

        colors = QGridLayout()
        colors.setSpacing(3)
        editor_col.addLayout(colors)
        self.buttons = []
        for index in range(32):
            button = _PaletteButton(str(index + 1))
            button.setObjectName(f'd64CustomBrushColor{index:02d}')
            button.setFixedSize(42, 24)
            button.clicked.connect(lambda _checked=False, i=index: self.select_color(i))
            button.doubleClicked.connect(lambda i=index: self.edit_color(i))
            colors.addWidget(button, index // 16, index % 16)
            self.buttons.append(button)

        right = QVBoxLayout()
        middle.addLayout(right)
        preview_label = QLabel('Musterwiederholung (128 × 128 Pixel)')
        preview_label.setObjectName('d64CustomBrushRepeatPreviewLabel')
        preview_label.setWordWrap(True)
        right.addWidget(preview_label)
        self.repeat_preview = _PatternRepeatPreview(self)
        right.addWidget(self.repeat_preview, 0, Qt.AlignHCenter)
        right.addStretch(1)
        self._refresh_colors()
        self.location = QLabel(self.file_path or 'Noch keine JSON-Datei')
        self.location.setWordWrap(True)
        outer.addWidget(self.location)
        controls = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        controls.accepted.connect(self.accept)
        controls.rejected.connect(self.reject)
        outer.addWidget(controls)

    CLIPBOARD_MIME = 'application/x-d64-custom-brush+json'

    def _changed(self):
        self.grid.update()
        self.repeat_preview.refresh_pattern()

    def _set_pattern(self, pattern):
        self.data = validated_pattern(pattern)
        for spin, value in ((self.width_spin, self.data['width']),
                            (self.height_spin, self.data['height'])):
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        self.grid.resize_grid()
        self._refresh_colors()

    def _resize_from_spinboxes(self, _value=None):
        if not hasattr(self, 'height_spin') or not hasattr(self, 'grid'):
            return
        width, height = self.width_spin.value(), self.height_spin.value()
        if (width, height) == (self.data['width'], self.data['height']):
            return
        old = self.data['pixels']
        old_w, old_h = self.data['width'], self.data['height']
        self.data['width'], self.data['height'] = width, height
        self.data['pixels'] = [
            [old[y][x] if x < old_w and y < old_h else 1 for x in range(width)]
            for y in range(height)
        ]
        self.grid.resize_grid()
        self._changed()

    def copy_pattern(self):
        clipboard = QApplication.clipboard()
        mime = QMimeData()
        mime.setData(self.CLIPBOARD_MIME, json.dumps(self.data).encode('utf-8'))
        mime.setImageData(pattern_pixmap(self.data).toImage())
        clipboard.setMimeData(mime)

    def paste_pattern(self):
        mime = QApplication.clipboard().mimeData()
        if mime is None or not mime.hasFormat(self.CLIPBOARD_MIME):
            QMessageBox.information(self, 'Custom Brush',
                                    'Kein Custom-Brush-Muster in der Zwischenablage.')
            return
        try:
            pattern = validated_pattern(json.loads(bytes(mime.data(self.CLIPBOARD_MIME)).decode('utf-8')))
        except (ValueError, KeyError, TypeError, UnicodeError) as exc:
            QMessageBox.warning(self, 'Custom Brush', f'Ungültiges Muster: {exc}')
            return
        # Der JSON-Dateipfad ist kein Teil der Zwischenablage und bleibt unverändert.
        self._set_pattern(pattern)

    def clear_pattern(self):
        # Inhalt leeren, ohne die gespeicherte JSON-Datei zu verändern.
        self.data['pixels'] = [[1] * self.data['width'] for _ in range(self.data['height'])]
        self._changed()

    def shift_pattern(self, dx, dy):
        width, height = self.data['width'], self.data['height']
        source = self.data['pixels']
        self.data['pixels'] = [
            [source[(y - dy) % height][(x - dx) % width] for x in range(width)]
            for y in range(height)
        ]
        self._changed()

    def flip_pattern(self, direction):
        if direction == 'vertical':
            self.data['pixels'] = list(reversed(self.data['pixels']))
        elif direction == 'horizontal':
            self.data['pixels'] = [list(reversed(row)) for row in self.data['pixels']]
        else:
            raise ValueError(f'Unbekannte Spiegelachse: {direction}')
        self._changed()

    def _refresh_colors(self):
        for i, button in enumerate(self.buttons):
            color = QColor(self.data['palette'][i])
            foreground = '#000' if color.lightness() > 140 else '#fff'
            border = '3px solid #FFD800' if i == self.color_index else '1px solid #707070'
            button.setStyleSheet(f'background:{color.name()}; color:{foreground}; border:{border};')
        self.grid.update()
        if hasattr(self, 'repeat_preview'):
            self.repeat_preview.refresh_pattern()

    def select_color(self, index):
        self.color_index = index
        self._refresh_colors()

    def edit_color(self, index):
        color = QColorDialog.getColor(QColor(self.data['palette'][index]), self, 'Palettenfarbe wählen')
        if color.isValid():
            self.data['palette'][index] = color.name().upper()
            self.select_color(index)

    def accept(self):
        # Bei bestätigtem Dialog muss der referenzierte Musterstand auf Platte liegen.
        if self.save():
            super().accept()

    def save(self):
        if not self.file_path:
            return self.save_as()
        try:
            Path(self.file_path).write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding='utf-8')
            self.location.setText(self.file_path)
            return True
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Custom Brush', str(exc))
            return False

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Custom Brush speichern', self.file_path or 'brush.json', 'JSON (*.json)')
        if not path:
            return False
        if not path.lower().endswith('.json'):
            path += '.json'
        self.file_path = path
        return self.save()

    def load(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Custom Brush laden', self.file_path, 'JSON (*.json)')
        if not path:
            return
        try:
            loaded = validated_pattern(json.loads(Path(path).read_text(encoding='utf-8')))
        except (ValueError, OSError, KeyError, TypeError) as exc:
            QMessageBox.warning(self, 'Custom Brush', str(exc))
            return
        self._set_pattern(loaded)
        self.file_path = path
        self.location.setText(path)
