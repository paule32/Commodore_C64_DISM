"""Stage 606: headless widget-hierarchy and named-project layout regression tests.

The actual PyQt5 window needs testing on Windows. This suite executes the
unchanged _create_project_tab method with minimal widget/layout stand-ins so
that its ownership, structure and signals are verified without Qt installed.
"""
from __future__ import annotations

import re
import textwrap
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("d64_dism.py").read_text(encoding="utf-8")


class Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, fn):
        self.callbacks.append(fn)

    def emit(self, *args):
        for fn in self.callbacks:
            fn(*args)


class Widget:
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.children = []
        self.attrs = {}
        self.object_name = ""
        self.text = ""
        self.style_sheet = ""
        self.clicked = Signal()
        self.currentIndexChanged = Signal()
        self.returnPressed = Signal()
        self.textChanged = Signal()
        self.customContextMenuRequested = Signal()
        self.itemDoubleClicked = Signal()
        self.itemClicked = Signal()
        self.itemChanged = Signal()
        if isinstance(parent, Widget):
            parent.children.append(self)

    def __getattr__(self, name):
        if name.startswith("set"):
            def setter(*values):
                self.attrs[name] = values
            return setter
        raise AttributeError(name)

    def setObjectName(self, name):
        self.object_name = name

    def setText(self, text):
        self.text = text
        self.textChanged.emit(text)

    def setStyleSheet(self, stylesheet):
        self.style_sheet = stylesheet


