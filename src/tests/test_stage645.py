"""Stage 645: Dateidialog-Scrollpfeile, harte Thumb-Grenzen und Sizer-Cursor.

Qt5/MinGW-GUI-Laufzeit ist in dieser Testumgebung nicht verfügbar; Qt-spezifische
Prüfungen validieren die Quellcode-Verdrahtung. Der C++-Geometrietest ist nativ.
"""
from pathlib import Path
import shutil
import subprocess
import textwrap

import pytest

ROOT = Path(__file__).resolve().parent
EDITOR = (ROOT / 'd64qt5/d64_turbo_editor.hpp').read_text(encoding='utf-8')
BAR = (ROOT / 'd64qt5/d64_turbo_scrollbar.hpp').read_text(encoding='utf-8')
GEOM = (ROOT / 'd64qt5/d64_turbo_scroll_geometry.hpp').read_text(encoding='utf-8')
DIALOG = EDITOR.split('class D64VirtualFileDialog final : public QWidget', 1)[1].split('// Stage 628: Mehrfenster-Editor.', 1)[0]


def test_both_file_views_have_both_arrow_scrollbars():
    assert 'auto installFileScrollbars = [](QAbstractScrollArea *view)' in DIALOG
    assert 'new D64TurboArrowScrollBar(Qt::Vertical, view)' in DIALOG
    assert 'new D64TurboArrowScrollBar(Qt::Horizontal, view)' in DIALOG
    assert 'view->setVerticalScrollBar(vertical);' in DIALOG
    assert 'view->setHorizontalScrollBar(horizontal);' in DIALOG
    assert 'installFileScrollbars(folders_);' in DIALOG
    assert 'installFileScrollbars(files_);' in DIALOG


def test_scrollbars_retain_model_wheel_keyboard_and_arrows():
    assert 'class D64TurboArrowScrollBar final : public QScrollBar' in BAR
    for source in ('paintArrow(painter, arrowStartRect(g), true)',
                   'paintArrow(painter, arrowEndRect(g), false)',
                   'triggerAction(QAbstractSlider::SliderSingleStepSub)',
                   'triggerAction(QAbstractSlider::SliderSingleStepAdd)',
                   'setRepeatAction(QAbstractSlider::SliderSingleStepSub',
                   'setRepeatAction(QAbstractSlider::SliderSingleStepAdd',
                   'setSliderPosition(g.valueForThumbStart('):
        assert source in BAR, source


def test_thumb_is_clipped_to_arrow_free_groove_in_both_axes():
    assert 'painter.setClipRect(groove)' in BAR
    assert 'int grooveEnd() const' in GEOM
    assert 'int arrowEndStart() const' in GEOM
    assert 'int thumbEnd() const' in GEOM
    assert 'g.grooveExtent = g.axisExtent - 2 * g.buttonExtent' in GEOM
    assert 'g.thumbStart = g.grooveStart + displacement' in GEOM
    assert 'orientation() == Qt::Vertical' in BAR
    assert 'QRect(g.thumbStart, 1, g.thumbExtent' in BAR
    assert 'QRect(1, g.thumbStart, qMax(0, width() - 2)' in BAR


def test_same_gray_dotted_turbo_theme_in_both_axes():
    assert DIALOG.count('setTurboEditorTheme();') == 2
    assert 'dottedGroove_ = true;' in BAR
    for color in ('#0000aa', '#686868', '#9999ad'):
        assert color in BAR
    assert 'vertical->setFixedWidth(15);' in DIALOG
    assert 'horizontal->setFixedHeight(15);' in DIALOG


def test_splitter_has_horizontal_sizer_only_at_handle():
    assert 'splitter_->handle(1)' in DIALOG
    assert 'handle->setCursor(Qt::SplitHCursor)' in DIALOG
    assert 'QSplitter::handle' in DIALOG


