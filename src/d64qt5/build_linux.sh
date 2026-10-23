#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v qmake >/dev/null 2>&1; then
  echo 'Qt5 qmake fehlt. Unter Ubuntu: sudo apt install qtbase5-dev qt5-qmake' >&2
  exit 1
fi
python3 generate_runtime_abi.py
mkdir -p release
qmake d64qt5_bridge.pro CONFIG+=release
make -j"$(nproc)"
# shell32.so is an opt-in compatibility alias with only the exported
# ShellExecuteA/W subset, not a Microsoft Windows Shell library.
ln -sfn libd64_qt5.so release/shell32.so
ln -sfn libd64_qt5.so release/user32.so
echo "Fertig: $PWD/release/libd64_qt5.so (Aliase: shell32.so, user32.so)"
