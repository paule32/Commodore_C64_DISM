# Stage 135 – Beep() in WFM Event-Prozeduren

Der Fehler

```text
WFM-Prozedur pb:
Statement noch nicht als Event-Assembler implementiert: Beep(750,300)
```

ist behoben.

Aus:

```dbase
PROCEDURE pb(Sender)
    Beep(750,300)
RETURN
```

wird bei PE32:

```asm
import Beep, "kernel32.dll", "Beep"

.section .text
__dbase_wfm_proc_pb:
    push 300
    push 750
    call Beep
    ret
```

`Beep` verwendet bei Win32 `WINAPI`/`__stdcall`; deshalb gibt es danach kein
`add esp,8`.

Bei PE32+:

```asm
mov ecx, 750
mov edx, 300
sub rsp, 40
call Beep
add rsp, 40
```

Sobald ein WFM-Methodenblock `Beep(...)` enthält, fügt der Compiler automatisch

```asm
import Beep, "kernel32.dll", "Beep"
```

hinzu. Das ist insbesondere für den COFF64-Objektwriter erforderlich.

`d64qt5.dll` wird für diese Erweiterung nicht geändert und muss für Stage 135
nicht neu gebaut werden.
