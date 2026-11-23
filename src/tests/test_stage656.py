# -*- coding: utf-8 -*-
"""Stage 656: only inner windows scroll; help clicks activate the window."""
from pathlib import Path
import subprocess
import shutil
import textwrap
import pytest

ROOT = Path(__file__).resolve().parent
BRIDGE = (ROOT / "d64qt5/d64qt5_bridge.cpp").read_text(encoding="utf-8")
HELP = (ROOT / "d64qt5/d64_turbo_help_window.hpp").read_text(encoding="utf-8")
BAR = (ROOT / "d64qt5/d64_turbo_scrollbar.hpp").read_text(encoding="utf-8")
GEO = (ROOT / "d64qt5/d64_turbo_scroll_geometry.hpp").read_text(encoding="utf-8")


def test_main_console_never_shows_scrollbars():
    assert 'g_console->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);' in BRIDGE
    assert 'g_console->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);' in BRIDGE
    assert 'g_console->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' not in BRIDGE
    assert 'g_console->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' not in BRIDGE


def test_help_viewer_stays_in_console_viewport():
    assert 'new D64TurboHelpWindow(g_console->viewport())' in BRIDGE
    assert 'new D64TurboHelpWindow(g_debug->viewport())' not in BRIDGE
    assert 'DBaseQtHelpShowMo(const char *utf8File)' in BRIDGE


def test_help_has_independent_arrow_scrollbars_both_directions():
    for orientation in ('Horizontal', 'Vertical'):
        assert f'new D64TurboArrowScrollBar(Qt::{orientation}, browser_)' in HELP
        assert f'browser_->set{orientation}ScrollBar(' in HELP
        assert f'browser_->set{orientation}ScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in HELP
    assert HELP.count('setTurboHelpTheme()') == 2
    assert 'paintArrow(painter, arrowStartRect(g), true)' in BAR
    assert 'paintArrow(painter, arrowEndRect(g), false)' in BAR
    assert 'triggerAction(QAbstractSlider::SliderSingleStepSub)' in BAR
    assert 'triggerAction(QAbstractSlider::SliderSingleStepAdd)' in BAR
    assert 'setRepeatAction(' in BAR


def test_help_activates_on_title_text_scrollbars_and_grip():
    assert 'void mousePressEvent(QMouseEvent *event) override' in HELP
    assert 'browser_->viewport()->installEventFilter(this);' in HELP
    assert 'helpHScroll->installEventFilter(this);' in HELP
    assert 'helpVScroll->installEventFilter(this);' in HELP
    assert 'obj == browser_->viewport()' in HELP
    assert 'obj == title_ || obj == grip_' in HELP
    assert 'raise();' in HELP
    assert 'return QWidget::eventFilter(obj, event);' in HELP
    assert 'QObject::connect(browser_, &QTextBrowser::anchorClicked' in HELP


def test_debug_remains_scrollable_with_arrows():
    for orientation in ('Horizontal', 'Vertical'):
        assert f'new D64TurboArrowScrollBar(Qt::{orientation}, g_debug)' in BRIDGE
        assert f'g_debug->set{orientation}ScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in BRIDGE
    assert BRIDGE.count('setTurboDebugTheme();') == 2
    assert 'QPlainTextEdit#dbaseDebug{color:#d3d3d3;' in BRIDGE


def test_thumbs_bound_to_arrows_same_for_paint_and_hit_test():
    assert 'g.thumbEnd() const' not in GEO  # method defined without prefix
    assert 'int thumbEnd() const' in GEO
    assert 'int arrowEndStart() const' in GEO
    assert 'painter.setClipRect(groove)' in BAR
    assert 'setSliderPosition(g.valueForThumbStart(' in BAR
    assert 'd64TurboScrollGeometry(' in BAR


def test_cpp_geometry_endpoint_checks(tmp_path):
    compiler = shutil.which('g++')
    if not compiler:
        pytest.skip('g++ not installed')
    source = tmp_path / 'thumb_bounds.cpp'
    binary = tmp_path / 'thumb_bounds'
    source.write_text(textwrap.dedent(r'''
        #include "d64_turbo_scroll_geometry.hpp"
        #include <cassert>
        int main() {
          for (int length=0; length<=600; length+=3)
          for (int thick : {16,17,20})
          for (int max : {0,1,20,1000})
          for (int value : {0,1,20,1000}) {
            const auto g = d64TurboScrollGeometry(length,thick,0,max,10,value);
            assert(g.grooveStart == g.buttonExtent);
            assert(g.grooveEnd() == g.arrowEndStart());
            assert(g.thumbStart >= g.grooveStart);
            assert(g.thumbEnd() <= g.arrowEndStart());
            assert(g.thumbExtent >= 0);
            assert(g.valueForThumbStart(-100000) == 0);
            assert(g.valueForThumbStart(100000) == max || g.thumbExtent == g.grooveExtent);
          }
        }
    '''), encoding='utf-8')
    subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror',
                    '-I',str(ROOT/'d64qt5'),str(source),'-o',str(binary)],
                   check=True,timeout=30,capture_output=True,text=True)
    subprocess.run([str(binary)],check=True,timeout=20,capture_output=True,text=True)


def test_no_turbo_help_host_reintroduced():
    assert not (ROOT / 'd64qt5/turbo_help_host.cpp').exists()
    assert not (ROOT / 'turbo_help_bridge_host.py').exists()
    assert (ROOT / 'build_and_deploy_dbase_editor_stage655.bat').exists()
