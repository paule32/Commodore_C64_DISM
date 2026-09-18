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
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtCore import QProcess, QSettings, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


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


class Bind9ServerPanel(ServerPanelBase):
    settings_prefix = "server/bind9"

    def __init__(self, host, settings: QSettings, parent=None):
        super().__init__(host, settings, parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        tabs = QTabWidget(self)
        root.addWidget(tabs, 1)

        dns = QWidget(tabs)
        dns_layout = QVBoxLayout(dns)
        paths = QGroupBox("BIND9 Programme und Konfiguration", dns)
        form = QFormLayout(paths)
        named_row, self.named_edit = self._file_row("named", "named.exe", "BIND named (named.exe);;Programme (*.exe);;Alle Dateien (*)")
        rndc_row, self.rndc_edit = self._file_row("rndc", "rndc.exe", "BIND rndc (rndc.exe);;Programme (*.exe);;Alle Dateien (*)")
        conf_row, self.conf_edit = self._file_row("named_conf", "", "BIND Konfiguration (*.conf);;Alle Dateien (*)")
        zones_row, self.zones_edit = self._directory_row("zone_dir", "")
        form.addRow("named.exe", named_row)
        form.addRow("rndc.exe", rndc_row)
        form.addRow("named.conf", conf_row)
        form.addRow("Zonen-Verzeichnis", zones_row)
        dns_layout.addWidget(paths)

        buttons = QHBoxLayout()
        for text, callback in (
            ("Version", self._show_version),
            ("Konfiguration prüfen", self._check_config),
            ("Status", self._status),
            ("Reload", self._reload),
        ):
            button = QPushButton(text, dns)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch(1)
        dns_layout.addLayout(buttons)
        dns_layout.addWidget(QLabel("Ausgabe", dns))
        dns_layout.addWidget(self._output, 1)
        tabs.addTab(dns, "DNS")

        ddns = QWidget(tabs)
        ddns_layout = QVBoxLayout(ddns)
        ddns_group = QGroupBox("Dynamische DNS-Aktualisierung", ddns)
        ddns_form = QFormLayout(ddns_group)
        nsupdate_row, self.nsupdate_edit = self._file_row("nsupdate", "nsupdate.exe", "BIND nsupdate (nsupdate.exe);;Programme (*.exe);;Alle Dateien (*)")
        key_row, self.tsig_key_edit = self._file_row("tsig_key", "", "TSIG Key (*.key *.private);;Alle Dateien (*)")
        self.ddns_server_edit = self._bound_line_edit("ddns_server", "127.0.0.1")
        self.ddns_zone_edit = self._bound_line_edit("ddns_zone", "local")
        self.ddns_host_edit = self._bound_line_edit("ddns_host", "host.local")
        self.ddns_address_edit = self._bound_line_edit("ddns_address", "127.0.0.1")
        ddns_form.addRow("nsupdate.exe", nsupdate_row)
        ddns_form.addRow("TSIG-Key", key_row)
        ddns_form.addRow("DNS-Server", self.ddns_server_edit)
        ddns_form.addRow("Zone", self.ddns_zone_edit)
        ddns_form.addRow("Hostname", self.ddns_host_edit)
        ddns_form.addRow("Adresse", self.ddns_address_edit)
        ddns_layout.addWidget(ddns_group)
        hint = QLabel("Die eigentliche Zone-/TSIG-Erzeugung wird in der nächsten Ausbaustufe ergänzt. Dieses Dock hält bereits alle Pfade und DynDNS-Zieldaten persistent.", ddns)
        hint.setWordWrap(True)
        ddns_layout.addWidget(hint)
        ddns_layout.addStretch(1)
        tabs.addTab(ddns, "DynDNS")
        self.set_dark_mode(self._dark_mode)

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


class OpenSSLServerPanel(ServerPanelBase):
    settings_prefix = "server/openssl"

    def __init__(self, host, settings: QSettings, parent=None):
        super().__init__(host, settings, parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        top = QHBoxLayout()
        openssl_row, self.openssl_edit = self._file_row("openssl", "openssl.exe", "OpenSSL (openssl.exe);;Programme (*.exe);;Alle Dateien (*)")
        top.addWidget(QLabel("OpenSSL:"))
        top.addWidget(openssl_row, 1)
        version = QPushButton("Version", self)
        version.clicked.connect(lambda: self.run_program(self.openssl_edit.text(), ["version", "-a"]))
        top.addWidget(version)
        root.addLayout(top)

        tabs = QTabWidget(self)
        root.addWidget(tabs, 1)

        ca_scroll = QScrollArea(tabs)
        ca_scroll.setWidgetResizable(True)
        ca_page = QWidget(ca_scroll)
        ca_layout = QVBoxLayout(ca_page)
        identity = QGroupBox("Client Authority CA", ca_page)
        form = QFormLayout(identity)
        ca_dir_row, self.ca_dir_edit = self._directory_row("ca_directory", "")
        self.fqdn_edit = self._bound_line_edit("fqdn", "ca.local")
        self.cn_edit = self._bound_line_edit("common_name", "d64 Development Root CA")
        self.org_edit = self._bound_line_edit("organization", "d64 Development")
        self.ou_edit = self._bound_line_edit("organizational_unit", "Development")
        self.country_edit = self._bound_line_edit("country", "DE")
        self.state_edit = self._bound_line_edit("state", "")
        self.locality_edit = self._bound_line_edit("locality", "")
        self.email_edit = self._bound_line_edit("email", "")
        self.days_spin = QSpinBox(identity)
        self.days_spin.setRange(1, 36500)
        self.days_spin.setValue(int(self.settings.value(self._key("ca_days"), 3650) or 3650))
        self.days_spin.valueChanged.connect(lambda v: self.settings.setValue(self._key("ca_days"), int(v)))
        self.bits_combo = QComboBox(identity)
        self.bits_combo.addItems(["2048", "3072", "4096"])
        self.bits_combo.setCurrentText(self._load_text("key_bits", "4096"))
        self.bits_combo.currentTextChanged.connect(lambda value: self._store_text("key_bits", value))
        form.addRow("CA-Verzeichnis", ca_dir_row)
        form.addRow("FQDN", self.fqdn_edit)
        form.addRow("Common Name / Aussteller", self.cn_edit)
        form.addRow("Organisation", self.org_edit)
        form.addRow("Organisationseinheit", self.ou_edit)
        form.addRow("Land", self.country_edit)
        form.addRow("Bundesland", self.state_edit)
        form.addRow("Ort", self.locality_edit)
        form.addRow("E-Mail", self.email_edit)
        form.addRow("Gültigkeit (Tage)", self.days_spin)
        form.addRow("RSA-Schlüssel", self.bits_combo)
        ca_layout.addWidget(identity)

        ca_actions = QGroupBox("CA-Aktionen", ca_page)
        ca_buttons = QHBoxLayout(ca_actions)
        init_button = QPushButton("CA-Verzeichnis anlegen", ca_actions)
        init_button.clicked.connect(self._initialize_ca_directory)
        ca_buttons.addWidget(init_button)
        root_button = QPushButton("Root-CA erzeugen", ca_actions)
        root_button.clicked.connect(self._create_root_ca)
        ca_buttons.addWidget(root_button)
        crl_button = QPushButton("CRL anzeigen", ca_actions)
        crl_button.clicked.connect(self._show_crl)
        ca_buttons.addWidget(crl_button)
        ca_buttons.addStretch(1)
        ca_layout.addWidget(ca_actions)

        requests = QGroupBox("Client-Anfragen / Zertifikatsanfragen", ca_page)
        request_layout = QVBoxLayout(requests)
        request_layout.addWidget(QLabel("Signieren, Ablehnen, Sperren, frühzeitiger Ablauf und Erneuern werden auf Basis des OpenSSL-CA-Index verwaltet. Die vollständige Request-Tabelle folgt in der nächsten CA-Ausbaustufe."))
        ca_layout.addWidget(requests)
        ca_layout.addStretch(1)
        ca_scroll.setWidget(ca_page)
        tabs.addTab(ca_scroll, "Client Authority CA")

        cert_page = QWidget(tabs)
        cert_layout = QVBoxLayout(cert_page)
        cert_group = QGroupBox("Zertifikate", cert_page)
        cert_form = QFormLayout(cert_group)
        cert_row, self.cert_edit = self._file_row("certificate", "", "Zertifikate (*.crt *.cer *.pem);;Alle Dateien (*)")
        csr_row, self.csr_edit = self._file_row("csr", "", "Certificate Requests (*.csr *.req *.pem);;Alle Dateien (*)")
        cert_form.addRow("Zertifikat", cert_row)
        cert_form.addRow("CSR", csr_row)
        cert_layout.addWidget(cert_group)
        cert_buttons = QHBoxLayout()
        inspect = QPushButton("Zertifikat anzeigen", cert_page)
        inspect.clicked.connect(self._inspect_certificate)
        cert_buttons.addWidget(inspect)
        inspect_csr = QPushButton("CSR anzeigen", cert_page)
        inspect_csr.clicked.connect(self._inspect_csr)
        cert_buttons.addWidget(inspect_csr)
        cert_buttons.addStretch(1)
        cert_layout.addLayout(cert_buttons)
        cert_layout.addWidget(self._output, 1)
        tabs.addTab(cert_page, "Zertifikate")
        self.set_dark_mode(self._dark_mode)

    def _subject(self) -> str:
        parts = []
        for key, edit in (("C", self.country_edit), ("ST", self.state_edit), ("L", self.locality_edit), ("O", self.org_edit), ("OU", self.ou_edit), ("CN", self.cn_edit), ("emailAddress", self.email_edit)):
            value = edit.text().strip()
            if value:
                parts.append(f"/{key}={value.replace('/', '_')}")
        return "".join(parts)

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
            self.append_output(f"CA-Verzeichnis vorbereitet: {base}")
        except Exception as exc:
            self._message("CA-Verzeichnis", str(exc), QMessageBox.Critical)

    def _create_root_ca(self):
        base_text = self.ca_dir_edit.text().strip()
        if not base_text:
            self._message("Root-CA", "Bitte zuerst ein CA-Verzeichnis auswählen.", QMessageBox.Warning)
            return
        base = Path(base_text)
        self._initialize_ca_directory()
        key = base / "private" / "ca.key.pem"
        cert = base / "certs" / "ca.cert.pem"
        args = [
            "req", "-x509", "-new", "-nodes",
            "-newkey", f"rsa:{self.bits_combo.currentText()}",
            "-sha256", "-days", str(self.days_spin.value()),
            "-keyout", str(key), "-out", str(cert),
            "-subj", self._subject(),
        ]
        self.run_program(self.openssl_edit.text(), args, str(base))

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

    def _inspect_certificate(self):
        path = self.cert_edit.text().strip()
        if path:
            self.run_program(self.openssl_edit.text(), ["x509", "-in", path, "-text", "-noout"])

    def _inspect_csr(self):
        path = self.csr_edit.text().strip()
        if path:
            self.run_program(self.openssl_edit.text(), ["req", "-in", path, "-text", "-noout"])


class ApacheServerPanel(ServerPanelBase):
    settings_prefix = "server/apache"

    def __init__(self, host, settings: QSettings, parent=None):
        super().__init__(host, settings, parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        config = QGroupBox("Apache HTTP Server", self)
        form = QFormLayout(config)
        httpd_row, self.httpd_edit = self._file_row("httpd", "httpd.exe", "Apache httpd (httpd.exe);;Programme (*.exe);;Alle Dateien (*)")
        conf_row, self.conf_edit = self._file_row("httpd_conf", "", "Apache Konfiguration (*.conf);;Alle Dateien (*)")
        root_row, self.document_root_edit = self._directory_row("document_root", "")
        self.service_edit = self._bound_line_edit("service_name", "Apache2.4")
        form.addRow("httpd.exe", httpd_row)
        form.addRow("httpd.conf", conf_row)
        form.addRow("DocumentRoot", root_row)
        form.addRow("Windows-Dienst", self.service_edit)
        root.addWidget(config)
        buttons = QHBoxLayout()
        for text, callback in (
            ("Version", self._version),
            ("Konfiguration prüfen", self._config_test),
            ("Start", self._start),
            ("Stop", self._stop),
            ("Restart", self._restart),
        ):
            button = QPushButton(text, self)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch(1)
        root.addLayout(buttons)
        hint = QLabel("Start/Stop/Restart verwenden Apaches native -k-Steuerung. Falls Apache als Windows-Dienst installiert ist, wird der eingestellte Dienstname mit -n übergeben.", self)
        hint.setWordWrap(True)
        root.addWidget(hint)
        root.addWidget(QLabel("Ausgabe", self))
        root.addWidget(self._output, 1)
        self.set_dark_mode(self._dark_mode)

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
