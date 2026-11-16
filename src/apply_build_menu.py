#!/usr/bin/env python3
# coding: utf-8
"""Gezieltes Menü-Update für Commodore_C64_DISM (GitHub main 0e3b8625).

Berührt ausschließlich die Menü-Zielwahl und zwei dazugehörige UI-Funktionen.
Alle sonstigen Python-Zeilen und ihre Formatierung bleiben unverändert.
"""

import argparse
import difflib
import hashlib
from pathlib import Path
import shutil
import sys

SOURCE_COMMIT = "0e3b8625f804fa28292f5ca274305e4a68e4ec52"
SOURCE_BLOB = "dacb0bb86226e7a457e6de1ce13db2e50bbf3f2f"
PLACEHOLDER_TARGETS = '{"win16", "dos32", "dos16"}'


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def replace_once(source: str, old: str, new: str, description: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"{description}: erwarteter Quelltext nicht eindeutig gefunden "
            f"(Treffer: {count}). Datei bleibt unverändert."
        )
    return source.replace(old, new, 1)


def update(source: str) -> str:
    # Kein automatisches Reformatieren: Original-Zeilenenden beibehalten.
    nl = "\r\n" if "\r\n" in source else "\n"

    start_marker = "            self.build_target_action_group = QActionGroup(self)" + nl
    end_marker = '            self.build_start_action = QAction("Starten", self)' + nl
    if source.count(start_marker) != 1 or source.count(end_marker) != 1:
        raise RuntimeError("Die Menü-Anker im Repository entsprechen nicht der erwarteten Basis.")
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    old_menu = source[start:end]
    if (old_menu.count("for target_key, caption in (") != 3
            or old_menu.count("self.build_target_action_group.addAction(action)") != 3
            or old_menu.count("self.build_menu.addSeparator()") != 3
            or any(old_menu.count(f'("{key}", ') != 1 for key in (
                "pe32", "pe64", "linux32", "linux64", "c64", "amiga"
            ))):
        raise RuntimeError("Menü-Zielwahl hat sich gegenüber dem GitHub-Basisstand geändert.")

    new_menu = '''            self.build_target_action_group = QActionGroup(self)
            self.build_target_action_group.setExclusive(True)
            self.build_target_actions = {}
            # Stage 489: The selected target is independent of whether a given
            # frontend can already compile for it. All nine choices stay marked.
            self._build_menu_selected_target = "pe32"
            self.build_target_action_labels = {}
            for target_key, caption in (
                ("pe64", "MS Windows 64 Bit"),
                ("pe32", "MS Windows 32 Bit"),
                ("win16", "MS Windows 16 Bit"),
                (None, None),
                ("dos32", "MS DOS 32 Bit"),
                ("dos16", "MS DOS 16 Bit"),
                (None, None),
                ("linux64", "Linux Ubuntu 22.04 64 Bit"),
                ("linux32", "Linux Ubuntu 22.04 32 Bit"),
                (None, None),
                ("amiga", "Amiga 500"),
                ("c64", "Commodore C= 64"),
            ):
                if target_key is None:
                    self.build_menu.addSeparator()
                    continue
                action = QAction(caption, self)
                action.setObjectName("build_target_" + target_key + "_action")
                action.setCheckable(True)
                action.setData(target_key)
                self.build_target_action_group.addAction(action)
                self.build_menu.addAction(action)
                self.build_target_actions[target_key] = action
                self.build_target_action_labels[target_key] = caption
                action.triggered.connect(
                    lambda _checked=False, target=target_key: self._build_menu_select_target(target)
                )
            # Stage 481: Start is available only for an actually linked build.
'''.replace("\n", nl)
    source = source[:start] + new_menu + source[end:]

    sync_start = source.index("        def _build_menu_sync_target(self) -> None:")
    sync_end = source.index("        @staticmethod", sync_start)
    sync = source[sync_start:sync_end]
    sync = replace_once(
        sync,
        '''            A checked QAction is a radio marker in Qt. The additional tick in
            the caption makes the choice visible with themes that suppress Qt's
            native radio indicator. Each document remembers its own selection.'''.replace("\n", nl),
        '''            Qt uses the native radio/check indicator of each checkable
            QAction. Each document remembers its own selection.'''.replace("\n", nl),
        "Beschreibung der Qt-Zielmarkierung",
    )
    sync = replace_once(
        sync,
        '                if self._dbase_form_is_active():' + nl,
        f'                if self._dbase_form_is_active() and target not in {PLACEHOLDER_TARGETS}:' + nl,
        "WFM-Auswahl-Synchronisierung",
    )
    sync = replace_once(
        sync,
        '                            action.setText(("✓ " if is_selected else "") + caption)' + nl,
        '                            action.setText(caption)' + nl,
        "Zusätzliches Häkchen im Menütext",
    )
    source = source[:sync_start] + sync + source[sync_end:]

    select_start = source.index("        def _build_menu_select_target(self, target: str) -> None:")
    select_end = source.index("        def _build_menu_compile(self, *, link: bool) -> bool:", select_start)
    select = source[select_start:select_end]
    select = replace_once(
        select,
        '            """Allow all six targets to be marked; validate support at build time."""' + nl,
        '            """Allow all nine targets to be marked; validate support at build time."""' + nl,
        "Beschreibung der Zielauswahl",
    )
    select = replace_once(
        select,
        '                if self._dbase_form_is_active():' + nl,
        (f'                if target in {PLACEHOLDER_TARGETS}:' + nl
         + '                    # Kein C64-Fallback für noch nicht implementierte Ziele.' + nl
         + '                    pass' + nl
         + '                elif self._dbase_form_is_active():' + nl),
        "Nicht implementierte Ziele ohne Build-Target-Fallback vorsehen",
    )
    source = source[:select_start] + select + source[select_end:]
    return source


