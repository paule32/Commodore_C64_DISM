[Deutsch](STAGE462_DBASE_QT_SHARED_STARTUP_SHUTDOWN.md) | [English](STAGE462_DBASE_QT_SHARED_STARTUP_SHUTDOWN.en.md)

# Stage 462 – Unified Qt5 Runtime Startup and Shutdown

Adds named, additive Qt5 runtime exports to coordinate initialization and shutdown. The existing `formatBuffer` remains a pointer slot in the program's `.bss` and is backed by a zero-initialized **96-byte buffer** allocated by the DLL helper. Initialization sets Workstation Mode and Debug Theme afterward and observes `guiMode` (`0` for non-GUI). Centralizing the sequence reduces duplicated startup/shutdown assembly across generated WFM executables. Tests and complete internally linked PE-image size comparisons are documented; Windows Qt runtime checks remain necessary.

## Source code and command examples (unchanged)

```c
int DBaseQtRuntimeStartup(const char *title, int workstationMode,
                         int debugTheme, int guiMode, void **formatBuffer);
void DBaseQtRuntimeShutdown(void **formatBuffer);
```

