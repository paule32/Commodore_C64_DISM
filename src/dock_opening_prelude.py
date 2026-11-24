# ---------------------------------------------------------------------------
# Stage 620: einheitlicher Lade-Vorspann fuer Docking-Fenster.
# Originale Qt-Widgets / Dock-Workspaces bleiben unveraendert.
# Keine Qt-Abhaengigkeit: Die bestehende MainWindow-Methode
# run_with_operation_prelude() erzeugt und schliesst den Splash.
# ---------------------------------------------------------------------------
from __future__ import annotations

from functools import wraps
from inspect import Parameter, signature

# Methoden, die ein Dock oeffnen, jedoch nicht "show_*_dock" heissen.
# Der vorhandene Vorspann fuer Projekt-Einstellungen und WFM bleibt erhalten.
DOCK_OPENING_TITLES = {
    # QAction HelpContents/F1 and contextual help both enter this method.
    # The viewer hides the prelude immediately before dialog.exec_().
    "show_chm_viewer": "Hilfe",
    "localize_dialog": "Localize PO/MO",
    "resource_dialog": "Ressourcen-Builder",
    "show_e_baukasten": "E-Baukasten",
    "show_dbase_form_designer": "dBASE Formular-Designer",
    "open_dbase_form_file": "dBASE Formular-Designer",
    "open_dbase_table_file": "dBASE Tabellen-Designer",
    "new_dbase_report": "dBASE Report-Builder",
    "open_dbase_report_file": "dBASE Report-Builder",
    "open_dbase_label_file": "dBASE Etiketten-Designer",
    "open_project_circuit": "E-Baukasten",
    "show_dbase_sql_builder": "dBASE SQL-Builder",
    "show_dbase_report_builder": "dBASE Report-Builder",
    "show_dbase_label_designer": "dBASE Etiketten-Designer",
    "show_dbase_table_designer": "dBASE Tabellen-Designer",
    "show_windows_resource_editor": "Windows Ressourcen-Editor",
    "open_prolog_knowledge_browser": "Prolog Wissensdatenbank",
    "open_project_c64_resource": "C64 Ressourcen-Editor",
    "new_c64_sprite_project": "C64 Sprite-Editor",
    "new_c64_bitmap_sprite_project": "C64 Bitmap-Sprite-Editor",
    "show_project_object_information": "Projekt – Objektinformationen",
    "show_project_archive_information": "Projekt – Archivanalyse",
    "show_sprite_editor": "C64 Sprite-Editor",
    "show_character_editor": "C64 Zeichen-Editor",
    "show_palette_editor": "C64 Paletten-Editor",
    "show_text_screen_editor": "C64 Textbildschirm-Editor",
    "show_pixel_screen_editor": "C64 Pixelbildschirm-Editor",
    "show_unit_circle_learning_dock": "Einheitskreis – Animation",
    "show_unit_circle_reference_dock": "Einheitskreis – Referenz",
    "show_math_learning_dock": "Mathematik",
    "show_music_keyboard_dock": "Musik-Tastatur",
    "show_doxygen_dock": "Doxygen Dokumentation",
    "show_bind9_server_dock": "BIND9 Server",
    "show_openssl_server_dock": "OpenSSL Server",
    "show_apache_server_dock": "Apache Server",
    "show_html_editor_dock": "HTML Editor",
    "show_settings_dock": "Desktop-Einstellungen",
    "show_software_installer_dock": "Software-Installer",
    "show_agent_0001_dock": "Agent 0001 – Deutscher Grammatikparser",
    "show_agent_0002_dock": "Agent 0002 – Grammatik-Assoziationen",
    "show_agent_0003_dock": "Agent 0003 – Bild-Erkennung",
    "show_math_formula_designer_dock": "Mathematischer Formel-Designer",
    "show_minesweeper_dock": "MineSweeper",
    "show_germany_geography_dock": "Geographie – Deutschland",
    "show_england_geography_dock": "Geographie – England",
    "show_france_geography_dock": "Geographie – Frankreich",
    "show_france_rivers_geography_dock": "Geographie – Frankreichs Flüsse",
    "show_chemie_learning_dock": "Chemie – Periodensystem",
    "show_chemie_baukasten_dock": "Chemie – Baukasten",
}