def get_source_file(path: Path) -> Path:
    if path.is_file():
        return path
    for candidate in (path / "d64_dism.py", path / "src" / "d64_dism.py"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"d64_dism.py im Verzeichnis {path} nicht gefunden")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path, help="Verzeichnis des Repositories oder d64_dism.py")
    parser.add_argument("--check", action="store_true", help="Nur prüfen, nichts ändern")
    parser.add_argument("--show-diff", action="store_true", help="Änderungen auf der Konsole ausgeben")
    args = parser.parse_args()
    try:
        file_path = get_source_file(args.repo.resolve())
        original = file_path.read_bytes()
        blob = git_blob_sha(original)
        source = original.decode("utf-8")
        result = update(source)
        updated = result.encode("utf-8")
        if blob != SOURCE_BLOB:
            print(f"Hinweis: lokale Datei weicht vom GitHub-Blob {SOURCE_BLOB} ab (gefunden: {blob}).")
            print("Die Menü-Anker wurden dennoch einzeln auf Eindeutigkeit geprüft.")
        if args.show_diff:
            diff = difflib.unified_diff(
                source.splitlines(keepends=True), result.splitlines(keepends=True),
                fromfile="a/d64_dism.py", tofile="b/d64_dism.py", n=3,
            )
            sys.stdout.writelines(diff)
        if args.check:
            print(f"OK: Patch kann angewendet werden: {file_path}")
            return 0
        backup = file_path.with_name(file_path.name + ".before_build_menu.bak")
        if backup.exists():
            raise FileExistsError(f"Sicherung existiert bereits: {backup}")
        shutil.copy2(file_path, backup)
        try:
            file_path.write_bytes(updated)
        except Exception:
            shutil.copy2(backup, file_path)
            raise
        print(f"Geändert: {file_path}")
        print(f"Backup:   {backup}")
        print(f"Bytes unveränderter Dateiteile und Zeilenenden bleiben erhalten.")
        return 0
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
