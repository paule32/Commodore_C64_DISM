# ---------------------------------------------------------------------------
# File:   locales.py
# Author: (c) 2024, 2025, 2026 Jens Kallup - paule32
# All rights reserved
# ---------------------------------------------------------------------------
from __future__    import annotations
from share.common  import *

import share.resrces.flags_rc

class _LocalizeLineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)


class LanguageRadioFlag(QWidget):
    def __init__(self, code: str, text: str, flag_path: str, parent=None):
        super().__init__(parent)

        self.code      = code
        self.text      = share.locales.tr(text)
        self.flag_path = f":/flags/{flag_path}.png"

        self.radio = QRadioButton(self.code)
        self.radio.setToolTip(self.text)
        
        self.radio.setFont(QFont("Consolas", 10))

        self.flag = QLabel()
        self.flag.setFixedSize(22, 12)
        self.flag.setAlignment(Qt.AlignCenter)
        self.flag.setToolTip(self.text)

        pix = QPixmap(self.flag_path)
        if not pix.isNull():
            self.flag.setPixmap(
                pix.scaled(
                    22,
                    12,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lay.addWidget(self.radio)
        lay.addWidget(self.flag)
        lay.addStretch(1)

class LocalizeCodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_number_area = _LocalizeLineNumberArea(self)
        try:
            self.blockCountChanged    .connect(self.updateLineNumberAreaWidth)
            self.updateRequest        .connect(self.updateLineNumberArea)
            self.cursorPositionChanged.connect(self.highlightCurrentLine)
        except Exception:
            pass
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        self.setFont(QFont("Arial", 10))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    def lineNumberAreaWidth(self):
        digits = 1
        maximum = max(1, self.blockCount())
        while maximum >= 10:
            maximum //= 10
            digits += 1
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(28, 28, 28))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(170, 170, 170))
                painter.drawText(0, top, self._line_number_area.width() - 4, self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlightCurrentLine(self):
        extra = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            line_color = QColor(255, 216, 102, 28)
            sel.format.setBackground(line_color)
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)


