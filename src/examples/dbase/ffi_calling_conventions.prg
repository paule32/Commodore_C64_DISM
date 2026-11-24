&& Stage 592: explizite ABI fuer Windows-DLLs.
&& cdecl: Aufrufer bereinigt die Stackargumente unter Windows PE32.
extern CINT CAbs(CINT) cdecl "msvcrt.dll" from "abs"
&& stdcall: aufgerufene Funktion bereinigt den Stack unter Windows PE32.
extern DWORD CurrentProcessId() stdcall "kernel32.dll" from "GetCurrentProcessId"
&& Windows PE64 verwendet fuer beide die Microsoft-x64-Aufrufkonvention.
&& Beispiel einer C-Runtime-Funktion, die eine gueltige VMT-Adresse voraussetzt:
extern PVOID jit_object_instance_new(PVOID) cdecl "libd64_qt5.dll" from "jit_object_instance_new"

result = CAbs(-42)
? result
pid = CurrentProcessId()
? pid
&& NICHT mit 0 oder einer erfundenen VMT-Adresse aufrufen!
