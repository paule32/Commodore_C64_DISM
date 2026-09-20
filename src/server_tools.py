# -*- coding: utf-8 -*-
"""Stage 155 - Native Windows server administration docks.

The panels deliberately keep the external server products separated:
- BIND9: DNS / DynDNS configuration and named/rndc/nsupdate invocation.
- OpenSSL: development CA / certificate administration surface.
- Apache: httpd configuration and Windows-service control.

The module does not bundle third-party binaries. Paths are project/user configurable
and persisted through the application's QSettings object.
"""
from __future__ import annotations

import os
import json
import base64
import ctypes
import subprocess
import time
import urllib.request
import urllib.parse
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtCore import QProcess, QSettings, QSize, QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QInputDialog,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)






# Stage 161: downloadable Windows OpenSSL versions for the Installation tab.
# OpenSSL itself publishes source archives; these Windows installers are the
# commonly used Shining Light Productions builds linked from its OpenSSL page.
OPENSSL_INSTALLER_DOWNLOADS = [
    ("OpenSSL 4.0.2 - Win64 Light", "https://slproweb.com/download/Win64OpenSSL_Light-4_0_2.exe"),
    ("OpenSSL 4.0.2 - Win32 Light", "https://slproweb.com/download/Win32OpenSSL_Light-4_0_2.exe"),
    ("OpenSSL 3.6.4 - Win64 Light", "https://slproweb.com/download/Win64OpenSSL_Light-3_6_4.exe"),
    ("OpenSSL 3.6.4 - Win32 Light", "https://slproweb.com/download/Win32OpenSSL_Light-3_6_4.exe"),
    ("OpenSSL 3.5.8 LTS - Win64 Light", "https://slproweb.com/download/Win64OpenSSL_Light-3_5_8.exe"),
    ("OpenSSL 3.5.8 LTS - Win32 Light", "https://slproweb.com/download/Win32OpenSSL_Light-3_5_8.exe"),
    ("OpenSSL 3.4.7 - Win64 Light", "https://slproweb.com/download/Win64OpenSSL_Light-3_4_7.exe"),
    ("OpenSSL 3.4.7 - Win32 Light", "https://slproweb.com/download/Win32OpenSSL_Light-3_4_7.exe"),
]

# Stage 176: Windows Apache HTTP Server packages are mirrored on the
# user-controlled kallup.net download server.  This avoids download pages that
# require cookie/browser interaction before the actual archive can be fetched.
# Keep all concrete package URLs derived from one base address so a future
# mirror move only needs one change.
APACHE_DOWNLOAD_BASE_URL = "https://kallup.net/downloads/apache/"
APACHE_INSTALLER_DOWNLOADS = [
    (
        "Apache HTTP Server 2.4.68 - Win64 VS18",
        APACHE_DOWNLOAD_BASE_URL + "httpd-2.4.68-260920-Win64-VS18.zip",
    ),
    (
        "Apache HTTP Server 2.4.68 - Win32 VS18",
        APACHE_DOWNLOAD_BASE_URL + "httpd-2.4.68-260617-win32-vs18.zip",
    ),
]

# ISO-3166-1 Alpha-2 country codes used by X.509/OpenSSL C=.
# The display names are deliberately German because the surrounding UI is German.
CA_COUNTRY_CODES = [
    ("AT", "Österreich"), ("AU", "Australien"), ("BE", "Belgien"),
    ("BR", "Brasilien"), ("CA", "Kanada"), ("CH", "Schweiz"),
    ("CN", "China"), ("CZ", "Tschechien"), ("DE", "Deutschland"),
    ("DK", "Dänemark"), ("EE", "Estland"), ("ES", "Spanien"),
    ("FI", "Finnland"), ("FR", "Frankreich"), ("GB", "Vereinigtes Königreich"),
    ("GR", "Griechenland"), ("HK", "Hongkong"), ("HR", "Kroatien"),
    ("HU", "Ungarn"), ("IE", "Irland"), ("IL", "Israel"),
    ("IN", "Indien"), ("IS", "Island"), ("IT", "Italien"),
    ("JP", "Japan"), ("KR", "Südkorea"), ("LI", "Liechtenstein"),
    ("LT", "Litauen"), ("LU", "Luxemburg"), ("LV", "Lettland"),
    ("MX", "Mexiko"), ("NL", "Niederlande"), ("NO", "Norwegen"),
    ("NZ", "Neuseeland"), ("PL", "Polen"), ("PT", "Portugal"),
    ("RO", "Rumänien"), ("SE", "Schweden"), ("SG", "Singapur"),
    ("SI", "Slowenien"), ("SK", "Slowakei"), ("TR", "Türkei"),
    ("TW", "Taiwan"), ("UA", "Ukraine"), ("US", "Vereinigte Staaten"),
    ("ZA", "Südafrika"),
]

# Country-dependent State/Province/Canton lists.  The tuple value is
# (short code, X.509 display value).  X.509 ST= receives the display value.
CA_SUBDIVISIONS = {
    "DE": [
        ("BW", "Baden-Württemberg"), ("BY", "Bayern"), ("BE", "Berlin"),
        ("BB", "Brandenburg"), ("HB", "Bremen"), ("HH", "Hamburg"),
        ("HE", "Hessen"), ("MV", "Mecklenburg-Vorpommern"),
        ("NI", "Niedersachsen"), ("NW", "Nordrhein-Westfalen"),
        ("RP", "Rheinland-Pfalz"), ("SL", "Saarland"), ("SN", "Sachsen"),
        ("ST", "Sachsen-Anhalt"), ("SH", "Schleswig-Holstein"),
        ("TH", "Thüringen"),
    ],
    "AT": [
        ("1", "Burgenland"), ("2", "Kärnten"), ("3", "Niederösterreich"),
        ("4", "Oberösterreich"), ("5", "Salzburg"), ("6", "Steiermark"),
        ("7", "Tirol"), ("8", "Vorarlberg"), ("9", "Wien"),
    ],
    "CH": [
        ("AG", "Aargau"), ("AI", "Appenzell Innerrhoden"),
        ("AR", "Appenzell Ausserrhoden"), ("BE", "Bern"),
        ("BL", "Basel-Landschaft"), ("BS", "Basel-Stadt"),
        ("FR", "Freiburg"), ("GE", "Genf"), ("GL", "Glarus"),
        ("GR", "Graubünden"), ("JU", "Jura"), ("LU", "Luzern"),
        ("NE", "Neuenburg"), ("NW", "Nidwalden"), ("OW", "Obwalden"),
        ("SG", "St. Gallen"), ("SH", "Schaffhausen"), ("SO", "Solothurn"),
        ("SZ", "Schwyz"), ("TG", "Thurgau"), ("TI", "Tessin"),
        ("UR", "Uri"), ("VD", "Waadt"), ("VS", "Wallis"),
        ("ZG", "Zug"), ("ZH", "Zürich"),
    ],
    "US": [
        ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"),
        ("CA", "California"), ("CO", "Colorado"), ("CT", "Connecticut"),
        ("DE", "Delaware"), ("DC", "District of Columbia"), ("FL", "Florida"),
        ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"), ("IL", "Illinois"),
        ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"), ("KY", "Kentucky"),
        ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"),
        ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"),
        ("MS", "Mississippi"), ("MO", "Missouri"), ("MT", "Montana"),
        ("NE", "Nebraska"), ("NV", "Nevada"), ("NH", "New Hampshire"),
        ("NJ", "New Jersey"), ("NM", "New Mexico"), ("NY", "New York"),
        ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"),
        ("OK", "Oklahoma"), ("OR", "Oregon"), ("PA", "Pennsylvania"),
        ("RI", "Rhode Island"), ("SC", "South Carolina"), ("SD", "South Dakota"),
        ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"), ("VT", "Vermont"),
        ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"),
        ("WI", "Wisconsin"), ("WY", "Wyoming"),
    ],
    "CA": [
        ("AB", "Alberta"), ("BC", "British Columbia"), ("MB", "Manitoba"),
        ("NB", "New Brunswick"), ("NL", "Newfoundland and Labrador"),
        ("NS", "Nova Scotia"), ("NT", "Northwest Territories"), ("NU", "Nunavut"),
        ("ON", "Ontario"), ("PE", "Prince Edward Island"), ("QC", "Quebec"),
        ("SK", "Saskatchewan"), ("YT", "Yukon"),
    ],
    "AU": [
        ("ACT", "Australian Capital Territory"), ("NSW", "New South Wales"),
        ("NT", "Northern Territory"), ("QLD", "Queensland"),
        ("SA", "South Australia"), ("TAS", "Tasmania"),
        ("VIC", "Victoria"), ("WA", "Western Australia"),
    ],
}

def _quote_display(value: str) -> str:
    if not value:
        return '""'
    return f'"{value}"' if any(ch.isspace() for ch in value) else value


class ServerPanelBase(QWidget):
    """Common themed process runner and persistent field helpers."""

    settings_prefix = "server/base"

    def __init__(self, host, settings: QSettings, parent=None):
        super().__init__(parent)
        self.host = host
        self.settings = settings
        self._dark_mode = bool(getattr(host, "dark_mode_enabled", True))
        self._process: Optional[QProcess] = None
        self._output = QPlainTextEdit(self)
        self._output.setReadOnly(True)
        fixed = QFont("Consolas")
        fixed.setStyleHint(QFont.Monospace)
        self._output.setFont(fixed)

    def _key(self, name: str) -> str:
        return f"{self.settings_prefix}/{name}"

    def _load_text(self, name: str, default: str = "") -> str:
        return str(self.settings.value(self._key(name), default) or default)

    def _store_text(self, name: str, value: str) -> None:
        self.settings.setValue(self._key(name), value)
        self.settings.sync()

    def _bound_line_edit(self, name: str, default: str = "") -> QLineEdit:
        edit = QLineEdit(self._load_text(name, default), self)
        edit.editingFinished.connect(
            lambda e=edit, n=name: self._store_text(n, e.text().strip())
        )
        return edit

    def _file_row(self, name: str, default: str = "", file_filter: str = "Alle Dateien (*)"):
        edit = self._bound_line_edit(name, default)
        button = QPushButton("…", self)
        button.setFixedWidth(34)
        button.clicked.connect(lambda: self._choose_file(edit, name, file_filter))
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        return row, edit

    def _directory_row(self, name: str, default: str = ""):
        edit = self._bound_line_edit(name, default)
        button = QPushButton("…", self)
        button.setFixedWidth(34)
        button.clicked.connect(lambda: self._choose_directory(edit, name))
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        return row, edit

    def _new_file_dialog(self, title: str) -> QFileDialog:
        dialog = QFileDialog(self, title)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setPalette(self.palette())
        return dialog

    def _choose_file(self, edit: QLineEdit, setting_name: str, file_filter: str) -> None:
        dialog = self._new_file_dialog("Datei auswählen")
        dialog.setNameFilter(file_filter)
        current = edit.text().strip()
        if current:
            current_path = Path(current)
            if current_path.parent.exists():
                dialog.setDirectory(str(current_path.parent))
                dialog.selectFile(current_path.name)
        if dialog.exec_() != QFileDialog.Accepted:
            return
        files = dialog.selectedFiles()
        if not files:
            return
        edit.setText(files[0])
        self._store_text(setting_name, files[0])

    def _choose_directory(self, edit: QLineEdit, setting_name: str) -> None:
        dialog = QFileDialog(self, "Verzeichnis auswählen")
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        current = edit.text().strip()
        if current and Path(current).exists():
            dialog.setDirectory(current)
        if dialog.exec_() != QFileDialog.Accepted:
            return
        files = dialog.selectedFiles()
        if not files:
            return
        edit.setText(files[0])
        self._store_text(setting_name, files[0])

    def append_output(self, text: str) -> None:
        if not text:
            return
        self._output.appendPlainText(text.rstrip())
        bar = self._output.verticalScrollBar()
        bar.setValue(bar.maximum())

    def run_program(self, program: str, arguments: list[str], cwd: str = "") -> None:
        program = str(program or "").strip()
        if not program:
            self._message("Programm fehlt", "Bitte zuerst den Programmpfad einstellen.", QMessageBox.Warning)
            return
        if self._process is not None and self._process.state() != QProcess.NotRunning:
            self._message("Prozess läuft", "Es läuft bereits ein Server-Werkzeug.", QMessageBox.Information)
            return
        self.append_output("> " + " ".join([_quote_display(program)] + [_quote_display(a) for a in arguments]))
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.MergedChannels)
        if cwd:
            proc.setWorkingDirectory(cwd)
        proc.readyReadStandardOutput.connect(lambda p=proc: self._read_process_output(p))
        proc.finished.connect(lambda code, status, p=proc: self._process_finished(p, code, status))
        proc.errorOccurred.connect(lambda error, p=proc: self._process_error(p, error))
        self._process = proc
        proc.start(program, arguments)

    def _read_process_output(self, proc: QProcess) -> None:
        data = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.append_output(data)

    def _process_finished(self, proc: QProcess, code: int, status) -> None:
        self._read_process_output(proc)
        self.append_output(f"[Exit {code}]")
        if self._process is proc:
            self._process = None
        proc.deleteLater()

    def _process_error(self, proc: QProcess, error) -> None:
        self.append_output(f"[QProcess-Fehler {int(error)}] {proc.errorString()}")

    def _message(self, title: str, text: str, icon=QMessageBox.Information) -> None:
        if hasattr(self.host, "_show_message_box"):
            self.host._show_message_box(icon, title, text)
            return
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(icon)
        box.setStandardButtons(QMessageBox.Ok)
        box.exec_()

    def set_dark_mode(self, dark: bool) -> None:
        self._dark_mode = bool(dark)
        if self._dark_mode:
            self.setStyleSheet("""
QWidget { color: #f0f0f0; background: #202020; }
QGroupBox { border: 1px solid #505050; border-radius: 4px; margin-top: 10px; padding-top: 8px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox { background: #151515; color: #f4f4f4; border: 1px solid #565656; selection-background-color: #365f85; }
QPushButton { background: #303030; color: #ffffff; border: 1px solid #595959; border-radius: 3px; padding: 5px 9px; }
QPushButton:hover { background: #3c3c3c; }
QTabWidget::pane { border: 1px solid #4b4b4b; }
QTabBar::tab { background: #292929; color: #e8e8e8; border: 1px solid #484848; padding: 6px 10px; }
QTabBar::tab:selected { background: #3a3a3a; color: #ffffff; }
QScrollArea { border: 0; }
""")
        else:
            self.setStyleSheet("""
QWidget { color: #111111; background: #f3f3f3; }
QGroupBox { border: 1px solid #b7b7b7; border-radius: 4px; margin-top: 10px; padding-top: 8px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox { background: #ffffff; color: #111111; border: 1px solid #a8a8a8; selection-background-color: #cfe6ff; }
QPushButton { background: #f7f7f7; color: #111111; border: 1px solid #a9a9a9; border-radius: 3px; padding: 5px 9px; }
QPushButton:hover { background: #e9f2fb; }
QTabWidget::pane { border: 1px solid #b7b7b7; }
QTabBar::tab { background: #e7e7e7; color: #111111; border: 1px solid #b9b9b9; padding: 6px 10px; }
QTabBar::tab:selected { background: #ffffff; }
QScrollArea { border: 0; }
""")


# Stage-155 regression markers; die genannten Seiten liegen ab Stage 157
# als Untertabs innerhalb des Haupttabs "Setup":
# tabs.addTab(dns, "DNS")
# tabs.addTab(ddns, "DynDNS")
# tabs.addTab(ca_scroll, "Client Authority CA")
# tabs.addTab(cert_page, "Zertifikate")

