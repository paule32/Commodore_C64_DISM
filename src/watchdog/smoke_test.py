"""Run ONLY for a deliberate crash test: python watchdog/smoke_test.py --native-abort"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from watchdog.gui_errors import install_exception_handler
from watchdog.native_watchdog import start_watchdog

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-abort', action='store_true', help='Trigger an intentional process abort')
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('This smoke test requires Windows')
    install_exception_handler(app_name='Commodore C64 DISM Smoke Test')
    if not start_watchdog(app_name='Commodore C64 DISM Smoke Test'):
        print('No external watchdog active; check MinGW build and error log', flush=True)
        return 2
    print('Native watchdog armed; test process will exit abnormally', flush=True)
    if args.native_abort:
        os.abort()
    os._exit(33)

if __name__ == '__main__':
    raise SystemExit(main())
