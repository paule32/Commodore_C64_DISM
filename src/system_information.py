"""Stage 536: Windows system information (native Win32 APIs) and themed Qt dialog.

Only the dialog imports Qt. Collecting system information is safe during tests
on non-Windows operating systems, where unavailable fields are labelled.
"""
from __future__ import annotations

import ctypes
import os
import platform
import struct
from ctypes import wintypes
from typing import Dict, List, Tuple


def _gib(value) -> str:
    if value is None:
        return "Nicht verfügbar"
    return f"{int(value) / (1024 ** 3):,.2f} GiB".replace(",", " ")


def _windows_processor_core_count() -> int | None:
    if os.name != "nt":
        return None
    # RelationProcessorCore = 0, Windows Vista and later.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    procedure = kernel.GetLogicalProcessorInformationEx
    procedure.argtypes = [wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
    procedure.restype = wintypes.BOOL
    size = wintypes.DWORD(0)
    procedure(0, None, ctypes.byref(size))
    if not size.value or size.value > 16 * 1024 * 1024:
        return None
    data = ctypes.create_string_buffer(size.value)
    if not procedure(0, data, ctypes.byref(size)):
        return None
    count = 0
    pos = 0
    while pos + 8 <= size.value:
        relationship, length = struct.unpack_from("<II", data, pos)
        if length < 8 or pos + length > size.value:
            break
        if relationship == 0:
            count += 1
        pos += length
    return count or None


def _memory_status() -> dict:
    if os.name != "nt":
        try:
            import psutil
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {"physical_total": vm.total, "physical_available": vm.available,
                    "commit_total": vm.total + swap.total,
                    "commit_available": vm.available + swap.free,
                    "address_total": None, "address_available": None,
                    "installed": None}
        except (ImportError, OSError):
            return {}

    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD)] + [
            (field, ctypes.c_ulonglong) for field in (
                "ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile",
                "ullTotalVirtual", "ullAvailVirtual", "ullAvailExtendedVirtual")]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    procedure = kernel.GlobalMemoryStatusEx
    procedure.argtypes = [ctypes.POINTER(MemoryStatusEx)]
    procedure.restype = wintypes.BOOL
    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(status)
    if not procedure(ctypes.byref(status)):
        return {}
    installed = ctypes.c_ulonglong(0)
    try:
        get_installed = kernel.GetPhysicallyInstalledSystemMemory
        get_installed.argtypes = [ctypes.POINTER(ctypes.c_ulonglong)]
        get_installed.restype = wintypes.BOOL
        if not get_installed(ctypes.byref(installed)):
            installed = None
    except AttributeError:
        installed = None
    return {
        "installed": installed.value * 1024 if installed is not None else None,
        "physical_total": status.ullTotalPhys,
        "physical_available": status.ullAvailPhys,
        "commit_total": status.ullTotalPageFile,
        "commit_available": status.ullAvailPageFile,
        "address_total": status.ullTotalVirtual,
        "address_available": status.ullAvailVirtual,
    }


def _windows_registry_values() -> dict:
    if os.name != "nt":
        return {}
    try:
        import winreg
        values = {}
        paths = (
            (r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
             ("ProductName", "EditionID", "DisplayVersion", "ReleaseId", "CurrentBuildNumber")),
            (r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
             ("VendorIdentifier", "ProcessorNameString")),
        )
        for path, fields in paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    for field in fields:
                        try:
                            values[field] = str(winreg.QueryValueEx(key, field)[0])
                        except OSError:
                            continue
            except OSError:
                continue
        return values
    except ImportError:
        return {}


def collect_system_information() -> List[Tuple[str, List[Tuple[str, str]]]]:
    """Returns fully labelled display rows, independent of Qt and locale APIs."""
    registry = _windows_registry_values()
    memory = _memory_status()
    logical = os.cpu_count() or 1
    physical = _windows_processor_core_count()
    cpu = registry.get("ProcessorNameString", platform.processor() or "Unbekannt")
    vendor_code = registry.get("VendorIdentifier", "")
    name = (cpu + " " + vendor_code).lower()
    vendor = "Intel" if "intel" in name else ("AMD" if "amd" in name else "Unbekannt")
    machine = platform.machine() or "Unbekannt"
    os_bitness = "64-Bit" if machine.lower() in {"amd64", "x86_64", "arm64", "aarch64"} else "32-Bit"
    if os.name == "nt":
        try:
            build = int(registry.get("CurrentBuildNumber", "0"))
        except ValueError:
            build = 0
        os_major = "Windows 11" if build >= 22000 else "Windows 10"
        edition = registry.get("EditionID", "")
        if "professional" in edition.lower() or edition.lower().startswith("pro"):
            edition_name = "Professional"
        elif "home" in edition.lower() or edition.lower().startswith("core"):
            edition_name = "Home"
        else:
            edition_name = edition or "Nicht verfügbar"
        version = registry.get("DisplayVersion") or registry.get("ReleaseId") or "Nicht verfügbar"
        build_text = str(build) if build else "Nicht verfügbar"
    else:
        os_major = platform.system()
        edition_name = "Nicht verfügbar (Windows erforderlich)"
        version = platform.release()
        build_text = platform.version()
    physical_label = str(physical) if physical is not None else "Nicht verfügbar"
    return [
        ("Betriebssystem", [
            ("System", os_major), ("Edition", edition_name),
            ("Version", version), ("Build", build_text),
            ("Systemarchitektur", os_bitness),
        ]),
        ("Prozessor", [
            ("Hersteller", vendor), ("Prozessor", cpu),
            ("Architektur", machine + " (" + os_bitness + ")"),
            ("Physische CPU-Kerne", physical_label),
            ("Logische Prozessoren", str(logical)),
        ]),
        ("Speicher", [
            ("Installierter RAM", _gib(memory.get("installed"))),
            ("Nutzbarer RAM (gesamt)", _gib(memory.get("physical_total"))),
            ("Aktuell verfügbarer RAM", _gib(memory.get("physical_available"))),
            ("Virtueller Speicher (Commit-Limit)", _gib(memory.get("commit_total"))),
            ("Verfügbarer virtueller Speicher (Commit)", _gib(memory.get("commit_available"))),
            ("Virtueller Adressraum des Prozesses", _gib(memory.get("address_total"))),
        ]),
    ]


