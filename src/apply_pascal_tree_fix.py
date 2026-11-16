from pathlib import Path
import argparse, ast, shutil

def one(s,a,b):
    if s.count(a)!=1: raise RuntimeError(f'Anker {a[:60]!r}: {s.count(a)} Treffer')
    return s.replace(a,b,1)

def patch(s):
    a='''            parent_item = group_item
            display_title = title.strip() or resolved.name or path_text
            if role == "units":
                namespace, leaf_title = project_pascal_unit_tree_parts(
                    resolved, display_title
                )
                namespace_item = self._project_pascal_unit_namespace_item(
                    group_item, namespace
                )
                if namespace_item is None:
                    return None
                parent_item = namespace_item
                display_title = leaf_title

            child = QTreeWidgetItem(parent_item, [display_title])'''
    b='''            parent_item = group_item
            display_title = title.strip() or resolved.name or path_text
            child = QTreeWidgetItem(parent_item, [display_title])'''
    s=one(s,a,b)
    a='''            sequence = 0
            for namespace_index in range(group_item.childCount()):
                namespace_item = group_item.child(namespace_index)
                if self._project_item_kind(namespace_item) != PROJECT_NODE_PASCAL_UNIT_NAMESPACE:
                    continue
                for leaf_index in range(namespace_item.childCount()):
                    leaf = namespace_item.child(leaf_index)
                    if self._project_item_kind(leaf) != PROJECT_NODE_PASCAL_TARGET_SOURCE:
                        continue
                    leaf.setData(0, Qt.UserRole + 308, sequence)
                    sequence += 1'''
    b='''            sequence = 0
            for leaf in self._project_pascal_source_items(group_item):
                leaf.setData(0, Qt.UserRole + 308, sequence)
                sequence += 1'''
    s=one(s,a,b)
    s=one(s,'''            if bool(item.data(0, Qt.UserRole + 307)):
                self._activate_unsaved_c64_leaf(item)
                return''','''            if (self._project_item_kind(item) == PROJECT_NODE_C64_SOURCE_FILE
                    and bool(item.data(0, Qt.UserRole + 307))):
                self._activate_unsaved_c64_leaf(item)
                return''')
    s=one(s,'''            if bool(item.data(0, Qt.UserRole + 307)):
                menu = self._project_popup_menu()
                edit_action = menu.addAction("Im Editor öffnen")''','''            if (kind == PROJECT_NODE_C64_SOURCE_FILE
                    and bool(item.data(0, Qt.UserRole + 307))):
                menu = self._project_popup_menu()
                edit_action = menu.addAction("Im Editor öffnen")''')
    s=one(s,'("Neu:  MS Windows 64 Bit Unit", "unit", "pe32"),','("Neu:  MS Windows 64 Bit Unit", "unit", "pe64"),')
    helper='''def _style_green_beige_editor_popup(menu):
    """Gleiche Farben wie das Hauptmenue, ohne QAction-Logik zu aendern."""
    window = QApplication.activeWindow()
    while window is not None and not callable(getattr(window, "_green_beige_menu_stylesheet", None)):
        window = window.parentWidget()
    if window is None:
        for widget in QApplication.topLevelWidgets():
            if callable(getattr(widget, "_green_beige_menu_stylesheet", None)):
                window = widget
                break
    if window is not None:
        menu.setObjectName("green_beige_popup_menu")
        menu.setAttribute(Qt.WA_StyledBackground, True)
        menu.setStyleSheet(window._green_beige_menu_stylesheet())


'''
    s=one(s,'def _execute_german_source_editor_context_menu(editor, global_position):\n    menu = editor.createStandardContextMenu()',helper+'def _execute_german_source_editor_context_menu(editor, global_position):\n    menu = editor.createStandardContextMenu()\n    _style_green_beige_editor_popup(menu)')
    s=one(s,'            standard_menu = self.createStandardContextMenu()\n            _translate_source_editor_context_menu(standard_menu)','            standard_menu = self.createStandardContextMenu()\n            _style_green_beige_editor_popup(standard_menu)\n            _translate_source_editor_context_menu(standard_menu)')
    s=one(s,'                menu = QMenu(self)\n                run_action = menu.addAction("Ausführen")','                menu = QMenu(self)\n                _style_green_beige_editor_popup(menu)\n                run_action = menu.addAction("Ausführen")')
    s=one(s,'                wrapper = QMenu(self)\n                create_action = wrapper.addAction("Neu Assembler")','                wrapper = QMenu(self)\n                _style_green_beige_editor_popup(wrapper)\n                create_action = wrapper.addAction("Neu Assembler")')
    s=one(s,'            menu = widget.createStandardContextMenu()\n            _dbase_translate_grid_editor_context_menu(menu)','            menu = widget.createStandardContextMenu()\n            _style_green_beige_editor_popup(menu)\n            _dbase_translate_grid_editor_context_menu(menu)')
    return s

def main():
    p=argparse.ArgumentParser();p.add_argument('repository');p.add_argument('--check',action='store_true');args=p.parse_args()
    f=Path(args.repository).expanduser().resolve()/'d64_dism.py'
    raw=f.read_bytes();bom=raw.startswith(b'\xef\xbb\xbf'); nl='\r\n' if b'\r\n' in raw else '\n'
    s=raw.decode('utf-8-sig').replace('\r\n','\n'); out=patch(s);ast.parse(out)
    if args.check: print('OK: alle Anker und Python-Syntax geprüft');return
    backup=f.with_name('d64_dism.py.before_pascal_tree_fix.bak')
    if backup.exists(): raise FileExistsError(str(backup))
    shutil.copy2(f,backup)
    f.write_bytes((b'\xef\xbb\xbf' if bom else b'')+out.replace('\n',nl).encode('utf-8'))
    print('Fertig:',f,'\nBackup:',backup)
if __name__=='__main__': main()
