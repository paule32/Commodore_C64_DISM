#!/bin/bash
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
