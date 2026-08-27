# ---------------------------------------------------------------------------
# File:   d64_bridge.pro
# Author: (c) 2026 Jens Kallup - paule32
# All rights reserved
# ---------------------------------------------------------------------------
# Purpose:
#   Minimal PE32 runtime symbol set reconstructed from test_raise.exe imports
#   and the supplied dBase2Many runtime sources.
# ---------------------------------------------------------------------------
QT += core gui widgets

TEMPLATE = lib
DESTDIR  = .

CONFIG  += dll release c++20
CONFIG  -= app_bundle

TARGET   = d64_qt5

DEFINES += D64QT5_BRIDGE_EXPORTS
SOURCES += d64qt5_bridge.cpp   \
           d64_workstation.cpp

HEADERS += d64qt5_bridge.h \
           d64_workstation.h

RUNTIME_IMPLIB = libd64_qt5.dll.a
win32:DEF_FILE = d64qt5_bridge.def

win32:LIBS             += -luser32 -lgdi32 -ladvapi32 -lodbc32 -lws2_32
win32:QMAKE_LFLAGS_DLL += "-Wl,--out-implib,$$RUNTIME_IMPLIB"