# Diese Methoden besitzen bereits ihren eigenen identischen Vorspann.
EXISTING_PRELUDE_METHODS = frozenset({
    "show_project_settings_dock", "open_project_wfm_with_prelude",
})


def install_dock_opening_preludes(main_window_class):
    """Sichert Qt-Signal-Slots VOR dem Konstruieren des Hauptfensters ab.

    Ein Methoden-Wrapper beginnt die Originalfunktion erst nach dem ersten
    Paint-Zyklus des bereits vorhandenen Vorspanns. Die Registrierung erfolgt
    auf Klassenebene, bevor QAction.triggered.connect() seine Slots bindet.

    Wichtige Schutzmechanismen:
      * keine Splash-Dialoge waehrend des Hauptfensteraufbaus;
      * interne, verschachtelte Dock-Oeffnungen erzeugen keinen zweiten Splash;
      * vorhandener Projekt-/WFM-Vorspann bleibt unveraendert;
      * normale Dock-Layout-/Theme-Wiederherstellungen bleiben synchron;
      * wiederholte Installation ist idempotent.
    """
    names = set(DOCK_OPENING_TITLES)
    names.update(
        name for name in vars(main_window_class)
        if name.startswith("show_") and name.endswith("_dock")
    )
    names.difference_update(EXISTING_PRELUDE_METHODS)

    installed = []
    for name in sorted(names):
        original = getattr(main_window_class, name, None)
        if not callable(original) or getattr(original, "_d64_dock_prelude_guard", False):
            continue
        title = DOCK_OPENING_TITLES.get(
            name, name.removeprefix("show_").removesuffix("_dock").replace("_", " ").title()
        )
        # QAction.triggered liefert in PyQt5 immer einen bool-Wert. Originale
        # Slots ohne _checked-Parameter ignorieren diesen Wert automatisch.
        # Durch den generischen *args-Wrapper wuerde er sonst erstmals an
        # etwa show_agent_0003_dock() weitergereicht -> TypeError.
        params = list(signature(original).parameters.values())[1:]
        positional = [p for p in params if p.kind in (
            Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD
        )]
        first = positional[0] if positional else None
        strip_qt_checked = (
            first is None or
            (first.default is not Parameter.empty and
             first.name not in ("_checked", "checked"))
        )

        @wraps(original)
        def opening(self, *args, _d64_original=original, _d64_title=title,
                    _d64_strip_checked=strip_qt_checked, **kwargs):
            if (_d64_strip_checked and len(args) == 1
                    and isinstance(args[0], bool)):
                args = ()
            # __init__ und gespeichertes Workspace-Layout duerfen nicht
            # verzögert aufgebaut werden. Im inneren Oeffnungsschritt gilt
            # dasselbe fuer weitere show_*-Aufrufe (z.B. Server/Designer).
            if (not getattr(self, "_dock_prelude_ready", False)
                    or getattr(self, "_dock_prelude_dispatching", False)):
                return _d64_original(self, *args, **kwargs)

            # Ein bereits aktiver Vorspann darf keine zweite Aktion vor
            # dessen Ausfuehrung starten. INNERHALB des Vorspann-Callbacks
            # dagegen werden weitere Dock-Methoden synchron ausgefuehrt
            # (etwa WFM -> open_dbase_form_file -> show_dbase_form_designer).
            if getattr(self, "_operation_prelude", None) is not None:
                if getattr(self, "_operation_prelude_executing", False):
                    return _d64_original(self, *args, **kwargs)
                return False

            def execute():
                self._dock_prelude_dispatching = True
                try:
                    result = _d64_original(self, *args, **kwargs)
                    return result is not False
                finally:
                    self._dock_prelude_dispatching = False

            return self.run_with_operation_prelude(
                _d64_title,
                f"{_d64_title} wird geladen …",
                execute,
            )

        opening._d64_dock_prelude_guard = True
        setattr(main_window_class, name, opening)
        installed.append(name)
    return tuple(installed)
