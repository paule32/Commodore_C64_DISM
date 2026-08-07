# Pascal Exception-Klassen und typisierte EXCEPT-Handler

Diese Erweiterung baut auf dem vorhandenen PE32 Class-Reference-/Heap- und
Stack-Unwinding-Modell auf.

## Exception als echte Klasse

Unter Windows PE32 stellt der Compiler einen eingebauten Basistyp bereit:

```pascal
Exception
```

Die Instanz ist eine normale Heap-Klassenreferenz und besitzt die öffentliche,
nur lesbare Property:

```pascal
Message: String
```

Eigene Exception-Typen werden normal vererbt:

```pascal
type
    EMyException = class(Exception)
    end;
```

Ein Raise wie

```pascal
raise EMyException.Create('Fehler');
```

erzeugt eine Heap-Instanz von `EMyException`, setzt `Message` und transportiert
die Objektadresse durch den vorhandenen Exception-Frame-Stack.

## VMT-Typinformation

Vor jeder PE32-VMT wird ein Parent-VMT-Zeiger abgelegt:

```text
[VMT - 4] = VMT der Basisklasse oder 0
[VMT + 0] = virtueller Slot 0
[VMT + 4] = virtueller Slot 1
...
```

Damit ändern sich die bestehenden virtuellen Methodenslots nicht. Die Runtime
kann aber bei einem `on`-Handler die Vererbungskette hochlaufen.

## Typisierte Handler

Unterstützt wird:

```pascal
try
    raise EMyException.Create('boom');
except
    on E: EMyException do
    begin
        WriteLn(E.Message);
    end;
end;
```

Mehrere Handler werden in Quellreihenfolge geprüft:

```pascal
except
    on E: EFileException do
        ...;
    on E: EMyException do
        ...;
    on E: Exception do
        ...;
end;
```

Ein Basisklassen-Handler fängt abgeleitete Instanzen. Passt kein Handler, wird
die unveränderte Exception automatisch an den nächsten äußeren Exception-Frame
weitergeworfen.

## Lebensdauer

- Normal beendeter Handler: Exception-Objekt wird freigegeben.
- `raise;`: dasselbe Exception-Objekt wird weitergeworfen.
- Neue Exception innerhalb eines Handlers: die alte aktive Exception wird beim
  Ersetzen freigegeben.
- Unbehandelte Exception: Meldung wird ausgegeben und der Prozess beendet sich.
- Runtime-Fehler wie NIL-Zugriff/OOM benutzen ein statisches `Exception`-Objekt mit gueltiger VMT; dadurch kann auch dort `on E: Exception do` sicher auf `E.Message` zugreifen.

## Kompatibilität mit vorhandenen ANTLR-Dateien

Die `.g4`-Quellen enthalten jetzt `ON` und `exceptionHandler`. Für die derzeit
mitgelieferten älteren generierten Parser schreibt eine Kompatibilitätsschicht

```pascal
on E: EMyException do
```

intern in einen Marker um. Der AST-Builder rekonstruiert daraus einen echten
`ExceptHandler` mit separatem Variablennamen, Typ und Handler-Statement.

## Aktueller Zielumfang

Der echte Exception-Objekttransport und das Stack-Unwinding sind derzeit für
Windows PE32 implementiert. C64 und Amiga behalten bis zu einem eigenen
Heap-/Unwinding-Modell den bisherigen Sprachumfang.