class SystemInformationDialog:
    """Lazy Qt wrapper: Qt is imported only when this GUI dialog is opened."""
    def __new__(cls, parent=None, *, dark_mode=False):
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import (
            QDialog, QDialogButtonBox, QGroupBox, QGridLayout, QLabel,
            QPushButton, QScrollArea, QVBoxLayout, QWidget)

        class Dialog(QDialog):
            def __init__(self):
                super().__init__(parent)
                self.setObjectName("d64_system_information_dialog")
                self.setWindowTitle("System-Informationen")
                self.resize(680, 580)
                self.setMinimumSize(520, 420)
                page = QVBoxLayout(self)
                heading = QLabel("System-Informationen", self)
                heading.setObjectName("system_info_heading")
                page.addWidget(heading)
                scroll = QScrollArea(self)
                scroll.setWidgetResizable(True)
                scroll.setFrameShape(QScrollArea.NoFrame)
                self.body = QWidget(scroll)
                self.details_layout = QVBoxLayout(self.body)
                self.details_layout.setContentsMargins(4, 4, 4, 4)
                self.details_layout.setSpacing(12)
                scroll.setWidget(self.body)
                page.addWidget(scroll, 1)
                buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
                refresh = QPushButton("Aktualisieren", self)
                refresh.setObjectName("system_info_refresh")
                buttons.addButton(refresh, QDialogButtonBox.ActionRole)
                buttons.rejected.connect(self.reject)
                refresh.clicked.connect(self.refresh)
                page.addWidget(buttons)
                self._dark_title_bar = bool(dark_mode)
                self.setStyleSheet(self._theme(self._dark_title_bar))
                self.refresh()

            def showEvent(self, event):
                super().showEvent(event)
                self._apply_native_title_theme()

            def _apply_native_title_theme(self):
                # Native Windows caption color is controlled by DWM, not Qt CSS.
                # Attribute 20 is standard; older Windows 10 builds use 19.
                if os.name != "nt":
                    return
                try:
                    dwm = ctypes.WinDLL("dwmapi", use_last_error=True)
                    dwm.DwmSetWindowAttribute.argtypes = (
                        ctypes.c_void_p, wintypes.DWORD,
                        ctypes.c_void_p, wintypes.DWORD)
                    dwm.DwmSetWindowAttribute.restype = ctypes.c_long
                    value = ctypes.c_int(int(self._dark_title_bar))
                    hwnd = ctypes.c_void_p(int(self.winId()))
                    for attribute in (20, 19):
                        status = dwm.DwmSetWindowAttribute(
                            hwnd, attribute, ctypes.byref(value),
                            ctypes.sizeof(value))
                        if status == 0:
                            break
                except (AttributeError, OSError, ValueError):
                    pass

            def _theme(self, dark: bool) -> str:
                bg, surface, foreground, muted, stroke, button = (
                    ("#111925", "#1C2737", "#E8EDF5", "#B8C7D9", "#3C5066", "#24374B")
                    if dark else ("#FAFBFC", "#FFFFFF", "#202C38", "#546779", "#C7D1DC", "#E8EEF3"))
                return f"""
                    QDialog#d64_system_information_dialog {{background: {bg}; color: {foreground};}}
                    QLabel {{color: {foreground}; background: transparent; font-size: 10pt;}}
                    QLabel#system_info_heading {{font-size: 15pt; font-weight: bold; padding: 4px;}}
                    QLabel#system_info_key {{color: {muted};}}
                    QScrollArea {{background: {bg}; border: none;}}
                    QGroupBox {{color: {foreground}; border: 1px solid {stroke};
                        border-radius: 6px; margin-top: 14px; padding: 12px;
                        background: {surface}; font-weight: bold;}}
                    QGroupBox::title {{subcontrol-origin: margin; left: 12px; padding: 0 5px;}}
                    QPushButton {{color: {foreground}; background: {button};
                        border: 1px solid {stroke}; border-radius: 4px; padding: 6px 14px;}}
                    QPushButton:hover {{border-color: {muted};}}
                    QWidget {{selection-background-color: {stroke};}}
                """

            def refresh(self):
                while self.details_layout.count():
                    entry = self.details_layout.takeAt(0)
                    widget = entry.widget()
                    if widget is not None:
                        widget.deleteLater()
                for title, records in collect_system_information():
                    group = QGroupBox(title, self.body)
                    grid = QGridLayout(group)
                    grid.setColumnStretch(1, 1)
                    for row, (name, value) in enumerate(records):
                        key = QLabel(name + ":", group)
                        key.setObjectName("system_info_key")
                        value_label = QLabel(value, group)
                        value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                        value_label.setWordWrap(True)
                        grid.addWidget(key, row, 0)
                        grid.addWidget(value_label, row, 1)
                    self.details_layout.addWidget(group)
                self.details_layout.addStretch(1)
        return Dialog()