class Bind9ServerPanel(ServerPanelBase):
    settings_prefix = "server/bind9"

    def __init__(self, host, settings: QSettings, parent=None):
        super().__init__(host, settings, parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # Stage 157: alle Server-Werkzeuge besitzen dieselben beiden Haupttabs.
        tabs = QTabWidget(self)
        self.main_tabs = tabs
        root.addWidget(tabs, 1)

        # ---------------------------------------------------------------
        # Setup: Laufzeit-/DNS-/DynDNS-Konfiguration.
        # ---------------------------------------------------------------
        setup_page = QWidget(tabs)
        setup_layout = QVBoxLayout(setup_page)
        setup_layout.setContentsMargins(6, 6, 6, 6)

        setup_scroll = QScrollArea(setup_page)
        setup_scroll.setWidgetResizable(True)
        setup_body = QWidget(setup_scroll)
        setup_body_layout = QVBoxLayout(setup_body)

        # Die bisherigen DNS/DynDNS-Ansichten bleiben als Untergliederung
        # des neuen Haupttabs "Setup" erhalten.
        setup_sections = QTabWidget(setup_body)

        dns = QWidget(setup_sections)
        dns_layout = QVBoxLayout(dns)
        config = QGroupBox("DNS-Konfiguration", dns)
        form = QFormLayout(config)
        conf_row, self.conf_edit = self._file_row(
            "named_conf", "", "BIND Konfiguration (*.conf);;Alle Dateien (*)"
        )
        zones_row, self.zones_edit = self._directory_row("zone_dir", "")
        form.addRow("named.conf", conf_row)
        form.addRow("Zonen-Verzeichnis", zones_row)
        dns_layout.addWidget(config)

        buttons = QHBoxLayout()
        for text, callback in (
            ("Konfiguration prüfen", self._check_config),
            ("Status", self._status),
            ("Reload", self._reload),
        ):
            button = QPushButton(text, dns)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch(1)
        dns_layout.addLayout(buttons)
        dns_layout.addStretch(1)
        setup_sections.addTab(dns, "DNS")

        ddns = QWidget(setup_sections)
        ddns_layout = QVBoxLayout(ddns)
        ddns_group = QGroupBox("Dynamische DNS-Aktualisierung", ddns)
        ddns_form = QFormLayout(ddns_group)
        key_row, self.tsig_key_edit = self._file_row(
            "tsig_key", "", "TSIG Key (*.key *.private);;Alle Dateien (*)"
        )
        self.ddns_server_edit = self._bound_line_edit("ddns_server", "127.0.0.1")
        self.ddns_zone_edit = self._bound_line_edit("ddns_zone", "local")
        self.ddns_host_edit = self._bound_line_edit("ddns_host", "host.local")
        self.ddns_address_edit = self._bound_line_edit("ddns_address", "127.0.0.1")
        ddns_form.addRow("TSIG-Key", key_row)
        ddns_form.addRow("DNS-Server", self.ddns_server_edit)
        ddns_form.addRow("Zone", self.ddns_zone_edit)
        ddns_form.addRow("Hostname", self.ddns_host_edit)
        ddns_form.addRow("Adresse", self.ddns_address_edit)
        ddns_layout.addWidget(ddns_group)
        hint = QLabel(
            "Hier werden Zone, Zielhost und TSIG-Daten für spätere nsupdate-Aufrufe "
            "verwaltet. Die Programmpfade selbst liegen im Tab Installation.", ddns
        )
        hint.setWordWrap(True)
        ddns_layout.addWidget(hint)
        ddns_layout.addStretch(1)
        setup_sections.addTab(ddns, "DynDNS")

        setup_body_layout.addWidget(setup_sections, 1)
        setup_body_layout.addWidget(QLabel("Ausgabe", setup_body))
        setup_body_layout.addWidget(self._output, 1)
        setup_scroll.setWidget(setup_body)
        setup_layout.addWidget(setup_scroll, 1)
        tabs.addTab(setup_page, "Setup")

        # ---------------------------------------------------------------
        # Installation: alle BIND9-Programm-/Installationspfade.
        # ---------------------------------------------------------------
        install_scroll = QScrollArea(tabs)
        install_scroll.setWidgetResizable(True)
        install_page = QWidget(install_scroll)
        install_layout = QVBoxLayout(install_page)

        install_group = QGroupBox("BIND9 Installation", install_page)
        install_form = QFormLayout(install_group)
        install_dir_row, self.install_dir_edit = self._directory_row("install_dir", "")
        named_row, self.named_edit = self._file_row(
            "named", "named.exe", "BIND named (named.exe);;Programme (*.exe);;Alle Dateien (*)"
        )
        rndc_row, self.rndc_edit = self._file_row(
            "rndc", "rndc.exe", "BIND rndc (rndc.exe);;Programme (*.exe);;Alle Dateien (*)"
        )
        nsupdate_row, self.nsupdate_edit = self._file_row(
            "nsupdate", "nsupdate.exe", "BIND nsupdate (nsupdate.exe);;Programme (*.exe);;Alle Dateien (*)"
        )
        installer_row, self.installer_edit = self._file_row(
            "installer", "", "Installer/Archiv-Helfer (*.exe *.msi);;Alle Dateien (*)"
        )
        install_form.addRow("Installationsverzeichnis", install_dir_row)
        install_form.addRow("named.exe", named_row)
        install_form.addRow("rndc.exe", rndc_row)
        install_form.addRow("nsupdate.exe", nsupdate_row)
        install_form.addRow("Installer", installer_row)
        install_layout.addWidget(install_group)

        install_buttons = QHBoxLayout()
        auto_paths = QPushButton("Programmpfade übernehmen", install_page)
        auto_paths.clicked.connect(self._apply_install_directory)
        install_buttons.addWidget(auto_paths)
        version = QPushButton("Version prüfen", install_page)
        version.clicked.connect(self._show_version)
        install_buttons.addWidget(version)
        run_installer = QPushButton("Installer starten", install_page)
        run_installer.clicked.connect(self._run_installer)
        install_buttons.addWidget(run_installer)
        install_buttons.addStretch(1)
        install_layout.addLayout(install_buttons)

        install_hint = QLabel(
            "Der Editor bündelt hier nur Installation, Pfade und Prüfung. "
            "BIND9 selbst wird nicht mit d64_dism ausgeliefert.", install_page
        )
        install_hint.setWordWrap(True)
        install_layout.addWidget(install_hint)
        install_layout.addStretch(1)
        install_scroll.setWidget(install_page)
        tabs.addTab(install_scroll, "Installation")
        self.set_dark_mode(self._dark_mode)

    def _store_path_edit(self, name: str, edit: QLineEdit, value: Path) -> None:
        text = str(value)
        edit.setText(text)
        self._store_text(name, text)

    def _apply_install_directory(self):
        base_text = self.install_dir_edit.text().strip()
        if not base_text:
            self._message("BIND9 Installation", "Bitte zuerst ein Installationsverzeichnis auswählen.", QMessageBox.Warning)
            return
        base = Path(base_text)
        binary_dir = base / "bin"
        if not binary_dir.exists():
            binary_dir = base
        self._store_path_edit("named", self.named_edit, binary_dir / "named.exe")
        self._store_path_edit("rndc", self.rndc_edit, binary_dir / "rndc.exe")
        self._store_path_edit("nsupdate", self.nsupdate_edit, binary_dir / "nsupdate.exe")
        self.append_output(f"BIND9 Programmpfade übernommen: {binary_dir}")

    def _run_installer(self):
        installer = self.installer_edit.text().strip()
        if not installer:
            self._message("BIND9 Installation", "Bitte zuerst einen Installer auswählen.", QMessageBox.Warning)
            return
        self.run_program(installer, [])

    def _show_version(self):
        self.run_program(self.named_edit.text(), ["-v"])

    def _check_config(self):
        named = self.named_edit.text().strip()
        check = str(Path(named).with_name("named-checkconf.exe")) if named else "named-checkconf.exe"
        args = [self.conf_edit.text().strip()] if self.conf_edit.text().strip() else []
        self.run_program(check, args)

    def _status(self):
        self.run_program(self.rndc_edit.text(), ["status"])

    def _reload(self):
        self.run_program(self.rndc_edit.text(), ["reload"])




class OpenSSLDownloadThread(QThread):
    """Download one selected OpenSSL package without blocking the Qt GUI."""

    completed = pyqtSignal(bool, str, bool, str)

    def __init__(self, url: str, target_dir: str, parent=None):
        super().__init__(parent)
        self.url = str(url)
        self.target_dir = str(target_dir)

    @staticmethod
    def _safe_extract_zip(archive: Path, target_dir: Path) -> None:
        target_root = target_dir.resolve()
        with zipfile.ZipFile(str(archive), "r") as zf:
            for member in zf.infolist():
                member_path = (target_dir / member.filename).resolve()
                try:
                    member_path.relative_to(target_root)
                except ValueError as exc:
                    raise RuntimeError("Unsicherer Pfad im ZIP-Archiv: " + member.filename) from exc
            zf.extractall(str(target_dir))

    def run(self):
        try:
            target_dir = Path(self.target_dir).expanduser()
            target_dir.mkdir(parents=True, exist_ok=True)

            request = urllib.request.Request(
                self.url,
                headers={
                    "User-Agent": "d64_dism OpenSSL Downloader/1.0",
                    "Accept": "*/*",
                },
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                final_url = response.geturl() or self.url
                filename = Path(urllib.parse.urlparse(final_url).path).name
                if not filename:
                    filename = "openssl-download.bin"
                destination = target_dir / filename
                partial = target_dir / (filename + ".part")
                with open(partial, "wb") as out:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        out.write(chunk)
                os.replace(str(partial), str(destination))

            extracted = zipfile.is_zipfile(str(destination))
            if extracted:
                self._safe_extract_zip(destination, target_dir)

            self.completed.emit(True, str(destination), extracted, "")
        except Exception as exc:
            self.completed.emit(False, "", False, str(exc))


class OpenSSLServerPanel(ServerPanelBase):
    settings_prefix = "server/openssl"

    def __init__(self, host, settings: QSettings, parent=None):
        super().__init__(host, settings, parent)
        self._ca_session_passwords: dict[str, str] = {}
        self._openssl_download_thread = None
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        tabs = QTabWidget(self)
        self.main_tabs = tabs
        root.addWidget(tabs, 1)

        # ---------------------------------------------------------------
        # Setup: CA und Zertifikate. Programminstallation steht getrennt.
        # ---------------------------------------------------------------
        setup_page = QWidget(tabs)
        setup_layout = QVBoxLayout(setup_page)
        setup_layout.setContentsMargins(6, 6, 6, 6)

        setup_sections = QTabWidget(setup_page)
        setup_layout.addWidget(setup_sections, 1)

        ca_scroll = QScrollArea(setup_sections)
        ca_scroll.setWidgetResizable(True)
        ca_page = QWidget(ca_scroll)
        ca_layout = QVBoxLayout(ca_page)

        # Stage 168: CA editors are managed as tabs.  The management toolbar
        # deliberately sits above the tabs so New/Import/Delete always act on
        # the CA editor area rather than on a separate summary widget.
        ca_toolbar = QWidget(ca_page)
        ca_toolbar_layout = QHBoxLayout(ca_toolbar)
        ca_toolbar_layout.setContentsMargins(0, 0, 0, 0)
        ca_toolbar_layout.setSpacing(6)

        self.ca_new_button = QPushButton("Neue CA anlegen", ca_toolbar)
        self.ca_new_button.setObjectName("opensslCaNewButton")
        self.ca_import_button = QPushButton("CA importieren", ca_toolbar)
        self.ca_import_button.setObjectName("opensslCaImportButton")
        self.ca_delete_button = QPushButton("CA löschen", ca_toolbar)
        self.ca_delete_button.setObjectName("opensslCaDeleteButton")
        self.ca_lock_button = QPushButton("Sperren", ca_toolbar)
        self.ca_export_button = QPushButton("Exportieren", ca_toolbar)

        self.ca_new_button.clicked.connect(self._new_ca_tab)
        self.ca_import_button.clicked.connect(self._import_ca)
        self.ca_delete_button.clicked.connect(self._delete_selected_ca)
        self.ca_lock_button.clicked.connect(self._lock_selected_ca)
        self.ca_export_button.clicked.connect(self._export_selected_ca)

        for button in (
            self.ca_new_button,
            self.ca_import_button,
            self.ca_delete_button,
            self.ca_lock_button,
            self.ca_export_button,
        ):
            ca_toolbar_layout.addWidget(button)
        ca_toolbar_layout.addStretch(1)
        ca_layout.addWidget(ca_toolbar)

        # Stage 158/159 compatibility markers for the refactored per-tab fields:
        # self.ca_password_edit.setEchoMode(QLineEdit.Password)
        # form.addRow("CA-Passwort", self.ca_password_edit)
        # self.country_combo = QComboBox(identity)
        # self.country_combo.addItem(f"{code} – {name}", code)
        # self.country_combo.currentIndexChanged.connect(self._on_ca_country_changed)
        # self._populate_ca_states(self._country_code(), self._load_text("state", ""))
        # self.postal_code_edit.setMaxLength(11)
        # self.locality_name_edit.setMaxLength(21)
        # QPushButton("Sperren") / QPushButton("Löschen") / QPushButton("Exportieren") / QPushButton("Importieren")
        self.ca_tabs = QTabWidget(ca_page)
        self.ca_tabs.setObjectName("opensslCaEditorTabs")
        self.ca_tabs.setTabsClosable(True)
        self.ca_tabs.setMovable(True)
        self.ca_tabs.currentChanged.connect(self._on_ca_tab_changed)
        self.ca_tabs.tabCloseRequested.connect(self._close_ca_tab)
        ca_layout.addWidget(self.ca_tabs, 1)

        requests = QGroupBox("Client-Anfragen / Zertifikatsanfragen", ca_page)
        request_layout = QVBoxLayout(requests)
        request_hint = QLabel(
            "Signieren, Ablehnen, Sperren, frühzeitiger Ablauf und Erneuern werden "
            "über den OpenSSL-CA-Index verwaltet. Die Request-Tabelle kann in einer "
            "folgenden CA-Ausbaustufe ergänzt werden.", requests
        )
        request_hint.setWordWrap(True)
        request_layout.addWidget(request_hint)
        ca_layout.addWidget(requests)
        ca_layout.addStretch(1)
        ca_scroll.setWidget(ca_page)
        # Stage-157 compatibility marker: setup_sections.addTab(ca_scroll, "Client Authority CA")
        setup_sections.addTab(ca_scroll, "CA")

        # Stage 164: Der komplette Zertifikate-Untertab liegt in einer eigenen
        # ScrollArea. Dadurch können die umfangreichen Benutzer-Zertifikat-
        # Formulare, die bereits ausgestellten Zertifikate und das Protokoll
        # deutlich großzügiger untereinander angeordnet werden, ohne dass die
        # verfügbare Dock-Höhe einzelne Bereiche zusammenquetscht.
        cert_scroll = QScrollArea(setup_sections)
        cert_scroll.setObjectName("opensslCertificatesScrollArea")
        cert_scroll.setWidgetResizable(True)
        cert_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        cert_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        cert_page = QWidget(cert_scroll)
        cert_page.setObjectName("opensslCertificatesScrollContent")
        cert_layout = QVBoxLayout(cert_page)
        cert_layout.setContentsMargins(6, 6, 6, 6)
        cert_layout.setSpacing(8)

        cert_toolbar = QHBoxLayout()
        cert_new = QPushButton("Neues Zertifikat", cert_page)
        cert_new.setObjectName("opensslUserCertificateNewButton")
        cert_new.clicked.connect(self._add_user_certificate_tab)
        cert_toolbar.addWidget(cert_new)
        cert_delete = QPushButton("Untertab löschen", cert_page)
        cert_delete.setObjectName("opensslUserCertificateDeleteButton")
        cert_delete.clicked.connect(self._delete_user_certificate_tab)
        cert_toolbar.addWidget(cert_delete)
        cert_toolbar.addStretch(1)
        cert_layout.addLayout(cert_toolbar)

        self.user_certificate_tabs = QTabWidget(cert_page)
        self.user_certificate_tabs.setObjectName("opensslUserCertificateTabs")
        self.user_certificate_tabs.setMovable(True)
        # Genügend sichtbare Formularfläche bereitstellen. Die äußere
        # ScrollArea übernimmt das Scrollen zum nächsten Zertifikat-Bereich.
        self.user_certificate_tabs.setMinimumHeight(620)
        self.user_certificate_tabs.currentChanged.connect(
            lambda _index: self._update_user_certificate_tabs_height()
        )
        cert_layout.addWidget(self.user_certificate_tabs)

        issued_group = QGroupBox("Ausgestellte Benutzer-Zertifikate", cert_page)
        issued_group.setObjectName("opensslIssuedUserCertificatesGroup")
        issued_layout = QVBoxLayout(issued_group)
        issued_layout.setContentsMargins(6, 6, 6, 6)
        self.issued_user_certificate_tabs = QTabWidget(issued_group)
        self.issued_user_certificate_tabs.setObjectName("opensslIssuedUserCertificateTabs")
        self.issued_user_certificate_tabs.setMovable(True)
        self.issued_user_certificate_tabs.setMinimumHeight(260)
        issued_layout.addWidget(self.issued_user_certificate_tabs, 1)
        issued_group.setMinimumHeight(310)
        cert_layout.addWidget(issued_group)

        self._output.setMinimumHeight(180)
        cert_layout.addWidget(self._output)
        cert_layout.addStretch(1)

        cert_scroll.setWidget(cert_page)
        # Stage-157 compatibility marker: setup_sections.addTab(cert_page, "Zertifikate")
        setup_sections.addTab(cert_scroll, "Zertifikate")
        tabs.addTab(setup_page, "Setup")

        # ---------------------------------------------------------------
        # Installation: OpenSSL-Binary, Installation und Basiskonfiguration.
        # ---------------------------------------------------------------
        install_scroll = QScrollArea(tabs)
        install_scroll.setWidgetResizable(True)
        install_page = QWidget(install_scroll)
        install_layout = QVBoxLayout(install_page)

        install_group = QGroupBox("OpenSSL Installation", install_page)
        install_form = QFormLayout(install_group)
        install_dir_row, self.install_dir_edit = self._directory_row("install_dir", "")
        openssl_row, self.openssl_edit = self._file_row(
            "openssl", "openssl.exe", "OpenSSL (openssl.exe);;Programme (*.exe);;Alle Dateien (*)"
        )
        openssl_conf_row, self.openssl_conf_edit = self._file_row(
            "openssl_conf", "", "OpenSSL Konfiguration (*.cnf *.conf);;Alle Dateien (*)"
        )
        installer_row, self.installer_edit = self._file_row(
            "installer", "", "OpenSSL Installer/Archiv (*.exe *.msi *.zip);;Alle Dateien (*)"
        )
        installer_download_row = QWidget(install_group)
        installer_download_layout = QHBoxLayout(installer_download_row)
        installer_download_layout.setContentsMargins(0, 0, 0, 0)
        installer_download_layout.setSpacing(6)
        self.openssl_version_combo = QComboBox(installer_download_row)
        self.openssl_version_combo.setObjectName("opensslInstallerVersionCombo")
        for label, url in OPENSSL_INSTALLER_DOWNLOADS:
            self.openssl_version_combo.addItem(label, url)
        saved_download = self._load_text("installer_download_version", "")
        if saved_download:
            found = self.openssl_version_combo.findText(saved_download)
            if found >= 0:
                self.openssl_version_combo.setCurrentIndex(found)
        self.openssl_version_combo.currentTextChanged.connect(
            lambda value: self._store_text("installer_download_version", value)
        )
        self.openssl_download_button = QPushButton("Download", installer_download_row)
        self.openssl_download_button.setObjectName("opensslInstallerDownloadButton")
        self.openssl_download_button.clicked.connect(self._download_selected_openssl)
        installer_download_layout.addWidget(self.openssl_version_combo, 2)
        installer_download_layout.addWidget(self.openssl_download_button)
        installer_target_label = QLabel("Verzeichnis", installer_download_row)
        installer_download_layout.addWidget(installer_target_label)
        installer_download_layout.addWidget(install_dir_row, 3)
        install_form.addRow("openssl.exe", openssl_row)
        install_form.addRow("openssl.cnf", openssl_conf_row)
        install_form.addRow("Installer", installer_download_row)
        install_form.addRow("Lokaler Installer", installer_row)
        install_layout.addWidget(install_group)

        install_buttons = QHBoxLayout()
        auto_paths = QPushButton("Programmpfade übernehmen", install_page)
        auto_paths.clicked.connect(self._apply_install_directory)
        install_buttons.addWidget(auto_paths)
        version = QPushButton("Version prüfen", install_page)
        version.clicked.connect(lambda: self.run_program(self.openssl_edit.text(), ["version", "-a"]))
        install_buttons.addWidget(version)
        run_installer = QPushButton("Installer starten", install_page)
        run_installer.clicked.connect(self._run_installer)
        install_buttons.addWidget(run_installer)
        install_buttons.addStretch(1)
        install_layout.addLayout(install_buttons)

        install_hint = QLabel(
            "OpenSSL wird nicht mit d64_dism ausgeliefert. Eine Version kann in der "
            "Installer-Zeile gewählt und in das dort angegebene Verzeichnis geladen werden. "
            "ZIP-Archive werden dort automatisch entpackt; EXE/MSI-Dateien "
            "werden als lokaler Installer übernommen.", install_page
        )
        install_hint.setWordWrap(True)
        install_layout.addWidget(install_hint)
        install_layout.addStretch(1)
        install_scroll.setWidget(install_page)
        tabs.addTab(install_scroll, "Installation")
        self.set_dark_mode(self._dark_mode)
        self._refresh_ca_tabs(prompt_selected=False)
        self._load_user_certificate_tabs()
        self._migrate_issued_user_certificate_records()
        self._refresh_issued_user_certificate_tabs()

    def _store_path_edit(self, name: str, edit: QLineEdit, value: Path) -> None:
        text = str(value)
        edit.setText(text)
        self._store_text(name, text)

    def _apply_install_directory(self):
        base_text = self.install_dir_edit.text().strip()
        if not base_text:
            self._message("OpenSSL Installation", "Bitte zuerst ein Installationsverzeichnis auswählen.", QMessageBox.Warning)
            return
        base = Path(base_text)
        binary_dir = base / "bin"
        if not binary_dir.exists():
            binary_dir = base
        self._store_path_edit("openssl", self.openssl_edit, binary_dir / "openssl.exe")
        conf_candidates = [base / "ssl" / "openssl.cnf", base / "bin" / "openssl.cnf", base / "openssl.cnf"]
        conf = next((candidate for candidate in conf_candidates if candidate.exists()), conf_candidates[0])
        self._store_path_edit("openssl_conf", self.openssl_conf_edit, conf)
        self.append_output(f"OpenSSL Programmpfade übernommen: {binary_dir}")

    def _download_selected_openssl(self):
        if self._openssl_download_thread is not None and self._openssl_download_thread.isRunning():
            self._message("OpenSSL Download", "Ein Download läuft bereits.", QMessageBox.Information)
            return

        target_dir = self.install_dir_edit.text().strip()
        if not target_dir:
            self._message(
                "OpenSSL Download",
                "Bitte zuerst ein Installationsverzeichnis auswählen.",
                QMessageBox.Warning,
            )
            return

        url = str(self.openssl_version_combo.currentData() or "").strip()
        label = self.openssl_version_combo.currentText().strip()
        if not url:
            self._message("OpenSSL Download", "Bitte eine OpenSSL-Version auswählen.", QMessageBox.Warning)
            return

        self._store_text("installer_download_version", label)
        self.openssl_download_button.setEnabled(False)
        self.openssl_version_combo.setEnabled(False)
        self.append_output(f"OpenSSL Download: {label}")
        self.append_output(f"Quelle: {url}")
        self.append_output(f"Ziel: {target_dir}")

        thread = OpenSSLDownloadThread(url, target_dir, self)
        thread.completed.connect(self._openssl_download_finished)
        thread.finished.connect(thread.deleteLater)
        self._openssl_download_thread = thread
        thread.start()

    def _openssl_download_finished(self, ok: bool, downloaded_file: str, extracted: bool, error: str):
        self.openssl_download_button.setEnabled(True)
        self.openssl_version_combo.setEnabled(True)
        self._openssl_download_thread = None

        if not ok:
            self.append_output("OpenSSL Download fehlgeschlagen: " + error)
            self._message("OpenSSL Download", "Download fehlgeschlagen:\n" + error, QMessageBox.Critical)
            return

        downloaded = Path(downloaded_file)
        self.append_output(f"Download abgeschlossen: {downloaded}")
        if extracted:
            self.append_output(f"ZIP-Archiv entpackt nach: {self.install_dir_edit.text().strip()}")
            self._discover_downloaded_openssl_paths()
            self._message(
                "OpenSSL Download",
                "Download abgeschlossen und ZIP-Archiv erfolgreich entpackt.",
                QMessageBox.Information,
            )
            return

        suffix = downloaded.suffix.lower()
        if suffix in (".exe", ".msi"):
            self._store_path_edit("installer", self.installer_edit, downloaded)
        self._message(
            "OpenSSL Download",
            "Download abgeschlossen.\n\n" + str(downloaded),
            QMessageBox.Information,
        )

    def _discover_downloaded_openssl_paths(self):
        target_text = self.install_dir_edit.text().strip()
        if not target_text:
            return
        root = Path(target_text)
        if not root.exists():
            return
        try:
            executables = list(root.rglob("openssl.exe"))
        except OSError:
            executables = []
        if executables:
            executables.sort(key=lambda p: (0 if p.parent.name.lower() == "bin" else 1, len(p.parts)))
            self._store_path_edit("openssl", self.openssl_edit, executables[0])
        try:
            configs = list(root.rglob("openssl.cnf"))
        except OSError:
            configs = []
        if configs:
            configs.sort(key=lambda p: len(p.parts))
            self._store_path_edit("openssl_conf", self.openssl_conf_edit, configs[0])

    def _run_installer(self):
        installer = self.installer_edit.text().strip()
        if not installer:
            self._message("OpenSSL Installation", "Bitte zuerst einen Installer auswählen.", QMessageBox.Warning)
            return
        self.run_program(installer, [])

    def _country_code(self) -> str:
        return str(self.country_combo.currentData() or "").strip().upper()

    def _state_value(self) -> str:
        data = self.state_combo.currentData()
        return str(data if data not in (None, "") else self.state_combo.currentText()).strip()

    def _locality_parts(self) -> tuple[str, str]:
        postal = self.postal_code_edit.text().strip()[:11]
        place = self.locality_name_edit.text().strip()[:21]
        # The displayed/stored combined location must never exceed 32 characters.
        # When both fields are present one separator character is included.
        if postal and place:
            allowed_place = max(0, 32 - len(postal) - 1)
            place = place[:allowed_place]
        return postal, place

    def _locality_value(self) -> str:
        postal, place = self._locality_parts()
        return " ".join(part for part in (postal, place) if part)[:32]

    def _store_ca_locality(self) -> None:
        postal, place = self._locality_parts()
        # Reflect a possible 32-character normalization back into the UI.
        if self.postal_code_edit.text().strip() != postal:
            self.postal_code_edit.setText(postal)
        if self.locality_name_edit.text().strip() != place:
            self.locality_name_edit.setText(place)
        self._store_text("postal_code", postal)
        self._store_text("locality_name", place)
        self._store_text("locality", self._locality_value())

    def _populate_ca_states(self, country_code: str, selected: Optional[str] = None) -> None:
        selected = self.state_combo.currentText().strip() if selected is None else selected.strip()
        entries = CA_SUBDIVISIONS.get(country_code, [])
        self.state_combo.blockSignals(True)
        self.state_combo.clear()
        if entries:
            self.state_combo.setEditable(False)
            self.state_combo.addItem("", "")
            for code, name in entries:
                self.state_combo.addItem(f"{code} – {name}", name)
            idx = -1
            if selected:
                for i in range(self.state_combo.count()):
                    if self.state_combo.itemData(i) == selected or self.state_combo.itemText(i) == selected:
                        idx = i
                        break
                if idx < 0:
                    for i in range(self.state_combo.count()):
                        if self.state_combo.itemText(i).endswith(" – " + selected):
                            idx = i
                            break
            self.state_combo.setCurrentIndex(idx if idx >= 0 else 0)
        else:
            # Not every country has a meaningful fixed State/Province catalogue.
            # Keep ST= available without pretending that a partial list is complete.
            self.state_combo.setEditable(True)
            if selected:
                self.state_combo.addItem(selected, selected)
                self.state_combo.setCurrentText(selected)
        self.state_combo.blockSignals(False)

    def _on_ca_country_changed(self, _index: int) -> None:
        code = self._country_code()
        self._store_text("country", code)
        self._populate_ca_states(code, "")
        self._store_text("state", self._state_value())

    def _subject(self) -> str:
        postal, place = self._locality_parts()
        values = (
            ("C", self._country_code()),
            ("ST", self._state_value()),
            ("postalCode", postal),
            ("L", place),
            ("O", self.org_edit.text().strip()),
            ("OU", self.ou_edit.text().strip()),
            ("CN", self.cn_edit.text().strip()),
            ("emailAddress", self.email_edit.text().strip()),
        )
        parts = []
        for key, value in values:
            if value:
                parts.append(f"/{key}={value.replace('/', '_')}")
        return "".join(parts)

    def _ca_openssl_config_text(self, base: Path) -> str:
        # Stage 170: Jede CA besitzt ihre eigene Konfiguration. Dadurch ist die
        # CA nicht vom globalen openssl.cnf einer bestimmten OpenSSL-Installation
        # abhängig. Vorwärtsschrägstriche funktionieren auch unter Windows und
        # vermeiden Escape-Probleme in OpenSSL-Konfigurationsdateien.
        ca_dir = str(base.resolve()).replace("\\", "/")
        key_bits = self.bits_combo.currentText().strip() or "4096"
        default_days = str(self.days_spin.value())
        return f"""# d64_dism - CA configuration
# Generated automatically for this CA.

[ ca ]
default_ca = CA_default

[ CA_default ]
dir               = {ca_dir}
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index.txt
serial            = $dir/serial
crlnumber         = $dir/crlnumber
certificate       = $dir/certs/ca.cert.pem
private_key       = $dir/private/ca.key.pem
default_md        = sha256
default_days      = {default_days}
default_crl_days  = 30
policy            = policy_loose
unique_subject    = no
copy_extensions   = copy

[ policy_loose ]
countryName             = optional
stateOrProvinceName     = optional
localityName            = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

[ req ]
default_bits        = {key_bits}
distinguished_name = req_distinguished_name
x509_extensions     = v3_ca
string_mask         = utf8only

[ req_distinguished_name ]

[ v3_ca ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints       = critical,CA:true
keyUsage               = critical,digitalSignature,cRLSign,keyCertSign
"""

    def _ensure_ca_openssl_config(self, base: Path, force: bool = False) -> Path:
        config = base / "openssl.cnf"
        if force or not config.is_file():
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(self._ca_openssl_config_text(base), encoding="utf-8")
            self.append_output(f"CA-Konfiguration erzeugt: {config}")
        return config

    def _initialize_ca_directory(self):
        base_text = self.ca_dir_edit.text().strip()
        if not base_text:
            self._message("CA-Verzeichnis", "Bitte zuerst ein CA-Verzeichnis auswählen.", QMessageBox.Warning)
            return
        base = Path(base_text)
        try:
            for child in ("certs", "crl", "newcerts", "private", "csr"):
                (base / child).mkdir(parents=True, exist_ok=True)
            (base / "index.txt").touch(exist_ok=True)
            if not (base / "serial").exists():
                (base / "serial").write_text("1000\n", encoding="ascii")
            if not (base / "crlnumber").exists():
                (base / "crlnumber").write_text("1000\n", encoding="ascii")
            self._ensure_ca_openssl_config(base)
            self.append_output(f"CA-Verzeichnis vorbereitet: {base}")
        except Exception as exc:
            self._message("CA-Verzeichnis", str(exc), QMessageBox.Critical)

    def _openssl_sync(self, args: list[str], password: str = "") -> tuple[bool, bytes, bytes]:
        program = self.openssl_edit.text().strip() or "openssl.exe"
        env = os.environ.copy()
        if password:
            env["D64_CA_PASSWORD"] = password
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            result = subprocess.run(
                [program] + list(args),
                input=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=flags,
                check=False,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as exc:
            return False, b"", str(exc).encode("utf-8", errors="replace")

    def _ca_password(self, title: str = "CA-Passwort") -> str:
        password = self.ca_password_edit.text()
        if password:
            return password
        value, ok = QInputDialog.getText(self, title, "Passwort für ca.key.pem:", QLineEdit.Password)
        return value if ok else ""

    def _ca_metadata(self, base: Path, status: str = "aktiv") -> dict:
        return {
            "fqdn": self.fqdn_edit.text().strip(),
            "common_name": self.cn_edit.text().strip(),
            "organization": self.org_edit.text().strip(),
            "organizational_unit": self.ou_edit.text().strip(),
            "country": self._country_code(),
            "state": self._state_value(),
            "postal_code": self._locality_parts()[0],
            "locality_name": self._locality_parts()[1],
            "locality": self._locality_value(),
            "email": self.email_edit.text().strip(),
            "days": int(self.days_spin.value()),
            "key_bits": int(self.bits_combo.currentText()),
            "ca_directory": str(base),
            "certificate": str(base / "certs" / "ca.cert.pem"),
            "private_key": str(base / "private" / "ca.key.pem"),
            "status": status,
            "updated_utc": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _backup_files(base: Path) -> dict:
        files = {}
        for rel in (
            "certs/ca.cert.pem", "private/ca.key.pem", "index.txt", "serial",
            "crlnumber", "crl/ca.crl.pem", "openssl.cnf"
        ):
            path = base / rel
            if path.is_file():
                files[rel] = base64.b64encode(path.read_bytes()).decode("ascii")
        return files

    def _encrypt_ca_payload(self, payload: dict, password: str) -> dict:
        raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        program = self.openssl_edit.text().strip() or "openssl.exe"
        env = os.environ.copy()
        env["D64_CA_JSON_PASS"] = password
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        result = subprocess.run(
            [program, "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
             "-md", "sha256", "-salt", "-pass", "env:D64_CA_JSON_PASS"],
            input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, creationflags=flags, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip() or "OpenSSL-Verschlüsselung fehlgeschlagen")
        return {
            "format": "d64-ca-backup",
            "version": 1,
            "cipher": "AES-256-CBC",
            "kdf": "PBKDF2-HMAC-SHA256",
            "iterations": 200000,
            "payload": base64.b64encode(result.stdout).decode("ascii"),
        }

    def _decrypt_ca_payload(self, container: dict, password: str) -> dict:
        if container.get("format") != "d64-ca-backup":
            raise RuntimeError("Unbekanntes CA-Backup-Format")
        encrypted = base64.b64decode(container.get("payload", ""))
        program = self.openssl_edit.text().strip() or "openssl.exe"
        env = os.environ.copy()
        env["D64_CA_JSON_PASS"] = password
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        result = subprocess.run(
            [program, "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
             "-md", "sha256", "-pass", "env:D64_CA_JSON_PASS"],
            input=encrypted, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, creationflags=flags, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("CA-Datei konnte nicht entschlüsselt werden. Passwort prüfen.")
        return json.loads(result.stdout.decode("utf-8"))


    # ------------------------------------------------------------------
    # Stage 168 - editable CA tabs
    # ------------------------------------------------------------------
    def _ca_editor_records(self) -> list[dict]:
        raw = self.settings.value(self._key("ca_editor_tabs"), "[]") or "[]"
        try:
            data = json.loads(str(raw))
        except Exception:
            return []
        return [dict(item) for item in data if isinstance(item, dict)]

    def _ca_page_record(self, page: QWidget) -> dict:
        controls = getattr(page, "_ca_input_fields", {})
        record = {
            "ca_directory": controls.get("ca_directory").text().strip() if controls.get("ca_directory") else "",
            "fqdn": controls.get("fqdn").text().strip() if controls.get("fqdn") else "",
            "common_name": controls.get("common_name").text().strip() if controls.get("common_name") else "",
            "organization": controls.get("organization").text().strip() if controls.get("organization") else "",
            "organizational_unit": controls.get("organizational_unit").text().strip() if controls.get("organizational_unit") else "",
            "country": str(controls.get("country").currentData() or "").strip().upper() if controls.get("country") else "DE",
            "state": "",
            "postal_code": controls.get("postal_code").text().strip()[:11] if controls.get("postal_code") else "",
            "locality_name": controls.get("locality_name").text().strip()[:21] if controls.get("locality_name") else "",
            "email": controls.get("email").text().strip() if controls.get("email") else "",
            "days": int(controls.get("days").value()) if controls.get("days") else 3650,
            "key_bits": controls.get("key_bits").currentText() if controls.get("key_bits") else "4096",
            "registered": bool(page.property("ca_registered")),
        }
        state_combo = controls.get("state")
        if state_combo is not None:
            data = state_combo.currentData()
            record["state"] = str(data if data not in (None, "") else state_combo.currentText()).strip()
        postal = record["postal_code"]
        place = record["locality_name"]
        record["locality"] = " ".join(x for x in (postal, place) if x)[:32]
        return record

    def _save_ca_editor_tabs(self) -> None:
        if not hasattr(self, "ca_tabs"):
            return
        records = []
        for index in range(self.ca_tabs.count()):
            page = self.ca_tabs.widget(index)
            if page is not None:
                records.append(self._ca_page_record(page))
        self.settings.setValue(self._key("ca_editor_tabs"), json.dumps(records, ensure_ascii=False))
        self.settings.sync()

    def _populate_state_combo_for_page(self, page: QWidget, country_code: str, selected: str = "") -> None:
        controls = getattr(page, "_ca_input_fields", {})
        combo = controls.get("state")
        if combo is None:
            return
        selected = str(selected or "").strip()
        entries = CA_SUBDIVISIONS.get(str(country_code or "").upper(), [])
        combo.blockSignals(True)
        combo.clear()
        if entries:
            combo.setEditable(False)
            combo.addItem("", "")
            for code, name in entries:
                combo.addItem(f"{code} – {name}", name)
            idx = -1
            for i in range(combo.count()):
                if combo.itemData(i) == selected or combo.itemText(i) == selected or combo.itemText(i).endswith(" – " + selected):
                    idx = i
                    break
            combo.setCurrentIndex(idx if idx >= 0 else 0)
        else:
            combo.setEditable(True)
            if selected:
                combo.addItem(selected, selected)
                combo.setCurrentText(selected)
        combo.blockSignals(False)

    def _create_ca_editor_page(self, record: dict | None = None, registered: bool = False) -> QWidget:
        record = dict(record or {})
        page = QWidget(self.ca_tabs)
        outer = QVBoxLayout(page)
        outer.setContentsMargins(6, 6, 6, 6)

        identity = QGroupBox("Client Authority CA", page)
        form = QFormLayout(identity)

        ca_dir_edit = QLineEdit(str(record.get("ca_directory", "")), identity)
        ca_dir_button = QPushButton("…", identity)
        ca_dir_button.setFixedWidth(34)
        ca_dir_row = QWidget(identity)
        ca_dir_layout = QHBoxLayout(ca_dir_row)
        ca_dir_layout.setContentsMargins(0, 0, 0, 0)
        ca_dir_layout.setSpacing(4)
        ca_dir_layout.addWidget(ca_dir_edit, 1)
        ca_dir_layout.addWidget(ca_dir_button)

        fqdn_edit = QLineEdit(str(record.get("fqdn", "ca.local")), identity)
        cn_edit = QLineEdit(str(record.get("common_name", "d64 Development Root CA")), identity)
        org_edit = QLineEdit(str(record.get("organization", "d64 Development")), identity)
        ou_edit = QLineEdit(str(record.get("organizational_unit", "Development")), identity)

        country_combo = QComboBox(identity)
        country_combo.setObjectName("opensslCaCountryCombo")
        for code, name in CA_COUNTRY_CODES:
            country_combo.addItem(f"{code} – {name}", code)
        country = str(record.get("country", "DE") or "DE").upper()
        idx = country_combo.findData(country)
        country_combo.setCurrentIndex(idx if idx >= 0 else country_combo.findData("DE"))

        state_combo = QComboBox(identity)
        state_combo.setObjectName("opensslCaStateCombo")
        postal_edit = QLineEdit(str(record.get("postal_code", ""))[:11], identity)
        postal_edit.setObjectName("opensslCaPostalCodeEdit")
        postal_edit.setMaxLength(11)
        postal_edit.setPlaceholderText("PLZ")
        locality_edit = QLineEdit(str(record.get("locality_name", ""))[:21], identity)
        locality_edit.setObjectName("opensslCaLocalityEdit")
        locality_edit.setMaxLength(21)
        locality_edit.setPlaceholderText("Ort")
        locality_row = QWidget(identity)
        locality_layout = QHBoxLayout(locality_row)
        locality_layout.setContentsMargins(0, 0, 0, 0)
        locality_layout.setSpacing(6)
        locality_layout.addWidget(postal_edit, 11)
        locality_layout.addWidget(locality_edit, 21)

        email_edit = QLineEdit(str(record.get("email", "")), identity)
        password_edit = QLineEdit(identity)
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.setPlaceholderText("Passwort für ca.key.pem und CA-Export")
        days_spin = QSpinBox(identity)
        days_spin.setRange(1, 36500)
        try:
            days_spin.setValue(int(record.get("days", 3650) or 3650))
        except Exception:
            days_spin.setValue(3650)
        bits_combo = QComboBox(identity)
        bits_combo.addItems(["2048", "3072", "4096"])
        bits_combo.setCurrentText(str(record.get("key_bits", "4096")))

        form.addRow("CA-Verzeichnis", ca_dir_row)
        form.addRow("FQDN", fqdn_edit)
        form.addRow("Common Name / Aussteller", cn_edit)
        form.addRow("Organisation", org_edit)
        form.addRow("Organisationseinheit", ou_edit)
        form.addRow("Land", country_combo)
        form.addRow("Bundesland / Kanton / Bundesstaat", state_combo)
        form.addRow("PLZ / Ort", locality_row)
        form.addRow("E-Mail", email_edit)
        form.addRow("CA-Passwort", password_edit)
        form.addRow("Gültigkeit (Tage)", days_spin)
        form.addRow("RSA-Schlüssel", bits_combo)
        outer.addWidget(identity)

        # Stage 169: Informationen des tatsächlich ausgestellten CA-Zertifikats
        # direkt unter den Eingabefeldern anzeigen. Die Anzeige wird nicht aus
        # den Editorwerten zusammengesetzt, sondern per ``openssl x509`` aus
        # certs/ca.cert.pem gelesen.
        cert_info_group = QGroupBox("CA-Zertifikat-Informationen", page)
        cert_info_group.setObjectName("opensslCaCertificateInfoGroup")
        cert_info_layout = QVBoxLayout(cert_info_group)
        cert_info_layout.setContentsMargins(6, 6, 6, 6)

        cert_info_edit = QPlainTextEdit(cert_info_group)
        cert_info_edit.setObjectName("opensslCaCertificateInfoEdit")
        cert_info_edit.setReadOnly(True)
        cert_info_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        cert_info_edit.setMinimumHeight(280)
        cert_info_edit.setPlainText(
            "Noch kein CA-Zertifikat vorhanden.\n"
            "Nach dem Erzeugen oder Importieren einer CA werden die Zertifikatsinformationen hier angezeigt."
        )
        cert_info_layout.addWidget(cert_info_edit, 1)

        cert_info_buttons = QHBoxLayout()
        cert_info_refresh = QPushButton("Zertifikat-Informationen aktualisieren", cert_info_group)
        cert_info_refresh.setObjectName("opensslCaCertificateInfoRefreshButton")
        cert_info_refresh.clicked.connect(lambda _checked=False, p=page: self._refresh_ca_certificate_info(p))
        cert_info_buttons.addWidget(cert_info_refresh)
        cert_info_buttons.addStretch(1)
        cert_info_layout.addLayout(cert_info_buttons)
        outer.addWidget(cert_info_group)

        page._ca_certificate_info_edit = cert_info_edit
        page._ca_certificate_info_group = cert_info_group

        actions = QGroupBox("CA-Aktionen", page)
        actions_layout = QHBoxLayout(actions)
        init_button = QPushButton("CA-Verzeichnis anlegen", actions)
        root_button = QPushButton("Root-CA erzeugen", actions)
        crl_button = QPushButton("CRL anzeigen", actions)
        init_button.clicked.connect(self._initialize_ca_directory)
        root_button.clicked.connect(self._create_root_ca)
        crl_button.clicked.connect(self._show_crl)
        actions_layout.addWidget(init_button)
        actions_layout.addWidget(root_button)
        actions_layout.addWidget(crl_button)
        actions_layout.addStretch(1)
        outer.addWidget(actions)
        outer.addStretch(1)

        page._ca_input_fields = {
            "ca_directory": ca_dir_edit,
            "fqdn": fqdn_edit,
            "common_name": cn_edit,
            "organization": org_edit,
            "organizational_unit": ou_edit,
            "country": country_combo,
            "state": state_combo,
            "postal_code": postal_edit,
            "locality_name": locality_edit,
            "email": email_edit,
            "password": password_edit,
            "days": days_spin,
            "key_bits": bits_combo,
        }
        page.setProperty("ca_directory", ca_dir_edit.text().strip())
        page.setProperty("ca_registered", bool(registered))
        self._populate_state_combo_for_page(page, country, str(record.get("state", "")))

        def select_directory():
            directory = QFileDialog.getExistingDirectory(
                self, "CA-Verzeichnis auswählen", ca_dir_edit.text().strip(),
                QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog,
            )
            if directory:
                ca_dir_edit.setText(directory)
                page.setProperty("ca_directory", directory)
                self._update_ca_tab_title(page)
                self._refresh_ca_certificate_info(page)
                self._save_ca_editor_tabs()

        ca_dir_button.clicked.connect(select_directory)

        def country_changed(_index):
            self._populate_state_combo_for_page(page, str(country_combo.currentData() or ""), "")
            self._save_ca_editor_tabs()

        country_combo.currentIndexChanged.connect(country_changed)
        cn_edit.editingFinished.connect(lambda: (self._update_ca_tab_title(page), self._save_ca_editor_tabs()))
        ca_dir_edit.editingFinished.connect(lambda: (page.setProperty("ca_directory", ca_dir_edit.text().strip()), self._update_ca_tab_title(page), self._refresh_ca_certificate_info(page), self._save_ca_editor_tabs()))
        for edit in (fqdn_edit, org_edit, ou_edit, postal_edit, locality_edit, email_edit):
            edit.editingFinished.connect(self._save_ca_editor_tabs)
        state_combo.currentTextChanged.connect(lambda _value: self._save_ca_editor_tabs())
        days_spin.valueChanged.connect(lambda _value: self._save_ca_editor_tabs())
        bits_combo.currentTextChanged.connect(lambda _value: self._save_ca_editor_tabs())
        return page

    def _refresh_ca_certificate_info(self, page: QWidget | None = None) -> None:
        """Read and display the real X.509 data of the CA certificate."""
        if page is None and hasattr(self, "ca_tabs"):
            page = self.ca_tabs.currentWidget()
        if page is None:
            return

        info_edit = getattr(page, "_ca_certificate_info_edit", None)
        controls = getattr(page, "_ca_input_fields", {})
        if info_edit is None or not controls:
            return

        ca_dir_edit = controls.get("ca_directory")
        base_text = ca_dir_edit.text().strip() if ca_dir_edit is not None else str(page.property("ca_directory") or "").strip()
        if not base_text:
            info_edit.setPlainText(
                "Noch kein CA-Verzeichnis ausgewählt.\n"
                "Nach dem Erzeugen oder Importieren einer CA werden die Zertifikatsinformationen hier angezeigt."
            )
            return

        base = Path(base_text)
        cert_path = base / "certs" / "ca.cert.pem"
        if not cert_path.is_file():
            info_edit.setPlainText(
                f"CA-Zertifikat noch nicht vorhanden:\n{cert_path}\n\n"
                "Erzeuge zuerst die Root-CA oder importiere eine bestehende CA."
            )
            return

        ok, out, err = self._openssl_sync([
            "x509", "-in", str(cert_path), "-noout",
            "-subject", "-issuer", "-serial",
            "-startdate", "-enddate",
            "-fingerprint", "-sha256", "-text",
        ])
        if not ok:
            error_text = err.decode("utf-8", errors="replace").strip()
            info_edit.setPlainText(
                f"CA-Zertifikat:\n{cert_path}\n\n"
                "Die Zertifikatsinformationen konnten nicht gelesen werden.\n"
                + (error_text or "OpenSSL lieferte keinen Fehlertext.")
            )
            return

        certificate_text = out.decode("utf-8", errors="replace").strip()
        info_edit.setPlainText(
            f"CA-Zertifikat:\n{cert_path}\n\n{certificate_text}"
        )
        info_edit.verticalScrollBar().setValue(0)

    def _bind_active_ca_page(self, page: QWidget | None) -> None:
        if page is None:
            return
        controls = getattr(page, "_ca_input_fields", {})
        if not controls:
            return
        self.ca_dir_edit = controls["ca_directory"]
        self.fqdn_edit = controls["fqdn"]
        self.cn_edit = controls["common_name"]
        self.org_edit = controls["organization"]
        self.ou_edit = controls["organizational_unit"]
        self.country_combo = controls["country"]
        self.country_edit = self.country_combo
        self.state_combo = controls["state"]
        self.state_edit = self.state_combo
        self.postal_code_edit = controls["postal_code"]
        self.locality_name_edit = controls["locality_name"]
        self.locality_edit = self.locality_name_edit
        self.email_edit = controls["email"]
        self.ca_password_edit = controls["password"]
        self.days_spin = controls["days"]
        self.bits_combo = controls["key_bits"]

    def _update_ca_tab_title(self, page: QWidget) -> None:
        if not hasattr(self, "ca_tabs"):
            return
        index = self.ca_tabs.indexOf(page)
        if index < 0:
            return
        controls = getattr(page, "_ca_input_fields", {})
        title = controls.get("common_name").text().strip() if controls.get("common_name") else ""
        if not title and controls.get("ca_directory"):
            base_text = controls["ca_directory"].text().strip()
            title = Path(base_text).name if base_text else ""
        self.ca_tabs.setTabText(index, title or f"CA {index + 1}")

    def _new_ca_tab(self) -> None:
        page = self._create_ca_editor_page({}, registered=False)
        index = self.ca_tabs.addTab(page, "Neue CA")
        self.ca_tabs.setCurrentIndex(index)
        self._bind_active_ca_page(page)
        self._update_ca_tab_title(page)
        self._save_ca_editor_tabs()

    def _close_ca_tab(self, index: int) -> None:
        if index < 0 or index >= self.ca_tabs.count():
            return
        page = self.ca_tabs.widget(index)
        self._save_ca_editor_tabs()
        self.ca_tabs.removeTab(index)
        if page is not None:
            page.deleteLater()
        if self.ca_tabs.count() > 0:
            self._bind_active_ca_page(self.ca_tabs.currentWidget())
        self._save_ca_editor_tabs()

    def _ca_registry(self) -> list[str]:
        raw = self.settings.value(self._key("ca_registry"), "[]") or "[]"
        try:
            values = json.loads(str(raw))
            return [str(Path(v)) for v in values if v]
        except Exception:
            return []

    def _set_ca_registry(self, values: list[str]) -> None:
        unique = []
        for value in values:
            value = str(Path(value))
            if value not in unique:
                unique.append(value)
        self.settings.setValue(self._key("ca_registry"), json.dumps(unique, ensure_ascii=False))
        self.settings.sync()

    def _register_ca(self, base: Path) -> None:
        values = self._ca_registry()
        if str(base) not in values:
            values.append(str(base))
            self._set_ca_registry(values)

    def _metadata_path(self, base: Path) -> Path:
        return base / "ca.info.json"

    def _write_encrypted_metadata(self, base: Path, metadata: dict, password: str, include_files: bool = False, target: Path | None = None) -> None:
        payload = {"ca": metadata}
        if include_files:
            payload["files"] = self._backup_files(base)
        container = self._encrypt_ca_payload(payload, password)
        (target or self._metadata_path(base)).write_text(json.dumps(container, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read_encrypted_metadata(self, path: Path, password: str) -> dict:
        return self._decrypt_ca_payload(json.loads(path.read_text(encoding="utf-8")), password)

    def _refresh_ca_tabs(self, prompt_selected: bool = True) -> None:
        if not hasattr(self, "ca_tabs"):
            return

        current_base = ""
        current = self.ca_tabs.currentWidget()
        if current is not None:
            current_base = str(current.property("ca_directory") or "")

        records = self._ca_editor_records()
        by_base = {str(Path(str(r.get("ca_directory")))): r for r in records if r.get("ca_directory")}
        merged = []
        seen = set()
        for base_text in self._ca_registry():
            key = str(Path(base_text))
            record = dict(by_base.get(key, {}))
            record["ca_directory"] = key
            record["registered"] = True
            merged.append(record)
            seen.add(key)
        for record in records:
            base_text = str(record.get("ca_directory", "")).strip()
            key = str(Path(base_text)) if base_text else ""
            if key and key in seen:
                continue
            if not bool(record.get("registered")):
                merged.append(record)

        self.ca_tabs.blockSignals(True)
        while self.ca_tabs.count():
            page = self.ca_tabs.widget(0)
            self.ca_tabs.removeTab(0)
            if page is not None:
                page.deleteLater()
        for record in merged:
            registered = bool(record.get("registered"))
            page = self._create_ca_editor_page(record, registered=registered)
            self.ca_tabs.addTab(page, "CA")
            self._update_ca_tab_title(page)
        if self.ca_tabs.count() == 0:
            page = self._create_ca_editor_page({}, registered=False)
            self.ca_tabs.addTab(page, "Neue CA")
            self._update_ca_tab_title(page)
        self.ca_tabs.blockSignals(False)

        target = 0
        if current_base:
            for index in range(self.ca_tabs.count()):
                page = self.ca_tabs.widget(index)
                if str(page.property("ca_directory") or "") == current_base:
                    target = index
                    break
        self.ca_tabs.setCurrentIndex(target)
        enabled = self.ca_tabs.count() > 0
        self.ca_delete_button.setEnabled(enabled)
        self.ca_lock_button.setEnabled(enabled and bool(self._selected_ca_base()))
        self.ca_export_button.setEnabled(enabled and bool(self._selected_ca_base()))
        self._bind_active_ca_page(self.ca_tabs.currentWidget())
        self._refresh_ca_certificate_info(self.ca_tabs.currentWidget())
        self._save_ca_editor_tabs()
        if enabled and prompt_selected:
            self._on_ca_tab_changed(self.ca_tabs.currentIndex())
        self._refresh_user_certificate_ca_choices()

    def authenticate_before_open(self, timeout_seconds: int = 120) -> bool:
        """Require a valid CA password before the OpenSSL dock may be shown.

        Stage 167 turns the old implicit CA-tab password query into an explicit
        access gate.  The overall retry window is bounded; a wrong password
        reopens the password dialog while Cancel or timeout aborts opening the
        OpenSSL workspace.
        """
        if not hasattr(self, "ca_tabs") or self.ca_tabs.count() <= 0:
            # Without an encrypted CA metadata file there is no existing
            # credential against which an access password can be verified.
            return True

        page = None
        base = None
        info = None
        for index in range(self.ca_tabs.count()):
            candidate = self.ca_tabs.widget(index)
            if candidate is None:
                continue
            base_text = str(candidate.property("ca_directory") or "").strip()
            if not base_text:
                continue
            candidate_base = Path(base_text)
            candidate_info = self._metadata_path(candidate_base)
            if candidate_info.is_file():
                page = candidate
                base = candidate_base
                info = candidate_info
                break
        if page is None or base is None or info is None:
            return True

        try:
            timeout_seconds = max(1, int(timeout_seconds))
        except (TypeError, ValueError):
            timeout_seconds = 120
        deadline = time.monotonic() + timeout_seconds
        wrong_password = False

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False

            dialog = QInputDialog(self)
            dialog.setObjectName("opensslAccessPasswordDialog")
            dialog.setWindowTitle("OpenSSL – Passwort")
            dialog.setInputMode(QInputDialog.TextInput)
            dialog.setTextEchoMode(QLineEdit.Password)
            dialog.setOkButtonText("OK")
            dialog.setCancelButtonText("Abbrechen")

            timer = QTimer(dialog)
            timer.setInterval(250)

            def update_timeout_label():
                seconds = max(0, int(deadline - time.monotonic() + 0.999))
                prefix = "Passwort falsch.\n\n" if wrong_password else ""
                dialog.setLabelText(
                    prefix
                    + f"Passwort für {base.name or base}:\n"
                    + f"Zeit bis zum automatischen Abbruch: {seconds} Sekunden"
                )
                if seconds <= 0:
                    timer.stop()
                    dialog.reject()

            timer.timeout.connect(update_timeout_label)
            update_timeout_label()
            timer.start()
            result = dialog.exec_()
            timer.stop()

            if result != QDialog.Accepted:
                return False

            password = dialog.textValue()
            if not password:
                wrong_password = True
                continue

            try:
                payload = self._read_encrypted_metadata(info, password)
            except FileNotFoundError:
                self._message(
                    "OpenSSL – Passwort",
                    "OpenSSL wurde nicht gefunden. Das Passwort kann daher nicht geprüft werden.",
                    QMessageBox.Critical,
                )
                return False
            except RuntimeError:
                # Wrong CA password: reopen the dialog while preserving the
                # original 120-second total timeout.
                wrong_password = True
                continue
            except Exception as exc:
                self._message(
                    "OpenSSL – Passwort",
                    f"Die Passwortprüfung konnte nicht durchgeführt werden:\n{exc}",
                    QMessageBox.Critical,
                )
                return False

            metadata = dict(payload.get("ca", {}))
            self._ca_session_passwords[str(base)] = password
            self._populate_ca_page(page, metadata)
            return True

    def _populate_ca_page(self, page: QWidget, metadata: dict) -> None:
        controls = getattr(page, "_ca_input_fields", {})
        if not controls:
            return
        text_map = {
            "ca_directory": "ca_directory",
            "fqdn": "fqdn",
            "common_name": "common_name",
            "organization": "organization",
            "organizational_unit": "organizational_unit",
            "postal_code": "postal_code",
            "locality_name": "locality_name",
            "email": "email",
        }
        for control_key, meta_key in text_map.items():
            widget = controls.get(control_key)
            if widget is not None and meta_key in metadata:
                widget.setText(str(metadata.get(meta_key, "")))
        country = str(metadata.get("country", "DE") or "DE").upper()
        country_combo = controls.get("country")
        if country_combo is not None:
            country_combo.blockSignals(True)
            idx = country_combo.findData(country)
            country_combo.setCurrentIndex(idx if idx >= 0 else country_combo.findData("DE"))
            country_combo.blockSignals(False)
        self._populate_state_combo_for_page(page, country, str(metadata.get("state", "")))
        if controls.get("days") is not None:
            try:
                controls["days"].setValue(int(metadata.get("days", 3650)))
            except Exception:
                pass
        if controls.get("key_bits") is not None:
            controls["key_bits"].setCurrentText(str(metadata.get("key_bits", "4096")))
        base = Path(str(metadata.get("ca_directory") or page.property("ca_directory") or ""))
        page.setProperty("ca_directory", str(base) if str(base) != "." else "")
        page.setProperty("ca_registered", bool(str(base) and str(base) != "."))
        self._update_ca_tab_title(page)
        if page is self.ca_tabs.currentWidget():
            self._bind_active_ca_page(page)
        self._refresh_ca_certificate_info(page)
        self._save_ca_editor_tabs()

    def _on_ca_tab_changed(self, index: int) -> None:
        if index < 0 or not hasattr(self, "ca_tabs"):
            return
        page = self.ca_tabs.widget(index)
        if page is None:
            return
        self._bind_active_ca_page(page)
        self._refresh_ca_certificate_info(page)
        base_text = str(page.property("ca_directory") or self.ca_dir_edit.text().strip())
        base = Path(base_text) if base_text else None
        has_registered = bool(base and self._metadata_path(base).exists())
        self.ca_delete_button.setEnabled(True)
        self.ca_lock_button.setEnabled(has_registered)
        self.ca_export_button.setEnabled(has_registered)
        if not has_registered:
            return
        info = self._metadata_path(base)
        password = self._ca_session_passwords.get(str(base), "") or self.ca_password_edit.text()
        if not password:
            password, ok = QInputDialog.getText(self, "CA Informationen", f"Passwort für {base.name or base}:", QLineEdit.Password)
            if not ok or not password:
                return
        try:
            payload = self._read_encrypted_metadata(info, password)
            metadata = dict(payload.get("ca", {}))
            self._ca_session_passwords[str(base)] = password
            self.ca_password_edit.setText(password)
            self._populate_ca_page(page, metadata)
        except Exception as exc:
            self._message("CA Informationen", str(exc), QMessageBox.Warning)

    def _selected_ca_base(self) -> Path | None:
        page = self.ca_tabs.currentWidget() if hasattr(self, "ca_tabs") else None
        if page is None:
            return None
        self._bind_active_ca_page(page)
        value = self.ca_dir_edit.text().strip()
        if not value:
            return None
        page.setProperty("ca_directory", value)
        return Path(value)

    def _create_root_ca(self):
        base_text = self.ca_dir_edit.text().strip()
        if not base_text:
            self._message("Root-CA", "Bitte zuerst ein CA-Verzeichnis auswählen.", QMessageBox.Warning)
            return
        password = self._ca_password("Neue CA")
        if not password:
            self._message("Root-CA", "Für eine neue CA ist ein Passwort erforderlich.", QMessageBox.Warning)
            return
        base = Path(base_text)
        self._initialize_ca_directory()
        key = base / "private" / "ca.key.pem"
        cert = base / "certs" / "ca.cert.pem"
        try:
            # Immer die CA-eigene Konfiguration verwenden. Das globale
            # Installation->openssl.cnf darf die CA-Erzeugung nicht blockieren.
            conf = self._ensure_ca_openssl_config(base)
        except Exception as exc:
            self._message("Root-CA", f"openssl.cnf konnte nicht erzeugt werden:\n{exc}", QMessageBox.Critical)
            return
        args = [
            "req", "-x509", "-new",
            "-newkey", f"rsa:{self.bits_combo.currentText()}",
            "-sha256", "-days", str(self.days_spin.value()),
            "-keyout", str(key), "-out", str(cert),
            "-passout", "env:D64_CA_PASSWORD", "-subj", self._subject(),
            "-config", str(conf), "-extensions", "v3_ca",
        ]
        ok, out, err = self._openssl_sync(args, password)
        if not ok:
            self._message("Root-CA", err.decode("utf-8", errors="replace") or "Root-CA konnte nicht erzeugt werden.", QMessageBox.Critical)
            return
        metadata = self._ca_metadata(base, "aktiv")
        try:
            self._write_encrypted_metadata(base, metadata, password)
            self._ca_session_passwords[str(base)] = password
            self._register_ca(base)
            page = self.ca_tabs.currentWidget() if hasattr(self, "ca_tabs") else None
            if page is not None:
                page.setProperty("ca_directory", str(base))
                page.setProperty("ca_registered", True)
                self._populate_ca_page(page, metadata)
            self._save_ca_editor_tabs()
            self._refresh_ca_tabs(prompt_selected=False)
            self.append_output(f"Root-CA erzeugt und registriert: {base}")
        except Exception as exc:
            self._message("CA-Metadaten", str(exc), QMessageBox.Critical)

    def _lock_selected_ca(self):
        base = self._selected_ca_base()
        if base is None:
            return
        password = self._ca_password("CA sperren")
        if not password:
            return
        try:
            payload = self._read_encrypted_metadata(self._metadata_path(base), password)
            payload["ca"]["status"] = "gesperrt"
            payload["ca"]["updated_utc"] = datetime.now(timezone.utc).isoformat()
            self._write_encrypted_metadata(base, payload["ca"], password)
            (base / ".d64_ca_locked").write_text("locked\n", encoding="ascii")
            self._refresh_ca_tabs()
            self.append_output(f"CA lokal gesperrt: {base}")
        except Exception as exc:
            self._message("CA sperren", str(exc), QMessageBox.Critical)

    def _delete_selected_ca(self):
        if not hasattr(self, "ca_tabs") or self.ca_tabs.count() <= 0:
            return
        index = self.ca_tabs.currentIndex()
        page = self.ca_tabs.currentWidget()
        if page is None:
            return
        self._bind_active_ca_page(page)
        base_text = self.ca_dir_edit.text().strip()
        label = self.ca_tabs.tabText(index) or "CA"
        answer = QMessageBox.question(
            self, "CA löschen",
            f'Die aktive CA "{label}" wirklich löschen?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        base = Path(base_text) if base_text else None
        registered = bool(base and self._metadata_path(base).exists())
        if registered:
            password = self._ca_password("CA löschen")
            if not password:
                return
            try:
                self._read_encrypted_metadata(self._metadata_path(base), password)
            except Exception as exc:
                self._message("CA löschen", str(exc), QMessageBox.Critical)
                return
            import shutil
            try:
                shutil.rmtree(base)
                self._set_ca_registry([v for v in self._ca_registry() if Path(v) != base])
                self._ca_session_passwords.pop(str(base), None)
                self.append_output(f"CA gelöscht: {base}")
            except Exception as exc:
                self._message("CA löschen", str(exc), QMessageBox.Critical)
                return

        self.ca_tabs.removeTab(index)
        page.deleteLater()
        if self.ca_tabs.count() == 0:
            self._new_ca_tab()
        else:
            self._bind_active_ca_page(self.ca_tabs.currentWidget())
            self._save_ca_editor_tabs()
        self._refresh_user_certificate_ca_choices()


    def _export_selected_ca(self):
        base = self._selected_ca_base()
        if base is None:
            return
        password = self._ca_password("CA exportieren")
        if not password:
            return
        try:
            payload = self._read_encrypted_metadata(self._metadata_path(base), password)
        except Exception as exc:
            self._message("CA exportieren", str(exc), QMessageBox.Critical)
            return
        dialog = QFileDialog(self, "CA exportieren")
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilter("d64 CA Backup (*.json);;JSON (*.json)")
        dialog.selectFile((base.name or "ca") + ".ca.json")
        if not dialog.exec_() or not dialog.selectedFiles():
            return
        target = Path(dialog.selectedFiles()[0])
        if target.suffix.lower() != ".json":
            target = target.with_suffix(".json")
        try:
            self._write_encrypted_metadata(base, payload["ca"], password, include_files=True, target=target)
            self.append_output(f"CA exportiert: {target}")
        except Exception as exc:
            self._message("CA exportieren", str(exc), QMessageBox.Critical)

    def _import_ca(self):
        dialog = QFileDialog(self, "CA importieren")
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("d64 CA Backup (*.json);;JSON (*.json)")
        if not dialog.exec_() or not dialog.selectedFiles():
            return
        source = Path(dialog.selectedFiles()[0])
        password, ok = QInputDialog.getText(self, "CA importieren", "Passwort der CA:", QLineEdit.Password)
        if not ok or not password:
            return
        try:
            payload = self._read_encrypted_metadata(source, password)
        except Exception as exc:
            self._message("CA importieren", str(exc), QMessageBox.Critical)
            return
        directory = QFileDialog.getExistingDirectory(self, "Zielverzeichnis der CA", "", QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog)
        if not directory:
            return
        base = Path(directory)
        try:
            base.mkdir(parents=True, exist_ok=True)
            for rel, encoded in payload.get("files", {}).items():
                if rel not in {"certs/ca.cert.pem", "private/ca.key.pem", "index.txt", "serial", "crlnumber", "crl/ca.crl.pem", "openssl.cnf"}:
                    continue
                target = base / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(base64.b64decode(encoded))
            # Ältere Backups können noch keine openssl.cnf enthalten. Eine
            # fremde/benutzerdefinierte Konfiguration wird dabei nicht ungefragt
            # überschrieben. Nur eine von d64_dism selbst erzeugte Konfiguration
            # wird auf das neue Import-Zielverzeichnis umgeschrieben.
            imported_conf = base / "openssl.cnf"
            rewrite_d64_conf = False
            if imported_conf.is_file():
                try:
                    rewrite_d64_conf = imported_conf.read_text(encoding="utf-8", errors="replace").startswith(
                        "# d64_dism - CA configuration"
                    )
                except OSError:
                    rewrite_d64_conf = False
            self._ensure_ca_openssl_config(base, force=rewrite_d64_conf)
            metadata = dict(payload.get("ca", {}))
            metadata["ca_directory"] = str(base)
            metadata["certificate"] = str(base / "certs" / "ca.cert.pem")
            metadata["private_key"] = str(base / "private" / "ca.key.pem")
            self._write_encrypted_metadata(base, metadata, password)
            self._ca_session_passwords[str(base)] = password
            self._register_ca(base)

            page = self._create_ca_editor_page(metadata, registered=True)
            page._ca_input_fields["password"].setText(password)
            index = self.ca_tabs.addTab(page, "CA")
            self.ca_tabs.setCurrentIndex(index)
            self._bind_active_ca_page(page)
            self._populate_ca_page(page, metadata)
            self._save_ca_editor_tabs()
            self._refresh_user_certificate_ca_choices()
            self.append_output(f"CA importiert: {base}")
        except Exception as exc:
            self._message("CA importieren", str(exc), QMessageBox.Critical)


    def _show_crl(self):
        base_text = self.ca_dir_edit.text().strip()
        if not base_text:
            self._message("CRL", "Bitte zuerst ein CA-Verzeichnis auswählen.", QMessageBox.Warning)
            return
        base = Path(base_text)
        crl = base / "crl" / "ca.crl.pem"
        if not crl.exists():
            self._message("CRL", "Noch keine CRL-Datei vorhanden.", QMessageBox.Information)
            return
        self.run_program(self.openssl_edit.text(), ["crl", "-in", str(crl), "-text", "-noout"], str(base))


    # ------------------------------------------------------------------
    # Stage 162 - Benutzer-Zertifikate / mehrere Zertifikats-Untertabs
    # ------------------------------------------------------------------
    def _default_user_certificate_record(self, index: int = 1) -> dict:
        return {
            "title": f"Benutzer {index}",
            "ca_directory": "",
            "common_name": "",
            "email": "",
            "organization": "",
            "organizational_unit": "",
            "country": "DE",
            "state": "",
            "postal_code": "",
            "locality": "",
            "days": 365,
            "key_bits": "2048",
            "digest": "sha256",
            "usage_preset": "Client-Authentifizierung",
            "key_usage": "digitalSignature, keyEncipherment",
            "extended_key_usage": "clientAuth",
            "subject_alt_name": "",
            "encrypt_private_key": True,
            "output_directory": "",
            "file_base": f"user{index}",
            "private_key": "",
            "csr": "",
            "certificate": "",
        }

    def _user_certificate_records(self) -> list[dict]:
        raw = self.settings.value(self._key("user_certificates"), "[]") or "[]"
        try:
            data = json.loads(str(raw))
            return [item for item in data if isinstance(item, dict)]
        except Exception:
            return []

    def _save_user_certificate_tabs(self) -> None:
        if not hasattr(self, "user_certificate_tabs"):
            return
        records = []
        for index in range(self.user_certificate_tabs.count()):
            page = self.user_certificate_tabs.widget(index)
            if page is not None:
                records.append(self._user_certificate_record_from_page(page))
        self.settings.setValue(
            self._key("user_certificates"),
            json.dumps(records, ensure_ascii=False),
        )
        self.settings.sync()

    def _load_user_certificate_tabs(self) -> None:
        if not hasattr(self, "user_certificate_tabs"):
            return
        self.user_certificate_tabs.clear()
        records = self._user_certificate_records()
        if not records:
            records = [self._default_user_certificate_record(1)]
        for record in records:
            self._create_user_certificate_page(record)
        self._update_user_certificate_tabs_height()
        self._save_user_certificate_tabs()

    # ------------------------------------------------------------------
    # Stage 163 - bereits ausgestellte Benutzer-Zertifikate
    # ------------------------------------------------------------------
    def _issued_user_certificate_records(self) -> list[dict]:
        raw = self.settings.value(self._key("issued_user_certificates"), "[]") or "[]"
        try:
            data = json.loads(str(raw))
            return [item for item in data if isinstance(item, dict)]
        except Exception:
            return []

    def _save_issued_user_certificate_records(self, records: list[dict]) -> None:
        self.settings.setValue(
            self._key("issued_user_certificates"),
            json.dumps(records, ensure_ascii=False),
        )
        self.settings.sync()

    @staticmethod
    def _certificate_path_key(value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        try:
            return os.path.normcase(os.path.abspath(text))
        except Exception:
            return text

    def _migrate_issued_user_certificate_records(self) -> None:
        """Stage-162 Zertifikate beim ersten Start in das neue Register übernehmen."""
        records = self._issued_user_certificate_records()
        known = {
            self._certificate_path_key(item.get("certificate", ""))
            for item in records
            if item.get("certificate")
        }
        changed = False
        for profile in self._user_certificate_records():
            cert_text = str(profile.get("certificate", "") or "").strip()
            if not cert_text or not Path(cert_text).is_file():
                continue
            key = self._certificate_path_key(cert_text)
            if not key or key in known:
                continue
            try:
                issued_at = datetime.fromtimestamp(
                    Path(cert_text).stat().st_mtime, timezone.utc
                ).isoformat()
            except OSError:
                issued_at = ""
            records.append({
                "title": str(profile.get("title", "") or ""),
                "common_name": str(profile.get("common_name", "") or ""),
                "email": str(profile.get("email", "") or ""),
                "organization": str(profile.get("organization", "") or ""),
                "organizational_unit": str(profile.get("organizational_unit", "") or ""),
                "ca_directory": str(profile.get("ca_directory", "") or ""),
                "certificate": cert_text,
                "csr": str(profile.get("csr", "") or ""),
                "private_key": str(profile.get("private_key", "") or ""),
                "issued_at": issued_at,
            })
            known.add(key)
            changed = True
        if changed:
            self._save_issued_user_certificate_records(records)

    def _register_issued_user_certificate(self, page: QWidget) -> None:
        record = self._user_certificate_record_from_page(page)
        cert_text = str(record.get("certificate", "") or "").strip()
        if not cert_text:
            return

        issued = {
            "title": str(record.get("title", "") or ""),
            "common_name": str(record.get("common_name", "") or ""),
            "email": str(record.get("email", "") or ""),
            "organization": str(record.get("organization", "") or ""),
            "organizational_unit": str(record.get("organizational_unit", "") or ""),
            "ca_directory": str(record.get("ca_directory", "") or ""),
            "certificate": cert_text,
            "csr": str(record.get("csr", "") or ""),
            "private_key": str(record.get("private_key", "") or ""),
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }

        records = self._issued_user_certificate_records()
        wanted = self._certificate_path_key(cert_text)
        replaced = False
        for index, old in enumerate(records):
            if self._certificate_path_key(old.get("certificate", "")) == wanted:
                records[index] = issued
                replaced = True
                break
        if not replaced:
            records.append(issued)
        self._save_issued_user_certificate_records(records)
        self._refresh_issued_user_certificate_tabs(select_certificate=cert_text)

    def _refresh_issued_user_certificate_tabs(self, select_certificate: str = "") -> None:
        if not hasattr(self, "issued_user_certificate_tabs"):
            return

        selected = self._certificate_path_key(select_certificate)
        if not selected:
            current = self.issued_user_certificate_tabs.currentWidget()
            current_record = getattr(current, "_issued_certificate_record", {}) if current is not None else {}
            selected = self._certificate_path_key(current_record.get("certificate", ""))

        self.issued_user_certificate_tabs.clear()
        select_index = -1
        for record in self._issued_user_certificate_records():
            cert_text = str(record.get("certificate", "") or "").strip()
            if not cert_text or not Path(cert_text).is_file():
                # "zur Verfügung stehend" bedeutet: Zertifikatsdatei ist noch vorhanden.
                continue
            page = self._create_issued_user_certificate_page(record)
            index = self.issued_user_certificate_tabs.indexOf(page)
            if self._certificate_path_key(cert_text) == selected:
                select_index = index

        if select_index >= 0:
            self.issued_user_certificate_tabs.setCurrentIndex(select_index)

    def _create_issued_user_certificate_page(self, record: dict) -> QWidget:
        page = QWidget(self.issued_user_certificate_tabs)
        page._issued_certificate_record = dict(record)
        outer = QVBoxLayout(page)
        outer.setContentsMargins(6, 6, 6, 6)

        form = QFormLayout()
        def ro(value: str) -> QLineEdit:
            edit = QLineEdit(str(value or ""), page)
            edit.setReadOnly(True)
            return edit

        certificate = str(record.get("certificate", "") or "")
        ca_directory = str(record.get("ca_directory", "") or "")
        issued_at = str(record.get("issued_at", "") or "")
        if issued_at:
            issued_at = issued_at.replace("T", " ").replace("+00:00", " UTC")

        form.addRow("Common Name / Benutzer", ro(record.get("common_name", "")))
        form.addRow("E-Mail", ro(record.get("email", "")))
        form.addRow("Organisation", ro(record.get("organization", "")))
        form.addRow("Organisationseinheit", ro(record.get("organizational_unit", "")))
        form.addRow("Ausstellende CA", ro(ca_directory))
        form.addRow("Ausgestellt", ro(issued_at))
        form.addRow("Zertifikat", ro(certificate))
        form.addRow("CSR", ro(record.get("csr", "")))
        form.addRow("Private Key", ro(record.get("private_key", "")))
        outer.addLayout(form)

        buttons = QHBoxLayout()
        inspect_button = QPushButton("Zertifikat anzeigen", page)
        inspect_button.setObjectName("opensslIssuedCertificateInspectButton")
        # Absichtlich an die konkrete Tab-Seite gebunden, nicht an einen Index.
        inspect_button.clicked.connect(
            lambda _checked=False, p=page: self._inspect_issued_user_certificate_page(p)
        )
        buttons.addWidget(inspect_button)
        buttons.addStretch(1)
        outer.addLayout(buttons)

        title = (
            str(record.get("common_name", "") or "").strip()
            or str(record.get("title", "") or "").strip()
            or Path(certificate).stem
            or "Zertifikat"
        )
        self.issued_user_certificate_tabs.addTab(page, title)
        return page

    def _select_issued_user_certificate(self, certificate: str) -> bool:
        if not hasattr(self, "issued_user_certificate_tabs"):
            return False
        wanted = self._certificate_path_key(certificate)
        if not wanted:
            return False
        for index in range(self.issued_user_certificate_tabs.count()):
            page = self.issued_user_certificate_tabs.widget(index)
            record = getattr(page, "_issued_certificate_record", {})
            if self._certificate_path_key(record.get("certificate", "")) == wanted:
                self.issued_user_certificate_tabs.setCurrentIndex(index)
                return True
        return False

    def _inspect_issued_user_certificate_page(self, page: QWidget) -> None:
        record = getattr(page, "_issued_certificate_record", {})
        path = str(record.get("certificate", "") or "").strip()
        if not path:
            return
        if not Path(path).is_file():
            self._message(
                "Benutzer-Zertifikat",
                "Die Zertifikatsdatei ist nicht mehr verfügbar.\n\n" + path,
                QMessageBox.Warning,
            )
            self._refresh_issued_user_certificate_tabs()
            return
        self.run_program(self.openssl_edit.text(), ["x509", "-in", path, "-text", "-noout"])

    def _inspect_current_issued_user_certificate(self) -> None:
        if not hasattr(self, "issued_user_certificate_tabs"):
            return
        page = self.issued_user_certificate_tabs.currentWidget()
        if page is not None:
            self._inspect_issued_user_certificate_page(page)

    def _add_user_certificate_tab(self) -> None:
        index = self.user_certificate_tabs.count() + 1
        page = self._create_user_certificate_page(self._default_user_certificate_record(index))
        self.user_certificate_tabs.setCurrentWidget(page)
        self._save_user_certificate_tabs()

    def _delete_user_certificate_tab(self) -> None:
        index = self.user_certificate_tabs.currentIndex()
        if index < 0:
            return
        title = self.user_certificate_tabs.tabText(index)
        answer = QMessageBox.question(
            self,
            "Zertifikats-Untertab löschen",
            f'Den Untertab "{title}" wirklich aus der Konfiguration löschen?\\n\\n'
            "Bereits erzeugte Zertifikatsdateien bleiben auf dem Datenträger erhalten.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        widget = self.user_certificate_tabs.widget(index)
        self.user_certificate_tabs.removeTab(index)
        if widget is not None:
            widget.deleteLater()
        if self.user_certificate_tabs.count() == 0:
            self._create_user_certificate_page(self._default_user_certificate_record(1))
        self._save_user_certificate_tabs()

    def _create_user_certificate_page(self, record: dict) -> QWidget:
        page = QWidget(self.user_certificate_tabs)
        outer = QVBoxLayout(page)
        outer.setContentsMargins(6, 6, 6, 6)

        # Stage 165: Nur die äußere ScrollArea des gesamten Zertifikate-Tabs
        # scrollt. Die Benutzer-Zertifikat-Untertabs enthalten keine eigene
        # ScrollArea mehr und bilden damit zusammen mit den übrigen Bereichen
        # eine einzige durchgängige Scroll-Fläche.
        body = page
        body_layout = outer

        subject_group = QGroupBox("Benutzer / Subject", body)
        subject_form = QFormLayout(subject_group)

        title_edit = QLineEdit(str(record.get("title", "Benutzer")), subject_group)
        title_edit.setObjectName("opensslUserCertificateTitleEdit")
        cn_edit = QLineEdit(str(record.get("common_name", "")), subject_group)
        cn_edit.setObjectName("opensslUserCertificateCommonNameEdit")
        email_edit = QLineEdit(str(record.get("email", "")), subject_group)
        email_edit.setObjectName("opensslUserCertificateEmailEdit")
        org_edit = QLineEdit(str(record.get("organization", "")), subject_group)
        ou_edit = QLineEdit(str(record.get("organizational_unit", "")), subject_group)

        country_combo = QComboBox(subject_group)
        for code, name in CA_COUNTRY_CODES:
            country_combo.addItem(f"{code} – {name}", code)
        country = str(record.get("country", "DE") or "DE").upper()
        country_index = country_combo.findData(country)
        country_combo.setCurrentIndex(country_index if country_index >= 0 else country_combo.findData("DE"))

        state_edit = QLineEdit(str(record.get("state", "")), subject_group)
        postal_edit = QLineEdit(str(record.get("postal_code", ""))[:11], subject_group)
        postal_edit.setMaxLength(11)
        postal_edit.setPlaceholderText("PLZ")
        locality_edit = QLineEdit(str(record.get("locality", ""))[:32], subject_group)
        locality_edit.setMaxLength(32)
        locality_edit.setPlaceholderText("Ort")
        locality_row = QWidget(subject_group)
        locality_layout = QHBoxLayout(locality_row)
        locality_layout.setContentsMargins(0, 0, 0, 0)
        locality_layout.setSpacing(6)
        locality_layout.addWidget(postal_edit, 1)
        locality_layout.addWidget(locality_edit, 2)

        san_edit = QLineEdit(str(record.get("subject_alt_name", "")), subject_group)
        san_edit.setPlaceholderText("z.B. email:max@example.de, DNS:pc01.local, URI:https://...")

        subject_form.addRow("Untertab / Bezeichnung", title_edit)
        subject_form.addRow("Common Name / Benutzer", cn_edit)
        subject_form.addRow("E-Mail", email_edit)
        subject_form.addRow("Organisation", org_edit)
        subject_form.addRow("Organisationseinheit", ou_edit)
        subject_form.addRow("Land", country_combo)
        subject_form.addRow("Bundesland / Kanton / Bundesstaat", state_edit)
        subject_form.addRow("PLZ / Ort", locality_row)
        subject_form.addRow("Subject Alternative Name", san_edit)
        body_layout.addWidget(subject_group)

        issuer_group = QGroupBox("Aussteller und Zertifikatsparameter", body)
        issuer_form = QFormLayout(issuer_group)
        ca_combo = QComboBox(issuer_group)
        ca_combo.setObjectName("opensslUserCertificateCaCombo")
        self._populate_user_certificate_ca_combo(ca_combo, str(record.get("ca_directory", "")))

        days_spin = QSpinBox(issuer_group)
        days_spin.setRange(1, 36500)
        days_spin.setValue(int(record.get("days", 365) or 365))
        key_bits = QComboBox(issuer_group)
        key_bits.addItems(["2048", "3072", "4096"])
        key_bits.setCurrentText(str(record.get("key_bits", "2048")))
        digest_combo = QComboBox(issuer_group)
        digest_combo.addItems(["sha256", "sha384", "sha512"])
        digest_combo.setCurrentText(str(record.get("digest", "sha256")))

        usage_combo = QComboBox(issuer_group)
        usage_combo.addItems([
            "Client-Authentifizierung",
            "E-Mail-Signatur",
            "Client + E-Mail",
            "Benutzerdefiniert",
        ])
        usage_combo.setCurrentText(str(record.get("usage_preset", "Client-Authentifizierung")))
        key_usage_edit = QLineEdit(str(record.get("key_usage", "digitalSignature, keyEncipherment")), issuer_group)
        key_usage_edit.setPlaceholderText("digitalSignature, keyEncipherment")
        eku_edit = QLineEdit(str(record.get("extended_key_usage", "clientAuth")), issuer_group)
        eku_edit.setPlaceholderText("clientAuth, emailProtection")
        encrypt_key = QCheckBox("Privaten Schlüssel mit Passwort verschlüsseln", issuer_group)
        encrypt_key.setChecked(bool(record.get("encrypt_private_key", True)))
        key_password = QLineEdit(issuer_group)
        key_password.setEchoMode(QLineEdit.Password)
        key_password.setPlaceholderText("wird nicht gespeichert")

        issuer_form.addRow("Ausstellende CA", ca_combo)
        issuer_form.addRow("Gültigkeit (Tage)", days_spin)
        issuer_form.addRow("RSA-Schlüssel", key_bits)
        issuer_form.addRow("Signatur-Hash", digest_combo)
        issuer_form.addRow("Verwendungsprofil", usage_combo)
        issuer_form.addRow("Key Usage", key_usage_edit)
        issuer_form.addRow("Extended Key Usage", eku_edit)
        issuer_form.addRow("Private Key", encrypt_key)
        issuer_form.addRow("Key-Passwort", key_password)
        body_layout.addWidget(issuer_group)

        output_group = QGroupBox("Ausgabedateien", body)
        output_form = QFormLayout(output_group)
        output_dir_edit = QLineEdit(str(record.get("output_directory", "")), output_group)
        output_dir_button = QPushButton("...", output_group)
        output_dir_button.setMaximumWidth(36)
        output_dir_row = QWidget(output_group)
        output_dir_layout = QHBoxLayout(output_dir_row)
        output_dir_layout.setContentsMargins(0, 0, 0, 0)
        output_dir_layout.addWidget(output_dir_edit, 1)
        output_dir_layout.addWidget(output_dir_button)

        file_base_edit = QLineEdit(str(record.get("file_base", "user")), output_group)
        file_base_edit.setPlaceholderText("z.B. max.mustermann")
        private_key_edit = QLineEdit(str(record.get("private_key", "")), output_group)
        csr_edit = QLineEdit(str(record.get("csr", "")), output_group)
        certificate_edit = QLineEdit(str(record.get("certificate", "")), output_group)
        for field in (private_key_edit, csr_edit, certificate_edit):
            field.setReadOnly(True)

        output_form.addRow("Ausgabeverzeichnis", output_dir_row)
        output_form.addRow("Dateibasis", file_base_edit)
        output_form.addRow("Private Key", private_key_edit)
        output_form.addRow("CSR", csr_edit)
        output_form.addRow("Zertifikat", certificate_edit)
        body_layout.addWidget(output_group)

        buttons = QHBoxLayout()
        issue_button = QPushButton("Zertifikat ausstellen", page)
        issue_button.setObjectName("opensslIssueUserCertificateButton")
        issue_button.clicked.connect(lambda _checked=False, p=page: self._issue_user_certificate(p))
        buttons.addWidget(issue_button)
        inspect_cert = QPushButton("Zertifikat anzeigen", page)
        inspect_cert.clicked.connect(lambda _checked=False, p=page: self._inspect_user_certificate_page(p))
        buttons.addWidget(inspect_cert)
        inspect_csr = QPushButton("CSR anzeigen", page)
        inspect_csr.clicked.connect(lambda _checked=False, p=page: self._inspect_user_csr_page(p))
        buttons.addWidget(inspect_csr)
        buttons.addStretch(1)
        outer.addLayout(buttons)

        page._cert_fields = {
            "title": title_edit,
            "ca_directory": ca_combo,
            "common_name": cn_edit,
            "email": email_edit,
            "organization": org_edit,
            "organizational_unit": ou_edit,
            "country": country_combo,
            "state": state_edit,
            "postal_code": postal_edit,
            "locality": locality_edit,
            "subject_alt_name": san_edit,
            "days": days_spin,
            "key_bits": key_bits,
            "digest": digest_combo,
            "usage_preset": usage_combo,
            "key_usage": key_usage_edit,
            "extended_key_usage": eku_edit,
            "encrypt_private_key": encrypt_key,
            "key_password": key_password,
            "output_directory": output_dir_edit,
            "file_base": file_base_edit,
            "private_key": private_key_edit,
            "csr": csr_edit,
            "certificate": certificate_edit,
        }

        title_edit.editingFinished.connect(lambda p=page: self._user_certificate_title_changed(p))
        output_dir_button.clicked.connect(lambda _checked=False, p=page: self._choose_user_certificate_output_directory(p))
        output_dir_edit.editingFinished.connect(lambda p=page: self._user_certificate_paths_changed(p))
        file_base_edit.editingFinished.connect(lambda p=page: self._user_certificate_paths_changed(p))
        usage_combo.currentTextChanged.connect(lambda value, p=page: self._apply_user_certificate_usage_preset(p, value))

        for edit in (cn_edit, email_edit, org_edit, ou_edit, state_edit, postal_edit, locality_edit, san_edit, key_usage_edit, eku_edit):
            edit.editingFinished.connect(self._save_user_certificate_tabs)
        for combo in (ca_combo, country_combo, key_bits, digest_combo):
            combo.currentIndexChanged.connect(self._save_user_certificate_tabs)
        days_spin.valueChanged.connect(self._save_user_certificate_tabs)
        encrypt_key.toggled.connect(self._save_user_certificate_tabs)

        tab_title = title_edit.text().strip() or cn_edit.text().strip() or "Benutzer-Zertifikat"
        self.user_certificate_tabs.addTab(page, tab_title)
        if not private_key_edit.text().strip() and output_dir_edit.text().strip():
            self._update_user_certificate_paths(page)
        self._update_user_certificate_tabs_height()
        return page

    def _update_user_certificate_tabs_height(self) -> None:
        """Höhe des aktuellen Formular-Tabs anpassen; gescrollt wird nur außen."""
        tabs = getattr(self, "user_certificate_tabs", None)
        if tabs is None or tabs.count() <= 0:
            return
        page = tabs.currentWidget()
        if page is None:
            return
        page.adjustSize()
        hint = page.sizeHint().height()
        tab_bar_height = tabs.tabBar().sizeHint().height()
        tabs.setMinimumHeight(max(620, hint + tab_bar_height + 24))

    def _populate_user_certificate_ca_combo(self, combo: QComboBox, selected: str = "") -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("<CA auswählen>", "")
        for base_text in self._ca_registry():
            base = Path(base_text)
            suffix = " (gesperrt)" if (base / ".d64_ca_locked").exists() else ""
            combo.addItem((base.name or str(base)) + suffix, str(base))
        if selected:
            index = combo.findData(str(Path(selected)))
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def _refresh_user_certificate_ca_choices(self) -> None:
        if not hasattr(self, "user_certificate_tabs"):
            return
        for index in range(self.user_certificate_tabs.count()):
            page = self.user_certificate_tabs.widget(index)
            fields = getattr(page, "_cert_fields", {})
            combo = fields.get("ca_directory")
            if combo is None:
                continue
            selected = str(combo.currentData() or "")
            self._populate_user_certificate_ca_combo(combo, selected)

    def _user_certificate_record_from_page(self, page: QWidget) -> dict:
        fields = getattr(page, "_cert_fields", {})
        def text(name: str) -> str:
            widget = fields.get(name)
            return widget.text().strip() if widget is not None else ""
        ca_combo = fields.get("ca_directory")
        country_combo = fields.get("country")
        return {
            "title": text("title"),
            "ca_directory": str(ca_combo.currentData() or "") if ca_combo is not None else "",
            "common_name": text("common_name"),
            "email": text("email"),
            "organization": text("organization"),
            "organizational_unit": text("organizational_unit"),
            "country": str(country_combo.currentData() or "") if country_combo is not None else "",
            "state": text("state"),
            "postal_code": text("postal_code")[:11],
            "locality": text("locality")[:32],
            "days": int(fields["days"].value()) if fields.get("days") is not None else 365,
            "key_bits": fields["key_bits"].currentText() if fields.get("key_bits") is not None else "2048",
            "digest": fields["digest"].currentText() if fields.get("digest") is not None else "sha256",
            "usage_preset": fields["usage_preset"].currentText() if fields.get("usage_preset") is not None else "Client-Authentifizierung",
            "key_usage": text("key_usage"),
            "extended_key_usage": text("extended_key_usage"),
            "subject_alt_name": text("subject_alt_name"),
            "encrypt_private_key": bool(fields["encrypt_private_key"].isChecked()) if fields.get("encrypt_private_key") is not None else True,
            # key_password is deliberately NOT persisted.
            "output_directory": text("output_directory"),
            "file_base": text("file_base"),
            "private_key": text("private_key"),
            "csr": text("csr"),
            "certificate": text("certificate"),
        }

    def _user_certificate_title_changed(self, page: QWidget) -> None:
        fields = getattr(page, "_cert_fields", {})
        title = fields.get("title").text().strip() if fields.get("title") is not None else ""
        if not title and fields.get("common_name") is not None:
            title = fields["common_name"].text().strip()
        index = self.user_certificate_tabs.indexOf(page)
        if index >= 0:
            self.user_certificate_tabs.setTabText(index, title or "Benutzer-Zertifikat")
        self._save_user_certificate_tabs()

    @staticmethod
    def _safe_user_certificate_file_base(value: str) -> str:
        value = value.strip()
        safe = "".join(ch if (ch.isalnum() or ch in "-_.") else "_" for ch in value)
        return safe.strip("._") or "user"

    def _update_user_certificate_paths(self, page: QWidget) -> None:
        fields = getattr(page, "_cert_fields", {})
        output_dir = fields.get("output_directory").text().strip() if fields.get("output_directory") is not None else ""
        file_base = self._safe_user_certificate_file_base(fields.get("file_base").text() if fields.get("file_base") is not None else "user")
        if fields.get("file_base") is not None:
            fields["file_base"].setText(file_base)
        if not output_dir:
            return
        base = Path(output_dir)
        fields["private_key"].setText(str(base / f"{file_base}.key.pem"))
        fields["csr"].setText(str(base / f"{file_base}.csr.pem"))
        fields["certificate"].setText(str(base / f"{file_base}.cert.pem"))

    def _user_certificate_paths_changed(self, page: QWidget) -> None:
        self._update_user_certificate_paths(page)
        self._save_user_certificate_tabs()

    def _choose_user_certificate_output_directory(self, page: QWidget) -> None:
        fields = getattr(page, "_cert_fields", {})
        current = fields.get("output_directory").text().strip() if fields.get("output_directory") is not None else ""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Ausgabeverzeichnis für Benutzer-Zertifikat",
            current,
            QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog,
        )
        if directory:
            fields["output_directory"].setText(directory)
            self._user_certificate_paths_changed(page)

    def _apply_user_certificate_usage_preset(self, page: QWidget, preset: str) -> None:
        fields = getattr(page, "_cert_fields", {})
        values = {
            "Client-Authentifizierung": ("digitalSignature, keyEncipherment", "clientAuth"),
            "E-Mail-Signatur": ("digitalSignature, nonRepudiation, keyEncipherment", "emailProtection"),
            "Client + E-Mail": ("digitalSignature, keyEncipherment", "clientAuth, emailProtection"),
        }
        if preset in values:
            key_usage, eku = values[preset]
            fields["key_usage"].setText(key_usage)
            fields["extended_key_usage"].setText(eku)
        self._save_user_certificate_tabs()

    @staticmethod
    def _normalize_user_certificate_san(value: str, email: str = "") -> str:
        parts = []
        raw_parts = [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]
        if not raw_parts and email:
            raw_parts = [f"email:{email}"]
        for item in raw_parts:
            if ":" not in item:
                item = ("email:" if "@" in item else "DNS:") + item
            parts.append(item)
        return ",".join(parts)

    def _user_certificate_subject(self, page: QWidget) -> str:
        fields = getattr(page, "_cert_fields", {})
        country_combo = fields.get("country")
        country = str(country_combo.currentData() or "") if country_combo is not None else ""
        values = (
            ("C", country),
            ("ST", fields["state"].text().strip()),
            ("postalCode", fields["postal_code"].text().strip()),
            ("L", fields["locality"].text().strip()),
            ("O", fields["organization"].text().strip()),
            ("OU", fields["organizational_unit"].text().strip()),
            ("CN", fields["common_name"].text().strip()),
            ("emailAddress", fields["email"].text().strip()),
        )
        return "".join(f"/{key}={value.replace('/', '_')}" for key, value in values if value)

    def _openssl_sync_env(self, args: list[str], extra_env: Optional[dict[str, str]] = None) -> tuple[bool, bytes, bytes]:
        program = self.openssl_edit.text().strip() or "openssl.exe"
        env = os.environ.copy()
        if extra_env:
            env.update({str(k): str(v) for k, v in extra_env.items()})
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            result = subprocess.run(
                [program] + list(args),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=flags,
                check=False,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as exc:
            return False, b"", str(exc).encode("utf-8", errors="replace")

    def _issue_user_certificate(self, page: QWidget) -> None:
        fields = getattr(page, "_cert_fields", {})
        common_name = fields["common_name"].text().strip()
        if not common_name:
            self._message("Benutzer-Zertifikat", "Bitte einen Common Name / Benutzer angeben.", QMessageBox.Warning)
            return

        ca_text = str(fields["ca_directory"].currentData() or "").strip()
        if not ca_text:
            self._message("Benutzer-Zertifikat", "Bitte eine ausstellende CA auswählen.", QMessageBox.Warning)
            return
        ca_base = Path(ca_text)
        if (ca_base / ".d64_ca_locked").exists():
            self._message("Benutzer-Zertifikat", "Die ausgewählte CA ist lokal gesperrt.", QMessageBox.Warning)
            return
        ca_cert = ca_base / "certs" / "ca.cert.pem"
        ca_key = ca_base / "private" / "ca.key.pem"
        if not ca_cert.is_file() or not ca_key.is_file():
            self._message("Benutzer-Zertifikat", "CA-Zertifikat oder privater CA-Schlüssel fehlt.", QMessageBox.Critical)
            return

        output_dir = fields["output_directory"].text().strip()
        if not output_dir:
            self._message("Benutzer-Zertifikat", "Bitte ein Ausgabeverzeichnis auswählen.", QMessageBox.Warning)
            return
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self._update_user_certificate_paths(page)
        key_path = Path(fields["private_key"].text())
        csr_path = Path(fields["csr"].text())
        cert_path = Path(fields["certificate"].text())

        ca_password = self._ca_session_passwords.get(str(ca_base), "")
        if not ca_password and self.ca_dir_edit.text().strip() == str(ca_base):
            ca_password = self.ca_password_edit.text()
        if not ca_password:
            ca_password, ok = QInputDialog.getText(
                self, "Benutzer-Zertifikat", f"Passwort der CA {ca_base.name or ca_base}:", QLineEdit.Password
            )
            if not ok or not ca_password:
                return
        try:
            self._read_encrypted_metadata(self._metadata_path(ca_base), ca_password)
            self._ca_session_passwords[str(ca_base)] = ca_password
        except Exception as exc:
            self._message("Benutzer-Zertifikat", str(exc), QMessageBox.Critical)
            return

        encrypt_key = fields["encrypt_private_key"].isChecked()
        key_password = fields["key_password"].text()
        if encrypt_key and not key_password:
            self._message(
                "Benutzer-Zertifikat",
                "Für den verschlüsselten privaten Benutzerschlüssel ist ein Key-Passwort erforderlich.",
                QMessageBox.Warning,
            )
            return

        env = {"D64_CA_PASSWORD": ca_password}
        if key_password:
            env["D64_CERT_KEY_PASSWORD"] = key_password

        key_args = ["genrsa"]
        if encrypt_key:
            key_args += ["-aes256", "-passout", "env:D64_CERT_KEY_PASSWORD"]
        key_args += ["-out", str(key_path), fields["key_bits"].currentText()]
        ok, out, err = self._openssl_sync_env(key_args, env)
        if not ok:
            self._message("Benutzer-Zertifikat", err.decode("utf-8", errors="replace") or "Privater Schlüssel konnte nicht erzeugt werden.", QMessageBox.Critical)
            return

        subject = self._user_certificate_subject(page)
        csr_args = ["req", "-new", "-key", str(key_path)]
        if encrypt_key:
            csr_args += ["-passin", "env:D64_CERT_KEY_PASSWORD"]
        csr_args += ["-out", str(csr_path), "-subj", subject]
        ok, out, err = self._openssl_sync_env(csr_args, env)
        if not ok:
            self._message("Benutzer-Zertifikat", err.decode("utf-8", errors="replace") or "CSR konnte nicht erzeugt werden.", QMessageBox.Critical)
            return

        key_usage = fields["key_usage"].text().strip()
        eku = fields["extended_key_usage"].text().strip()
        san = self._normalize_user_certificate_san(fields["subject_alt_name"].text(), fields["email"].text().strip())
        ext_path = Path(output_dir) / ("." + self._safe_user_certificate_file_base(fields["file_base"].text()) + ".extensions.cnf")
        ext_lines = [
            "[user_certificate]",
            "basicConstraints=critical,CA:FALSE",
            "subjectKeyIdentifier=hash",
            "authorityKeyIdentifier=keyid,issuer",
        ]
        if key_usage:
            ext_lines.append("keyUsage=critical," + key_usage)
        if eku:
            ext_lines.append("extendedKeyUsage=" + eku)
        if san:
            ext_lines.append("subjectAltName=" + san)
        ext_path.write_text("\\n".join(ext_lines) + "\\n", encoding="utf-8")

        digest = fields["digest"].currentText().strip() or "sha256"
        sign_args = [
            "x509", "-req", "-in", str(csr_path),
            "-CA", str(ca_cert), "-CAkey", str(ca_key),
            "-passin", "env:D64_CA_PASSWORD",
            "-CAserial", str(ca_base / "ca.srl"), "-CAcreateserial",
            "-out", str(cert_path), "-days", str(fields["days"].value()),
            f"-{digest}", "-extfile", str(ext_path), "-extensions", "user_certificate",
        ]
        try:
            ok, out, err = self._openssl_sync_env(sign_args, env)
        finally:
            try:
                ext_path.unlink()
            except OSError:
                pass
        if not ok:
            self._message("Benutzer-Zertifikat", err.decode("utf-8", errors="replace") or "Zertifikat konnte nicht signiert werden.", QMessageBox.Critical)
            return

        self._save_user_certificate_tabs()
        self._register_issued_user_certificate(page)
        self.append_output(f"Benutzer-Zertifikat ausgestellt: {cert_path}")
        self.append_output(f"CSR: {csr_path}")
        self.append_output(f"Private Key: {key_path}")
        self._message(
            "Benutzer-Zertifikat",
            "Zertifikat wurde erfolgreich ausgestellt.\\n\\n" + str(cert_path),
            QMessageBox.Information,
        )

    def _inspect_user_certificate_page(self, page: QWidget) -> None:
        fields = getattr(page, "_cert_fields", {})
        path = fields.get("certificate").text().strip() if fields.get("certificate") is not None else ""
        if not path:
            return
        # Ist das Zertifikat unten als ausgestelltes Zertifikat geöffnet, wird genau
        # dieser Tab aktiviert und dessen gebundene Anzeige-Aktion verwendet.
        if self._select_issued_user_certificate(path):
            self._inspect_current_issued_user_certificate()
            return
        if Path(path).is_file():
            self.run_program(self.openssl_edit.text(), ["x509", "-in", path, "-text", "-noout"])

    def _inspect_user_csr_page(self, page: QWidget) -> None:
        fields = getattr(page, "_cert_fields", {})
        path = fields.get("csr").text().strip() if fields.get("csr") is not None else ""
        if path:
            self.run_program(self.openssl_edit.text(), ["req", "-in", path, "-text", "-noout"])

    def _inspect_certificate(self):
        page = self.user_certificate_tabs.currentWidget() if hasattr(self, "user_certificate_tabs") else None
        if page is not None:
            self._inspect_user_certificate_page(page)

    def _inspect_csr(self):
        page = self.user_certificate_tabs.currentWidget() if hasattr(self, "user_certificate_tabs") else None
        if page is not None:
            self._inspect_user_csr_page(page)



class ApacheDownloadThread(QThread):
    """Download and safely unpack an Apache package without blocking Qt."""

    completed = pyqtSignal(bool, str, bool, str)

    def __init__(self, url: str, target_dir: str, parent=None):
        super().__init__(parent)
        self.url = str(url)
        self.target_dir = str(target_dir)

    @staticmethod
    def _safe_extract_zip(archive: Path, target_dir: Path) -> None:
        target_root = target_dir.resolve()
        with zipfile.ZipFile(str(archive), "r") as zf:
            for member in zf.infolist():
                member_path = (target_dir / member.filename).resolve()
                try:
                    member_path.relative_to(target_root)
                except ValueError as exc:
                    raise RuntimeError("Unsicherer Pfad im ZIP-Archiv: " + member.filename) from exc
            zf.extractall(str(target_dir))

    def run(self):
        partial = None
        destination = None
        try:
            target_dir = Path(self.target_dir).expanduser()
            target_dir.mkdir(parents=True, exist_ok=True)

            # Use a normal Windows browser User-Agent.  The package source is
            # the user-controlled kallup.net mirror; Stage 173 validation still
            # rejects HTML/error responses and invalid ZIP archives explicitly.
            request = urllib.request.Request(
                self.url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/153.0.0.0 Safari/537.36"
                    ),
                    "Accept": "application/zip,application/octet-stream,*/*;q=0.8",
                    "Accept-Encoding": "identity",
                    "Referer": APACHE_DOWNLOAD_BASE_URL,
                    "X-d64-dism-Agent": "d64_dism Apache Downloader/1.0",
                },
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                final_url = response.geturl() or self.url
                status = int(getattr(response, "status", 200) or 200)
                content_type = str(response.headers.get("Content-Type", "")).strip()
                content_length = str(response.headers.get("Content-Length", "")).strip()

                if status < 200 or status >= 300:
                    raise RuntimeError(f"HTTP-Fehler {status} beim Apache-Download.")

                filename = Path(urllib.parse.urlparse(final_url).path).name
                if not filename:
                    filename = "apache-download.bin"
                destination = target_dir / filename
                partial = target_dir / (filename + ".part")

                expected_zip = (
                    urllib.parse.urlparse(self.url).path.lower().endswith(".zip")
                    or urllib.parse.urlparse(final_url).path.lower().endswith(".zip")
                    or filename.lower().endswith(".zip")
                )

                # A text/html response is never a valid Apache ZIP package.  Fail
                # before it can be mistaken for an installer archive.
                lower_content_type = content_type.lower()
                if expected_zip and (
                    lower_content_type.startswith("text/")
                    or "text/html" in lower_content_type
                    or "application/json" in lower_content_type
                ):
                    raise RuntimeError(
                        "Der Server hat keine ZIP-Datei geliefert, sondern "
                        f"'{content_type or 'unbekannter Content-Type'}'.\n"
                        f"Quelle: {final_url}\n"
                        f"Content-Length: {content_length or 'unbekannt'} Bytes"
                    )

                with open(partial, "wb") as out:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        out.write(chunk)
                os.replace(str(partial), str(destination))
                partial = None

            file_size = destination.stat().st_size
            expected_zip = destination.suffix.lower() == ".zip"

            if expected_zip:
                # A real Apache HTTP Server binary archive is many megabytes.  A
                # few-kilobyte response is typically an HTML error page or access
                # notice saved under the .zip filename.
                if file_size < 1024 * 1024:
                    destination.unlink(missing_ok=True)
                    raise RuntimeError(
                        "Die heruntergeladene Apache-ZIP-Datei ist ungewöhnlich klein "
                        f"({file_size} Bytes). Sie wurde verworfen.\n"
                        "Vermutlich wurde statt des ZIP-Archivs eine Fehler- oder HTML-Seite geliefert.\n"
                        f"Quelle: {self.url}"
                    )

                if not zipfile.is_zipfile(str(destination)):
                    try:
                        with open(destination, "rb") as fh:
                            signature = fh.read(16).hex(" ")
                    except Exception:
                        signature = "nicht lesbar"
                    destination.unlink(missing_ok=True)
                    raise RuntimeError(
                        "Die heruntergeladene Datei ist kein gültiges ZIP-Archiv und wurde verworfen.\n"
                        f"Größe: {file_size} Bytes\n"
                        f"Dateisignatur: {signature}\n"
                        f"Quelle: {self.url}"
                    )

                self._safe_extract_zip(destination, target_dir)
                extracted = True
            else:
                extracted = False

            self.completed.emit(True, str(destination), extracted, "")
        except Exception as exc:
            if partial is not None:
                try:
                    Path(partial).unlink(missing_ok=True)
                except Exception:
                    pass
            # Do not leave a broken HTML/error response behind under a .zip name.
            if destination is not None:
                try:
                    if Path(destination).suffix.lower() == ".zip" and Path(destination).exists():
                        if not zipfile.is_zipfile(str(destination)):
                            Path(destination).unlink(missing_ok=True)
                except Exception:
                    pass
            self.completed.emit(False, "", False, str(exc))



# Stage 178: lightweight Apache configuration editor with line-number gutter
# and a synchronized minimap.  It deliberately lives in server_tools.py so the
# server dock also works when this module is used outside the monolithic build.
class ApacheConfigLineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class ApacheConfigTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        fixed = QFont("Consolas")
        fixed.setStyleHint(QFont.Monospace)
        self.setFont(fixed)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.line_number_area = ApacheConfigLineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

    def line_number_area_width(self):
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_area_width(self, _=0):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            cr.left(), cr.top(), self.line_number_area_width(), cr.height()
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        palette = self.palette()
        background = palette.color(QPalette.Base)
        foreground = palette.color(QPalette.Text)
        if background.lightness() < 128:
            background = background.lighter(118)
            foreground = QColor("#b8b8b8")
        else:
            background = background.darker(106)
            foreground = QColor("#555555")
        painter.fillRect(event.rect(), background)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(foreground)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1


class ApacheConfigMiniMap(QPlainTextEdit):
    def __init__(self, editor: ApacheConfigTextEdit, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setReadOnly(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedWidth(118)
        mini_font = QFont("Consolas")
        mini_font.setStyleHint(QFont.Monospace)
        mini_font.setPointSize(3)
        self.setFont(mini_font)
        self.setCursorWidth(0)
        self.editor.textChanged.connect(self._sync_text)
        self.editor.verticalScrollBar().valueChanged.connect(self._sync_from_editor)
        self.editor.verticalScrollBar().rangeChanged.connect(
            lambda _a, _b: self._sync_from_editor(self.editor.verticalScrollBar().value())
        )
        self._sync_text()
        QTimer.singleShot(0, lambda: self._sync_from_editor(self.editor.verticalScrollBar().value()))

    def _sync_text(self):
        current = self.verticalScrollBar().value()
        self.setPlainText(self.editor.toPlainText())
        self.verticalScrollBar().setValue(current)
        self._sync_from_editor(self.editor.verticalScrollBar().value())

    def _sync_from_editor(self, value):
        source = self.editor.verticalScrollBar()
        target = self.verticalScrollBar()
        maximum = source.maximum()
        ratio = (float(value) / float(maximum)) if maximum > 0 else 0.0
        target.setValue(int(round(ratio * target.maximum())))

    def mousePressEvent(self, event):
        if self.viewport().height() > 0:
            ratio = max(0.0, min(1.0, float(event.pos().y()) / float(self.viewport().height())))
            bar = self.editor.verticalScrollBar()
            bar.setValue(int(round(ratio * bar.maximum())))
        event.accept()


class ApacheConfigEditorPane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        self.editor = ApacheConfigTextEdit(self)
        self.minimap = ApacheConfigMiniMap(self.editor, self)
        layout.addWidget(self.editor, 1)
        layout.addWidget(self.minimap)
        self.setMinimumHeight(420)


class ApacheServerPanel(ServerPanelBase):
    settings_prefix = "server/apache"

    def __init__(self, host, settings: QSettings, parent=None):
        super().__init__(host, settings, parent)
        self._apache_download_thread = None
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        tabs = QTabWidget(self)
        self.main_tabs = tabs
        root.addWidget(tabs, 1)

        # ---------------------------------------------------------------
        # Setup: Webserver-Konfiguration und laufender Dienst.
        # Stage 178: Der komplette Setup-Inhalt liegt in genau dieser
        # ScrollArea. Oberhalb der Ausgabe befindet sich der Apache-
        # Konfigurationseditor mit Gutter und Mini-Map.
        # ---------------------------------------------------------------
        setup_scroll = QScrollArea(tabs)
        setup_scroll.setObjectName("apacheSetupScrollArea")
        setup_scroll.setWidgetResizable(True)
        setup_page = QWidget(setup_scroll)
        setup_layout = QVBoxLayout(setup_page)
        setup_layout.setContentsMargins(6, 6, 6, 6)

        config = QGroupBox("Apache HTTP Server - Setup", setup_page)
        form = QFormLayout(config)
        conf_row, self.conf_edit = self._file_row("httpd_conf", "", "Apache Konfiguration (*.conf);;Alle Dateien (*)")
        root_row, self.document_root_edit = self._directory_row("document_root", "")
        self.service_edit = self._bound_line_edit("service_name", "Apache2.4")
        form.addRow("httpd.conf", conf_row)
        form.addRow("DocumentRoot", root_row)
        form.addRow("Windows-Dienst", self.service_edit)
        setup_layout.addWidget(config)

        buttons = QHBoxLayout()
        for text, callback in (
            ("Konfiguration prüfen", self._config_test),
            ("Start", self._start),
            ("Stop", self._stop),
            ("Restart", self._restart),
        ):
            button = QPushButton(text, setup_page)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch(1)
        setup_layout.addLayout(buttons)
        hint = QLabel(
            "Start/Stop/Restart verwenden Apaches native -k-Steuerung. Falls Apache "
            "als Windows-Dienst installiert ist, wird der eingestellte Dienstname mit -n übergeben.", setup_page
        )
        hint.setWordWrap(True)
        setup_layout.addWidget(hint)

        editor_group = QGroupBox("Apache Konfigurationseditor", setup_page)
        editor_group.setObjectName("apacheConfigEditorGroup")
        editor_group.setMinimumHeight(520)
        editor_layout = QVBoxLayout(editor_group)
        editor_toolbar = QHBoxLayout()
        self.apache_config_save_button = QPushButton("Speichern", editor_group)
        self.apache_config_save_button.setObjectName("apacheConfigSaveButton")
        self.apache_config_save_button.clicked.connect(self.save_current_config)
        editor_toolbar.addWidget(self.apache_config_save_button)
        self.apache_config_save_as_button = QPushButton("Speichern unter ...", editor_group)
        self.apache_config_save_as_button.setObjectName("apacheConfigSaveAsButton")
        self.apache_config_save_as_button.clicked.connect(self.save_current_config_as)
        editor_toolbar.addWidget(self.apache_config_save_as_button)
        self.apache_config_combo = QComboBox(editor_group)
        self.apache_config_combo.setObjectName("apacheConfigFileCombo")
        self.apache_config_combo.addItems(["httpd.conf", "ssl.conf", "vhost.conf"])
        saved_config_selection = self._load_text("config_editor_selection", "httpd.conf")
        selected_index = self.apache_config_combo.findText(saved_config_selection)
        if selected_index >= 0:
            self.apache_config_combo.setCurrentIndex(selected_index)
        editor_toolbar.addWidget(self.apache_config_combo, 1)
        editor_layout.addLayout(editor_toolbar)

        # Stage 180: im normalen d64_dism-GUI exakt denselben Editor-Container
        # wie die Pascal-Quelltexteditoren verwenden.  Der Host erzeugt dabei
        # SourceEditorWithMiniMap -> SourceTextEdit + SourceMiniMap.
        self.apache_config_editor_pane = self._create_shared_source_editor_pane(editor_group)
        self.apache_config_editor_pane.setObjectName("apacheConfigEditorPane")
        self.apache_config_editor = self.apache_config_editor_pane.editor
        self.apache_config_minimap = self.apache_config_editor_pane.minimap
        self.apache_config_editor.setObjectName("apacheConfigTextEdit")
        self.apache_config_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        if hasattr(self.apache_config_editor, "set_gutter_dark_mode"):
            self.apache_config_editor.set_gutter_dark_mode(bool(self._dark_mode))
        editor_layout.addWidget(self.apache_config_editor_pane, 1)
        setup_layout.addWidget(editor_group)

        setup_layout.addWidget(QLabel("Ausgabe", setup_page))
        self._output.setMinimumHeight(180)
        setup_layout.addWidget(self._output)
        setup_scroll.setWidget(setup_page)
        tabs.addTab(setup_scroll, "Setup")

        self._apache_config_switching = False
        self._apache_config_current_key = ""
        self._apache_config_current_path = None
        self.apache_config_combo.currentIndexChanged.connect(self._apache_config_selection_changed)
        self.conf_edit.editingFinished.connect(self._apache_httpd_conf_path_changed)
        tabs.currentChanged.connect(self._apache_main_tab_changed)

        # ---------------------------------------------------------------
        # Installation: Binary/Installer, Installationspfad und Dienstanlage.
        # ---------------------------------------------------------------
        install_scroll = QScrollArea(tabs)
        install_scroll.setWidgetResizable(True)
        install_page = QWidget(install_scroll)
        install_layout = QVBoxLayout(install_page)

        install_group = QGroupBox("Apache Installation", install_page)
        install_form = QFormLayout(install_group)
        install_dir_row, self.install_dir_edit = self._directory_row("install_dir", "")
        httpd_row, self.httpd_edit = self._file_row(
            "httpd", "httpd.exe", "Apache httpd (httpd.exe);;Programme (*.exe);;Alle Dateien (*)"
        )
        installer_row, self.installer_edit = self._file_row(
            "installer", "", "Apache Installer/Archiv (*.exe *.msi *.zip);;Alle Dateien (*)"
        )

        installer_download_row = QWidget(install_group)
        installer_download_layout = QHBoxLayout(installer_download_row)
        installer_download_layout.setContentsMargins(0, 0, 0, 0)
        installer_download_layout.setSpacing(6)
        self.apache_version_combo = QComboBox(installer_download_row)
        self.apache_version_combo.setObjectName("apacheInstallerVersionCombo")
        for label, url in APACHE_INSTALLER_DOWNLOADS:
            self.apache_version_combo.addItem(label, url)
        saved_download = self._load_text("installer_download_version", "")
        if saved_download:
            found = self.apache_version_combo.findText(saved_download)
            if found >= 0:
                self.apache_version_combo.setCurrentIndex(found)
        self.apache_version_combo.currentTextChanged.connect(
            lambda value: self._store_text("installer_download_version", value)
        )
        self.apache_download_button = QPushButton("Download", installer_download_row)
        self.apache_download_button.setObjectName("apacheInstallerDownloadButton")
        self.apache_download_button.clicked.connect(self._download_selected_apache)
        installer_download_layout.addWidget(self.apache_version_combo, 2)
        installer_download_layout.addWidget(self.apache_download_button)
        installer_target_label = QLabel("Verzeichnis", installer_download_row)
        installer_download_layout.addWidget(installer_target_label)
        installer_download_layout.addWidget(install_dir_row, 3)

        install_form.addRow("httpd.exe", httpd_row)
        install_form.addRow("Installer", installer_download_row)
        install_form.addRow("Lokaler Installer", installer_row)
        install_layout.addWidget(install_group)

        install_buttons = QHBoxLayout()
        auto_paths = QPushButton("Programmpfade übernehmen", install_page)
        auto_paths.clicked.connect(self._apply_install_directory)
        install_buttons.addWidget(auto_paths)
        version = QPushButton("Version prüfen", install_page)
        version.clicked.connect(self._version)
        install_buttons.addWidget(version)
        run_installer = QPushButton("Installer starten", install_page)
        run_installer.clicked.connect(self._run_installer)
        install_buttons.addWidget(run_installer)
        install_buttons.addStretch(1)
        install_layout.addLayout(install_buttons)

        service_group = QGroupBox("Windows-Dienst installieren", install_page)
        service_buttons = QHBoxLayout(service_group)
        install_service = QPushButton("Dienst installieren (Admin)", service_group)
        install_service.clicked.connect(self._install_service)
        service_buttons.addWidget(install_service)
        uninstall_service = QPushButton("Dienst entfernen (Admin)", service_group)
        uninstall_service.clicked.connect(self._uninstall_service)
        service_buttons.addWidget(uninstall_service)
        service_buttons.addStretch(1)
        install_layout.addWidget(service_group)

        install_hint = QLabel(
            "Apache wird nicht mit d64_dism ausgeliefert. Eine Windows-Version kann in der "
            "Installer-Zeile gewählt und in das dort angegebene Verzeichnis geladen werden. "
            "ZIP-Pakete werden sicher entpackt und die Apache-Pfade automatisch erkannt; "
            "die Installation bzw. Windows-Dienstinstallation muss danach manuell über "
            "'Installer starten' oder 'Dienst installieren' ausgelöst werden. EXE/MSI-Pakete "
            "werden nach dem Download automatisch gestartet. Für die Dienstinstallation können "
            "Administratorrechte erforderlich sein.", install_page
        )
        install_hint.setWordWrap(True)
        install_layout.addWidget(install_hint)
        install_layout.addStretch(1)
        install_scroll.setWidget(install_page)
        tabs.addTab(install_scroll, "Installation")
        self.set_dark_mode(self._dark_mode)
        self._load_apache_config(self.apache_config_combo.currentText().strip(), force=True)
        self._notify_host_document_actions()


    def _create_shared_source_editor_pane(self, parent: QWidget) -> QWidget:
        """Create the same editor/gutter/minimap container used by Pascal.

        In the monolithic d64_dism GUI the host exposes the run_gui-local
        SourceEditorWithMiniMap class through a factory.  server_tools.py keeps
        the old Stage-178 editor only as a compatibility fallback for hosts
        which do not provide that shared editor factory.
        """
        factory = getattr(self.host, "_create_pascal_source_editor_with_minimap", None)
        if callable(factory):
            pane = factory(parent)
            pane.setMinimumHeight(420)
            return pane

        shared_class = globals().get("_D64_SOURCE_EDITOR_WITH_MINIMAP_CLASS")
        if shared_class is not None:
            pane = shared_class(parent)
            pane.setMinimumHeight(420)
            return pane

        pane = ApacheConfigEditorPane(parent)
        pane.setMinimumHeight(420)
        return pane

    def set_dark_mode(self, dark: bool) -> None:
        super().set_dark_mode(dark)
        editor = getattr(self, "apache_config_editor", None)
        if editor is not None and hasattr(editor, "set_gutter_dark_mode"):
            editor.set_gutter_dark_mode(bool(dark))
        minimap = getattr(self, "apache_config_minimap", None)
        if minimap is not None:
            minimap.update()


    # ------------------------------------------------------------------
    # Stage 178: Apache configuration editor.
    # ------------------------------------------------------------------
    @staticmethod
    def _apache_config_setting_suffix(key: str) -> str:
        return str(key or "").strip().lower().replace(".", "_").replace("-", "_")

    def _notify_host_document_actions(self) -> None:
        callback = getattr(self.host, "_update_document_actions", None)
        if callable(callback):
            try:
                callback()
            except Exception:
                pass

    def _apache_main_tab_changed(self, _index: int) -> None:
        self._notify_host_document_actions()

    def config_editor_is_active(self) -> bool:
        return bool(
            getattr(self, "main_tabs", None) is not None
            and self.main_tabs.currentIndex() == 0
            and getattr(self, "apache_config_editor", None) is not None
        )

    def _apache_config_directory(self) -> Optional[Path]:
        conf_text = self.conf_edit.text().strip()
        if conf_text:
            return Path(conf_text).expanduser().parent
        install_text = self.install_dir_edit.text().strip() if hasattr(self, "install_dir_edit") else ""
        if install_text:
            return Path(install_text).expanduser() / "conf"
        httpd_text = self.httpd_edit.text().strip() if hasattr(self, "httpd_edit") else ""
        if httpd_text:
            httpd_path = Path(httpd_text).expanduser()
            if httpd_path.parent.name.lower() == "bin":
                return httpd_path.parent.parent / "conf"
        return None

    def _apache_config_candidates(self, key: str):
        key = str(key or "httpd.conf").strip()
        result = []
        suffix = self._apache_config_setting_suffix(key)
        saved = self._load_text(f"config_editor_path_{suffix}", "").strip()
        if saved:
            result.append(Path(saved).expanduser())

        if key == "httpd.conf":
            conf_text = self.conf_edit.text().strip()
            if conf_text:
                result.append(Path(conf_text).expanduser())

        directory = self._apache_config_directory()
        if directory is not None:
            if key == "httpd.conf":
                result.append(directory / "httpd.conf")
            elif key == "ssl.conf":
                # Eigener d64_dism-Name zuerst, danach die Apache-Standarddatei.
                result.extend([
                    directory / "ssl.conf",
                    directory / "extra" / "httpd-ssl.conf",
                ])
            elif key == "vhost.conf":
                result.extend([
                    directory / "vhost.conf",
                    directory / "extra" / "httpd-vhosts.conf",
                ])

        unique = []
        seen = set()
        for path in result:
            marker = os.path.normcase(os.path.abspath(str(path)))
            if marker not in seen:
                seen.add(marker)
                unique.append(path)
        return unique

    def _resolve_apache_config_path(self, key: str) -> Optional[Path]:
        candidates = self._apache_config_candidates(key)
        for path in candidates:
            if path.is_file():
                return path
        return candidates[0] if candidates else None

    def _remember_apache_config_path(self, key: str, path: Path) -> None:
        suffix = self._apache_config_setting_suffix(key)
        self._store_text(f"config_editor_path_{suffix}", str(path))
        if key == "httpd.conf":
            self.conf_edit.setText(str(path))
            self._store_text("httpd_conf", str(path))

    def _read_apache_config_text(self, path: Path) -> str:
        data = path.read_bytes()
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace")

    def _load_apache_config(self, key: str, force: bool = False) -> bool:
        key = str(key or "httpd.conf").strip()
        if not key:
            return False
        editor = getattr(self, "apache_config_editor", None)
        if editor is None:
            return False

        path = self._resolve_apache_config_path(key)
        try:
            text = self._read_apache_config_text(path) if path is not None and path.is_file() else ""
        except Exception as exc:
            self._message(
                "Apache Konfiguration",
                f"Die Konfigurationsdatei konnte nicht geladen werden:\n\n{path}\n\n{exc}",
                QMessageBox.Critical,
            )
            return False

        self._apache_config_current_key = key
        self._apache_config_current_path = path
        self._store_text("config_editor_selection", key)
        editor.setPlainText(text)
        editor.document().setModified(False)
        if path is not None and path.is_file():
            self.append_output(f"Apache Konfiguration geladen: {path}")
        elif path is not None:
            self.append_output(f"Apache Konfiguration noch nicht vorhanden: {path}")
        else:
            self.append_output(f"Für {key} ist noch kein Apache-Konfigurationsverzeichnis eingestellt.")
        return True

    def _apache_config_selection_changed(self, index: int) -> None:
        if getattr(self, "_apache_config_switching", False):
            return
        new_key = self.apache_config_combo.itemText(index).strip()
        old_key = getattr(self, "_apache_config_current_key", "")
        editor = getattr(self, "apache_config_editor", None)

        # Vor dem Wechsel werden die zuletzt geänderten Daten der aktuell
        # geöffneten Datei gespeichert. Scheitert/abgebrochen: Auswahl zurück.
        if old_key and editor is not None and editor.document().isModified():
            if not self.save_current_config():
                old_index = self.apache_config_combo.findText(old_key)
                if old_index >= 0:
                    self._apache_config_switching = True
                    try:
                        self.apache_config_combo.setCurrentIndex(old_index)
                    finally:
                        self._apache_config_switching = False
                return

        if not self._load_apache_config(new_key):
            old_index = self.apache_config_combo.findText(old_key)
            if old_index >= 0:
                self._apache_config_switching = True
                try:
                    self.apache_config_combo.setCurrentIndex(old_index)
                finally:
                    self._apache_config_switching = False

    def _apache_httpd_conf_path_changed(self) -> None:
        if getattr(self, "_apache_config_current_key", "") != "httpd.conf":
            return
        editor = getattr(self, "apache_config_editor", None)
        if editor is not None and editor.document().isModified():
            if not self.save_current_config():
                return
        self._load_apache_config("httpd.conf", force=True)

    def save_current_config(self) -> bool:
        editor = getattr(self, "apache_config_editor", None)
        if editor is None:
            return False
        key = getattr(self, "_apache_config_current_key", "") or self.apache_config_combo.currentText().strip()
        path = getattr(self, "_apache_config_current_path", None) or self._resolve_apache_config_path(key)
        if path is None:
            return self.save_current_config_as()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(editor.toPlainText(), encoding="utf-8", newline="")
        except Exception as exc:
            self._message(
                "Apache Konfiguration speichern",
                f"Die Datei konnte nicht gespeichert werden:\n\n{path}\n\n{exc}",
                QMessageBox.Critical,
            )
            return False
        self._apache_config_current_path = path
        self._remember_apache_config_path(key, path)
        editor.document().setModified(False)
        self.append_output(f"Apache Konfiguration gespeichert: {path}")
        return True

    def save_current_config_as(self) -> bool:
        editor = getattr(self, "apache_config_editor", None)
        if editor is None:
            return False
        key = getattr(self, "_apache_config_current_key", "") or self.apache_config_combo.currentText().strip() or "httpd.conf"
        current = getattr(self, "_apache_config_current_path", None) or self._resolve_apache_config_path(key)
        initial = str(current) if current is not None else key
        filename, _filter = QFileDialog.getSaveFileName(
            self,
            "Apache Konfiguration speichern unter",
            initial,
            "Apache Konfiguration (*.conf);;Alle Dateien (*)",
        )
        if not filename:
            return False
        path = Path(filename)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(editor.toPlainText(), encoding="utf-8", newline="")
        except Exception as exc:
            self._message(
                "Apache Konfiguration speichern unter",
                f"Die Datei konnte nicht gespeichert werden:\n\n{path}\n\n{exc}",
                QMessageBox.Critical,
            )
            return False
        self._apache_config_current_path = path
        self._remember_apache_config_path(key, path)
        editor.document().setModified(False)
        self.append_output(f"Apache Konfiguration gespeichert unter: {path}")
        return True


    def _store_path_edit(self, name: str, edit: QLineEdit, value: Path) -> None:
        text = str(value)
        edit.setText(text)
        self._store_text(name, text)

    def _apply_install_directory(self):
        base_text = self.install_dir_edit.text().strip()
        if not base_text:
            self._message("Apache Installation", "Bitte zuerst ein Installationsverzeichnis auswählen.", QMessageBox.Warning)
            return
        base = Path(base_text)
        self._store_path_edit("httpd", self.httpd_edit, base / "bin" / "httpd.exe")
        self._store_path_edit("httpd_conf", self.conf_edit, base / "conf" / "httpd.conf")
        self._store_path_edit("document_root", self.document_root_edit, base / "htdocs")
        self.append_output(f"Apache Programmpfade übernommen: {base}")


    def _download_selected_apache(self):
        if self._apache_download_thread is not None and self._apache_download_thread.isRunning():
            self._message("Apache Download", "Ein Download läuft bereits.", QMessageBox.Information)
            return

        target_dir = self.install_dir_edit.text().strip()
        if not target_dir:
            self._message(
                "Apache Download",
                "Bitte zuerst ein Installationsverzeichnis auswählen.",
                QMessageBox.Warning,
            )
            return

        url = str(self.apache_version_combo.currentData() or "").strip()
        label = self.apache_version_combo.currentText().strip()
        if not url:
            self._message("Apache Download", "Bitte eine Apache-Version auswählen.", QMessageBox.Warning)
            return

        self._store_text("installer_download_version", label)

        download_path = urllib.parse.urlparse(url).path.lower()
        if download_path.endswith(".zip"):
            self._message(
                "Apache ZIP-Download",
                "Die ausgewählte Apache-Version wird als ZIP-Datei heruntergeladen.\n\n"
                "Das ZIP-Archiv wird nach dem Download in das angegebene "
                "Installationsverzeichnis entpackt.\n\n"
                "Ein Installer bzw. die Windows-Dienstinstallation wird danach NICHT "
                "automatisch gestartet. Bitte lösen Sie die Installation anschließend "
                "manuell über 'Installer starten' oder 'Dienst installieren' aus.",
                QMessageBox.Information,
            )

        self.apache_download_button.setEnabled(False)
        self.apache_version_combo.setEnabled(False)
        self.append_output(f"Apache Download: {label}")
        self.append_output(f"Quelle: {url}")
        self.append_output(f"Ziel: {target_dir}")

        thread = ApacheDownloadThread(url, target_dir, self)
        thread.completed.connect(self._apache_download_finished)
        thread.finished.connect(thread.deleteLater)
        self._apache_download_thread = thread
        thread.start()

    def _apache_download_finished(self, ok: bool, downloaded_file: str, extracted: bool, error: str):
        self.apache_download_button.setEnabled(True)
        self.apache_version_combo.setEnabled(True)
        self._apache_download_thread = None

        if not ok:
            self.append_output("Apache Download fehlgeschlagen: " + error)
            self._message(
                "Apache Download - Fehler",
                "Der Apache-Download konnte nicht erfolgreich abgeschlossen werden.\n\n"
                + error
                + "\n\nBitte Internetverbindung, Download-URL und Zielverzeichnis prüfen.",
                QMessageBox.Critical,
            )
            return

        downloaded = Path(downloaded_file)
        self.append_output(f"Download abgeschlossen: {downloaded}")
        self._store_path_edit("installer", self.installer_edit, downloaded)

        if extracted:
            install_dir = self.install_dir_edit.text().strip()
            self.append_output(f"ZIP-Archiv entpackt nach: {install_dir}")
            if not self._discover_downloaded_apache_paths():
                self._message(
                    "Apache Installation",
                    "Das ZIP-Archiv wurde entpackt, aber bin\\httpd.exe wurde nicht gefunden.",
                    QMessageBox.Critical,
                )
                return

            self.append_output(
                "ZIP-Download abgeschlossen. Die Installation wird nicht automatisch gestartet; "
                "bitte manuell 'Installer starten' oder 'Dienst installieren' verwenden."
            )
            self._message(
                "Apache ZIP-Download",
                "Das ZIP-Archiv wurde erfolgreich in das angegebene Installationsverzeichnis "
                "entpackt.\n\n"
                "Die Apache-Programmpfade wurden übernommen. Ein Installer bzw. die "
                "Windows-Dienstinstallation wurde NICHT automatisch gestartet.\n\n"
                "Bitte starten Sie die Installation anschließend manuell über "
                "'Installer starten' oder 'Dienst installieren'.",
                QMessageBox.Information,
            )
            return

        self._store_path_edit("installer", self.installer_edit, downloaded)
        self._start_downloaded_apache_installation(downloaded, extracted=False)

    def _discover_downloaded_apache_paths(self) -> bool:
        target_text = self.install_dir_edit.text().strip()
        if not target_text:
            return False
        root = Path(target_text)
        if not root.exists():
            return False

        try:
            executables = list(root.rglob("httpd.exe"))
        except OSError:
            executables = []
        if not executables:
            return False

        # Prefer the canonical Apache layout <root>/bin/httpd.exe.
        httpd = next((p for p in executables if p.parent.name.lower() == "bin"), executables[0])
        apache_root = httpd.parent.parent if httpd.parent.name.lower() == "bin" else httpd.parent
        self._store_path_edit("install_dir", self.install_dir_edit, apache_root)
        self._store_path_edit("httpd", self.httpd_edit, httpd)

        conf = apache_root / "conf" / "httpd.conf"
        htdocs = apache_root / "htdocs"
        self._store_path_edit("httpd_conf", self.conf_edit, conf)
        self._store_path_edit("document_root", self.document_root_edit, htdocs)
        self._rewrite_downloaded_apache_server_root(apache_root, conf)
        self.append_output(f"Apache Programmpfade erkannt: {apache_root}")
        return True

    def _rewrite_downloaded_apache_server_root(self, apache_root: Path, conf: Path) -> None:
        if not conf.exists():
            return
        try:
            raw = conf.read_bytes()
            encoding = "utf-8"
            try:
                text = raw.decode(encoding)
            except UnicodeDecodeError:
                encoding = "cp1252"
                text = raw.decode(encoding)
            root_value = apache_root.resolve().as_posix()
            lines = text.splitlines(True)
            changed = False
            for index, line in enumerate(lines):
                stripped = line.strip()
                if stripped.lower().startswith("define srvroot "):
                    ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
                    lines[index] = f'Define SRVROOT "{root_value}"{ending}'
                    changed = True
                    break
            if changed:
                conf.write_text("".join(lines), encoding=encoding, newline="")
                self.append_output(f"Apache SRVROOT angepasst: {root_value}")
        except Exception as exc:
            self.append_output("Hinweis: SRVROOT konnte nicht automatisch angepasst werden: " + str(exc))

    def _start_downloaded_apache_installation(self, package: Path, extracted: bool) -> None:
        if extracted:
            self.append_output("Apache ZIP-Installation abgeschlossen; Windows-Dienstinstallation wird angestoßen.")
            self._install_service()
            self._message(
                "Apache Installation",
                "Apache wurde entpackt und die Programmpfade wurden übernommen.\n\n"
                "Die Installation des Windows-Dienstes wurde angestoßen. "
                "Dafür können Administratorrechte erforderlich sein.",
                QMessageBox.Information,
            )
            return

        suffix = package.suffix.lower()
        if suffix == ".msi":
            self.append_output("MSI-Installation wird gestartet.")
            self.run_program("msiexec.exe", ["/i", str(package)])
        elif suffix == ".exe":
            self.append_output("EXE-Installation wird gestartet.")
            self.run_program(str(package), [])
        else:
            self._message(
                "Apache Installation",
                "Das heruntergeladene Paket kann nicht automatisch installiert werden:\n" + str(package),
                QMessageBox.Warning,
            )

    def _run_installer(self):
        installer = self.installer_edit.text().strip()
        if not installer:
            self._message("Apache Installation", "Bitte zuerst einen Installer auswählen.", QMessageBox.Warning)
            return
        package = Path(installer)
        suffix = package.suffix.lower()
        if suffix == ".zip":
            target = self.install_dir_edit.text().strip()
            if not target:
                self._message("Apache Installation", "Bitte zuerst ein Installationsverzeichnis auswählen.", QMessageBox.Warning)
                return
            try:
                target_dir = Path(target).expanduser()
                target_dir.mkdir(parents=True, exist_ok=True)
                ApacheDownloadThread._safe_extract_zip(package, target_dir)
            except Exception as exc:
                self._message("Apache Installation", "ZIP-Archiv konnte nicht entpackt werden:\n" + str(exc), QMessageBox.Critical)
                return
            if self._discover_downloaded_apache_paths():
                self._start_downloaded_apache_installation(package, extracted=True)
            return
        self._start_downloaded_apache_installation(package, extracted=False)

    def _base_args(self) -> list[str]:
        args = []
        conf = self.conf_edit.text().strip()
        if conf:
            args += ["-f", conf]
        return args

    def _service_args(self, verb: str) -> list[str]:
        args = self._base_args() + ["-k", verb]
        service = self.service_edit.text().strip()
        if service:
            args += ["-n", service]
        return args

    def _version(self):
        self.run_program(self.httpd_edit.text(), ["-V"])

    def _config_test(self):
        self.run_program(self.httpd_edit.text(), self._base_args() + ["-t"])

    def _start(self):
        self.run_program(self.httpd_edit.text(), self._service_args("start"))

    def _stop(self):
        self.run_program(self.httpd_edit.text(), self._service_args("stop"))

    def _restart(self):
        self.run_program(self.httpd_edit.text(), self._service_args("restart"))

    def _run_program_as_admin(self, program: str, args: list[str], action_text: str) -> bool:
        """Start a single Windows operation elevated through the UAC prompt.

        The main d64_dism process deliberately stays unelevated. Only the requested
        Apache service action receives administrator rights.
        """
        program = str(program or "").strip()
        if not program:
            self._message(
                "Apache Dienst",
                "Bitte zuerst den Pfad zu httpd.exe auswählen.",
                QMessageBox.Warning,
            )
            return False

        executable = Path(program).expanduser()
        if not executable.is_file():
            self._message(
                "Apache Dienst",
                "Die Apache-Datei wurde nicht gefunden:\n" + str(executable),
                QMessageBox.Critical,
            )
            return False

        if os.name != "nt":
            self._message(
                "Apache Dienst",
                "Die UAC-Anforderung mit Administratorrechten ist nur unter Windows verfügbar.",
                QMessageBox.Critical,
            )
            return False

        parameters = subprocess.list2cmdline([str(value) for value in args])
        workdir = str(executable.parent)

        try:
            shell_execute = ctypes.windll.shell32.ShellExecuteW
            shell_execute.argtypes = [
                ctypes.c_void_p,
                ctypes.c_wchar_p,
                ctypes.c_wchar_p,
                ctypes.c_wchar_p,
                ctypes.c_wchar_p,
                ctypes.c_int,
            ]
            shell_execute.restype = ctypes.c_void_p

            result = shell_execute(
                None,
                "runas",
                str(executable),
                parameters,
                workdir,
                1,
            )
            result_value = int(result or 0)
        except Exception as exc:
            self.append_output(f"{action_text}: UAC-Start fehlgeschlagen: {exc}")
            self._message(
                "Apache Dienst",
                f"{action_text} konnte nicht mit Administratorrechten gestartet werden.\n\n{exc}",
                QMessageBox.Critical,
            )
            return False

        if result_value <= 32:
            # ShellExecute errors <= 32 include access denied / user-cancelled UAC.
            self.append_output(
                f"{action_text}: UAC wurde abgebrochen oder Windows meldete Fehlercode {result_value}."
            )
            self._message(
                "Apache Dienst",
                f"{action_text} wurde nicht gestartet.\n\n"
                "Die Windows-UAC-Abfrage wurde möglicherweise abgebrochen oder abgelehnt.\n"
                f"ShellExecute-Fehlercode: {result_value}",
                QMessageBox.Critical,
            )
            return False

        self.append_output(
            f"{action_text}: mit Windows-UAC/Administratorrechten gestartet."
        )
        self._message(
            "Apache Dienst",
            f"{action_text} wurde mit Administratorrechten gestartet.\n\n"
            "Bitte bestätige die Windows-UAC-Abfrage.",
            QMessageBox.Information,
        )
        return True

    def _install_service(self):
        args = self._base_args() + ["-k", "install"]
        service = self.service_edit.text().strip()
        if service:
            args += ["-n", service]
        self._run_program_as_admin(
            self.httpd_edit.text(),
            args,
            "Apache-Dienstinstallation",
        )

    def _uninstall_service(self):
        service = self.service_edit.text().strip() or "Apache2.4"
        answer = QMessageBox.question(
            self,
            "Apache Dienst entfernen",
            f'Soll der Windows-Dienst "{service}" wirklich entfernt werden?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        args = ["-k", "uninstall"]
        if service:
            args += ["-n", service]
        self._run_program_as_admin(
            self.httpd_edit.text(),
            args,
            "Apache-Dienstentfernung",
        )

