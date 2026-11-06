# -*- coding: utf-8 -*-
"""Gezielter Menü-Patch für Commodore_C64_DISM (GitHub main, 2026-11-05).

Ändert ausschließlich den Aufbau von Werkzeuge in src/d64_dism.py.
Vorhandene QAction-Objekte, Signalverbindungen und Codeformatierung bleiben erhalten.
"""

import argparse
import os
import shutil
import stat
import tempfile
from pathlib import Path


OLD_BLOCK = '''            tools_menu = self.main_menu_bar.addMenu("&Werkzeuge")
            tools_menu.addAction(self.character_editor_action)
            tools_menu.addAction(self.palette_editor_action)
            tools_menu.addSeparator()
            tools_menu.addAction(self.text_screen_editor_action)
            tools_menu.addAction(self.pixel_screen_editor_action)
            tools_menu.addSeparator()
            tools_menu.addAction(self.coff32_archive_action)
            tools_menu.addAction(self.pe32_linker_action)
            tools_menu.addAction(self.coff64_archive_action)
            tools_menu.addAction(self.pe64_linker_action)
            tools_menu.addAction(self.windows_graphics_header_action)
            tools_menu.addAction(self.windows_graphics_build_action)
            tools_menu.addSeparator()
            tools_menu.addAction(self.resource_editor_action)
            tools_menu.addAction(self.resource_action)
            tools_menu.addAction(self.localize_action)
            tools_menu.addAction(self.doxygen_action)
            tools_menu.addSeparator()
            tools_menu.addAction(self.html_editor_action)
            tools_menu.addSeparator()
            tools_menu.addAction(self.dbase_runtime_pe32_action)
            tools_menu.addAction(self.dbase_runtime_pe64_action)'''

NEW_BLOCK = '''            tools_menu = self.main_menu_bar.addMenu("&Werkzeuge")
            tools_menu.setObjectName("tools_menu")

            self.tools_windows64_menu = tools_menu.addMenu("MS Windows 64 Bit")
            self.tools_windows64_menu.setObjectName("tools_windows64_menu")
            self.tools_windows64_menu.addAction(self.coff64_archive_action)
            self.tools_windows64_menu.addAction(self.pe64_linker_action)
            self.tools_windows64_menu.addAction(self.dbase_runtime_pe64_action)

            self.tools_windows32_menu = tools_menu.addMenu("MS Windows 32 Bit")
            self.tools_windows32_menu.setObjectName("tools_windows32_menu")
            self.tools_windows32_menu.addAction(self.coff32_archive_action)
            self.tools_windows32_menu.addAction(self.pe32_linker_action)
            self.tools_windows32_menu.addAction(self.dbase_runtime_pe32_action)
            self.tools_windows32_menu.addSeparator()
            self.tools_windows32_menu.addAction(self.windows_graphics_header_action)
            self.tools_windows32_menu.addAction(self.windows_graphics_build_action)

            self.tools_windows16_menu = tools_menu.addMenu("MS Windows 16 Bit")
            self.tools_windows16_menu.setObjectName("tools_windows16_menu")
            self.tools_windows16_menu.addAction("Noch keine Werkzeuge").setEnabled(False)

            self.tools_dos32_menu = tools_menu.addMenu("MS DOS 32 Bit")
            self.tools_dos32_menu.setObjectName("tools_dos32_menu")
            self.tools_dos32_menu.addAction("Noch keine Werkzeuge").setEnabled(False)

            self.tools_dos16_menu = tools_menu.addMenu("MS DOS 16 Bit")
            self.tools_dos16_menu.setObjectName("tools_dos16_menu")
            self.tools_dos16_menu.addAction("Noch keine Werkzeuge").setEnabled(False)

            tools_menu.addSeparator()
            self.tools_amiga_menu = tools_menu.addMenu("Amiga 500")
            self.tools_amiga_menu.setObjectName("tools_amiga_menu")
            self.tools_amiga_menu.addAction(self.winuae_action)

            self.tools_c64_menu = tools_menu.addMenu("Commodore C= 64")
            self.tools_c64_menu.setObjectName("tools_c64_menu")
            self.tools_c64_menu.addAction(self.character_editor_action)
            self.tools_c64_menu.addAction(self.palette_editor_action)
            self.tools_c64_menu.addSeparator()
            self.tools_c64_menu.addAction(self.text_screen_editor_action)
            self.tools_c64_menu.addAction(self.pixel_screen_editor_action)

            tools_menu.addSeparator()
            tools_menu.addAction(self.resource_editor_action)
            tools_menu.addAction(self.resource_action)
            tools_menu.addAction(self.localize_action)
            tools_menu.addAction(self.doxygen_action)
            tools_menu.addSeparator()
            tools_menu.addAction(self.html_editor_action)'''


def apply_patch(source: Path, *, check: bool = False, backup: bool = True) -> str:
    data = source.read_bytes()
    newline = '\r\n' if b'\r\n' in data else '\n'
    old = OLD_BLOCK.replace('\n', newline).encode('utf-8')
    new = NEW_BLOCK.replace('\n', newline).encode('utf-8')

    if data.count(new) == 1:
        return 'Bereits angewendet – keine Änderung nötig.'
    if data.count(old) != 1:
        raise RuntimeError('Menüblock der GitHub-Basis nicht genau einmal gefunden. Datei unverändert.')
    if check:
        return 'Prüfung OK: Menüblock passt; Patch kann angewendet werden.'

    patched = data.replace(old, new, 1)
    if backup:
        backup_path = source.with_name(source.name + '.before_tools_menu.bak')
        if backup_path.exists():
            raise FileExistsError(f'Backup existiert schon, bitte prüfen: {backup_path}')
        shutil.copy2(source, backup_path)

    original_mode = stat.S_IMODE(source.stat().st_mode)
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(dir=source.parent, prefix='.tools_menu_', suffix='.tmp', delete=False) as tmp:
            tmp.write(patched)
            tmp_name = tmp.name
        os.chmod(tmp_name, original_mode)
        os.replace(tmp_name, source)
    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return 'Werkzeuge-Menü erfolgreich geändert; übriger Quelltext bytegenau erhalten.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', nargs='?', default='.', help='Pfad zum Repository oder zu d64_dism.py')
    parser.add_argument('--check', action='store_true', help='Nur prüfen, nichts ändern')
    parser.add_argument('--no-backup', action='store_true', help='Keine .bak-Sicherung erzeugen')
    args = parser.parse_args()
    path = Path(args.repo)
    source = path if path.is_file() else path / 'd64_dism.py'
    if not source.is_file():
        parser.error(f'Python-Quelldatei fehlt: {source}')
    try:
        print(apply_patch(source, check=args.check, backup=not args.no_backup))
    except (OSError, RuntimeError) as exc:
        parser.exit(1, f'FEHLER: {exc}\n')


if __name__ == '__main__':
    main()