def test_column_resizers_show_sizer_but_header_labels_keep_arrow():
    assert 'files_->header()->viewport()->installEventFilter(this)' in DIALOG
    assert 'files_->header()->viewport()->setMouseTracking(true)' in DIALOG
    assert 'watched == files_->header()->viewport()' in DIALOG
    assert 'header->sectionViewportPosition(section)' in DIALOG
    assert 'header->sectionSize(section)' in DIALOG
    assert 'qAbs(x - right) <= 5' in DIALOG
    assert 'area->setCursor(atDivider ? Qt::SplitHCursor : Qt::ArrowCursor)' in DIALOG


def test_rest_of_mouse_cursors_preserved():
    assert 'folders_->itemAt(pos) != nullptr' in DIALOG
    assert 'files_->itemAt(pos) != nullptr' in DIALOG
    assert 'area->setCursor(overEntry ? Qt::PointingHandCursor : Qt::ArrowCursor)' in DIALOG
    assert 'button->setCursor(Qt::PointingHandCursor);' in DIALOG
    assert 'closeButton_->setCursor(Qt::PointingHandCursor);' in DIALOG
    assert 'view->verticalScrollBar()->setCursor(Qt::ArrowCursor);' in DIALOG
    assert 'view->horizontalScrollBar()->setCursor(Qt::ArrowCursor);' in DIALOG


def test_file_dialog_stays_internal_and_vfs_unchanged():
    assert 'setParent(&layer, Qt::Widget)' in DIALOG
    assert 'QFileDialog' not in DIALOG
    assert 'D64TurboModalLayer layer(desktop);' in DIALOG
    assert 'D64ApplicationVfs' in EDITOR
    assert 'D64ApplicationVfs::join(currentDirectory_, name)' in DIALOG
    assert 'readableFile(' in DIALOG
    assert 'writableFile(' in DIALOG


def test_geometry_cxx_boundaries_real_compiler(tmp_path):
    cc = shutil.which('g++')
    if not cc:
        pytest.skip('g++ fehlt')
    f = tmp_path/'scroll645.cpp'
    exe = tmp_path/'scroll645'
    f.write_text(textwrap.dedent('''
        #include "d64_turbo_scroll_geometry.hpp"
        #include <cassert>
        int main() {
            for (int axis = 0; axis <= 430; ++axis)
              for (int thick : {8,15,19})
               for (int maximum : {0,1,13,237})
                for (int page : {1,10,55})
                 for (int value : {0,1,13,237}) {
                    auto g=d64TurboScrollGeometry(axis,thick,0,maximum,page,value);
                    assert(g.grooveStart == g.buttonExtent);
                    assert(g.grooveEnd() == g.arrowEndStart());
                    assert(g.thumbStart >= g.grooveStart);
                    assert(g.thumbEnd() <= g.arrowEndStart());
                    assert(g.thumbEnd() <= axis);
                    assert(g.thumbExtent >= 0);
                    assert(g.buttonExtent * 2 <= axis);
                    assert(g.valueForThumbStart(-100) == 0);
                    if (maximum > 0 && g.grooveExtent > g.thumbExtent)
                      assert(g.valueForThumbStart(10000) == maximum);
                 }
            for (int maximum: {1,10,200}) {
                auto start = d64TurboScrollGeometry(250,15,0,maximum,10,0);
                auto end = d64TurboScrollGeometry(250,15,0,maximum,10,maximum);
                assert(start.thumbStart == start.buttonExtent);
                assert(end.thumbEnd() == end.arrowEndStart());
            }
            return 0;
        }
    '''), encoding='utf-8')
    cmd=[cc,'-std=c++17','-O2','-Wall','-Wextra','-Werror','-I',str(ROOT/'d64qt5'), str(f), '-o', str(exe)]
    subprocess.run(cmd,check=True,timeout=20,capture_output=True,text=True)
    subprocess.run([str(exe)],check=True,timeout=20,capture_output=True,text=True)