class TextWidget(Widget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text


class Layout:
    def __init__(self, parent=None):
        self.parent = parent
        self.widgets = []
        self.layouts = []
        self.cells = {}
        if isinstance(parent, Widget):
            parent.layout = self

    def __getattr__(self, name):
        if name.startswith("set"):
            def setter(*values):
                setattr(self, name + "_args", values)
            return setter
        raise AttributeError(name)

    def addWidget(self, widget, *args):
        self.widgets.append(widget)
        if len(args) >= 2:
            self.cells[(args[0], args[1])] = widget
        if hasattr(self, 'parent') and isinstance(self.parent, Widget):
            widget.parent = self.parent

    def addLayout(self, layout, *args):
        self.layouts.append(layout)


class Header(Widget):
    pass


class Tree(Widget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._header = Header(self)
        self._model = Model()

    def header(self):
        return self._header

    def model(self):
        return self._model


class Model:
    def __init__(self):
        self.rowsInserted = Signal()
        self.rowsRemoved = Signal()


class Splitter(Widget):
    def __init__(self, direction, parent=None):
        super().__init__(parent)
        self.direction = direction
        self.widgets = []
        self.sizes = []
        self.stretches = {}

    def addWidget(self, widget):
        self.widgets.append(widget)
        widget.parent = self

    def setStretchFactor(self, index, factor):
        self.stretches[index] = factor

    def setSizes(self, sizes):
        self.sizes = list(sizes)


class ScrollArea(Widget):
    def setWidget(self, widget):
        self.widget = widget
        widget.parent = self


class LineEdit(Widget):
    Normal = 0

    def text_(self):
        return self.text


class Styler:
    def standardIcon(self, name):
        return ("icon", name)


class FakeMain:
    def __init__(self):
        self.created = False
        self.events = []
        self.dark_mode_enabled = True

    def style(self):
        return Styler()

    def _project_tree_checkbox_stylesheet(self):
        return "checkbox_css"

    def _project_named_tree_header_stylesheet(self):
        return "tree_header_css"

    def _project_named_panel_stylesheet(self):
        return "panel_css"

    def reset_project_tree(self):
        self.created = True

    def __getattr__(self, name):
        if name.startswith(("choose_", "load_", "save_", "new_", "show_", "_on_", "_project_named_")):
            def handle(*args):
                self.events.append((name, args))
            return handle
        raise AttributeError(name)


class Qt:
    Vertical = "vertical"
    AlignVCenter = 1
    AlignRight = 2
    ScrollBarAsNeeded = 3
    CustomContextMenu = 4


class QFrame:
    NoFrame = 0


class QStyle:
    SP_DialogOpenButton = 10
    SP_DirIcon = 11


class QHeaderView:
    Interactive = 1


class QSizePolicy:
    Expanding = 1
    Fixed = 2


class QAbstractItemView:
    ExtendedSelection = 1
    SelectRows = 2


def method_body(name):
    match = re.search(rf"^        def {name}\(.*", SOURCE, re.M)
    if match is None:
        raise AssertionError(f"missing MainWindow.{name}")
    # Every method on this nested MainWindow class starts with 8-space indent.
    following = re.search(r"^        def \w+\(", SOURCE[match.end():], re.M)
    end = (match.end() + following.start()) if following else len(SOURCE)
    code = textwrap.dedent(SOURCE[match.start():end])
    # Remove sibling-level comments that precede the next definition, if any.
    return code


def fixture():
    import project_named_targets
    ns = {
        "QWidget": Widget,
        "QVBoxLayout": Layout,
        "QHBoxLayout": Layout,
        "QGridLayout": Layout,
        "QToolButton": Widget,
        "QLineEdit": LineEdit,
        "QLabel": TextWidget,
        "QTreeWidget": Tree,
        "QScrollArea": ScrollArea,
        "QSplitter": Splitter,
        "ProjectTargetMenuButton": Widget,
        "QPushButton": TextWidget,
        "QFrame": QFrame,
        "QStyle": QStyle,
        "QHeaderView": QHeaderView,
        "QSizePolicy": QSizePolicy,
        "QAbstractItemView": QAbstractItemView,
        "Qt": Qt,
        "NAMED_PROJECT_PROFILE_FIELDS": project_named_targets.PROFILE_FIELDS,
        "normalize_named_project_names": project_named_targets.normalize_names,
    }
    exec(compile(method_body('_create_project_tab'), 'd64_dism.py', 'exec'), ns)
    main = FakeMain()
    tab = ns['_create_project_tab'](main, Widget())
    return main, tab, ns


class Stage606Tests(unittest.TestCase):
    def test_splitter_is_vertical_and_holds_tree_then_scroll(self):
        main, tab, _ = fixture()
        splitter = main.project_tree_name_splitter
        self.assertTrue(main.created)
        self.assertEqual(splitter.object_name, 'project_tree_name_splitter')
        self.assertEqual(splitter.direction, Qt.Vertical)
        self.assertEqual(splitter.widgets, [main.project_tree, main.project_names_scroll_area])
        self.assertEqual(splitter.stretches, {0: 3, 1: 1})
        self.assertEqual(splitter.attrs['setChildrenCollapsible'], (False,))
        self.assertEqual(splitter.attrs['setHandleWidth'], (6,))
        self.assertIn(splitter, tab.layout.widgets)
        self.assertNotIn(main.project_tree, tab.layout.widgets)

    def test_eight_rows_share_one_scrollable_widget(self):
        main, _, _ = fixture()
        scroll = main.project_names_scroll_area
        self.assertEqual(scroll.object_name, 'project_names_scroll_area')
        self.assertEqual(scroll.attrs['setWidgetResizable'], (True,))
        self.assertEqual(scroll.attrs['setVerticalScrollBarPolicy'], (Qt.ScrollBarAsNeeded,))
        self.assertEqual(scroll.widget, main.project_names_scroll_content)
        self.assertEqual(len(main.project_name_edits), 8)
        import project_named_targets
        grid = scroll.widget.layout
        self.assertEqual(len(grid.cells), 8 * 3)
        for i, (language, title) in enumerate(project_named_targets.PROFILE_FIELDS):
            self.assertEqual(grid.cells[i, 0].text, f'{title}:')
            self.assertIs(grid.cells[i, 1], main.project_name_edits[language])
            self.assertEqual(grid.cells[i, 2].object_name, f'project_name_{language}_dialog_button')
        self.assertEqual(grid.setRowStretch_args, (8, 1))

    def test_existing_name_change_signal_still_connected(self):
        main, _, _ = fixture()
        main.project_name_edits['pascal_program'].setText('MeinProgramm')
        self.assertIn(('_project_named_text_changed', ('pascal_program', 'MeinProgramm')), main.events)

    def test_name_dialog_button_still_connected(self):
        main, _, _ = fixture()
        content = main.project_names_scroll_content
        grid = content.layout
        grid.cells[2, 2].clicked.emit(False)
        self.assertIn(('_project_named_edit_dialog', ('pascal_library',)), main.events)

    def test_new_save_buttons_stay_outside_scroll_area(self):
        main, tab, _ = fixture()
        self.assertIs(main.project_new_button.parent, tab)
        self.assertIs(main.project_save_button.parent, tab)
        self.assertIs(main.project_save_as_button.parent, tab)
        self.assertIsNot(main.project_name_combo.parent, main.project_names_scroll_content)

    def test_theme_styles_cover_splitter_and_scroll(self):
        text = method_body('_project_named_panel_stylesheet')
        for object_name in ('project_tree_name_splitter', 'project_names_scroll_area', 'project_names_scroll_content'):
            self.assertGreaterEqual(text.count(object_name), 2)
        self.assertIn('self.dark_mode_enabled', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
