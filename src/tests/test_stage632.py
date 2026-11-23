"""Stage 632: Fensterlisten-API des blauen Turbo-Vision-Editors."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
EDITOR = (ROOT / "d64qt5/d64_turbo_editor.hpp").read_text(encoding="utf-8")
BRIDGE = (ROOT / "d64qt5/d64qt5_bridge.cpp").read_text(encoding="utf-8")


def test_public_caption_method_for_window_menu():
    start = EDITOR.index("class D64TurboEditorWidget final : public QWidget")
    scope = EDITOR[start:]
    public = scope.index("public:")
    private = scope.find("private:", public)
    assert private > public
    public_code = scope[public:private]
    assert re.search(r"QString\s+windowCaption\(\)\s+const", public_code)
    assert "QStringLiteral(\"Unbenannt\")" in public_code
    assert "QFileInfo(relativeFile_).fileName()" in public_code
    assert "isModified() ? QStringLiteral(\" *\")" in public_code


def test_title_and_window_menu_reuse_the_same_caption():
    assert 'title_->setText(QStringLiteral(" Editor – %1 ").arg(windowCaption()));' in EDITOR
    assert 'arg(editor->windowCaption())' in BRIDGE
    assert 'QStringLiteral("Editor %1 – %2")' in BRIDGE


def test_editor_still_has_original_activation_and_file_support():
    for marker in (
        'void activate()',
        'bool saveDocument(bool forceDialog = false)',
        'bool openDocument()',
        'bool confirmClose()',
        'void setClosedCallback(',
        'D64VirtualFileDialog dialog(',
        'QPlainTextEdit *textEditor() const',
    ):
        assert marker in EDITOR


def test_window_menu_still_builds_dynamic_entries():
    for marker in (
        'void rebuild_turbo_windows_menu()',
        'void layout_turbo_windows(bool cascade)',
        'QStringLiteral("Kaskadieren")',
        'QStringLiteral("Nebeneinander")',
        'activate_turbo_window(guarded.data())',
    ):
        assert marker in BRIDGE
