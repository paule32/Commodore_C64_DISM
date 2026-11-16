#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal-Patch fuer Commodore_C64_DISM, GitHub main 2026-11-05 b1037dbe.

Aendert nur gezielte Textstellen in src/d64_dism.py. Kein Reformatting.
Verwendung: py apply_pascal_project_update.py T:\\GitHub\\Commodore_C64_DISM
            py apply_pascal_project_update.py T:\\GitHub\\Commodore_C64_DISM --check
"""

from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime

BASE_COMMIT = "b1037dbe674f0ebdda1b04dba2f69e835c4e8222"
MARKER = "# Stage Pascal-Projekt-Kontext 2026-11-05"
I = " " * 8


def insert_before(source: str, anchor: str, addition: str, label: str) -> str:
    count = source.count(anchor)
    if count != 1:
        raise RuntimeError(f"{label}: Erwartet 1 Anker, gefunden {count}. Abbruch ohne Schreiben.")
    return source.replace(anchor, addition + anchor, 1)


def replace_one(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: Erwartet 1 Abschnitt, gefunden {count}. Abbruch ohne Schreiben.")
    return source.replace(old, new, 1)


# Die Methoden werden bewusst wie im Original mit 8 Leerzeichen eingerueckt.
# Fuer die Anwendung wird jede Zeile der Quelltexte ansonsten unveraendert gelassen.
NEW_METHODS = r'''        # Stage Pascal-Projekt-Kontext 2026-11-05: Projekt-Popup-Menues
        # verwenden das gleiche green_beige-Design wie das Hauptmenue.
        def _project_popup_menu(self) -> QMenu:
            menu = QMenu(self.project_tree)
            menu.setObjectName("green_beige_popup_menu")
            menu.setAttribute(Qt.WA_StyledBackground, True)
            menu.setStyleSheet(self._green_beige_menu_stylesheet())
            return menu

        def _project_restore_current_editor(self, document: DocumentEditor) -> None:
            # QTreeWidget hat die Auswahl beim Mausklick schon umgestellt.
            # Daher das Blatt der bisher geoeffneten Datei wieder selektieren.
            previous = getattr(self, "_project_last_active_leaf", None)
            old_path = getattr(document, "path", None)
            if old_path is not None:
                wanted = os.path.normcase(str(Path(old_path).resolve())).casefold()
                iterator = QTreeWidgetItemIterator(self.project_tree)
                while iterator.value() is not None:
                    candidate = iterator.value()
                    path_text = str(candidate.data(0, Qt.UserRole + 302) or "")
                    if (path_text and self._project_item_kind(candidate) == PROJECT_NODE_PASCAL_TARGET_SOURCE
                            and os.path.normcase(str(Path(path_text).resolve())).casefold() == wanted):
                        previous = candidate
                        break
                    iterator += 1
            if previous is not None:
                was_blocked = self.project_tree.blockSignals(True)
                try:
                    self.project_tree.clearSelection()
                    self.project_tree.setCurrentItem(previous)
                    previous.setSelected(True)
                    self.project_tree.scrollToItem(previous)
                finally:
                    self.project_tree.blockSignals(was_blocked)
            self.document_tabs.setCurrentWidget(document)
            document.focus_preferred_editor()
            QTimer.singleShot(0, document.focus_preferred_editor)

        def _project_confirm_leave_document(self, next_item: Optional[QTreeWidgetItem]) -> bool:
            document = self.current_document()
            if not isinstance(document, DocumentEditor) or not document.is_modified:
                return True
            next_path = str(next_item.data(0, Qt.UserRole + 302) or "") if next_item is not None else ""
            if next_path and document.path is not None:
                old_key = os.path.normcase(str(Path(document.path).resolve())).casefold()
                next_key = os.path.normcase(str(Path(next_path).resolve())).casefold()
                if old_key == next_key:
                    return True
            dialog = self._create_message_box(
                QMessageBox.Question,
                "Änderungen speichern",
                "Es wurden Änderungen an der Datei vorgenommen. Sollen diese Änderungen gespeichert werden ?",
                buttons=QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                default_button=QMessageBox.Yes,
            )
            for kind, text in (
                (QMessageBox.Yes, "Ja"),
                (QMessageBox.No, "Nein"),
                (QMessageBox.Cancel, "Abbrechen"),
            ):
                button = dialog.button(kind)
                if button is not None:
                    button.setText(text)
            answer = dialog.exec_()
            if answer == QMessageBox.Yes:
                if self._save_document(document, save_as=False):
                    return True
                self._project_restore_current_editor(document)
                return False
            if answer == QMessageBox.No:
                # Kein Dateischreibzugriff; die ungespeicherten Aenderungen
                # bleiben im bisherigen, weiter geoeffneten Editor erhalten.
                return True
            self._project_restore_current_editor(document)
            return False

        def _project_new_pascal_leaf(
            self, kind: str, target: str = "pe32"
        ) -> Optional[QTreeWidgetItem]:
            if not self._project_confirm_leave_document(None):
                return None
            if target not in {"pe32", "pe64"} or kind not in {"unit", "module", "resource", "table"}:
                return None
            self._ensure_project_for_new_document()
            directory = self._project_new_file_directory()
            suffix = ".dbf" if kind == "table" else ".rc" if kind == "resource" else ".pas"
            path = directory / ("Unbenannt" + suffix)
            counter = 2
            while path.exists() or any(
                sibling.name.casefold() == path.name.casefold()
                for sibling in directory.iterdir()
            ):
                path = directory / (f"Unbenannt_{counter}" + suffix)
                counter += 1
            try:
                if kind == "table":
                    write_dbase_dbf(path, [DBaseDBFField("ID", "N", 10, 0)])
                else:
                    if kind == "unit":
                        initial_text = (
                            f"unit {path.stem};\n\n"
                            "interface\n\nimplementation\n\nend.\n"
                        )
                    elif kind == "module":
                        initial_text = f"program {path.stem};\n\nbegin\nend.\n"
                    else:
                        initial_text = "// Neue Windows-Resource-Datei\n"
                    with path.open("x", encoding="utf-8", newline="\n") as stream:
                        stream.write(initial_text)
            except (OSError, ValueError) as exc:
                self.show_error("Pascal-Projektdatei konnte nicht erstellt werden", str(exc))
                return None

            if kind in {"unit", "module"}:
                role = "units" if kind == "unit" else "modules"
                group = self.project_pascal_group_nodes.get((target, role))
                item = (self._add_project_pascal_target_entry(group, path, title=path.name)
                        if group is not None else None)
            elif kind == "resource":
                item = self._add_project_resource_entry("pascal", target, path, title=path.name)
            else:
                group = self.project_pascal_table_nodes.get(target)
                item = (self._add_project_pascal_table_entry(group, path, title=path.name)
                        if group is not None else None)
            if item is None:
                self.show_error("Projektknoten nicht gefunden", f"Die Datei wurde erstellt, aber nicht eingebunden:\n{path}")
                return None
            if self.current_project_path is not None:
                self.save_project()
            self.project_tree.setCurrentItem(item)
            item.setSelected(True)
            self.project_tree.scrollToItem(item)
            # Die Speicherfrage wurde VOR dem Erstellen schon beantwortet.
            self._project_skip_pascal_save_question = True
            try:
                self.open_project_item(item)
            finally:
                self._project_skip_pascal_save_question = False
            self.statusBar().showMessage(f"Projektdatei erstellt: {path.name}", 6000)
            return item

        def _project_rename_pascal_leaf(self, item: QTreeWidgetItem) -> bool:
            if self._project_item_kind(item) != PROJECT_NODE_PASCAL_TARGET_SOURCE:
                return False
            old_text = str(item.data(0, Qt.UserRole + 302) or "").strip()
            if not old_text:
                return False
            old_path = Path(old_text).expanduser().resolve()
            if not old_path.is_file():
                self.show_error("Umbenennen", f"Datei nicht gefunden:\n{old_path}")
                return False
            name, accepted = QInputDialog.getText(
                self, "Pascal-Datei umbenennen", "Neuer Dateiname:",
                QLineEdit.Normal, old_path.name,
            )
            if not accepted:
                return False
            name = name.strip()
            if not name or name in {".", ".."} or name != Path(name).name or any(
                char in name for char in '<>:"/\\|?*'
            ) or name.endswith((".", " ")):
                self.show_error("Ungültiger Dateiname", "Bitte nur einen gültigen Dateinamen eingeben.")
                return False
            if not Path(name).suffix:
                name += old_path.suffix
            if Path(name).suffix.casefold() not in {".pas", ".pp"}:
                self.show_error("Ungültige Dateiendung", "Erlaubt sind .pas und .pp")
                return False
            if Path(name).stem.split(".")[0].upper() in {
                "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
                "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2",
                "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
            }:
                self.show_error("Ungültiger Dateiname", "Dieser Name ist unter Windows reserviert.")
                return False
            new_path = old_path.with_name(name)
            if old_path == new_path:
                return True
            try:
                collision = any(
                    sibling.name.casefold() == name.casefold()
                    and sibling.name.casefold() != old_path.name.casefold()
                    for sibling in old_path.parent.iterdir()
                )
                if collision or (new_path.exists() and not new_path.samefile(old_path)):
                    self.show_error("Datei bereits vorhanden", f"Die Zieldatei existiert bereits:\n{new_path}")
                    return False
                document = self._find_open_document(old_path)
                if isinstance(document, DocumentEditor) and document.is_modified:
                    if not self._save_document(document, save_as=False):
                        return False
                old_path.rename(new_path)
            except OSError as exc:
                self.show_error("Umbenennen fehlgeschlagen", str(exc))
                return False
            new_path = new_path.resolve()
            self._replace_project_path_reference(old_path, new_path)
            item.setData(0, Qt.UserRole + 309, new_path.name)
            item.setText(0, new_path.name)
            item.setToolTip(0, str(new_path))
            item.setIcon(0, self.icon_provider.icon(QFileInfo(str(new_path))))
            if isinstance(document, DocumentEditor):
                document.path = new_path
                document.custom_display_name = None
                document.update_syntax_highlighting()
                document.invalidate_assembly_result("Pascal-Datei umbenannt")
                self._update_document_tab(document)
            self.set_project_modified(True)
            if self.current_project_path is not None:
                self.save_project()
            if old_path.parent == self.current_directory:
                self.populate_file_list()
            self.statusBar().showMessage(f"Pascal-Datei umbenannt: {old_path.name} -> {new_path.name}", 6000)
            return True

        def _show_project_pascal_root_menu(self, item: QTreeWidgetItem, position) -> None:
            menu = self._project_popup_menu()
            actions = {}
            specs = (
                ("Neu:  MS Windows 64 Bit Unit", "unit", "pe32"),
                ("Neu:  MS Windows 32 Bit Unit", "unit", "pe32"),
                ("Neu:  MS Windows 16 Bit Unit", "", ""),
                None,
                ("Neu:  MS Windows 64 Bit Resource", "resource", "pe64"),
                ("Neu:  MS Windows 32 Bit Resource", "resource", "pe32"),
                None,
                ("Neu:  Commodore C= 64 Unit", "", ""),
                None,
                ("Neu:  Module 64 Bit", "module", "pe64"),
                ("Neu:  Module 64 Bit", "module", "pe64"),
                ("Neu:  Tabelle", "table", "pe32"),
            )
            for spec in specs:
                if spec is None:
                    menu.addSeparator()
                    continue
                label, kind, target = spec
                action = menu.addAction(label)
                if not kind:
                    # Noch kein 16-Bit-/C64-Pascal-Zielknoten/Backend vorhanden.
                    action.setEnabled(False)
                else:
                    actions[action] = (kind, target)
            selected = menu.exec_(self.project_tree.viewport().mapToGlobal(position))
            if selected in actions:
                kind, target = actions[selected]
                self._project_new_pascal_leaf(kind, target)

'''


def build_patch(source: str) -> str:
    if MARKER in source:
        raise RuntimeError("Der Pascal-Projekt-Kontext-Patch ist bereits vorhanden.")

    menu_decl = "menu = QMenu(self.project_tree)"
    count = source.count(menu_decl)
    if count != 22:
        raise RuntimeError(f"Projekt-Popup-Menues: erwartet 22, gefunden {count}.")
    source = source.replace(menu_decl, "menu = self._project_popup_menu()")

    # Deklarationen oberhalb der Menue-Dispatch-Methode einfuegen.
    source = insert_before(
        source,
        "        def show_project_context_menu(self, position) -> None:\n",
        NEW_METHODS,
        "Neue Projektmethoden",
    )

    # Der Pascal-Hauptknoten (category='pascal') besitzt bisher nur
    # das generische Projekt-Kontextmenue. Vor der generischen Dispatch-Kette.
    old = (
        "            kind = self._project_item_kind(item)\n"
        "            if self._project_item_kind(item) in {\n"
    )
    new = (
        "            kind = self._project_item_kind(item)\n"
        "            if (item.parent() is None\n"
        "                    and str(item.data(0, Qt.UserRole + 301) or \"\").casefold() == \"pascal\"):\n"
        "                self._show_project_pascal_root_menu(item, position)\n"
        "                return\n"
        "            if self._project_item_kind(item) in {\n"
    )
    source = replace_one(source, old, new, "Pascal-Hauptknoten")

    # Einfachklick: Pascal-Dateiblatt wie bisher schon dBASE/C64 oeffnen.
    old = (
        "            kind = self._project_item_kind(item)\n"
        "            if kind in {\n"
        "                PROJECT_NODE_C64_RESOURCE_FILE, PROJECT_NODE_C64_SOURCE_FILE,\n"
        "                PROJECT_NODE_DBASE_FILE,\n"
    )
    new = (
        "            kind = self._project_item_kind(item)\n"
        "            if kind in {PROJECT_NODE_PASCAL_TARGET_SOURCE, PROJECT_NODE_PASCAL_TABLE_FILE} or (\n"
        "                kind == PROJECT_NODE_RESOURCE_FILE\n"
        "                and str(item.data(0, Qt.UserRole + 301) or \"\").casefold() == \"pascal\"\n"
        "            ):\n"
        "                self.open_project_item(item)\n"
        "                return\n"
        "            if kind in {\n"
        "                PROJECT_NODE_C64_RESOURCE_FILE, PROJECT_NODE_C64_SOURCE_FILE,\n"
        "                PROJECT_NODE_DBASE_FILE,\n"
    )
    source = replace_one(source, old, new, "Pascal-Einfachklick")

    old = (
        "            kind = self._project_item_kind(item)\n"
        "            if kind == PROJECT_NODE_DBASE_FILE or (\n"
    )
    new = (
        "            kind = self._project_item_kind(item)\n"
        "            if kind in {PROJECT_NODE_PASCAL_TARGET_SOURCE, PROJECT_NODE_PASCAL_TABLE_FILE} or (\n"
        "                kind == PROJECT_NODE_RESOURCE_FILE\n"
        "                and str(item.data(0, Qt.UserRole + 301) or \"\").casefold() == \"pascal\"\n"
        "            ):\n"
        "                return\n"
        "            if kind == PROJECT_NODE_DBASE_FILE or (\n"
    )
    source = replace_one(source, old, new, "Doppelklick-Entdopplung")

    # Defensive Speichernabfrage fuer alle Pascal-Blaetter, egal ob Click,
    # Doppelklick oder expliziter Befehl aus dem Kontextmenue.
    old = (
        "        def open_project_item(\n"
        "            self,\n"
        "            item: QTreeWidgetItem,\n"
        "            _column: int = 0,\n"
        "        ) -> None:\n"
        "            kind = self._project_item_kind(item)\n"
    )
    new = (
        "        def open_project_item(\n"
        "            self,\n"
        "            item: QTreeWidgetItem,\n"
        "            _column: int = 0,\n"
        "        ) -> None:\n"
        "            kind = self._project_item_kind(item)\n"
        "            if not getattr(self, \"_project_skip_pascal_save_question\", False) and (\n"
        "                kind in {PROJECT_NODE_PASCAL_TARGET_SOURCE, PROJECT_NODE_PASCAL_TABLE_FILE}\n"
        "                or (kind == PROJECT_NODE_RESOURCE_FILE\n"
        "                    and str(item.data(0, Qt.UserRole + 301) or \"\").casefold() == \"pascal\")\n"
        "            ) and not self._project_confirm_leave_document(item):\n"
        "                return\n"
        "            if kind == PROJECT_NODE_PASCAL_TARGET_SOURCE:\n"
        "                self._project_last_active_leaf = item\n"
    )
    source = replace_one(source, old, new, "Speichern-Abfrage")

    # Blatt-Kontextmenue: bestehende Kompilier-/Oeffnen-Aktionen behalten;
    # nur Umbenennen hinzufuegen und die Anzeige des Entfernens anpassen.
    old = (
        "            compile_action.setShortcut(QKeySequence(\"F2\"))\n"
        "            open_action = menu.addAction(\"Öffnen\")\n"
        "            menu.addSeparator()\n"
        "            remove_action = menu.addAction(\"Aus Knoten entfernen\")\n"
    )
    new = (
        "            compile_action.setShortcut(QKeySequence(\"F2\"))\n"
        "            open_action = menu.addAction(\"Öffnen\")\n"
        "            rename_action = menu.addAction(\"Umbenennen\")\n"
        "            menu.addSeparator()\n"
        "            remove_action = menu.addAction(\"Aus Projekt entnehmen\")\n"
    )
    source = replace_one(source, old, new, "Pascal-Datei-Kontextmenue")
    old = (
        "            elif selected is open_action:\n"
        "                self.open_project_item(item)\n"
        "            elif selected is remove_action:\n"
        "                self.remove_project_pascal_target_entry(item)\n"
    )
    new = (
        "            elif selected is open_action:\n"
        "                self.open_project_item(item)\n"
        "            elif selected is rename_action:\n"
        "                self._project_rename_pascal_leaf(item)\n"
        "            elif selected is remove_action:\n"
        "                self.remove_project_pascal_target_entry(item)\n"
    )
    source = replace_one(source, old, new, "Pascal-Blatt-Kommandos")

    return source


def syntax_check(source: str) -> None:
    ast.parse(source)
    compile(source, "d64_dism.py", "exec", dont_inherit=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", nargs="?", default=".", help="Repository-Hauptverzeichnis")
    parser.add_argument("--check", action="store_true", help="Nur Anker und Syntax pruefen, nicht schreiben")
    args = parser.parse_args(argv)
    root = Path(args.repository).expanduser().resolve()
    path = root / "d64_dism.py"
    if not path.is_file():
        parser.error(f"Quelldatei nicht gefunden: {path}")

    data = path.read_bytes()
    has_bom = data.startswith(b"\xef\xbb\xbf")
    if b"\r\n" in data and b"\n" in data.replace(b"\r\n", b""):
        raise RuntimeError("Gemischte LF/CRLF-Zeilenenden: aus Schutz vor Reformatierung abgebrochen.")
    encoding = "utf-8-sig" if has_bom else "utf-8"
    text = data.decode(encoding)
    nl = "\r\n" if b"\r\n" in data else "\n"
    if nl == "\r\n":
        text = text.replace("\r\n", "\n")
    result = build_patch(text)
    syntax_check(result)
    output = result.replace("\n", nl).encode(encoding)
    if args.check:
        print(f"PASS: Patch und Python-Syntax gueltig fuer {path}")
        print(f"Alt {len(data)} Bytes, Neu {len(output)} Bytes; nur Menue-/Projekt-Methoden betroffen.")
        return 0

    backup = path.with_name(path.name + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(path, backup)
    temp = path.with_suffix(path.suffix + ".new")
    try:
        with temp.open("wb") as f:
            f.write(output)
            f.flush()
            os.fsync(f.fileno())
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()
    print(f"OK: {path}")
    print(f"Backup: {backup}")
    print("Hinweis: GitHub wurde nicht veraendert. Das lokale Programm bitte unter Windows testen.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, SyntaxError, UnicodeError) as exc:
        print("FEHLER:", exc, file=sys.stderr)
        raise SystemExit(1)
