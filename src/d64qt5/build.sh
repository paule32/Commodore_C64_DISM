#!/bin/bash
python3 "$(dirname "$0")/generate_runtime_abi.py"
rm  -rf release
mkdir release

rm -rf Makefile
rm -rf Makefile.*

qmake workstation_runner.pro  CONFIG+=release
mingw32-make release

rm -rf Makefile
rm -rf Makefile.*

qmake d64qt5_bridge.pro  CONFIG+=release
mingw32-make release

# Stage 208/209 runtime alias expected by generated dBase/WFM PE files.
if [ ! -f release/libd64_qt5.dll ] && [ -f release/d64_qt5.dll ]; then
    cp -f release/d64_qt5.dll release/libd64_qt5.dll
fi
