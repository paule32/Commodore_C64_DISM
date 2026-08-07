# Pascal Class References, Heap und Exceptions (PE32)

Diese Erweiterung baut auf dem vorhandenen Pascal-OOP-/VMT-Modell auf. Für
Windows PE32 werden Klassenvariablen jetzt als echte 32-Bit-Referenzen auf
Heap-Instanzen behandelt.

## Objektmodell

Eine Klassenvariable speichert nur einen Zeiger:

```text
var Obj: TObject;

Obj
 +0  DWORD -> Heap-Instanz oder NIL
```

Die Heap-Instanz besitzt weiterhin das vorhandene VMT-/Feldlayout:

```text
TObject instance
 +0  DWORD VMT pointer
 +4  erstes Feld
 ... weitere/geerbte Felder
```

`TChild.Create` kann einer Basisklassenreferenz zugewiesen werden:

```pascal
var Base: TBase;
Base := TChild.Create;
Base.Show;              { virtueller Dispatch über TChild-VMT }
```

Die umgekehrte Zuweisung `TChild := TBase.Create` wird als inkompatibel
abgewiesen.

## Heap-Allokation

Der PE32-Code verwendet ausschließlich den internen PE32-Assembler/Linker und
Win32-Imports aus `kernel32.dll`:

```text
GetProcessHeap
HeapAlloc
HeapFree
```

`TClass.Create` erzeugt intern:

```text
GetProcessHeap
HeapAlloc(HEAP_ZERO_MEMORY, InstanceSize)
VMT-Adresse nach [Objekt+0]
Constructor aufrufen
Referenz in Zielvariable speichern
```

Es wird kein MinGW, MSVC, externer Assembler oder externer Linker benötigt.

## Free / Destroy

Ohne explizit deklarierte `Free`-Methode behandelt der Compiler

```pascal
Obj.Free;
```

als Sprachhelfer:

1. bei `Obj = nil`: nichts tun,
2. `Destroy` aufrufen (virtuell, wenn als `virtual` deklariert),
3. `HeapFree` aufrufen,
4. die Pascal-Referenz auf `nil` setzen.

Damit ist wiederholtes `Free` auf derselben auf `nil` gesetzten Variable ein
No-op.

## Constructor-Unwinding

Um den eigentlichen Konstruktor wird ein versteckter Exception-Frame gelegt.
Wirft der Konstruktor eine Exception, wird die teilweise erzeugte Instanz
aufgeräumt:

```text
HeapAlloc
  -> Constructor
       -> raise
  -> Constructor-Unwind-Handler
       -> Destroy (falls vorhanden)
       -> HeapFree
       -> Zielreferenz := nil
       -> re-raise
```

## Exception-Transport

Unter PE32 besitzt die Runtime einen Stack verketteter Exception-Frames. Ein
Frame belegt derzeit 24 Byte:

```text
+00 previous frame
+04 handler address
+08 saved EBP
+12 saved ESI
+16 saved EBX
+20 saved EDI
```

`raise` springt nicht mit einem normalen `ret` zurück. Die Runtime nimmt den
obersten Frame, entfernt ihn aus der Handlerkette, stellt Register und Stack
wieder her und springt direkt zur gespeicherten Handleradresse.

Sinngemäß:

```asm
mov ecx, [__pas_exception_top]
mov edx, [ecx+4]        ; handler
mov [__pas_exception_top], [ecx]
mov ebp, [ecx+8]
mov esi, [ecx+12]
mov ebx, [ecx+16]
mov edi, [ecx+20]
lea esp, [ecx+24]
jmp edx
```

Damit kann eine tief aufgerufene Methode bis zu einem Handler in ihrem
Aufrufer zurück unwinden.

## Unterstützte Raise-Formen

```pascal
raise Exception.Create('Fehlertext');
raise 'Fehlertext';
raise;
```

`raise;` wirft die aktuell behandelte Exception erneut.

Für die aktuelle erste Exception-Stufe transportiert `Exception.Create(...)`
noch kein vollständiges Pascal-Exception-Objekt. Transportiert werden:

```text
ExceptionCode()     Integer
ExceptionMessage()  String
```

Beispiel:

```pascal
try
    Worker.Fail;
except
    WriteLn(ExceptionMessage());
end;
```

## TRY..FINALLY beim Unwinding

Ein `try..finally` legt einen Exception-Frame an. Auf dem normalen Pfad wird
der Frame entfernt und danach der `finally`-Block ausgeführt.

Bei einer Exception:

1. Stack wird zum `try..finally`-Handler zurückgesetzt,
2. `finally` wird ausgeführt,
3. die Exception wird automatisch mit `__pas_reraise` weitergegeben.

Dadurch funktioniert beispielsweise:

```pascal
try
    try
        Worker.Fail;
    finally
        WriteLn('cleanup');
    end;
except
    WriteLn(ExceptionMessage());
end;
```

in der Reihenfolge:

```text
Worker.Fail
cleanup
outer except
```

## TRY..EXCEPT

`try..except` fängt den Exception-Transport am nächstgelegenen Handler ab.
Nach normalem Ende des `except`-Blocks werden Message und Code gelöscht.
Ein `raise;` im Handler erreicht diese Löschung nicht und reicht die Exception
an den nächsten äußeren Handler weiter.

## BREAK / CONTINUE und Exception-Frames

Wenn `break` oder `continue` einen geschützten `try`-Bereich verlässt, erzeugt
das PE32-Backend einen Cleanup-Trampolin. Vor dem Sprung zum Schleifenziel wird
der zugehörige Runtime-Exception-Frame entfernt. Bei verschachtelten
`try`-Blöcken bilden diese Trampoline automatisch eine Kette.

`finally`-Blöcke werden dabei wie bisher vor dem Sprung ausgeführt.

## NIL

PE32 unterstützt `nil` für Klassenreferenzen:

```pascal
Obj := nil;
Obj.Free;       { No-op }
```

Ein Zugriff auf einen Member über eine `nil`-Klassenreferenz löst über die
Exception-Runtime die Meldung `Nil class reference` aus.

## Aktuelle Grenzen

Die vollständige Heap-/Exception-Implementierung dieser Stufe gilt zunächst
für Windows PE32. C64 und Amiga behalten vorerst ihr bisheriges statisches
Klassenmodell.

Noch nicht implementiert sind insbesondere:

- typisierte Handler `on E: EMyException do`,
- ein echtes Heap-Objekt für `Exception` und Exception-Unterklassen,
- RTTI-basierte Exception-Typprüfung,
- Thread-lokale Exception-Stacks,
- `finally`-gesteuerte automatische Freigabe beliebiger lokaler Interfaces
  oder managed Types.

Der jetzige Stack-Unwinder ist aber bereits die Grundlage, um diese Funktionen
später aufzusetzen.
