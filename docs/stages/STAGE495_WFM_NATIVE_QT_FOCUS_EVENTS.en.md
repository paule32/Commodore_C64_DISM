[Deutsch](STAGE495_WFM_NATIVE_QT_FOCUS_EVENTS.md) | [English](STAGE495_WFM_NATIVE_QT_FOCUS_EVENTS.en.md)

# Stage 495 – Native Qt5 Focus Events OnGotFocus and OnLostFocus

Implements real Qt5 focus-enter and focus-leave event delivery in both the Windows `d64qt5_bridge.cpp` path and Linux `d64qt5_linux_form.cpp`. Previously Windows event filters did not fully detect focus acquisition and Linux only connected `clicked(bool)`. Forms can declare handlers such as `PROCEDURE PushButton1_onGotFocus(Sender)`; on Windows, `Sender` refers to the originating native `QObject*`. PE32, PE32+, ELF32, and ELF64 paths receive corresponding event dispatch and parameter conventions. The documentation includes build requirements and distinguishes automated code-generation tests from actual native focus-navigation testing.
