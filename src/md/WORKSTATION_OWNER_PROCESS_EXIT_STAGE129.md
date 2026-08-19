# Stage 129 – Workstation Owner-Prozess wirklich beenden

Stage 128 beendete Child-Prozesse und zerlegte die Workstation korrekt,
aber `DBaseQtShutdown()` kehrte nach `D64WorkstationFinalizeLeave()` wieder
zum generierten Programmcode zurück. Dadurch konnte der Prozess, der die
Workstation erzeugt hatte, unsichtbar weiterleben.

Stage 129 unterscheidet weiterhin:

- normales X eines Console-/WFM-Fensters:
  nur Hide + Eingabe/Fokus unterbrechen; Prozess bleibt aktiv.
- globales X/EXIT der Workstation:
  vollständige Session beenden.

Beim globalen EXIT wird `g_exit_authorized` vor dem Cleanup gesichert.
Nach:

1. Child-Prozess-Shutdown,
2. Qt-/DB-/Session-Cleanup,
3. Loeschen der WFM-/Console-Fenster,
4. `D64WorkstationFinalizeLeave()`,
5. Freigabe von Panels, Desktop-Handles und Mutexe,

wird als allerletzte Windows-Operation:

```cpp
ExitProcess(0);
```

ausgeführt.

Damit endet auch der Owner-Prozess selbst. `ExitProcess` beendet zugleich
alle noch lebenden Threads dieses Prozesses und verhindert unsichtbare
Restprozesse, die neue EXE/OBJ/DLL-Dateien blockieren.
