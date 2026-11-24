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

HEADERS += d64_turbo_editor.hpp \
           d64_turbo_help_window.hpp \
           d64_debug_context_menu.hpp \
           d64_debug_title_surface.hpp \
           d64_debug_navy_scrollbar.hpp \
           d64qt5_bridge.h \
           d64_workstation.h \
           d64_dbase_runtime.hpp \
           d64_dbase_case_tables.inc \
           d64_runtime_abi.hpp \
           d64_runtime_abi.inc

DEF_FILE = d64qt5_bridge.def

win32 {
    # Stage 675: the eleven Pascal console exports are part of libd64_qt5.dll.
    SOURCES += d64_pascal_console.cpp
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
    # Stage 678: link native JIT/dBASE/Pascal core into the Qt DLL itself.
    # Qt's CRT must remain its only DLL entrypoint.
    QT5_COMPILER_MACHINE = $$system(g++ -dumpmachine)
    contains(QT5_COMPILER_MACHINE, i686-w64-mingw32) {
        QT5_NATIVE_ARCHIVE = ../runtime/win32/libd64_qt5_native.a
        QT5_NATIVE_BUILD = ../runtime/build.qt5_embedded.win32.sh
        qt5_native_runtime.target = $$QT5_NATIVE_ARCHIVE
        qt5_native_runtime.commands = bash $$QT5_NATIVE_BUILD
        # Stage 680: changes to the native runtime must invalidate the .a.
        # Without explicit prerequisites, qmake reuses the Stage-678 archive,
        # although the Stage-679 DEF expects jit_default_tobject_vmt_abi.
        QT5_NATIVE_DEPENDS = d64qt5_bridge.pro $$QT5_NATIVE_BUILD \
            ../runtime/dbase_runtime_merged.cc \
            ../runtime/jitObject.cc \
            ../runtime/args.cc \
            ../runtime/error.cc \
            ../runtime/exception.cc \
            ../runtime/print.cc \
            ../runtime/locale.cc \
            ../runtime/windows.cc \
            ../runtime/qt5_embedded_misc.cc \
            ../runtime/memory_nt32.asm \
            ../runtime/setjmp32.asm \
            ../runtime/pascal/inttostr.asm \
            ../runtime/pascal/strtoint.asm \
            ../runtime/pascal/cookie32.asm
        QT5_NATIVE_DEPENDS += $$files(../runtime/*.h) $$files(../runtime/*.inc)
        QT5_NATIVE_DEPENDS += $$files(../runtime/pascal/*.h) $$files(../runtime/pascal/*.inc)
        qt5_native_runtime.depends = $$QT5_NATIVE_DEPENDS
        QMAKE_EXTRA_TARGETS += qt5_native_runtime
        PRE_TARGETDEPS += $$QT5_NATIVE_ARCHIVE
        LIBS += -Wl,--whole-archive $$QT5_NATIVE_ARCHIVE -Wl,--no-whole-archive
        LIBS += -lmpr -lbcrypt -lmsvcrt
    } else {
        # PE64: no equivalent freestanding 64-bit runtime core yet.
        # Explicit failure is better than a DLL with missing exports.
        error("Stage 678: Qt5 native runtime merge currently needs MINGW32 (PE32); PE32+ core pending.")
    }
    LIBS             += -luser32 -lgdi32 -ladvapi32 -lodbc32 -lws2_32 -lshell32
    QMAKE_LFLAGS_DLL += "-Wl,--out-implib,$$RUNTIME_IMPLIB"
}

DISTFILES += generate_runtime_abi.py

# Stage 488: native Linux .so (Qt5), without Windows import libraries.
unix:!macx {
    TARGET = d64_qt5
    DESTDIR = release
    SOURCES = d64qt5_linux_form.cpp
    HEADERS = d64qt5_bridge.h
    QMAKE_LFLAGS_SONAME = -Wl,-soname,libd64_qt5.so
    CONFIG -= dll
    CONFIG += shared
}
