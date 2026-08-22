Stage 160 – Locale-Warnungen und Timer-Property-Absturz behoben

1. Python 3.15 / locale
----------------------
Die ausführbaren Aufrufe von locale.getdefaultlocale() wurden entfernt.

Neu:

    _current_locale_name(default)

Der Helper verwendet:

    locale.getlocale()[0]

und, falls keine Sprache geliefert wird:

    locale.setlocale(locale.LC_CTYPE)

TranslationManager behält seinen Fallback "en".
Der Komponenten-MO-Katalog behält seinen Fallback "de".

2. Timer Property Tree
----------------------
Der Absturz entstand durch:

    timer_items = {QTreeWidgetItem, ...}

QTreeWidgetItem ist in PyQt5 unhashable.

Jetzt werden die Objekte in Tuples gehalten und per Identität geprüft:

    top_item is candidate

Dadurch kann ein Timer wieder ohne TypeError selektiert werden.

Unverändert:
- Timer 42 x 42
- Name / Interval / Active-Enabled
- OnTimer
- Stage-159 mo:-Marker
- übriger Formdesigner

Validierung:
- py_compile: OK
- AST: 0 Aufrufe von getdefaultlocale
- AST: 0 Timer-QTreeWidgetItem-Sets

Native PyQt5-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
