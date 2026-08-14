QT += core gui widgets
TEMPLATE = lib
CONFIG += dll release c++11
CONFIG -= app_bundle
TARGET = d64qt5
DEFINES += D64QT5_BRIDGE_EXPORTS
SOURCES += d64qt5_bridge.cpp \
           d64_workstation.cpp
HEADERS += d64qt5_bridge.h \
           d64_workstation.h
win32:DEF_FILE = d64qt5_bridge.def
DESTDIR = .

win32:LIBS += -luser32 -lgdi32 -ladvapi32 -lodbc32 -lws2_32
