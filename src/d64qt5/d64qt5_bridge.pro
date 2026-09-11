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

CONFIG  += dll release c++20
CONFIG  -= app_bundle

DEFINES += D64QT5_BRIDGE_EXPORTS
SOURCES += d64qt5_bridge.cpp   \
           d64_workstation.cpp

HEADERS += d64qt5_bridge.h \
           d64_workstation.h

DEF_FILE = d64qt5_bridge.def

win32 {
    debug {
        TARGET  = libd64_qt5d
        DESTDIR = debug
        RUNTIME_IMPLIB = d64_qt5d.dll.a
    }
    release {
        TARGET  = libd64_qt5
        DESTDIR = release
        RUNTIME_IMPLIB = d64_qt5.dll.a
    }
    LIBS             += -luser32 -lgdi32 -ladvapi32 -lodbc32 -lws2_32
    QMAKE_LFLAGS_DLL += "-Wl,--out-implib,$$RUNTIME_IMPLIB"
}
