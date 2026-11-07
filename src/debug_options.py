# -*- coding: utf-8 -*-
"""Project Debug settings for Commodore_C64_DISM (PyQt5, opt-in)."""
from __future__ import annotations
from dataclasses import dataclass
from configparser import ConfigParser
from pathlib import Path

SECTION = 'Settings.Debug'  # Legacy input (Stage 527-529).
ARCH_SECTIONS = {
    'pe32': 'Settings.Windows.32Bit.Debug',
    'pe64': 'Settings.Windows.64Bit.Debug',
}


def target_section(target: str | None = None) -> str:
    if target is None:
        return SECTION
    key = str(target).casefold()
    if key not in ARCH_SECTIONS:
        raise ValueError(f'Unsupported debug target: {target}')
    return ARCH_SECTIONS[key]

@dataclass
class DebugOptions:
    enable_debug: bool = False
    ces: bool = False
    dwarf_enabled: bool = False
    dwarf_version: int = 3

    def __post_init__(self):
        if self.dwarf_version not in (2, 3):
            raise ValueError('DWARF version must be 2 or 3')

    @property
    def emit_dwarf(self) -> bool:
        return self.enable_debug and self.dwarf_enabled

    @classmethod
    def from_parser(cls, cfg: ConfigParser, target: str | None = None) -> 'DebugOptions':
        section = target_section(target)
        if not cfg.has_section(section):
            # The old single section is imported into each profile at first load.
            if cfg.has_section(SECTION):
                section = SECTION
            elif target is None and cfg.has_section(ARCH_SECTIONS['pe32']):
                section = ARCH_SECTIONS['pe32']
            else:
                return cls()
        return cls(
            enable_debug=cfg.getboolean(section, 'EnableDebug', fallback=False),
            ces=cfg.getboolean(section, 'CheckEarlyStart', fallback=False),
            dwarf_enabled=cfg.getboolean(section, 'DwarfEnabled', fallback=False),
            dwarf_version=cfg.getint(section, 'DwarfVersion', fallback=3),
        )

    def to_parser(self, cfg: ConfigParser, target: str | None = None) -> None:
        section = target_section(target)
        if not cfg.has_section(section):
            cfg.add_section(section)
        cfg[section].update({
            'Title': 'Debug',
            'EnableDebug': str(self.enable_debug).lower(),
            'CheckEarlyStart': str(self.ces).lower(),
            'DwarfEnabled': str(self.dwarf_enabled).lower(),
            'DwarfVersion': str(self.dwarf_version),
        })


def read_options(project_path: str | Path, target: str | None = None) -> DebugOptions:
    cfg = ConfigParser(interpolation=None)
    cfg.optionxform = str
    cfg.read(project_path, encoding='utf-8-sig')
    return DebugOptions.from_parser(cfg, target=target)


def update_project_file(project_path: str | Path, options: DebugOptions,
                        target: str | None = None) -> None:
    """Update the chosen Debug block, preserving existing project bytes elsewhere.

    This is intentionally not a generic ConfigParser rewrite: Pascal .pro files
    contain extensive JSON and ordered sections that must stay unchanged.
    """
    p = Path(project_path)
    raw = p.read_bytes()
    encoding = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    text = raw.decode(encoding)
    newline = '\r\n' if '\r\n' in text else '\n'
    section = target_section(target)
    block = newline.join([
        '[' + section + ']',
        'Title = Debug',
        'EnableDebug = ' + str(options.enable_debug).lower(),
        'CheckEarlyStart = ' + str(options.ces).lower(),
        'DwarfEnabled = ' + str(options.dwarf_enabled).lower(),
        'DwarfVersion = ' + str(options.dwarf_version),
        '',
    ])
    import re
    pattern = re.compile(r'(?m)^\[' + re.escape(section) + r'\][ \t]*\r?\n(?:^(?!\[).*(?:\r?\n|$))*')
    if pattern.search(text):
        text = pattern.sub(lambda _: block, text, count=1)
    else:
        if not text.endswith(('\r', '\n')):
            text += newline
        text += newline + block
    tmp = p.with_suffix(p.suffix + '.debugtmp')
    tmp.write_bytes(text.encode(encoding))
    tmp.replace(p)


try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QGroupBox, QCheckBox, QRadioButton,
        QButtonGroup, QFrame,
    )
except ImportError:
    QWidget = object


class DebugSettingsPage(QWidget):
    """Right-hand page for a 'Debug' main node in the Project Settings tree."""
    def __init__(self, options: DebugOptions | None = None, parent=None):
        if QWidget is object:
            raise RuntimeError('PyQt5 is required for DebugSettingsPage')
        super().__init__(parent)
        options = options or DebugOptions()
        layout = QVBoxLayout(self)
        debug_group = QGroupBox('Debug: ', self)
        debug_layout = QVBoxLayout(debug_group)
        self.enable_debug = QCheckBox('Enable Debug', debug_group)
        self.ces = QCheckBox('CES - Check Early Start', debug_group)
        debug_layout.addWidget(self.enable_debug)
        debug_layout.addWidget(self.ces)
        # DWARF belongs inside the architecture-specific Debug group.
        self.debug_group = debug_group
        layout.addWidget(debug_group)
        dwarf_group = QGroupBox('DWARF: ', debug_group)
        self.dwarf_group = dwarf_group
        dwarf_layout = QVBoxLayout(dwarf_group)
        self.dwarf_enabled = QCheckBox('Enabled', dwarf_group)
        dwarf_layout.addWidget(self.dwarf_enabled)
        self.dwarf_v2 = QRadioButton('DWARF Version 2', dwarf_group)
        self.dwarf_v3 = QRadioButton('DWARF Version 3', dwarf_group)
        self.dwarf_versions = QButtonGroup(self)
        self.dwarf_versions.setExclusive(True)
        self.dwarf_versions.addButton(self.dwarf_v2, 2)
        self.dwarf_versions.addButton(self.dwarf_v3, 3)
        dwarf_layout.addWidget(self.dwarf_v2)
        dwarf_layout.addWidget(self.dwarf_v3)
        debug_layout.addWidget(dwarf_group)
        layout.addStretch(1)
        self.enable_debug.toggled.connect(self._refresh)
        self.dwarf_enabled.toggled.connect(self._refresh)
        self.set_options(options)

    def _refresh(self, *_):
        dwarf_active = self.enable_debug.isChecked() and self.dwarf_enabled.isChecked()
        self.dwarf_v2.setEnabled(dwarf_active)
        self.dwarf_v3.setEnabled(dwarf_active)

    def set_options(self, options: DebugOptions):
        self.enable_debug.setChecked(options.enable_debug)
        self.ces.setChecked(options.ces)
        self.dwarf_enabled.setChecked(options.dwarf_enabled)
        (self.dwarf_v2 if options.dwarf_version == 2 else self.dwarf_v3).setChecked(True)
        self._refresh()

    def options(self) -> DebugOptions:
        return DebugOptions(
            self.enable_debug.isChecked(),
            self.ces.isChecked(),
            self.dwarf_enabled.isChecked(),
            self.dwarf_versions.checkedId(),
        )
