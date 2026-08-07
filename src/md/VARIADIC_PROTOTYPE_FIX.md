# C-Compiler: variadische Prototypen

## Behobener Fehler

Ein Header-Prototyp wie

```c
int printf(const char *format, ...);
```

wurde bisher von `_function_signature()` als variadische Funktionsdefinition
behandelt und mit folgender Meldung abgewiesen:

```text
Variadische Funktionsdefinitionen werden nicht unterstuetzt.
```

## Neue Unterscheidung

Der Compiler unterscheidet nun zwischen:

```c
int printf(const char *format, ...);   /* Prototyp: erlaubt */
```

und:

```c
int my_printf(const char *format, ...) /* Definition: noch nicht erlaubt */
{
    return 0;
}
```

Variadische Prototypen werden vollständig eingelesen. Die fest benannten
Parameter werden in der Routineninformation gespeichert. `printf()` wird wie
bisher durch die vorhandene Formatverarbeitung für `%d`, `%i`, `%u`, `%c`,
`%s` und `%%` abgesenkt.

Eigene variadische Funktionskörper bleiben bis zur Implementierung von
`va_list`, `va_start`, `va_arg`, `va_end` und der jeweiligen C64-/Amiga-ABI
bewusst gesperrt.
