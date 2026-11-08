# Stage 542 – Pascal-Class-DLL-Export/Import

**Verbindliche Basis:** Stage 541. Der Import-Cache, das optionale `.imports.inc` und die 32-/64-Bit-Compilerpfade bleiben erhalten.

## 1. Verlangte ASM-Anpassung

Bei aktivierter Import-Auslagerung werden alle weiteren `import`-/`extern`-Deklarationszeilen **leer** belassen statt mit
`; Stage 541: Import in .imports.inc` beschrieben zu werden. Die einzige eingefügte Anweisung ist das weiterhin erforderliche `%include "datei.asm.imports.inc"`. Leere Zeilen erhalten die Zeilenzuordnung.

## 2. Direktive `{$export Klassenname}`

Die Direktive muss vor der nächsten passenden Klassendeklaration im **Interface-Bereich einer Unit** stehen.

```pascal
unit UFoo;
interface
uses System;
type
  {$export TFoo}
  TFoo = class(TObject)
  private
    FValue: Integer;
  public
    constructor Create(AValue: Integer);
    procedure Bar;
  published
    property Value: Integer read FValue write FValue;
  end;
implementation
...
end.
```

Der Marker wird im Präprozessor durch aktive IFDEF-Zweige transportiert, aber nicht als ausführbare Quellanweisung behandelt. Bei falschem oder doppelt markiertem Klassennamen folgt eine gezielte Fehlermeldung.

## 3. `.pui` vor Assembler

Die Unit erzeugt beziehungsweise aktualisiert die `.pui` vor dem Erzeugen des Windows-Assemblers. PUI-Version und Quellenfingerprint werden nach den bisherigen Projektregeln geprüft. Neu sind:

- `exported_classes` und `class_export_abi: 1`.
- Klassen mit `dll_export: true`; public-/protected-Methoden mit `dll_export_name` und `dll_bridge_symbol`.
- Public-/protected-Felder mit Offset, Typ und `dll_get_export`/`dll_set_export`.
- Öffentliche/published Properties mit `read`/`write` und stabilen Getter-/Setter-Exportnamen.
- Private Felder werden nicht als selbständige Member exportiert. Wenn sie eine öffentliche Property absichern, ist für deren Wrapper der Offset in den Interface-Metadaten enthalten.

Die PUI enthält **keinen Pascal-Implementierungsquelltext**. Externe Imports werden anhand dieses Vertrags aufgelöst.

## 4. Export aus einer DLL

Eine `library libfoo; uses UFoo; begin end.` bindet die Unit-Objektdatei und veröffentlicht ihre `{$export ...}`-Klassen unter stabilen Namen:

- `TFoo_Bar`: Instanzmethode (Selbst-Zeiger explizit als erstes Argument nach außen).
- `TFoo_Create` und `TFoo_new_Create`: Konstruktoraufruf und Objektfabrik. Die Fabrik legt das Objekt mit der **VMT der DLL** an.
- `TFoo_get_FProtected` / `TFoo_set_FProtected`: typisierte Feldbrücken für public/protected Members.
- `TFoo_get_Value` / `TFoo_set_Value`: Property-Brücken, bei feldbasierten Properties über die interne Feldbrücke.
- Methodengestützte Properties erhalten zusätzlich einen Exportalias mit ihrem Property-Namen auf die erklärte Getter-/Setter-Methode.

Die Instanz-Feldbrücken haben die ABI `void get(Self, void* out)` / `void set(Self, const void* in)`. Die Bridge kopiert den deklarierten Wert in/aus den vom Aufrufer bereitgestellten Speicher. Keine privaten Objektfelder werden als globale Windows-DLL-Datensymbole deklariert.

**PE32:** Öffentliche Wrapper verwenden `cdecl`; das interne Pascal-Self in ESI wird adaptiert. **PE32+:** Windows-x64-ABI mit RCX für Self, RDX/R8/R9 für Wertparameter. DLL-Methoden mit Aggregaten/ungewöhnlichen Signaturen brauchen weitere ABI-Unterstützung, sonst wird eine Compilerdiagnose ausgelöst.

## 5. Import durch ein Programm

```pascal
program test_libfoo;
{$L libfoo}
uses System, UFoo;
var Foo: TFoo;
begin
  Foo := TFoo.Create(42);
  try
    WriteLn(Foo.Value);
  finally
    Foo.Free;
  end;
end.
```

Beim `uses UFoo` lädt der Resolver die PUI. Durch `{$L libfoo}` wird die exportierte Klasse als extern markiert, **die ursprüngliche Unit-Implementierung nicht erneut in das Hauptprogramm eingebettet**. Die Codegenerierung importiert stattdessen die DLL-Brücken. Der DLL-Konstruktor erzeugt das Objekt mit der korrekten, in der DLL befindlichen VMT. Der Destruktor-Aufruf bleibt über die importierte Klassenmethode funktionsfähig.

**Vor der Client-Kompilierung muss die passende DLL vorhanden sein.** Der Compiler prüft MZ-/PE-Header, DLL-Kennzeichen, PE32/PE32+-Architektur und die nach PUI verlangten Exportnamen. Eine fehlende DLL/ein fehlender Export wird vor der Client-ASM-Ausgabe gemeldet. Suchen zuerst die explizite `{$L}`-Datei, dann Ausgabe-, Quell-, Link-Suchverzeichnisse und PATH. Es werden keine laufzeitabhängigen DLL-Funktionsadressen in die PUI geschrieben oder gecacht. Der CES-Loader bleibt zuständig für spätere Laufzeitfehler.

Die Beispieldateien liegen unter `examples/pascal/dll_class_exports/`.

## 6. Tests und Grenzen

- `python -m unittest -v test_stage542`: gezielte Tests zu Direktive, Unit-PUI, PE32/PE64-Wrappern, Konstruktorfabriken, Feldern/Properties, DLL-Exportnamen und Import-Auslagerung.
- Das Host-System hat eine abweichende ANTLR-Runtime (4.9.3 statt projektseitig 4.13.2). AST-/ASM-/PE-Header-Tests können ausgeführt werden; der echte Pascal-Quelltext-Compiler samt Windows-DLL-Laufzeit kann hier nicht abschließend getestet werden.
- `class var`, überladene Methoden mit identischem Namen und vollständige freie Unit-Variablenexporte sind noch kein allgemein unterstützter stabiler DLL-ABI-Vertrag. Datentypen wie `Double` sowie Aggregatparameter benötigen je nach Methode die bestehende FPU-/XMM-Konvention beziehungsweise einen späteren marshalingfähigen Wrapper. Für skalare Feldbrücken sind Typen von 1/2/4/8 Byte vorgesehen; größere Aggregate sind derzeit gesperrt oder nur als private Layout-Daten verfügbar.
- Änderungen an exportierten Klassenlayouts und VMT-Verträgen erfordern einen koordinierten Neu-Build von Unit/DLL/Client. Veraltete PUI/DLL-Kombinationen werden bezüglich **Exportnamen**, aber nicht aller Laufzeitlayout-Hashes erkannt.
- Wenn `TApplication.Destroy` das Formular freigibt, darf ein WindowProc nicht dieselbe Instanz zuvor via `AppForm.Free` löschen. Diese Besitzregel gehört in die Unit selbst und wird nicht durch einen DLL-Wrapper beseitigt.
