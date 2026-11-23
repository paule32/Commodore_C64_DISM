"""Stage 630: Scrollbar-Geometrie und identische Editor-Optik.

Die Geometrie wird als echtes C++-Programm getestet, ohne Qt vorauszusetzen.
Native Qt5-/MinGW32-Interaktion muss weiterhin unter Windows validiert werden.
"""
from pathlib import Path
import shutil
import subprocess
import textwrap

import pytest

ROOT = Path(__file__).resolve().parent
BAR = (ROOT / 'd64qt5/d64_turbo_scrollbar.hpp').read_text(encoding='utf-8')
GEOMETRY = (ROOT / 'd64qt5/d64_turbo_scroll_geometry.hpp').read_text(encoding='utf-8')
EDITOR = (ROOT / 'd64qt5/d64_turbo_editor.hpp').read_text(encoding='utf-8')
OUTPUT = (ROOT / 'd64qt5/d64_turbo_output.hpp').read_text(encoding='utf-8')


def test_editor_scrollbars_use_one_shared_blue_gray_theme():
    # Stage 645 benutzt dieselbe Theme-Routine zusaetzlich in beiden Dateilisten.
    assert EDITOR.count('setTurboEditorTheme();') == 4
    assert 'D64TurboArrowScrollBar(Qt::Vertical, edit_)' in EDITOR
    assert 'D64TurboArrowScrollBar(Qt::Horizontal, this)' in EDITOR
    for value in ['#0000aa', '#000080', '#686868', '#bababa', '#353535', '#9999ad']:
        assert value in BAR
    assert EDITOR.count('background:#686868;') == 2
    assert 'dottedGroove_ = true;' in BAR


def test_arrow_areas_remain_solid_blue_not_dotted():
    assert 'painter.fillRect(button, arrowBackground_)' in BAR
    assert 'painter.fillRect(groove, grooveBackground_)' in BAR
    assert 'painter.setClipRect(groove)' in BAR
    assert 'painter.drawPoint(x, y);' in BAR
    assert 'painter.setClipRect(button)' in BAR


def test_same_geometry_drives_draw_and_mouse_interaction():
    assert BAR.count('geometryForCurrentValue()') >= 4
    assert 'thumbRect(g)' in BAR
    assert 'arrowStartRect(g)' in BAR
    assert 'arrowEndRect(g)' in BAR
    assert 'g.valueForThumbStart(axisCoordinate(event->pos()) - dragOffset_)' in BAR
    assert 'style()->subControlRect(' not in BAR
    assert 'QScrollBar::paintEvent(event)' not in BAR


def test_native_scrollbar_signals_and_keyboard_wheel_behavior_preserved():
    assert 'class D64TurboArrowScrollBar final : public QScrollBar' in BAR
    assert 'setSliderPosition(' in BAR
    assert 'setRepeatAction(' in BAR
    assert 'QScrollBar::mouseMoveEvent(event);' in BAR
    assert 'horizontalBar_, &QScrollBar::setValue' in EDITOR
    assert 'internalH, &QScrollBar::setValue' in EDITOR


def test_green_output_remains_green_and_uses_its_original_arrows():
    assert 'D64TurboArrowScrollBar(Qt::Vertical, editor_)' in OUTPUT
    assert 'D64TurboArrowScrollBar(Qt::Horizontal, editor_)' in OUTPUT
    assert 'setTurboEditorTheme()' not in OUTPUT
    assert '#55bf62' in OUTPUT
    assert 'arrowBackground_ = QColor(QStringLiteral("#076b30"))' in BAR


def test_old_qt_subcontrol_overlap_is_removed():
    assert 'subControlRect' not in BAR
    assert 'SC_ScrollBarSlider' not in BAR
    assert 'thumbEnd() const' in GEOMETRY
    assert 'grooveEnd() const' in GEOMETRY
    assert 'arrowEndStart() const' in GEOMETRY


def test_cpp_geometry_compiles_and_never_overlaps_arrows(tmp_path):
    compiler = shutil.which('g++')
    if compiler is None:
        pytest.skip('C++ compiler not installed')
    source = tmp_path / 'geometry_test.cpp'
    binary = tmp_path / 'geometry_test'
    source.write_text(textwrap.dedent(r'''
        #include "d64_turbo_scroll_geometry.hpp"
        #include <cassert>
        #include <algorithm>
        #include <cstdio>
        int main() {
            int count = 0;
            for (int extent = 0; extent <= 512; ++extent)
              for (int thickness : {8, 15, 21})
                for (int maxv : {0, 1, 50, 500})
                  for (int page : {1, 8, 40, 400}) {
                    auto prev = -1;
                    for (int value = 0; value <= maxv; ++value) {
                      auto g = d64TurboScrollGeometry(extent, thickness, 0, maxv, page, value);
                      assert(g.buttonExtent >= 0);
                      assert(g.grooveStart == g.buttonExtent);
                      assert(g.grooveEnd() == g.arrowEndStart());
                      assert(g.thumbStart >= g.grooveStart);
                      assert(g.thumbEnd() <= g.arrowEndStart());
                      assert(g.thumbExtent >= 0);
                      assert(g.thumbStart >= prev);
                      prev = g.thumbStart;
                      if (g.grooveExtent > g.thumbExtent) {
                        const auto reverse = g.valueForThumbStart(g.thumbStart);
                        assert(reverse >= 0 && reverse <= maxv);
                      }
                      count++;
                    }
                  }
            auto a = d64TurboScrollGeometry(140, 15, 0, 500, 10, 0);
            auto b = d64TurboScrollGeometry(140, 15, 0, 500, 10, 500);
            assert(a.thumbStart == 15);
            assert(b.thumbEnd() == 125);
            assert(a.valueForThumbStart(-1000) == 0);
            assert(a.valueForThumbStart(1000) == 500);
            auto c = d64TurboScrollGeometry(10, 15, 0, 500, 10, 500);
            assert(c.thumbExtent == 0); // zu kurz: keine unzulaessige Sliderflaeche
            std::printf("Verified %d positions and edge cases.\n", count);
        }
    '''), encoding='utf-8')
    cmd = [compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror', '-O2',
           '-I', str(ROOT / 'd64qt5'), str(source), '-o', str(binary)]
    subprocess.run(cmd, check=True, timeout=30, capture_output=True, text=True)
    subprocess.run([str(binary)], check=True, timeout=40, capture_output=True, text=True)


def test_build_and_deploy_script_exists():
    path = ROOT / 'build_and_deploy_dbase_editor_stage630.bat'
    assert path.exists()
    script = path.read_text(encoding='utf-8')
    assert 'build_d64qt5_mingw32.bat' in script
    assert 'libd64_qt5.dll' in script