class LocalizeToolWindow(QWidget):
    HEADER_FIELDS = [
        "Project-Id-Version",
        "Report-Msgid-Bugs-To",
        "POT-Creation-Date",
        "PO-Revision-Date",
        "Last-Translator",
        "Language-Team",
        "Language",
        "MIME-Version",
        "Content-Type",
        "Content-Transfer-Encoding",
    ]

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        
        self.main_window = main_window
        
        self.setMinimumWidth (920)
        self.setMinimumHeight(400)
        
        self.entries = []
        
        self._current_index = -1
        self._block_lang_sync = False
        
        self.setFont(QFont("Arial", 10))
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        self._build_ui()
        self._load_state()
        self._apply_default_headers()
        
        self.ed_po_path.setText("")
        self.ed_mo_path.setText("")
        
        try:
            if hasattr(self, "_sync_language_buttons"):
                self._sync_language_buttons()
        except Exception:
            pass
        self._refresh_msgid_list()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.tabs = QTabWidget(self)
        root.addWidget(self.tabs, 1)
        
        self.tabs.addTab(self._build_entries_tab (), share.locales.tr("Entries"))
        self.tabs.addTab(self._build_settings_tab(), share.locales.tr("Settings"))

        #btn_row = QHBoxLayout()
        #self.btn_create = QPushButton(share.locales.tr("Create"), self)
        #self.btn_help   = QPushButton(share.locales.tr("Help")  , self)
        #self.btn_cancel = QPushButton(share.locales.tr("Cancel"), self)
        #for b in (self.btn_create, self.btn_help, self.btn_cancel):
        #    b.setMinimumWidth(95)
        #    btn_row.addWidget(b)
        #root.addLayout(btn_row)

        #self.btn_create.clicked.connect(self._create_mo_file)
        #self.btn_help  .clicked.connect(self._show_help)
        #self.btn_cancel.clicked.connect(self._close_self)

    def _build_entries_tab(self):
        content = QWidget()
        outer = QHBoxLayout(content)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        right_tabs = QTabWidget(content)
        right_tabs.setMinimumWidth(240)

        msgstr_tab = QWidget(right_tabs)
        msgstr_lay = QVBoxLayout(msgstr_tab)
        
        msgstr_lay.setContentsMargins(6, 6, 6, 6)
        msgstr_lay.setSpacing(6)
        
        
        lang_tab = QWidget(right_tabs)
        lang_lay = QVBoxLayout(lang_tab)
        
        lang_lay.setContentsMargins(6, 6, 6, 6)
        lang_lay.setSpacing(6)
        
        lang_row = QHBoxLayout()
        lang_row.setSpacing(8)

        self.gb_source  = QGroupBox(share.locales.tr("Source"), lang_tab)
        self.gb_dest    = QGroupBox(share.locales.tr("Destination"), lang_tab)
        
        self.gb_source.setMinimumHeight(1500)
        self.gb_dest  .setMinimumHeight(1500)
        
        self.gb_source.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.gb_dest  .setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        self.src_group  = QButtonGroup(self)
        self.dst_group  = QButtonGroup(self)
        
        self.src_radios = {}
        self.dst_radios = {}

        src_lay = QVBoxLayout(self.gb_source)
        dst_lay = QVBoxLayout(self.gb_dest)
        
        src_lay.setSpacing(4)
        dst_lay.setSpacing(4)
        
        for code, title, flag_path in share.locales.LANGUAGE_CODES:
            row_src = LanguageRadioFlag(code + " ", title, flag_path, self.gb_source)
            self.src_group.addButton(row_src.radio)
            self.src_radios[code] = row_src.radio
            src_lay.addWidget(row_src)
            
            row_dst = LanguageRadioFlag(code + " ", title, flag_path, self.gb_dest)
            self.dst_group.addButton(row_dst.radio)
            self.dst_radios[code] = row_dst.radio
            dst_lay.addWidget(row_dst)
        
        lang_row.addWidget(self.gb_source)
        lang_row.addWidget(self.gb_dest)
        
        #lang_lay.addLayout(lang_row)
        #lang_lay.addStretch(1)
        
        lang_scroll = QScrollArea(lang_tab)
        
        lang_scroll.setWidgetResizable(True)
        lang_scroll.setFrameShape(QFrame.NoFrame)
        
        lang_scroll.setVerticalScrollBarPolicy  (Qt.ScrollBarAsNeeded )
        lang_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded )
        lang_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        lang_scroll_host = QWidget()
        lang_scroll_lay = QVBoxLayout(lang_scroll_host)
        lang_scroll_lay.setContentsMargins(0, 0, 0, 0)
        lang_scroll_lay.setSpacing(0)
        lang_scroll_lay.addLayout(lang_row)
        lang_scroll_lay.addStretch(1)

        lang_scroll.setWidget(lang_scroll_host)

        lang_lay.addWidget(lang_scroll, 1)

        self.msgid_list = QListWidget(msgstr_tab)
        self.msgid_list.setMinimumWidth(240)
        
        msgstr_lay.addWidget(self.msgid_list, 1)

        right_tabs.addTab(msgstr_tab, "MSGSTR")
        right_tabs.addTab(lang_tab, share.locales.tr("Language"))

        editor_col = QVBoxLayout()
        editor_hor = QHBoxLayout()
        
        editor_col.setSpacing(6)
        editor_col.addWidget(QLabel("MSGID:", content))
        
        self.btn_insert = QPushButton(share.locales.tr("Insert"), content)
        self.btn_apply  = QPushButton(share.locales.tr("Apply" ), content)
        self.btn_delete = QPushButton(share.locales.tr("Delete"), content)
        
        self.btn_insert.clicked.connect(self._insert_entry)
        self.btn_apply .clicked.connect(self._apply_entry)
        self.btn_delete.clicked.connect(self._delete_selected_entry)
        
        self.btn_create = QPushButton(share.locales.tr("Create"), content)
        self.btn_cancel = QPushButton(share.locales.tr("Cancel"), content)
        
        self.btn_create.clicked.connect(self._create_mo_file)
        self.btn_cancel.clicked.connect(self._close_self)
        
        editor_hor.addWidget(self.btn_insert)
        editor_hor.addWidget(self.btn_apply)
        editor_hor.addWidget(self.btn_delete)
        
        editor_col.addLayout(editor_hor)
        
        self.ed_msgid = QLineEdit(content)
        self.ed_msgid.setFont(QFont("Arial", 10))
        
        editor_col.addWidget(self.ed_msgid)
        editor_col.addWidget(QLabel("MSGSTR:", content))
        
        self.text_msgstr = LocalizeCodeEditor(content)
        self.text_msgstr.setMinimumSize(350, 260)
        editor_col.addWidget(self.text_msgstr, 1)
        editor_col.addStretch()
        
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)
        
        self.ws1 = QWidget()
        self.ws1.setMinimumHeight(20)
        
        #self.btn_insert       = QPushButton(share.locales.tr("Insert")        , content)
        #self.btn_apply        = QPushButton(share.locales.tr("Apply")         , content)
        #self.btn_delete_msgid = QPushButton(share.locales.tr("Delete MSGID")  , content)
        #
        self.btn_open_po      = QPushButton(share.locales.tr("Open")          , content)
        #
        self.btn_save_po      = QPushButton(share.locales.tr("Save")          , content)
        self.btn_save_as_po   = QPushButton(share.locales.tr("Save As ...")   , content)
        #
        self.btn_paste        = QPushButton(share.locales.tr("Paste")         , content)
        self.btn_cut          = QPushButton(share.locales.tr("Cut")           , content)
        self.btn_delete_text  = QPushButton(share.locales.tr("Delete")        , content)

        for b in (
            #self.btn_insert,
            #self.btn_apply,
            #self.btn_delete_msgid,
            #
            self.btn_open_po,
            #
            self.btn_save_po,
            self.btn_save_as_po,
            #
            self.btn_paste,
            self.btn_cut,
            self.btn_delete_text,
            #
            self.btn_create,
            self.btn_cancel,
        ):
            b.setMinimumWidth(110)
        
        btn_col.addWidget(self.ws1)
        #btn_col.addWidget(self.btn_insert)
        #btn_col.addWidget(self.btn_apply)
        #btn_col.addWidget(self.btn_delete_msgid)
        btn_col.addSpacing(2)
        
        btn_col.addWidget(self.btn_open_po)
        btn_col.addWidget(self.btn_save_po)
        btn_col.addWidget(self.btn_save_as_po)
        btn_col.addSpacing(2)
        
        btn_col.addWidget(self.btn_paste)
        btn_col.addWidget(self.btn_cut)
        btn_col.addWidget(self.btn_delete_text)
        btn_col.addSpacing(2)

        btn_col.addStretch(1)
        
        btn_col.addWidget(self.btn_create)
        btn_col.addWidget(self.btn_cancel)

        center_right_splitter = QSplitter(Qt.Horizontal, content)

        editor_host = QWidget(center_right_splitter)
        editor_host.setLayout(editor_col)

        center_right_splitter.addWidget(editor_host)
        center_right_splitter.addWidget(right_tabs)
        center_right_splitter.setStretchFactor(0, 1)
        center_right_splitter.setStretchFactor(1, 0)

        outer.addLayout(btn_col, 0)
        outer.addWidget(center_right_splitter, 1)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(content)
        
        self.msgid_list         .currentRowChanged.connect(self._on_msgid_selection_changed)
        
        self.src_group          .buttonClicked.connect(self._sync_language_buttons)
        self.dst_group          .buttonClicked.connect(self._sync_language_buttons)
        
        self.btn_save_po        .clicked.connect(self._save_po)
        self.btn_save_as_po     .clicked.connect(self._save_po_as)
        
        self.btn_open_po.clicked.connect(self._choose_and_open_po)
        self.btn_paste.clicked  .connect(self._paste_into_focused)
        self.btn_cut.clicked    .connect(self._cut_from_focused)
        
        self.btn_delete_text    .clicked.connect(self._delete_in_focused)
        #self.btn_delete_msgid   .clicked.connect(self._delete_selected_entry)
        
        #self.btn_insert.clicked .connect(self._insert_entry)
        #self.btn_apply.clicked  .connect(self._apply_entry)
        
        return scroll

    def _build_settings_tab(self):
        content = QWidget()
        lay = QGridLayout(content)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setHorizontalSpacing(8)
        lay.setVerticalSpacing(8)

        row = 0
        lay.addWidget(QLabel("Input file (*.po):", content), row, 0)
        self.ed_po_path = QLineEdit(content)
        self.ed_po_path.setFont(QFont("Arial", 10))
        lay.addWidget(self.ed_po_path, row, 1)
        self.btn_load_po_path = QPushButton(share.locales.tr("Load"), content)
        lay.addWidget(self.btn_load_po_path, row, 2)
        row += 1

        lay.addWidget(QLabel("Output file (*.mo):", content), row, 0)
        self.ed_mo_path = QLineEdit(content)
        self.ed_mo_path.setFont(QFont("Arial", 10))
        lay.addWidget(self.ed_mo_path, row, 1)
        self.btn_load_mo_path = QPushButton(share.locales.tr("Load"), content)
        lay.addWidget(self.btn_load_mo_path, row, 2)
        row += 1

        self.header_edits = {}
        for header in self.HEADER_FIELDS:
            lay.addWidget(QLabel(header + ":", content), row, 0)
            ed = QLineEdit(content)
            ed.setFont(QFont("Arial", 10))
            self.header_edits[header] = ed
            lay.addWidget(ed, row, 1, 1, 2)
            row += 1

        lay.setColumnStretch(1, 1)
        lay.setRowStretch(row, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(content)

        self.btn_load_po_path.clicked.connect(self._choose_and_open_po)
        self.btn_load_mo_path.clicked.connect(self._choose_mo_path)
        try:
            self.header_edits['Language'].editingFinished.connect(self._apply_language_from_header)
        except Exception:
            pass
        return scroll

    def _focused_text_widget(self):
        fw = QApplication.focusWidget()
        if isinstance(fw, (QLineEdit, QTextEdit, QPlainTextEdit)):
            return fw
        return self.text_msgstr

    def _paste_into_focused(self):
        w = self._focused_text_widget()
        try:
            w.paste()
        except Exception:
            pass

    def _cut_from_focused(self):
        w = self._focused_text_widget()
        try:
            w.cut()
        except Exception:
            pass

    def _delete_in_focused(self):
        w = self._focused_text_widget()
        try:
            if isinstance(w, QLineEdit):
                if w.hasSelectedText():
                    txt = w.text()
                    a = w.selectionStart()
                    b = a + len(w.selectedText())
                    w.setText(txt[:a] + txt[b:])
                    w.setCursorPosition(a)
                else:
                    w.clear()
            else:
                tc = w.textCursor()
                if tc.hasSelection():
                    tc.removeSelectedText()
                    w.setTextCursor(tc)
                else:
                    tc.select(QTextCursor.LineUnderCursor)
                    tc.removeSelectedText()
                    w.setTextCursor(tc)
        except Exception:
            pass

    def _normalize_text(self, text):
        return (text or "").replace("\r\n", "\n").replace("\r", "\n")

    def _escape_po_text(self, text):
        return (text or "").replace('\\', '\\\\').replace('"', '\\"').replace('\t', '\\t')

    def _serialize_po_lines(self, text):
        text = self._normalize_text(text)
        parts = text.split('\n')
        if parts == ['']:
            return ['""']
        out = []
        for idx, part in enumerate(parts):
            suffix = '\\n' if idx < len(parts) - 1 else ''
            out.append(f'"{self._escape_po_text(part)}{suffix}"')
        return out or ['""']

    def _language_schema_value(self):
        return f"{self._current_source_code()}:{self._current_destination_code()}"

    def _parse_language_schema(self, value):
        text = (value or '').strip().upper()
        if ':' not in text:
            return 'ENU', 'DEU'
        src, dst = [part.strip() for part in text.split(':', 1)]
        if src not in self.src_radios or dst not in self.dst_radios or src == dst:
            return 'ENU', 'DEU'
        return src, dst

    def _set_language_pair(self, src, dst):
        src, dst = self._parse_language_schema(f"{src}:{dst}")
        self._block_lang_sync = True
        try:
            if src in self.src_radios:
                self.src_radios[src].setChecked(True)
            else:
                self.src_radios['ENU'].setChecked(True)
            if dst in self.dst_radios:
                self.dst_radios[dst].setChecked(True)
            else:
                self.dst_radios['DEU'].setChecked(True)
        finally:
            self._block_lang_sync = False
        self._sync_language_buttons()

    def _apply_language_from_header(self):
        value = self.header_edits.get('Language', QLineEdit()).text().strip()
        src, dst = self._parse_language_schema(value)
        self._set_language_pair(src, dst)

    def _metadata(self):
        data = {}
        for key, ed in self.header_edits.items():
            data[key] = (ed.text() or "").strip()
        data["Language"] = self._language_schema_value()
        return data

    def _serialize_po_content(self):
        meta = self._metadata()
        lines = []
        lines.append('msgid ""')
        lines.append('msgstr ""')
        for key in self.HEADER_FIELDS:
            value = meta.get(key, "")
            value = f"{key}: {value}" if value else f"{key}:"
            lines.append(f'"{self._escape_po_text(value)}\\n"')
        lines.append("")
        for entry in self.entries:
            msgid = self._normalize_text(entry.get('msgid', ''))
            msgstr = self._normalize_text(entry.get('msgstr', ''))
            lines.append('msgid ""')
            lines.extend(self._serialize_po_lines(msgid))
            lines.append('msgstr ""')
            lines.extend(self._serialize_po_lines(msgstr))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _find_entry_index(self, msgid):
        msgid = self._normalize_text(msgid)
        for idx, entry in enumerate(self.entries):
            if self._normalize_text(entry.get('msgid', '')) == msgid:
                return idx
        return -1

    def _duplicate_msgids(self):
        counts = {}
        for entry in self.entries:
            msgid = self._normalize_text(entry.get('msgid', ''))
            counts[msgid] = counts.get(msgid, 0) + 1
        return {msgid for msgid, count in counts.items() if msgid and count > 1}

    def _refresh_msgid_list(self, select_index=None):
        self.msgid_list.blockSignals(True)
        self.msgid_list.clear()
        duplicate_ids = self._duplicate_msgids()
        for entry in self.entries:
            raw_msgid = self._normalize_text(entry.get('msgid', ''))
            title = raw_msgid.replace('\n', ' ⏎ ')
            item = QListWidgetItem(title)
            if raw_msgid in duplicate_ids:
                item.setBackground(QColor('#b00000'))
                item.setForeground(QColor('#ffffff'))
            self.msgid_list.addItem(item)
        self.msgid_list.blockSignals(False)
        if self.entries:
            if select_index is None:
                select_index = 0 if self._current_index < 0 else min(self._current_index, len(self.entries) - 1)
            self.msgid_list.setCurrentRow(max(0, min(select_index, len(self.entries) - 1)))
        else:
            self._current_index = -1
            self.ed_msgid.clear()
            self.text_msgstr.clear()

    def _on_msgid_selection_changed(self, row):
        if row < 0 or row >= len(self.entries):
            self._current_index = -1
            return
        self._current_index = row
        entry = self.entries[row]
        self.ed_msgid.setText(self._normalize_text(entry.get('msgid', '')))
        self.text_msgstr.setPlainText(self._normalize_text(entry.get('msgstr', '')))

    def _insert_entry(self):
        msgid = self._normalize_text(self.ed_msgid.text())
        msgstr = self._normalize_text(self.text_msgstr.toPlainText())
        if not msgid:
            QMessageBox.warning(self, 'Localize', 'Bitte zuerst eine MSGID eingeben.')
            self.ed_msgid.setFocus()
            return
        idx = self._find_entry_index(msgid)
        if idx >= 0:
            self.entries[idx]['msgstr'] = msgstr
            self._current_index = idx
        else:
            self.entries.append({'msgid': msgid, 'msgstr': msgstr})
            self._current_index = len(self.entries) - 1
        self._refresh_msgid_list(select_index=self._current_index)

    def _apply_entry(self):
        if self._current_index < 0 or self._current_index >= len(self.entries):
            self._insert_entry()
            return
        msgid = self._normalize_text(self.ed_msgid.text())
        msgstr = self._normalize_text(self.text_msgstr.toPlainText())
        if not msgid:
            QMessageBox.warning(self, 'Localize', 'Bitte zuerst eine MSGID eingeben.')
            return
        old_msgid = self._normalize_text(self.entries[self._current_index].get('msgid', ''))
        other = self._find_entry_index(msgid)
        if other >= 0 and other != self._current_index and msgid != old_msgid:
            QMessageBox.warning(self, 'Localize', 'Die MSGID existiert bereits.')
            return
        self.entries[self._current_index] = {'msgid': msgid, 'msgstr': msgstr}
        self._refresh_msgid_list(select_index=self._current_index)

    def _delete_selected_entry(self):
        row = self.msgid_list.currentRow()
        if row < 0 or row >= len(self.entries):
            return
        del self.entries[row]
        self._current_index = -1
        self._refresh_msgid_list(select_index=min(row, len(self.entries) - 1))

    def _choose_and_open_po(self):
        start = self.ed_po_path.text().strip() or os.getcwd()
        title = share.locales.tr("Load PO-File")
        exten = share.locales.tr("PO-Files (*.po);;All Files (*.*)")
        path, _ = QFileDialog.getOpenFileName(self, title, start, exten)
        path = (path or '').strip()
        if not path:
            return
        
        base, ext = os.path.splitext(path)
        po_file   = base + ".po"
        mo_file   = base + ".mo"
        
        self.ed_po_path.setText(po_file)
        self.ed_mo_path.setText(mo_file)
        
        self._open_po(po_file)

    def _choose_mo_path(self):
        start = self.ed_mo_path.text().strip() or os.getcwd()
        title = share.locales.tr("Select MO-File")
        exten = share.locales.tr("MO-Files (*.mo);;All Files (*.*)")
        path, _ = QFileDialog.getSaveFileName(self, title, start, exten)
        path = (path or '').strip()
        if not path:
            return
        self.ed_mo_path.setText(path)

    def _open_po(self, path):
        path = os.path.normpath((path or '').strip())
        if not path:
            return
        try:
            import polib
        except Exception as e:
            title = share.locales.tr("Localize")
            error = share.locales.tr("polib could not be open")
            QMessageBox.warning(self, title, f'{error}:\n{e}')
            return
        try:
            po = polib.pofile(path)
            self.entries = []
            for entry in po:
                if getattr(entry, 'obsolete', False):
                    continue
                self.entries.append({'msgid': self._normalize_text(entry.msgid), 'msgstr': self._normalize_text(entry.msgstr)})
            for key in self.HEADER_FIELDS:
                self.header_edits[key].setText(po.metadata.get(key, ''))
            schema = (self.header_edits.get('Language', QLineEdit()).text() or '').strip()
            src, dst = self._parse_language_schema(schema)
            self._set_language_pair(src, dst)
            self.header_edits['Language'].setText(self._language_schema_value())
            self._refresh_msgid_list(select_index=0)
            self._save_state()
        except Exception as e:
            QMessageBox.warning(self, 'Localize', f'PO-Datei konnte nicht geladen werden:\n{e}')

    def _sort_entries_by_msgid(self):
        current_msgid = self._normalize_text(self.ed_msgid.text())
        self.entries.sort(key=lambda entry: self._normalize_text(entry.get('msgid', '')))
        select_index = None
        if current_msgid:
            idx = self._find_entry_index(current_msgid)
            if idx >= 0:
                select_index = idx
        self._refresh_msgid_list(select_index=select_index)

    def _write_po_file(self, path):
        path = os.path.normpath((path or '').strip())
        if not path:
            raise ValueError('Kein Dateiname für die Eingabedatei (*.po) angegeben.')
        self._sort_entries_by_msgid()
        folder = os.path.dirname(path) or os.getcwd()
        os.makedirs(folder, exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(self._serialize_po_content())
        self.ed_po_path.setText(path)
        self._save_state()

    def _save_po(self):
        path = self.ed_po_path.text().strip()
        if not path:
            return self._save_po_as()
        try:
            self._write_po_file(path)
            QMessageBox.information(self,
            share.locales.tr("Locales"),
            share.locales.tr("PO-Datei was saved."))
        except Exception as e:
            msg = share.locales.tr("PO-File could not be saved")
            QMessageBox.warning(self, share.locales.tr("Localies"), f"{msg}:\n{e}")

    def _save_po_as(self):
        start = self.ed_po_path.text().strip() or os.path.join(os.getcwd(), 'messages.po')
        path, _ = QFileDialog.getSaveFileName(self,
            share.locales.tr('Save PO-File'),
            start,
            'PO Dateien (*.po);;Alle Dateien (*.*)')
        path = (path or '').strip()
        if not path:
            return
        try:
            self._write_po_file(path)
            QMessageBox.information(self,
            share.locales.tr("Locales"),
            share.locales.tr("PO-File successfull created."))
        except Exception as e:
            msg = share.locales.tr("PO-File could not be saved")
            QMessageBox.warning(self, share.locales.tr("Locales"), f"{msg}:\n{e}")

    def _ensure_output_writable(self, path):
        folder = os.path.dirname(path) or os.getcwd()
        os.makedirs(folder, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix='localize_', suffix='.tmp', dir=folder)
        os.close(fd)
        os.remove(tmp_path)

    def _create_mo_file(self):
        po_path = self.ed_po_path.text().strip()
        mo_path = self.ed_mo_path.text().strip()
        if not po_path:
            QMessageBox.warning(self,
            share.locales.tr('Locales'),
            share.locales.tr("Firstly, select an input file (*.po)"))
            self.tabs.setCurrentIndex(1)
            self.ed_po_path.setFocus()
            return
        if not mo_path:
            QMessageBox.warning(self,
            share.locales.tr('Locales'),
            share.locales.tr("Please select an output file (*.mo)"))
            self.tabs.setCurrentIndex(1)
            self.ed_mo_path.setFocus()
            return
        try:
            self._write_po_file(po_path)
            self._ensure_output_writable(mo_path)
            import polib
            po = polib.pofile(po_path)
            po.save_as_mofile(mo_path)
            QMessageBox.information(self,
            share.locales.tr('Locales'),
            share.locales.tr('MO-File was created.'))
        except Exception as e:
            msg = share.locales.tr("MO-File could not be created")
            QMessageBox.warning(self, share.locales.tr("Locales"), f'{msg}:\n{e}')

    def _show_help(self):
        try:
            help_mw = share.utildef.helpwin.HelpMainWindow()
            open_helpwindow(self.main_window.mdi, help_mw)
        except Exception:
            QMessageBox.information(self,
                share.locales.tr('Help'),
                share.loclaes.tr("No Help Found."))

    def _close_self(self):
        try:
            self._save_state()
        except Exception:
            pass
        try:
            host = self.parent()
            if isinstance(host, QMdiSubWindow):
                host.close()
                return
        except Exception:
            pass
        try:
            self.close()
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle(share.locales.tr("Close Locales Window"))
            box.setText(share.locales.tr("Do you want to close the Locales window?"))
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.setDefaultButton(QMessageBox.No)
            box.setEscapeButton (QMessageBox.No)
            
            result = box.exec_()
            
            if result == QMessageBox.No:
                event.ignore()
                return
            
            event.accept()
            self._save_state()
        
        except Exception as e:
            print(e)

    def _current_source_code(self):
        for code, rb in self.src_radios.items():
            if rb.isChecked():
                return code
        return 'ENU'

    def _current_destination_code(self):
        for code, rb in self.dst_radios.items():
            if rb.isChecked():
                return code
        return 'DEU'

    def _sync_language_buttons(self):
        if self._block_lang_sync:
            return
        self._block_lang_sync = True
        try:
            src = self._current_source_code()
            dst = self._current_destination_code()
            for code, rb in self.src_radios.items():
                rb.setEnabled(code != dst)
            for code, rb in self.dst_radios.items():
                rb.setEnabled(code != src)
            if src == dst:
                src, dst = self._parse_language_schema('ENU:DEU')
                if src in self.src_radios:
                    self.src_radios[src].setChecked(True)
                if dst in self.dst_radios:
                    self.dst_radios[dst].setChecked(True)
                for code, rb in self.src_radios.items():
                    rb.setEnabled(code != dst)
                for code, rb in self.dst_radios.items():
                    rb.setEnabled(code != src)
            self.header_edits.get('Language', QLineEdit()).setText(self._language_schema_value())
        finally:
            self._block_lang_sync = False

    def _apply_default_headers(self):
        now = QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mmZ')
        defaults = {
            'Project-Id-Version': '1.0',
            'Report-Msgid-Bugs-To': '',
            'POT-Creation-Date': now,
            'PO-Revision-Date': now,
            'Last-Translator': '',
            'Language-Team': '',
            'Language': self._language_schema_value(),
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=UTF-8',
            'Content-Transfer-Encoding': '8bit',
        }
        for key, value in defaults.items():
            if not self.header_edits[key].text().strip():
                self.header_edits[key].setText(value)

    def _load_state(self):
        try:
            schema = (self.main_window._settings.value('localize/header/Language', '', type=str) or '').strip()
            if not schema:
                src_saved = (self.main_window._settings.value('localize/source_lang', 'ENU', type=str) or 'ENU').strip()
                dst_saved = (self.main_window._settings.value('localize/dest_lang', 'DEU', type=str) or 'DEU').strip()
                schema = f"{src_saved}:{dst_saved}"
            src, dst = self._parse_language_schema(schema)
            self._set_language_pair(src, dst)
            self.ed_po_path.setText((self.main_window._settings.value('localize/po_path', '', type=str) or '').strip())
            self.ed_mo_path.setText((self.main_window._settings.value('localize/mo_path', '', type=str) or '').strip())
            for key in self.HEADER_FIELDS:
                self.header_edits[key].setText((self.main_window._settings.value(f'localize/header/{key}', '', type=str) or '').strip())
            self.header_edits['Language'].setText(self._language_schema_value())
        except Exception:
            try:
                self._set_language_pair('ENU', 'DEU')
                self.header_edits['Language'].setText(self._language_schema_value())
            except Exception:
                pass

    def _save_state(self):
        try:
            self.header_edits['Language'].setText(self._language_schema_value())
            self.main_window._settings.setValue('localize/source_lang'  , self._current_source_code())
            self.main_window._settings.setValue('localize/dest_lang'    , self._current_destination_code())
            self.main_window._settings.setValue('localize/po_path'      , self.ed_po_path.text().strip())
            self.main_window._settings.setValue('localize/mo_path'      , self.ed_mo_path.text().strip())
            for key in self.HEADER_FIELDS:
                self.main_window._settings.setValue(f'localize/header/{key}', self.header_edits[key].text().strip())
        except Exception:
            pass
