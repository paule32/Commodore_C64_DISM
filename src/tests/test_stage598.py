"""Stage 598: Projektzuordnung als QToolButton/QMenu statt enger QComboBox.

Widget wird mit Qt-Doubles direkt aus dem Produktionsquelltext getestet;
kein Grafikserver und keine PyQt5-Installation fuer diese Tests notwendig.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class FakeFont:
    def __init__(self, arg=10):
        self.points = arg.points if isinstance(arg, FakeFont) else float(arg)

    def pointSizeF(self):
        return self.points

    def setPointSizeF(self, size):
        self.points = size


class FontInfo:
    def __init__(self, font):
        self.font = font

    def pointSizeF(self):
        return self.font.pointSizeF()


class FontMetrics:
    def __init__(self, font):
        self.font = font

    def horizontalAdvance(self, text):
        return int(len(text) * self.font.points * 0.7)

    def elidedText(self, text, _mode, width):
        if self.horizontalAdvance(text) <= width:
            return text
        allowed = max(0, int(width / (self.font.points * 0.7)) - 1)
        return text[:allowed] + '…'


class FakeQt:
    ToolButtonTextOnly = 1
    ElideRight = 2
    UserRole = 256
    ToolTipRole = 3


class FakeToolButton:
    InstantPopup = 7

    def __init__(self, parent=None):
        self.parent = parent
        self._font = FakeFont(10)
        self._width = 110
        self._text = ''
        self.tooltip = ''
        self.menu = None
        self.currentIndexChanged = Signal()
        self.destroyed = Signal()
        self._blocked = False

    def setToolButtonStyle(self, value):
        self.button_style = value

    def setPopupMode(self, value):
        self.popup_mode = value

    def setSizePolicy(self, *args):
        pass

    def setMenu(self, menu):
        self.menu = menu

    def width(self):
        return self._width

    def font(self):
        return self._font

    def fontMetrics(self):
        return FontMetrics(self._font)

    def setText(self, value):
        self._text = value

    def setToolTip(self, value):
        self.tooltip = value

    def window(self):
        return self.parent.window() if self.parent is not None else self

    def rect(self):
        return type('Rect', (), {'bottomLeft': lambda self: (0, 0)})()

    def mapToGlobal(self, position):
        return position

    def resizeEvent(self, event):
        pass

    def blockSignals(self, flag):
        previous = self._blocked
        self._blocked = flag
        return previous

    def setObjectName(self, value):
        self.name = value

    def setEnabled(self, value):
        self.enabled = value


class FakeAction:
    def __init__(self, text):
        self.text = text
        self.triggered = Signal()
        self.checked = False
        self.tooltip = ''

    def setCheckable(self, value):
        self.checkable = value

    def setChecked(self, value):
        self.checked = value

    def setToolTip(self, value):
        self.tooltip = value


class FakeMenu:
    def __init__(self, host):
        self.host = host
        self.aboutToShow = Signal()
        self.actions = []
        self.minimum_width = None
        self.style = ''
        self.deleted = False

    def deleteLater(self):
        self.deleted = True

    def setObjectName(self, value):
        self.name = value

    def clear(self):
        self.actions.clear()

    def setFont(self, font):
        self.font = font

    def setStyleSheet(self, value):
        self.style = value

    def addAction(self, label):
        action = FakeAction(label)
        self.actions.append(action)
        return action

    def setMinimumWidth(self, width):
        self.minimum_width = width


class FakeScreen:
    class Geometry:
        def width(self):
            return 1440

    def availableGeometry(self):
        return self.Geometry()


class FakeApplication:
    @staticmethod
    def screenAt(position):
        return FakeScreen()

    @staticmethod
    def primaryScreen():
        return FakeScreen()


class FakeParent:
    def __init__(self, dark=False):
        self.dark_mode_enabled = dark

    def window(self):
        return self


class FakeSizePolicy:
    Expanding = 1
    Fixed = 2


def production_button():
    source = (ROOT / 'project_target_menu.py').read_text(encoding='utf-8')
    node = next(x for x in ast.parse(source).body
                if isinstance(x, ast.ClassDef) and x.name == 'ProjectTargetMenuButton')
    node.decorator_list = []
    tree = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                            node], type_ignores=[])
    ast.fix_missing_locations(tree)
    env = {
        'QToolButton': FakeToolButton,
        'QMenu': FakeMenu,
        'QFont': FakeFont,
        'QFontInfo': FontInfo,
        'QFontMetrics': FontMetrics,
        'Qt': FakeQt,
        'QApplication': FakeApplication,
        'QSizePolicy': FakeSizePolicy,
        'pyqtSignal': lambda *_: Signal(),
    }
    exec(compile(tree, 'project_target_menu.py', 'exec'), env)
    return env['ProjectTargetMenuButton']


class Stage598Tests(unittest.TestCase):
    def setUp(self):
        self.Button = production_button()

    def test_popup_is_parented_to_window_not_to_tree_cell(self):
        host = FakeParent()
        b = self.Button(host)
        self.assertIs(b.menu.host, host)
        self.assertEqual(b.popup_mode, FakeToolButton.InstantPopup)
        self.assertEqual(b.menu.name, 'project_target_popup')

    def test_popup_is_released_when_tree_cell_widget_is_destroyed(self):
        b = self.Button(FakeParent())
        menu = b.menu
        b.destroyed.emit()
        self.assertTrue(menu.deleted)

    def test_menu_font_is_exactly_one_point_larger(self):
        b = self.Button(FakeParent())
        b.addItem('Programm: Alpha', 'pascal|program')
        b._rebuild_menu()
        self.assertEqual(b.font().pointSizeF(), 10)
        self.assertEqual(b.menu.font.pointSizeF(), 11)

    def test_full_labels_in_popup_and_elided_button_only(self):
        b = self.Button(FakeParent())
        name = 'Pascal: Bibliothek — SehrLangerProjektname'
        b.addItem(name, 'pascal|library')
        b._rebuild_menu()
        self.assertEqual(b.menu.actions[0].text, name)
        self.assertGreater(b.menu.minimum_width, b.width())
        self.assertNotEqual(b._text, name)
        self.assertEqual(b.tooltip, name)

    def test_action_changes_assignment_without_losing_user_data(self):
        b = self.Button(FakeParent())
        b.addItem('Programm: Foo', 'pascal|program')
        b.addItem('Bibliothek: Bar', 'pascal|library')
        seen = []
        b.currentIndexChanged.connect(seen.append)
        b._rebuild_menu()
        self.assertTrue(b.menu.actions[0].checked)
        b.menu.actions[1].triggered.emit(False)
        self.assertEqual(b.currentData(), 'pascal|library')
        self.assertEqual(b.currentIndex(), 1)
        self.assertEqual(seen, [1])
        self.assertEqual(b.findData('pascal|library'), 1)

    def test_old_combobox_compatible_methods_and_tooltip_role(self):
        b = self.Button(FakeParent())
        b.blockSignals(True)
        b.addItem('Projekt auswählen', '')
        b.addItem('Programm: Foo', 'dbase|program')
        b.setItemData(1, 'dBASE / Programm: Foo', FakeQt.ToolTipRole)
        b.setCurrentIndex(1)
        self.assertEqual(b.itemData(1), 'dbase|program')
        self.assertEqual(b.itemData(1, FakeQt.ToolTipRole), 'dBASE / Programm: Foo')
        b._rebuild_menu()
        self.assertEqual(b.menu.actions[1].tooltip, 'dBASE / Programm: Foo')

    def test_ampersand_is_not_used_as_accidental_menu_hotkey(self):
        b = self.Button(FakeParent())
        b.addItem('Pascal: Programm — A&B', 'pascal|program')
        b._rebuild_menu()
        self.assertEqual(b.menu.actions[0].text, 'Pascal: Programm — A&&B')
        self.assertEqual(b.currentText(), 'Pascal: Programm — A&B')

    def test_theme_is_updated_each_time_menu_is_opened(self):
        host = FakeParent(True)
        b = self.Button(host)
        b.addItem('Programm: Foo', 'basic|program')
        b._rebuild_menu()
        self.assertIn('background:#252d39', b.menu.style)
        host.dark_mode_enabled = False
        b._rebuild_menu()
        self.assertIn('background:#fff', b.menu.style)

    def test_project_tree_and_top_choice_use_new_class(self):
        src = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        self.assertIn('self.project_name_combo = ProjectTargetMenuButton(tab)', src)
        self.assertIn('combo = ProjectTargetMenuButton(tree)', src)
        self.assertIn('if not isinstance(combo, ProjectTargetMenuButton)', src)
        self.assertIn('project_name_combo.currentIndexChanged.connect', src)
        self.assertIn('combo.currentIndexChanged.connect', src)
        self.assertIn('QToolButton#project_leaf_name_combo::menu-indicator', src)
        self.assertNotIn('combo = QComboBox(tree)', src)


if __name__ == '__main__':
    unittest.main()
