"""Stage 637 – DOS-Zeichenraster und erreichbare MessageBox-Titelleiste.

Statische Qt5-Integration plus ein aus dem echten C++-Quelltext extrahierter,
mit g++ kompilierter Geometrie-Test. Kein Ersatz fuer Win32-Qt5-GUI-Test.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import pytest

ROOT = Path(__file__).resolve().parent
H = (ROOT/'d64qt5/d64_turbo_messagebox.hpp').read_text(encoding='utf-8')


def test_drag_is_blockwise_and_uses_console_font_not_dialog_font():
    assert 'const QWidget *console = desktop->parentWidget();' in H
    assert 'const QFont gridFont = console ? console->font() : desktop->font();' in H
    assert 'const QFontMetrics metrics(gridFont, desktop);' in H
    assert "metrics.horizontalAdvance(QLatin1Char('M'))" in H
    assert 'metrics.lineSpacing()' in H
    assert 'const QSize grid = d64_turbo_message_grid::cellSize(desktop);' in H
    assert 'dragStartColumn_ + d64_turbo_message_grid::roundCells(delta.x(), grid.width())' in H
    assert 'dragStartRow_ + d64_turbo_message_grid::roundCells(delta.y(), grid.height())' in H
    assert 'setGridPosition(' in H
    assert 'move(d64_turbo_message_grid::gridPixels(cells, desktop));' in H


def test_title_row_24_and_overflow_right_without_window_size_clamp():
    assert 'const int visibleTitleCols = qMin(10, viewportCols);' in H
    assert 'const int maxCol = qMin(79, qMax(0, viewportCols - visibleTitleCols));' in H
    assert 'const int maxRow = qMin(24, qMax(0, viewportRows - 1));' in H
    assert 'qMax(0, desktop->width() - width())' not in H
    assert 'qMax(0, desktop->height() - height())' not in H
    assert 'width()-window->width()' not in H
    assert 'height()-window->height()' not in H


def test_dialog_position_is_saved_as_cells_and_zoom_recalculated():
    assert 'setProperty("d64GridCol", gridColumn_);' in H
    assert 'setProperty("d64GridRow", gridRow_);' in H
    assert 'const bool viewportResized =' in H
    assert 'const bool consoleFontChanged =' in H
    assert 'event->type() == QEvent::FontChange' in H
    assert 'event->type() == QEvent::Resize' in H
    assert 'window->property("d64GridCol").toInt()' in H
    assert 'window->property("d64GridRow").toInt()' in H
    assert 'window->move(d64_turbo_message_grid::gridPixels(cells, parentWidget()));' in H


def test_initial_center_placement_snaps_to_dos_cells():
    block=H.split('static int showMessage(',1)[1].split('static void information(',1)[0]
    assert 'box.setGridPosition(' in block
    assert 'd64_turbo_message_grid::roundCells((layer.width() - box.width()) / 2,' in block
    assert 'd64_turbo_message_grid::roundCells((layer.height() - box.height()) / 2,' in block


def test_modal_interaction_and_font_regressions():
    for marker in (
        'grabMouse();', 'releaseMouse();',
        'if (event->key() == Qt::Key_Escape)',
        '[this]() { done(Cancel); }',
        '[this, result = spec.second]() { done(result); }',
        'QStringLiteral("Consolas")',
        'QPen borderPen(QColor(0x52, 0x52, 0x52), 2);',
    ):
        assert marker in H


def test_actual_cpp_geometry_helper_compiles_and_respects_80x25():
    if not shutil.which('g++'):
        pytest.skip('g++ zum Kompilieren des C++-Geometriehelpers nicht verfuegbar')
    code = H.split('namespace d64_turbo_message_grid {',1)[1].split('} // namespace d64_turbo_message_grid',1)[0]
    stubs = r'''
#include <algorithm>
#include <cassert>
struct QFont { int cw, ch; };
struct QWidget {
    QWidget *p; QFont f; int w,h;
    QWidget(QWidget *parent,QFont font,int width,int height):p(parent),f(font),w(width),h(height){}
    QWidget *parentWidget() const {return p;}
    QFont font() const {return f;}
    int width() const {return w;}
    int height() const {return h;}
};
struct QSize { int w,h; QSize(int a,int b):w(a),h(b){} int width() const{return w;} int height() const{return h;} };
struct QPoint { int x_,y_; QPoint(int a,int b):x_(a),y_(b){} int x() const{return x_;} int y() const{return y_;} };
struct QFontMetrics { QFont f; QFontMetrics(QFont font,const QWidget *):f(font){} int horizontalAdvance(char)const{return f.cw;} int lineSpacing()const{return f.ch;} };
inline char QLatin1Char(char x){return x;}
inline int qMax(int a,int b){return std::max(a,b);}
inline int qMin(int a,int b){return std::min(a,b);}
inline int qBound(int lo,int n,int hi){return std::clamp(n,lo,hi);}
namespace d64_turbo_message_grid {
'''
    assertions=r'''
}
int main() {
    using namespace d64_turbo_message_grid;
    QWidget console(nullptr,{10,16},800,400), desktop(&console,{4,4},800,400);
    assert(cellSize(&desktop).width()==10 && cellSize(&desktop).height()==16);
    assert(clampCells(1000,1000,&desktop).x()==70);
    assert(clampCells(1000,1000,&desktop).y()==24);
    assert(gridPixels(clampCells(70,24,&desktop),&desktop).x()==700);
    assert(gridPixels(clampCells(70,24,&desktop),&desktop).y()==384);
    assert(700+440>800 && 384+175>400); // Fensterinhalt darf hinausragen
    assert(roundCells(4,10)==0 && roundCells(5,10)==1);
    assert(roundCells(-4,10)==0 && roundCells(-5,10)==-1);
    // Zoom mit doppelten Zellabmessungen und doppeltem Viewport.
    QWidget zoomConsole(nullptr,{20,32},1600,800), zoomDesktop(&zoomConsole,{4,4},1600,800);
    assert(clampCells(100,100,&zoomDesktop).x()==70);
    assert(clampCells(100,100,&zoomDesktop).y()==24);
    assert(gridPixels(clampCells(70,24,&zoomDesktop),&zoomDesktop).y()==768);
    // Kleiner Viewport: die Titelleiste bleibt erreichbar.
    QWidget smallConsole(nullptr,{10,16},250,160), smallDesktop(&smallConsole,{4,4},250,160);
    assert(clampCells(1000,1000,&smallDesktop).x()==15);
    assert(clampCells(1000,1000,&smallDesktop).y()==9);
    return 0;
}
'''
    with tempfile.TemporaryDirectory() as directory:
        src = Path(directory)/'grid.cpp'
        exe = Path(directory)/'grid'
        src.write_text(stubs+code+assertions,encoding='utf8')
        result=subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)], capture_output=True,text=True)
        assert result.returncode==0, result.stderr
        result=subprocess.run([str(exe)],capture_output=True,text=True)
        assert result.returncode==0, result.stderr
