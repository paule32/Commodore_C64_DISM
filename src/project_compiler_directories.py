"""Stage 593: unabhängige Compiler-Verzeichnisse für PE32/PE64 und Sprachen."""

LANGUAGES = ("dbase", "pascal", "prolog")


def compiler_language(document):
    """Ermittle die Sprache auch für WFM-Dokumente mit abweichender Endung."""
    for name in LANGUAGES:
        if bool(getattr(document, "is_" + name + "_document", False)):
            return name
    source = getattr(document, "source_language", None)
    if callable(source):
        try:
            name = str(source()).casefold()
            if name in LANGUAGES:
                return name
        except (ValueError, TypeError):
            pass
    name = str(getattr(document, "language_override", "") or "").casefold()
    return name if name in LANGUAGES else ""


def settings_for(target, language):
    """Schlüssel für *.pro-Speicherung; keine geteilten Compiler-Pfade."""
    target = "pe64" if str(target).casefold() == "pe64" else "pe32"
    language = str(language).casefold()
    if language not in LANGUAGES:
        raise ValueError("Ungültige Compiler-Sprache: " + language)
    tag = "64Bit" if target == "pe64" else "32Bit"
    base = f"Settings.Windows.{tag}.Compiler.{language if language != 'dbase' else 'dBASE'}"
    stem = f"__windows_{target}_{language}_"
    return {
        "input_key": stem + "input_directories__",
        "output_key": stem + "output_directory__",
        "cache_key": stem + "assembler_cache__",
        "input_relative_key": stem + "input_relative__",
        "output_relative_key": stem + "output_relative__",
        "input_section": base + ".InputDirectories",
        "output_section": base + ".OutputDirectory",
    }


def language_output_for_document(mapping, document):
    """Gib nur das Ausgabeverzeichnis der aktuellen Sprache/ABI zurück."""
    name = compiler_language(document)
    target = str(getattr(document, "build_target", "") or "")
    if target not in {"pe32", "pe64"} or not name:
        return ""
    return str(mapping.get(target, {}).get(name, "") or "")
