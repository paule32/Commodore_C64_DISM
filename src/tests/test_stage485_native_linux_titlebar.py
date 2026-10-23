"""Stage 485: native Linux titlebar and unchanged frameless Windows chrome.

These tests isolate the real menu chrome factory with Qt stand-ins, because
PyQt5 and a native Linux/Windows display server are not required to run them.
"""
from pathlib import Path
from types import SimpleNamespace
import textwrap


SOURCE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')


class Widget:
    def __init__(self, *args):
        self.args = args
        self.children = []
        self.name = None
        self.height = None
        self.native_menu = None
    def setObjectName(self, name):
        self.name = name
    def setSizePolicy(self, *args):
        self.policy = args
    def setFixedHeight(self, height):
        self.height = height
    def setNativeMenuBar(self, value):
        self.native_menu = value
    def setAttribute(self, *args):
        self.attribute = args
    def setContentsMargins(self, *args):
        self.margins = args
    def setSpacing(self, value):
        self.spacing = value
    def addWidget(self, child):
        self.children.append(child)


class Layout:
    def __init__(self, parent):
        self.parent = parent
        parent.layout = self
        self.children = []

    def setContentsMargins(self, *args):
        self.margins = args

    def setSpacing(self, value):
        self.spacing = value

    def addWidget(self, child):
        self.children.append(child)


class ChromeMain:
    def __init__(self, custom):
        self._use_custom_main_title_bar = custom
        self.menu_widget = None
        self.styled = False
    def setMenuWidget(self, widget):
        self.menu_widget = widget
    def _apply_green_beige_chrome_style(self):
        self.styled = True


def factory():
    start = SOURCE.index('        def _create_green_beige_window_chrome(self) -> None:')
    end = SOURCE.index('\n        def _green_beige_menu_stylesheet', start)
    body = textwrap.dedent(SOURCE[start:end])
    ns = dict(
        QWidget=Widget,
        QMenuBar=Widget,
        QVBoxLayout=Layout,
        GreenBeigeTitleBar=Widget,
        QSizePolicy=SimpleNamespace(Expanding=1, Fixed=2),
        Qt=SimpleNamespace(WA_StyledBackground=9),
    )
    exec(body, ns)
    return ns['_create_green_beige_window_chrome']


def test_linux_has_only_native_window_titlebar_and_embedded_menu():
    window = ChromeMain(custom=False)
    factory()(window)
    assert not hasattr(window, 'main_title_bar')
    assert window.menu_widget is window.main_top_chrome
    assert window.main_top_chrome.name == 'green_beige_top_chrome'
    assert window.main_menu_bar.name == 'green_beige_menu_bar'
    assert window.main_menu_bar.native_menu is False
    assert window.main_menu_bar.height == 31
    assert window.styled
    # The client area starts directly at the menu without a dummy titlebar.
    assert window.main_top_chrome.layout.children == [window.main_menu_bar]
    assert window.main_top_chrome.layout.margins == (0, 0, 0, 0)
    assert window.main_top_chrome.layout.spacing == 0


def test_windows_keeps_existing_titlebar_buttons_and_menu():
    window = ChromeMain(custom=True)
    factory()(window)
    assert hasattr(window, 'main_title_bar')
    assert window.main_title_bar.args == (window, window.main_top_chrome)
    assert window.main_menu_bar.native_menu is False
    assert window.main_top_chrome.layout.children == [
        window.main_title_bar, window.main_menu_bar
    ]
    assert window.styled


def test_platform_flags_and_custom_resize_are_windows_only():
    start = SOURCE.index('            self._use_custom_main_title_bar = sys.platform == "win32"')
    end = SOURCE.index('            # Stage 240:', start)
    init = SOURCE[start:end]
    assert 'if self._use_custom_main_title_bar:' in init
    assert 'Qt.FramelessWindowHint' in init
    assert 'self.setWindowFlag(Qt.FramelessWindowHint, False)' in init
    assert 'self.setContentsMargins(0, 0, 0, 0)' in init
    assert 'if self._use_custom_main_title_bar:\n                self._update_frameless_corner_mask()' in SOURCE
    assert 'if self._use_custom_main_title_bar:\n                self._create_frameless_resize_overlays()' in SOURCE
    # Existing resize overlays and border painting already have their own
    # explicit win32 checks, so they cannot cover Linux native decorations.
    assert 'def _create_frameless_resize_overlays(self)' in SOURCE
    assert 'if sys.platform != "win32":' in SOURCE


def test_window_title_sync_call_sites_are_optional():
    assert 'if hasattr(self, "main_title_bar"):' in SOURCE
    assert 'self.main_title_bar.sync_window_state()' in SOURCE
    assert 'self.main_title_bar.update()' in SOURCE
