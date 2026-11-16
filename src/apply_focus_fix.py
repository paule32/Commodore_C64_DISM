#!/usr/bin/env python3
"""Patch project-leaf tab activation and editor keyboard focus in Commodore_C64_DISM.

Reference: paule32/Commodore_C64_DISM, main, src/d64_dism.py
Original Git blob: 89a1b394bf96aa960b412b8dbcafb1189ad8be5f
The previous Pascal-tree / editor-menu changes are already included in this revision.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path
import sys

TARGET = Path("d64_dism.py")
BASE_BLOB = "89a1b394bf96aa960b412b8dbcafb1189ad8be5f"

# Class method: no tab is created when the document is already open.
# The delayed callback lets Qt finish routing mouse/focus events from QTreeWidget.
# It must not steal the focus if the user changed tabs in the meantime.
HELPER = '''        def _project_activate_document_tab(
            self, document: Optional[DocumentEditor]
        ) -> None:
            """Select an existing document tab and focus its real editor widget."""
            if not isinstance(document, DocumentEditor):
                return
            if self._document_index(document) < 0:
                return
            self.document_tabs.setCurrentWidget(document)
            self._update_document_tab(document)
            document.focus_preferred_editor()

            def focus_after_tree_click(value=document):
                try:
                    if (
                        self._document_index(value) >= 0
                        and self.document_tabs.currentWidget() is value
                    ):
                        value.focus_preferred_editor()
                except RuntimeError:
                    # Tab/editor may have been closed before the queued callback.
                    pass

            QTimer.singleShot(0, focus_after_tree_click)

'''


REPLACEMENTS = [
    (
        # Existing unsaved C64 source file already selects the document tab.
        # Delegate the focus scheduling to the same central routine.
        '''                    self.document_tabs.setCurrentWidget(document)
                    document.focus_preferred_editor()
                    return True
            # Blatt eines bereits geschlossenen ungespeicherten Dokuments''',
        '''                    self._project_activate_document_tab(document)
                    return True
            # Blatt eines bereits geschlossenen ungespeicherten Dokuments''',
    ),
    (
        # Regular C64 source leaf: click activates the document (new or open).
        '''            if kind == PROJECT_NODE_C64_SOURCE_FILE:
                path = Path(str(item.data(0, Qt.UserRole + 302) or ""))
                if path.is_file():
                    self.open_document(path)
                else:''',
        '''            if kind == PROJECT_NODE_C64_SOURCE_FILE:
                path = Path(str(item.data(0, Qt.UserRole + 302) or ""))
                if path.is_file():
                    if self.open_document(path):
                        self._project_activate_document_tab(
                            self._find_open_document(path)
                        )
                else:''',
    ),
    (
        # dBase text programs in the project tree are source editors too.
        '''                if role == "programs":
                    if self.open_document(path, language_override="dbase"):
                        self._remember_recent_file(path)''',
        '''                if role == "programs":
                    if self.open_document(path, language_override="dbase"):
                        self._project_activate_document_tab(
                            self._find_open_document(path)
                        )
                        self._remember_recent_file(path)''',
    ),
    (
        # Important bug: _project_pascal_document() returns a valid document
        # but DOES NOT select the tab if the file was already open.
        '''                            document = self._project_pascal_document(path, target)
                            if document is not None:
                                target_name = (''',
        '''                            document = self._project_pascal_document(path, target)
                            if document is not None:
                                self._project_activate_document_tab(document)
                                target_name = (''',
    ),
    (
        # Other Pascal/COFF input leaves, including .o/.obj, keep their
        # existing open_document() routing and get focus if they have a tab.
        '''                        else:
                            self.open_document(path)
                    else:
                        self.show_error(
                            "Pascal-Projektdatei nicht gefunden",''',
        '''                        else:
                            if self.open_document(path):
                                self._project_activate_document_tab(
                                    self._find_open_document(path)
                                )
                    else:
                        self.show_error(
                            "Pascal-Projektdatei nicht gefunden",''',
    ),
    (
        # Generic text leaves opened with double-click/context menu.
        '''            if path.suffix.casefold() in self.EDITOR_EXTENSIONS:
                self.open_document(path)
            else:
                self.open_path(path)''',
        '''            if path.suffix.casefold() in self.EDITOR_EXTENSIONS:
                if self.open_document(path):
                    self._project_activate_document_tab(
                        self._find_open_document(path)
                    )
            else:
                self.open_path(path)''',
    ),
]

INSERTION_ANCHOR = '''        def _project_pascal_document(
            self,
            path: Path,
            target: str,
        ) -> Optional[DocumentEditor]:'''


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def patch_text(source: str) -> str:
    if source.count(INSERTION_ANCHOR) != 1:
        raise ValueError("Cannot locate exactly one _project_pascal_document definition")
    if "def _project_activate_document_tab(" in source:
        raise ValueError("Focus patch appears already applied; no changes made")
    patched = source.replace(INSERTION_ANCHOR, HELPER + INSERTION_ANCHOR, 1)
    for i, (old, new) in enumerate(REPLACEMENTS, 1):
        number = patched.count(old)
        if number != 1:
            raise ValueError(f"Patch context #{i} occurred {number} times (expected 1)")
        patched = patched.replace(old, new, 1)
    if patched.count("self._project_activate_document_tab(") != len(REPLACEMENTS):
        raise ValueError("Unexpected number of editor activation calls")
    ast.parse(patched, filename=str(TARGET))
    return patched


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(),
                        help="Local Commodore_C64_DISM working tree")
    parser.add_argument("--check", action="store_true", help="Validate only; do not write")
    args = parser.parse_args(argv)

    path = args.repo / TARGET
    if not path.is_file():
        parser.error(f"Missing source file: {path}")
    raw = path.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    sha = git_blob_sha(lf)
    if sha != BASE_BLOB:
        parser.error(
            f"File differs from the verified GitHub revision (blob={sha}, "
            f"expected={BASE_BLOB}). Nothing changed."
        )
    try:
        result = patch_text(lf.decode("utf-8"))
    except (UnicodeError, ValueError, SyntaxError) as exc:
        print(f"Patch failed: {exc}", file=sys.stderr)
        return 1
    print(f"Patch validation and Python syntax check OK: {path}")
    if args.check:
        print("Dry run – nothing written")
        return 0

    backup = path.with_name(path.name + ".before_project_editor_focus.bak")
    if backup.exists():
        parser.error(f"Backup exists: {backup}; nothing changed")
    backup.write_bytes(raw)
    updated = result.encode("utf-8")
    if b"\r\n" in raw:
        updated = updated.replace(b"\n", b"\r\n")
    try:
        path.write_bytes(updated)
    except OSError:
        path.write_bytes(raw)
        raise
    print(f"Modified: {path}")
    print(f"Backup: {backup}")
    print("GUI test under Windows/PyQt5 remains necessary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
