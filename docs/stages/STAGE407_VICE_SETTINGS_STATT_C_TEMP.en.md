[Deutsch](STAGE407_VICE_SETTINGS_STATT_C_TEMP.md) | [English](STAGE407_VICE_SETTINGS_STATT_C_TEMP.en.md)

# Stage 407 – Stop Redirecting VICE Drive 8 to C:\TEMP

**Basis:** `d64_dism_asm_406.zip`.

## Reproduced cause

Stages 402–406 always prepared sprite assets under `tempfile.gettempdir()/d64_dism_vice_drive8/<hash>`. On Windows, this usually resolves to an AppData Temp folder. The VICE option `-fs8` then changed `FSDevice8Dir` for the active VICE session to this temporary directory—even when a user's `vice.ini` specified a different drive-8 directory (for example on `T:`).

This is primarily a **drive-directory configuration problem**, not proof that the `vice.ini` file itself was moved. VICE also supports loading a configuration explicitly through `-config <file>`.

## Change

Stage 407 preserves the configured VICE environment and avoids silently replacing the selected drive-8 location with a host temporary directory. Sprite preparation must honor the existing drive-directory configuration and avoid changing unrelated files or machine settings. The code distinguishes host staging and drive configuration from the location of `vice.ini` itself.

## Validation

The relevant start settings, drive-8 directory selection, and VICE resource commands should be checked with the user's actual `vice.ini` and emulator version. A host-only regression test does not establish that every Windows VICE configuration behaves identically.
