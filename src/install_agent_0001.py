#!/usr/bin/env python3
"""Integration Agent -> 0001 in eine bestehende src/d64_dism.py.

Aufruf:
    py install_agent_0001.py T:/GitHub/Commodore_C64_DISM/src/d64_dism.py
    py install_agent_0001.py src/d64_dism.py --check

Der bestehende Code bleibt erhalten. Vor dem Schreiben entsteht ein Backup.
Die zugehörige Python-Paketstruktur wird nach src/agent_0001 kopiert.
"""
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

MODULE_MARKER = 'self.agent_0001_action.setObjectName("agent_0001_action")'
METHOD_MARKER = 'def show_agent_0001_dock(self):'
MENU_ANCHOR = '            help_menu = self.main_menu_bar.addMenu("&Hilfe")'
METHOD_ANCHOR = '        def _sync_formula_zoom_control_checks(self, _value=None):'

MENU_CODE = '''            # Agent 0001: deutscher Grammatikparser (modulares Dock).
            self.agent_menu = self.main_menu_bar.addMenu("&Agent")
            self.agent_menu.setObjectName("agent_menu")
            self.agent_0001_action = QAction("0001", self)
            self.agent_0001_action.setObjectName("agent_0001_action")
            self.agent_0001_action.setStatusTip(
                "Deutschen Grammatikparser öffnen (Syntax, Kongruenz, Intent)")
            self.agent_0001_action.triggered.connect(self.show_agent_0001_dock)
            self.agent_menu.addAction(self.agent_0001_action)

'''

METHOD_CODE = '''        def show_agent_0001_dock(self):
            """Agent -> 0001: Parser im bestehenden exklusiven Dock-Workspace."""
            from agent_0001 import GermanGrammarWidget

            dock = getattr(self, "agent_0001_dock", None)
            if dock is None:
                dock = QDockWidget("Agent 0001 – Deutscher Grammatikparser", self)
                dock.setObjectName("agent_0001_grammar_dock")
                dock.setAllowedAreas(Qt.AllDockWidgetAreas)
                dock.setWidget(GermanGrammarWidget(dock))
                self.addDockWidget(Qt.LeftDockWidgetArea, dock)
                dock.visibilityChanged.connect(
                    lambda visible, current=dock:
                    self._exclusive_tool_workspace_visibility_changed(
                        bool(visible), current)
                )
                self.agent_0001_dock = dock

            self._activate_exclusive_tool_workspace(dock)
            dock.show()
            dock.raise_()
            self._expand_exclusive_tool_workspace(dock)
            QTimer.singleShot(
                0, lambda current=dock:
                self._expand_exclusive_tool_workspace(current)
            )
            self.statusBar().showMessage("Agent 0001: Grammatikparser geöffnet")

'''


def integrate(source: str) -> tuple[str, bool]:
    """Patch-Strings nur bei genau bekannten Ankerstellen; idempotent."""
    if MODULE_MARKER in source and METHOD_MARKER in source:
        return source, False
    if MODULE_MARKER in source or METHOD_MARKER in source:
        raise ValueError("Unvollständige Agent-0001-Integration vorhanden – bitte manuell prüfen.")
    if source.count(MENU_ANCHOR) != 1:
        raise ValueError("Menü-Anker für &Hilfe nicht eindeutig gefunden. Datei unverändert.")
    if source.count(METHOD_ANCHOR) != 1:
        raise ValueError("Methoden-Anker nicht eindeutig gefunden. Datei unverändert.")
    if "def _create_menu(self)" not in source:
        raise ValueError("_create_menu() fehlt. Datei unverändert.")
    if "def _activate_exclusive_tool_workspace(" not in source:
        raise ValueError("Workspace-API fehlt. Datei unverändert.")
    if source.index(MENU_ANCHOR) >= source.index(METHOD_ANCHOR):
        raise ValueError("Unerwartete Reihenfolge der Methoden. Datei unverändert.")
    result = source.replace(MENU_ANCHOR, MENU_CODE + MENU_ANCHOR, 1)
    result = result.replace(METHOD_ANCHOR, METHOD_CODE + METHOD_ANCHOR, 1)
    return result, True


def install(target: Path, check_only: bool = False) -> str:
    target = target.expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(f"Datei nicht gefunden: {target}")
    source_bytes = target.read_bytes()
    if b"\x00" in source_bytes:
        raise ValueError("Unerwartetes Binärformat. Datei unverändert.")
    text = source_bytes.decode("utf-8-sig")
    modified, changed = integrate(text)
    package = Path(__file__).resolve().parent / "agent_0001"
    if not (package / "grammar.py").is_file() or not (package / "gui.py").is_file():
        raise FileNotFoundError("Paketdateien agent_0001/ fehlen.")
    destination = target.parent / "agent_0001"

    if check_only:
        return ("CHECK OK: Einfügestellen eindeutig, Patch erforderlich."
                if changed else "CHECK OK: Agent 0001 bereits integriert.")

    if destination.exists():
        for file in ("__init__.py", "grammar.py", "gui.py"):
            original = package / file
            installed = destination / file
            if installed.exists() and installed.read_bytes() != original.read_bytes():
                raise FileExistsError(
                    f"Vorhandenes Modul würde überschrieben: {installed}. "
                    "Bitte Änderungen zunächst sichern.")
    if changed:
        backup = target.with_name(target.name + ".bak.agent0001")
        if backup.exists():
            raise FileExistsError(f"Backup {backup} existiert bereits. Kein Überschreiben.")
        shutil.copy2(target, backup)
        newline = "\r\n" if source_bytes.count(b"\r\n") > source_bytes.count(b"\n") // 2 else "\n"
        if newline == "\r\n":
            modified = modified.replace("\r\n", "\n").replace("\n", "\r\n")
        output = (b"\xef\xbb\xbf" if source_bytes.startswith(b"\xef\xbb\xbf") else b"") + modified.encode("utf-8")
        fd, name = tempfile.mkstemp(prefix=".agent0001_", suffix=".tmp", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(output)
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    destination.mkdir(exist_ok=True)
    for file in ("__init__.py", "grammar.py", "gui.py"):
        shutil.copy2(package / file, destination / file)
    return ("INSTALLIERT: Agent -> 0001 eingebaut, Backup erstellt: " + str(target)
            if changed else "BEREITS INTEGRIERT: Parser-Modul geprüft: " + str(target))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("d64_dism", type=Path, nargs="?", default=Path("d64_dism.py"),
                    help="Pfad zur vorhandenen d64_dism.py")
    ap.add_argument("--check", action="store_true", help="Nur Prüfen, keine Änderungen")
    args = ap.parse_args()
    try:
        print(install(args.d64_dism, args.check))
    except (ValueError, FileExistsError, OSError, UnicodeError) as ex:
        ap.exit(1, f"FEHLER: {ex}\n")


if __name__ == "__main__":
    main()
