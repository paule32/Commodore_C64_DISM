[Deutsch](STAGE456_DBASE_UI_JSON_COMPILER.md) | [English](STAGE456_DBASE_UI_JSON_COMPILER.en.md)

# Stage 456 – dBASE FORM: External UI Components as JSON

New project settings **external UI components** and subordinate **compress json** (both default off) control whether static FORM/widget geometry, fonts, and properties are serialized into JSON per form. With compression enabled the JSON payload is zlib-compressed before assembly/linking. `d64dbase/wfm_external_ui.py` writes version-1 UTF-8 JSON and can produce an adjacent `.ui.json` sidecar. The editor source is not altered by data extraction. Compiler and tests distinguish embedded runtime data from external files and preserve legacy WFM builds when the option is disabled.
