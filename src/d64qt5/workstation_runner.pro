# ---------------------------------------------------------------------------
# File:   workstation_runner.pro
# Stage:  117
# Zweck:  Qt5-Workstation-Runner mit zentralem QPlainTextEdit-Ausgabedialog.
# ---------------------------------------------------------------------------
QT += core gui widgets

# Stage 117: Der Runner benoetigt zwingend Qt Widgets. Ein direktes g++
# workstation_runner.cpp ohne die von qmake erzeugten Include-/Link-Flags
# ist nicht unterstuetzt.
lessThan(QT_MAJOR_VERSION, 5): error("Qt 5 oder neuer wird benoetigt")

TEMPLATE = app
CONFIG += release c++11 windows
CONFIG -= app_bundle

TARGET = d64_workstation_runner
DESTDIR = release

SOURCES += workstation_runner.cpp \
           d64_workstation.cpp

HEADERS += d64_workstation.h

win32:LIBS += -luser32 -lgdi32
