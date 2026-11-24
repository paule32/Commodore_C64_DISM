"""Stage 684: project-settings tooltips are limited to the visible right pane."""
from __future__ import annotations

from pathlib import Path

from project_settings_tooltips import tooltip_html, wrap_tooltip_lines

HERE = Path(__file__).resolve().parent


def test_pixel_width_wrapping_preserves_all_words():
    text = ("Komprimiert JSON-Linker-Metadaten in COFF-Objekten mit zlib. "
            "Der interne Linker entpackt die Daten automatisch.")
    # Simulate a proportional font; character count is not the same as width.
    def measure(t):
        return sum(9 if c in 'MW' else (3 if c in 'il.,' else 6) for c in t)

    lines = wrap_tooltip_lines(text, 137, measure)
    assert len(lines) >= 4
    assert all(measure(line) <= 137 for line in lines)
    assert ' '.join(lines) == text


def test_very_long_unbroken_tokens_wrap_inside_the_token():
    value = 'C:/sehr/langer/ordner/mit/einerextremlangenDatei.obj'
    lines = wrap_tooltip_lines(value, 50, lambda text: len(text) * 5)
    assert len(lines) > 1
    assert ''.join(lines) == value
    assert all(len(line) <= 10 for line in lines)


def test_existing_newlines_and_html_sensitive_characters():
    value = 'Zeile eins\n\n<pfad> & "Name"'
    lines = wrap_tooltip_lines(value, 200, lambda text: len(text) * 5)
    assert lines == ['Zeile eins', '', '<pfad> & "Name"']
    markup = tooltip_html(value, 200, lambda text: len(text) * 5)
    assert markup == '<qt>Zeile eins<br/><br/>&lt;pfad&gt; &amp; &quot;Name&quot;</qt>'


def test_narrow_width_remains_bounded():
    value = 'ÄÖÜlong string'
    lines = wrap_tooltip_lines(value, 1, lambda text: len(text) * 9)
    assert ''.join(lines).replace(' ', '') == value.replace(' ', '')
    assert all(len(line) <= 1 for line in lines)


def test_integration_is_scoped_to_project_settings_and_dynamic_right_pane():
    source = (HERE / 'd64_dism.py').read_text(encoding='utf-8')
    module = (HERE / 'project_settings_tooltips.py').read_text(encoding='utf-8')
    assert 'from project_settings_tooltips import install_project_settings_tooltip_limiter' in source
    assert 'install_project_settings_tooltip_limiter(dock, panel, scroll)' in source
    assert 'self.project_settings_dock = dock' in source
    assert 'tab is self._panel.windows_tab' in module
    assert 'self._panel.windows_arch_tabs.currentWidget()' in module
    assert 'tab is self._panel.c64_tab' in module
    assert 'self._panel.c64_arch_tabs.currentWidget()' in module
    assert 'pane_rect.intersected(view_rect).width()' in module
    assert 'if not self._inside_dock(watched):' in module
    assert 'QToolTip.showText(event.globalPos(), formatted, watched)' in module
    assert 'QToolTip.font()' in module
    assert 'Qt.ToolTipRole' in module
