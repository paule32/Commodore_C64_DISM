# -*- coding: utf-8 -*-
"""Stage 692: subprocess owns the GIF event loop during blocking operations."""
from __future__ import annotations

import ast
import io
import json
from pathlib import Path
from types import SimpleNamespace

import splash_animation_bridge as bridge

ROOT = Path(__file__).resolve().parent
LAUNCHER = (ROOT / 'examples' / '__main__.py').read_text('utf-8')
WORKER = (ROOT / 'examples' / 'splash_animation_worker.py').read_text('utf-8')
IDE = (ROOT / 'd64_dism.py').read_text('utf-8')


class FakeStream:
    def __init__(self):
        self.lines = []
        self.closed = False
    def write(self, data):
        self.lines.append(data)
    def flush(self):
        pass
    def close(self):
        self.closed = True


class FakeProc:
    def __init__(self, args, **kwargs):
        self.args = args
        self.options = kwargs
        self.stdin = FakeStream()
        self.stdout = io.BytesIO(b'READY\n')
        self.exitcode = None
        self.waited = False
    def poll(self):
        return self.exitcode
    def wait(self, timeout=None):
        self.waited = True
        self.exitcode = 0
        return 0
    def terminate(self):
        self.exitcode = -1
    def kill(self):
        self.exitcode = -9


def test_bridge_starts_once_and_transfers_overlay_coordinates(monkeypatch, tmp_path):
    gif = tmp_path / 'loader.gif'
    gif.write_bytes(b'GIF89a' + b'xx')
    launched = []
    monkeypatch.setattr(bridge.subprocess, 'Popen',
                        lambda *args, **kwargs: launched.append(FakeProc(*args, **kwargs)) or launched[-1])
    monkeypatch.setattr(bridge, '_process', None)
    monkeypatch.setattr(bridge, '_registered', True)
    assert bridge.start_startup_splash(gif)
    assert bridge.show_preloader_overlay(gif, 123, 456, 30, 30)
    bridge.hide_preloader_overlay()
    bridge.finish_startup_splash()
    assert len(launched) == 1
    proc = launched[0]
    assert Path(proc.args[2]).name == 'splash_animation_worker.py'
    commands = [json.loads(line) for line in proc.stdin.lines]
    assert commands == [
        {'command': 'startup'},
        {'command': 'overlay', 'x': 123, 'y': 456, 'width': 30, 'height': 30},
        {'command': 'hide_overlay'}, {'command': 'hide_startup'},
    ]
    bridge.close_splash_bridge()
    assert proc.stdin.closed and proc.waited
    assert bridge._process is None


def test_bridge_missing_asset_skips_worker(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, '_process', None)
    assert not bridge.start_startup_splash(tmp_path / 'missing.gif')
    assert not bridge.show_preloader_overlay(tmp_path / 'missing.gif', 0, 0)


def test_bridge_frozen_app_keeps_original_movie(monkeypatch, tmp_path):
    gif = tmp_path / 'loader.gif'
    gif.write_bytes(b'GIF89a')
    monkeypatch.setattr(bridge.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(bridge, '_process', None)
    assert not bridge.start_startup_splash(gif)
    assert bridge._process is None


def test_launcher_does_not_sleep_while_gif_must_advance():
    assert 'time.sleep(1.5)' not in LAUNCHER
    assert 'start_startup_splash(loader_path)' in LAUNCHER
    assert 'finish_startup_splash()' in LAUNCHER
    assert 'close_splash_bridge()' in LAUNCHER
    assert 'if not independent_splash:' in LAUNCHER
    assert 'first_paint.exec_()' in LAUNCHER
    ast.parse(LAUNCHER)


def test_dock_loader_displays_independent_overlay_and_cleans_it_up():
    begin = IDE.index('    class D64OperationPreludeDialog(QDialog):')
    end = IDE.index('    class C64ToolEditorDock(QDockWidget):', begin)
    code = IDE[begin:end]
    assert 'corner = self._loader_label.mapToGlobal(QPoint(0, 0))' in code
    assert 'self._loader_overlay_active = show_preloader_overlay(' in code
    assert 'hide_preloader_overlay()' in code
    assert 'self._loader_movie.start()' in code  # existing fallback
    assert 'self._loader_movie.stop()' in code
    assert code.index('hide_preloader_overlay()') < code.index('self._loader_movie.stop()')


def test_child_qt_process_owns_independent_event_loop():
    assert 'QApplication([sys.argv[0]])' in WORKER
    assert 'app.exec_()' in WORKER
    assert "sys.stdout.write('READY\\n')" in WORKER
    assert 'QTimer()' in WORKER and 'timer.start(25)' in WORKER
    assert 'threading.Thread(target=read_commands, daemon=True).start()' in WORKER
    assert "messages.put({'command': 'quit'})" in WORKER
    assert 'Qt.WA_TransparentForMouseEvents' in WORKER
    assert 'Qt.WindowStaysOnTopHint' in WORKER
    assert 'QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)' in WORKER
    assert '_make_c64_splash' in WORKER
    ast.parse(WORKER)


def test_existing_dock_prelude_logic_not_changed():
    assert 'QTimer.singleShot(40, perform_operation)' in IDE
    assert 'def run_with_operation_prelude(' in IDE
    assert 'dialog.exec_()' in IDE



def test_ipc_real_child_process_survives_blocking_parent_and_exits(tmp_path, monkeypatch):
    """Exercise actual Python pipe/handshake/EOF without depending on Qt."""
    script = tmp_path / 'bridge_stub.py'
    output = tmp_path / 'commands.jsonl'
    gif = tmp_path / 'loader.gif'
    gif.write_bytes(b'GIF89a')
    script.write_text('''import sys, json
from pathlib import Path
output = Path(sys.argv[sys.argv.index('--gif') + 1]).with_suffix('.jsonl')
print('READY', flush=True)
with output.open('w', encoding='utf-8') as f:
    for line in sys.stdin:
        f.write(line)
        f.flush()
''', encoding='utf-8')
    monkeypatch.setattr(bridge, '_worker_script', lambda: script)
    monkeypatch.setattr(bridge, '_process', None)
    assert bridge.start_startup_splash(gif)
    assert bridge.show_preloader_overlay(gif, 4, 8, 30, 30)
    bridge.hide_preloader_overlay()
    bridge.finish_startup_splash()
    bridge.close_splash_bridge()
    assert bridge._process is None
    data = [json.loads(line) for line in gif.with_suffix('.jsonl').read_text('utf-8').splitlines()]
    assert [d['command'] for d in data] == [
        'startup', 'overlay', 'hide_overlay', 'hide_startup'
    ]


def test_unready_child_process_falls_back_to_old_splash(tmp_path, monkeypatch):
    script = tmp_path / 'bridge_stub_invalid.py'
    gif = tmp_path / 'loader.gif'
    gif.write_bytes(b'GIF89a')
    script.write_text("print('INVALID', flush=True)\n", encoding='utf-8')
    monkeypatch.setattr(bridge, '_worker_script', lambda: script)
    monkeypatch.setattr(bridge, '_process', None)
    assert not bridge.start_startup_splash(gif)
    assert bridge._process is None
