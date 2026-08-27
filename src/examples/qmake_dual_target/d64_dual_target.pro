QT -= gui
CONFIG += c++11

contains(CONFIG, d64_dll) {
    TEMPLATE = lib
    CONFIG += dll
    TARGET = d64_sample
    DEFINES += D64_SAMPLE_LIBRARY
    HEADERS += sample_library.h
    SOURCES += sample_library.cpp
} else {
    TEMPLATE = app
    CONFIG += console
    TARGET = d64_sample_console
    SOURCES += main.cpp
}

win32-g++ {
    contains(QT_ARCH, x86_64) {
        D64_ARCH = pe64
    } else:contains(QMAKE_TARGET.arch, x86_64) {
        D64_ARCH = pe64
    } else {
        D64_ARCH = pe32
    }

    DESTDIR = $$clean_path($$OUT_PWD/bin/$$D64_ARCH)
    OBJECTS_DIR = $$clean_path($$OUT_PWD/obj/$$D64_ARCH)
    MOC_DIR = $$clean_path($$OUT_PWD/moc/$$D64_ARCH)
    RCC_DIR = $$clean_path($$OUT_PWD/rcc/$$D64_ARCH)
    UI_DIR = $$clean_path($$OUT_PWD/ui/$$D64_ARCH)

    contains(CONFIG, d64_dll) {
        D64_IMPLIB = $$clean_path($$DESTDIR/lib$${TARGET}.a)
        QMAKE_LFLAGS_DLL += -Wl,--out-implib,$$shell_path($$D64_IMPLIB)
    }
}

