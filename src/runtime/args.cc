// ---------------------------------------------------------------------------
// File: args.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "windows.h"
# include "string.h"
# include "args.h"
# include "memory.h"

static char  * g_argument_storage = nullptr;
static char ** g_argument_vector  = nullptr;
static int32_t g_argument_count   = 0;
static int     g_argument_ready   = 0;

static const char g_empty_string[] = "";

static int
is_command_line_space(char value) {
    return (value == ' ' || value == '\t');
}

static void
free_argument_storage(void)
{
    if (g_argument_vector != nullptr) {
        _jit_free(g_argument_vector);
        g_argument_vector  = nullptr;
    }

    if (g_argument_storage != nullptr) {
        _jit_free(g_argument_storage);
        g_argument_storage =  nullptr;
    }

    g_argument_count = 0;
    g_argument_ready = 0;
}

/*
 * Zerlegt eine Windows-Kommandozeile.
 *
 * Regeln:
 *
 *   - Leerzeichen und TAB trennen Argumente außerhalb von Quotes.
 *   - Quotes werden nicht in das Ergebnis übernommen.
 *   - 2*n Backslashes vor " ergeben n Backslashes und schalten
 *     den Quote-Modus um.
 *   - 2*n+1 Backslashes vor " ergeben n Backslashes und ein
 *     literales Anführungszeichen.
 *   - "" innerhalb eines gequoteten Arguments ergibt ein
 *     literales Anführungszeichen.
 */
static int
parse_command_line(
    const char *command_line
)
{
    size_t source_length;
    size_t pointer_capacity;

    const char *source;
    char       *destination;

    int32_t argc;

    if (command_line == nullptr) {
        command_line = g_empty_string;
    }

    source_length = _jit_strlen(command_line);

    /*
     * Im ungünstigsten Fall ist fast jedes zweite Zeichen ein
     * Ein-Zeichen-Argument. len + 2 ist deshalb eine einfache,
     * sichere Obergrenze für die Pointeranzahl.
     */
    pointer_capacity = source_length + 2;
    g_argument_storage = (char *)_jit_malloc(source_length + 1);

    if (g_argument_storage == nullptr) {
        return 0;
    }

    g_argument_vector = (char **)_jit_malloc(
        pointer_capacity * sizeof(char *)
    );

    if (g_argument_vector == nullptr) {
        free_argument_storage();
        return 0;
    }

    source      = command_line;
    destination = g_argument_storage;
    argc        = 0;

    while (*source != '\0') {
        int in_quotes;

        while (is_command_line_space(*source)) {
            ++source;
        }

        if (*source == '\0') {
            break;
        }

        g_argument_vector[argc] = destination;
        ++argc;

        in_quotes = 0;

        while (*source != '\0') {
            size_t backslash_count;
            size_t index;

            if ( !in_quotes && is_command_line_space(*source)) {
                break;
            }

            if (*source == '\\') {
                backslash_count = 0;

                while (*source == '\\') {
                    ++backslash_count;
                    ++source;
                }

                if (*source == '"') {
                    /*
                     * Je zwei Backslashes werden zu einem
                     * Backslash.
                     */
                    for (
                        index = 0;
                        index < backslash_count / 2;
                        ++index) {
                        *destination++ = '\\';
                    }

                    if ((backslash_count & 1U) != 0) {
                        /*
                         * Ungerade Anzahl:
                         * Das Quote ist ein normales Zeichen.
                         */
                        *destination++ = '"';
                        ++source;
                    }   else {
                        /*
                         * Gerade Anzahl:
                         * Quote-Modus wechseln.
                         */
                        ++source;

                        if (in_quotes && *source == '"') {
                            /*
                             * Zwei Quotes innerhalb eines
                             * gequoteten Arguments.
                             */
                            *destination++ = '"';
                            ++source;
                        }   else {
                            in_quotes = !in_quotes;
                        }
                    }

                    continue;
                }

                /*
                 * Backslashes, die nicht vor einem Quote stehen,
                 * werden unverändert übernommen.
                 */
                for (
                    index = 0;
                    index < backslash_count;
                    ++index) {
                    *destination++ = '\\';
                }

                continue;
            }

            if (*source == '"') {
                ++source;

                if (in_quotes && *source == '"') {
                    *destination++ = '"';
                    ++source;
                }   else {
                    in_quotes = !in_quotes;
                }

                continue;
            }

            *destination++ = *source++;
        }

        *destination++ = '\0';

        while (is_command_line_space(*source)) {
            ++source;
        }
    }

    g_argument_vector[argc] = nullptr;
    g_argument_count        = argc;
    g_argument_ready        = 1;

    return 1;
}

DLL_API int32_t
JIT_CDECL
_jit_args_init(void) {
    const char *command_line;

    if (g_argument_ready) {
        return 1;
    }

    free_argument_storage();
    command_line = GetCommandLineA();

    if (!parse_command_line(command_line)) {
        return 0;
    }

    return 1;
}

DLL_API void
JIT_CDECL
_jit_args_shutdown(void) { free_argument_storage(); }

DLL_API int32_t
JIT_CDECL
_jit_param_count(void)
{
    if (!g_argument_ready) {
        if (!_jit_args_init()) {
            return 0;
        }
    }

    if (g_argument_count <= 1) {
        return 0;
    }

    return g_argument_count - 1;
}

DLL_API const char *
JIT_CDECL
_jit_param_str_cstr(int32_t index)
{
    if (!g_argument_ready) {
        if (!_jit_args_init()) {
            return g_empty_string;
        }
    }

    if (index < 0 || index >= g_argument_count) {
        return g_empty_string;
    }

    return g_argument_vector[index];
}

DLL_API const char *
JIT_CDECL
_jit_command_line_cstr(void)
{
    const char *command_line;

    command_line = GetCommandLineA();

    if (command_line == nullptr) {
        return g_empty_string;
    }

    return command_line;
}

DLL_API LPCSTR
JIT_CDECL
_jit_GetCommandLineA(VOID) {
    return p_GetCommandLineA();
}
