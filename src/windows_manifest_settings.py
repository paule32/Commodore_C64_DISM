"""Stage 149: PyQt5 manifest editor used by both Windows project profiles."""
from pathlib import Path

from PyQt5.QtCore import Qt, QRegularExpression, pyqtSignal
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
    QPushButton, QFileDialog, QMessageBox,
)
from windows_manifest import (
    IDENTITY_DEFAULTS, SUPPORTED_OS, GUID_PATTERN,
    normalize_manifest_settings, manifest_xml,
)


class WindowsManifestSettingsPage(QScrollArea):
    settingsChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._syncing = False
        self._data = normalize_manifest_settings()
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        body = QWidget(self)
        self.setWidget(body)
        layout = QVBoxLayout(body)

        self.identity_group = QGroupBox("Identity Attribute", body)
        form = QFormLayout(self.identity_group)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.identity_edits = {}
        labels = {"type": "Type", "name": "Name", "language": "Language",
                  "processorArchitecture": "processorArchitektur", "version": "Version",
                  "publicKeyToken": "publicKeyToken"}
        for key, default in IDENTITY_DEFAULTS.items():
            edit = QLineEdit(default, self.identity_group)
            edit.setObjectName("manifest_" + key)
            self.identity_edits[key] = edit
            form.addRow(labels[key], edit)
            edit.textChanged.connect(self._identity_changed)
        self.identity_edits["type"].setValidator(QRegularExpressionValidator(QRegularExpression("[a-z0-9]*"), self))
        self.identity_edits["type"].setToolTip("Nur Kleinbuchstaben und Ziffern; Windows-Manifeste verwenden win32.")
        self.identity_edits["version"].setPlaceholderText("mmmmm.nnnnn.ooooo.ppppp")
        self.identity_edits["version"].setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]{1,5}(\.[0-9]{1,5}){3}"), self))
        self.identity_edits["version"].setToolTip("Vier Zahlen von 0 bis 65535, getrennt durch Punkte.")
        self.identity_edits["publicKeyToken"].setValidator(QRegularExpressionValidator(QRegularExpression("[0-9a-fA-F]{0,16}"), self))
        self.identity_edits["language"].setToolTip("* = sprachneutral; beim Export der Anwendungsidentität wird language dann weggelassen.")
        self.identity_edits["name"].setPlaceholderText("MyOrganization.MyDivision.MySampleApp")
        layout.addWidget(self.identity_group)

        self.compatibility_group = QGroupBox("Kompatibel mit:", body)
        compatibility_layout = QHBoxLayout(self.compatibility_group)
        self.os_list = QListWidget(self.compatibility_group)
        self.os_list.setObjectName("manifest_supported_os")
        self.os_list.setMinimumHeight(170)
        for name, _ in SUPPORTED_OS:
            item = QListWidgetItem(name, self.os_list)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
        compatibility_layout.addWidget(self.os_list, 1)
        id_layout = QVBoxLayout()
        id_layout.addWidget(QLabel("Id (supportedOS)", self.compatibility_group))
        self.os_id_edit = QLineEdit(self.compatibility_group)
        self.os_id_edit.setObjectName("manifest_supported_os_id")
        self.os_id_edit.setValidator(QRegularExpressionValidator(QRegularExpression(GUID_PATTERN + "|"), self))
        id_layout.addWidget(self.os_id_edit)
        self.os_hint = QLabel(self.compatibility_group)
        self.os_hint.setWordWrap(True)
        id_layout.addWidget(self.os_hint)
        id_layout.addStretch(1)
        compatibility_layout.addLayout(id_layout, 2)
        layout.addWidget(self.compatibility_group)

        self.general_group = QGroupBox("Allgemein:", body)
        general_layout = QVBoxLayout(self.general_group)
        general_layout.addWidget(QLabel("longPathAware", self.general_group))
        radio_layout = QHBoxLayout()
        self.long_path_group = QButtonGroup(self.general_group)
        self.long_path_true = QRadioButton("TRUE", self.general_group)
        self.long_path_false = QRadioButton("FALSE", self.general_group)
        for button in (self.long_path_true, self.long_path_false):
            self.long_path_group.addButton(button)
            radio_layout.addWidget(button)
        radio_layout.addStretch(1)
        general_layout.addLayout(radio_layout)
        self.long_path_true.setChecked(True)
        layout.addWidget(self.general_group)
        self.export_button = QPushButton("Manifest speichern …", body)
        self.export_button.setToolTip("Als XML-Datei exportieren, z. B. MeineAnwendung.exe.manifest")
        layout.addWidget(self.export_button, 0, Qt.AlignLeft)
        layout.addStretch(1)

        self.os_list.currentItemChanged.connect(self._os_selected)
        self.os_list.itemChanged.connect(self._os_checked)
        self.os_id_edit.textChanged.connect(self._id_changed)
        self.long_path_true.toggled.connect(self._long_path_changed)
        self.export_button.clicked.connect(self._export)
        self.os_list.setCurrentRow(1)

    def settings(self):
        return normalize_manifest_settings(self._data)

    def set_settings(self, value):
        self._syncing = True
        try:
            self._data = normalize_manifest_settings(value)
            for key, edit in self.identity_edits.items():
                edit.setText(self._data["identity"][key])
            for row in range(self.os_list.count()):
                item = self.os_list.item(row)
                item.setCheckState(Qt.Checked if self._data["compatibility"][item.text()]["checked"] else Qt.Unchecked)
            self.long_path_true.setChecked(self._data["longPathAware"])
            self.long_path_false.setChecked(not self._data["longPathAware"])
            self._os_selected(self.os_list.currentItem(), None)
        finally:
            self._syncing = False

    def _notify(self):
        if not self._syncing:
            self.settingsChanged.emit(self.settings())

    def _identity_changed(self, _text):
        if not self._syncing:
            self._data["identity"] = {key: edit.text() for key, edit in self.identity_edits.items()}
            self._notify()

    def _os_selected(self, current, _previous):
        blocked = self.os_id_edit.blockSignals(True)
        try:
            name = current.text() if current else ""
            self.os_id_edit.setText(self._data["compatibility"].get(name, {}).get("id", ""))
            self.os_id_edit.setEnabled(bool(current) and name != "Windows XP")
            if name == "Windows XP":
                hint = "Windows XP verwendet kein supportedOS-Element. Die Auswahl wird nur im Projekt gespeichert."
            elif name == "Windows 12":
                hint = "Keine ID in der Microsoft-Dokumentation. Für den XML-Export ist bei aktivierter Auswahl eine gültige ID erforderlich."
            elif name in {"Windows 10", "Windows 11"}:
                hint = "Windows 10 und 11 verwenden dieselbe ID. Im XML erscheint eine gemeinsame ID nur einmal."
            else:
                hint = "Die ID gehört zur ausgewählten Windows-Version. Das Häkchen bestimmt die Aufnahme ins Manifest."
            self.os_hint.setText(hint)
        finally:
            self.os_id_edit.blockSignals(blocked)

    def _os_checked(self, item):
        if not self._syncing:
            self._data["compatibility"][item.text()]["checked"] = item.checkState() == Qt.Checked
            self._notify()

    def _id_changed(self, text):
        item = self.os_list.currentItem()
        if not self._syncing and item:
            self._data["compatibility"][item.text()]["id"] = text
            self._notify()

    def _long_path_changed(self, checked):
        if not self._syncing:
            self._data["longPathAware"] = bool(checked)
            self._notify()

    def _export(self):
        try:
            xml = manifest_xml(self.settings())
        except ValueError as exc:
            QMessageBox.warning(self, "Manifest", str(exc))
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Manifest speichern", "Anwendung.exe.manifest", "Manifest-Dateien (*.manifest);;XML-Dateien (*.xml)")
        if not filename:
            return
        try:
            Path(filename).write_text(xml, encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Manifest speichern", str(exc))
