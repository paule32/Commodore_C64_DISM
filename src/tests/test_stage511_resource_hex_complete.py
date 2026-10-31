# -*- coding: utf-8 -*-
"""Stage 511: HEX overview must include every compiled RC entry, including MENU."""
import ast
import textwrap
from pathlib import Path
from types import SimpleNamespace

from test_stage504_resource_hex_codepage import SCOPE

SOURCE = Path(__file__).with_name('d64_dism.py').read_text('utf-8')
TREE = ast.parse(SOURCE)


def _extract(name, top_level=True):
    nodes = TREE.body if top_level else next(
        c for c in TREE.body if isinstance(c, ast.ClassDef) and c.name == 'WindowsResourceEditorWidget').body
    node = next(n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name)
    return textwrap.dedent(''.join(SOURCE.splitlines(True)[node.lineno - 1:node.end_lineno]))

SCOPE['describe_resource_id'] = SCOPE['describe_resource_id']
exec(_extract('format_resource_collection_hex'), SCOPE)

SOURCE_RC = '''#pragma code_page(1200)
LANGUAGE 0x0007, 0x01
STRINGTABLE
BEGIN
1 "Deutsch Form"
2 "Drück mich"
3 "Schließen"
4 "Name"
5 "Vorname"
6 "Auswahl 1"
7 "Auswahl 2"
8 "Blau"
9 "Rot"
10 "Rot"
11 "Gelb"
12 "Grün"
13 "Kreis"
14 "Quadrat"
15 "Dies ist kein Fehler. Ich wette, das Sie den Button gedrückt haben."
16 "Alaram !"
17 "OK"
END
100 MENU
BEGIN
    POPUP "Datei"
    BEGIN
        MENUITEM "Öffnen", 3011
        MENUITEM SEPARATOR
        MENUITEM "Beenden", 3012
    END
    POPUP "Hilfe"
    BEGIN
        MENUITEM "Über ...", 3013
    END
END
'''


def entries(tmp_path):
    path = tmp_path / 'Resource32.rc'
    path.write_text(SOURCE_RC, encoding='utf-8')
    return SCOPE['compile_rc'](path).entries


def test_compiler_produces_two_string_blocks_and_menu(tmp_path):
    items = entries(tmp_path)
    assert [(e.type_id, e.name_id) for e in items] == [
        (SCOPE['RT_STRING'], 1), (SCOPE['RT_STRING'], 2), (SCOPE['RT_MENU'], 100)]
    assert [len(e.data) for e in items] == [346, 52, 98]


def test_hex_overview_shows_all_compiled_binary_sections(tmp_path):
    items = entries(tmp_path)
    before = [bytes(e.data) for e in items]
    hex_text = SCOPE['format_resource_collection_hex'](items)
    assert '3 Einträge, 496 Bytes Nutzdaten' in hex_text
    assert '[1/3] STRINGTABLE (6) | ID 1' in hex_text
    assert '[2/3] STRINGTABLE (6) | ID 2' in hex_text
    assert '[3/3] MENU (4) | ID 100' in hex_text
    assert 'MENU (4) | ID 100 | LANGID 0x0407 | 98 Bytes' in hex_text
    assert '00000000' in hex_text
    assert 'Offset' in hex_text
    assert [bytes(e.data) for e in items] == before


def test_grouped_view_limits_only_to_one_type(tmp_path):
    items = entries(tmp_path)
    result = SCOPE['format_resource_collection_hex'](items, resource_type_label='MENU (4)')
    assert '1 Einträge, 98 Bytes' in result
    assert 'MENU (4) | ID 100' in result
    assert 'STRINGTABLE' not in result


def test_empty_overview_is_explicit():
    assert 'Keine kompilierten' in SCOPE['format_resource_collection_hex']([])


def test_real_gui_has_all_resources_checkbox_default_on():
    assert 'self.hex_all_resources.setChecked(True)' in SOURCE
    assert 'self.hex_all_resources.toggled.connect(self._refresh_hex_scope)' in SOURCE
    assert 'self.tabs.addTab(hex_page, "Hex")' in SOURCE
    assert '("group", type_label)' in SOURCE


def test_hex_mode_switches_between_overview_leaf_and_group(tmp_path):
    namespace = {
        'format_resource_collection_hex': SCOPE['format_resource_collection_hex'],
        'format_resource_hex': SCOPE['format_resource_hex'],
    }
    class Qt: UserRole = 0x100
    namespace['Qt'] = Qt
    exec(_extract('_refresh_hex_scope', top_level=False), namespace)
    callback = namespace['_refresh_hex_scope']

    class Editor:
        def __init__(self): self.value = ''
        def setPlainText(self, value): self.value = value
        def clear(self): self.value = ''
    class Selection:
        def __init__(self, value): self.value = value
        def data(self, col, role): return self.value
    class Tree:
        current = None
        def currentItem(self): return Selection(self.current)
    class Toggle:
        checked = True
        def isChecked(self): return self.checked

    class Widget:
        _refresh_hex_scope = callback
        def __init__(self):
            self.entries = entries(tmp_path)
            self.hex_edit = Editor()
            self.resource_tree = Tree()
            self.hex_all_resources = Toggle()
    gui = Widget()
    gui.resource_tree.current = 0
    gui._refresh_hex_scope()
    assert 'MENU (4) | ID 100' in gui.hex_edit.value
    gui.hex_all_resources.checked = False
    gui._refresh_hex_scope()
    assert 'MENU (4)' not in gui.hex_edit.value
    assert '00000150  61 00 62 00 65 00 6E 00' in gui.hex_edit.value
    gui.resource_tree.current = ('group', 'MENU (4)')
    gui._refresh_hex_scope()
    assert 'MENU (4) | ID 100' in gui.hex_edit.value
    assert 'STRINGTABLE' not in gui.hex_edit.value
    gui.resource_tree.current = 2
    gui._refresh_hex_scope()
    assert 'MENU (4) | ID 100' not in gui.hex_edit.value
    assert 'Offset' in gui.hex_edit.value
