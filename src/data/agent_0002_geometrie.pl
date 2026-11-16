% Agent 0002: kleine, erweiterbare Wissensbasis fuer euklidische Grundformen.
% Dokumentierte Annahme: "rund" meint idealisiert ohne Ecken, nicht
% umgangssprachlich "mit abgerundeten Ecken".
%
% Diese Datei wird neben der EXE unter data/ geladen. Ein fehlender Beweis
% bedeutet NICHT, dass eine Eigenschaft automatisch richtig ist.

form(kreis).
form(dreieck).
form(quadrat).

% Eckenzahl als Atome, weil der Prolog-Resolver auch ohne Arithmetik arbeitet.
ecken(kreis, null).
ecken(dreieck, drei).
ecken(quadrat, vier).

% Anforderungen der geometrischen Eigenschaft.
fordert_ecken(quadratisch, vier).
fordert_ecken(dreieckig, drei).
fordert_ecken(rund, null).
fordert_ecken(kreisfoermig, null).

% Explizite Unterschiede: kein NOT-as-failure erforderlich.
verschieden(null, drei).
verschieden(null, vier).
verschieden(drei, null).
verschieden(drei, vier).
verschieden(vier, null).
verschieden(vier, drei).

widerspruch(Eigenschaft, Form) :-
    fordert_ecken(Eigenschaft, Erwartet),
    ecken(Form, Vorhanden),
    verschieden(Erwartet, Vorhanden).

vereinbar(Eigenschaft, Form) :-
    fordert_ecken(Eigenschaft, Ecken),
    ecken(Form, Ecken).
