# Markdown-Vorschau Stage 54

Diese Datei zeigt die neue **Live-Vorschau** im Tab `MarkDown`.

## Textformatierung

Normaler Text mit **fett**, *kursiv*, ~~durchgestrichen~~ und `Inline-Code`.

Ein Link zu [GitHub](https://github.com/).

> Blockquotes werden wie bei GitHub abgesetzt dargestellt.

## Listen

- Erster Punkt
- Zweiter Punkt
  - Unterpunkt

1. Erster nummerierter Punkt
2. Zweiter nummerierter Punkt

### Task-Liste

- [x] Markdown-Datei öffnen
- [x] Rohdaten mit Gutter und Mini-Map anzeigen
- [ ] Text ändern und Live-Vorschau beobachten

## Tabelle

| Funktion | Status | Ansicht |
|---|---|---|
| Gutter | aktiv | Rohdaten |
| Mini-Map | aktiv | Rohdaten |
| Markdown | live | MarkDown |

---

## Codeblock

```prolog
apfel(gesund, X, Y) :-
    writeln("Apfel ist gesund"),
    apfel(X, Y).
```

Änderungen im Tab **Rohdaten** werden nach kurzer Entprellung direkt in der Vorschau sichtbar.
