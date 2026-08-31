// ---------------------------------------------------------------------------
// File: locale.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "windows.h"

#ifdef __cplusplus
extern "C" {
#endif

static const JitLocaleEntry
jit_locales[] = {
    { 0x0407, "de-DE", "German",     "de"    },
    { 0x0409, "en-US", "English US", "en"    },
    { 0x0809, "en-GB", "English UK", "en_GB" },
    { 0x040C, "fr-FR", "French",     "fr"    },
    { 0x0C0A, "es-ES", "Spanish",    "es"    },
    { 0x0410, "it-IT", "Italian",    "it"    },
    { 0x0416, "pt-BR", "Portuguese", "pt_BR" },
    { 0x0419, "ru-RU", "Russian",    "ru"    },
    { 0x0411, "ja-JP", "Japanese",   "ja"    },
    { 0x0804, "zh-CN", "Chinese",    "zh_CN" }
};

static constexpr DWORD JIT_LOCALE_COUNT( VOID ) noexcept {
    return (sizeof(jit_locales) / sizeof(jit_locales[0]));
}

DLL_API LCID JIT_CDECL _jit_locale_user  (void) { return p_GetUserDefaultLCID  (); }
DLL_API LCID JIT_CDECL _jit_locale_system(void) { return p_GetSystemDefaultLCID(); }

#ifdef __cplusplus
};
#endif

// ---------------------------------------------------------------------------
// alternatives for C #define macros for language code identifier ...
// ---------------------------------------------------------------------------
static constexpr LANGID LangIdFromLcid(LCID locale_id) {
    return (LANGID)(( DWORD)locale_id & 0xFFFFUL);
}
static constexpr WORD SortIdFromLcid(LCID locale_id) {
    return (WORD)(((DWORD)locale_id >> 16) & 0x000FUL);
}
static constexpr LANGID MakeLangId(WORD primary, WORD sublanguage) noexcept {
    return static_cast<LANGID>(((static_cast<WORD>(sublanguage) & 0x003FU) << 10) | (
           static_cast<WORD>(primary)
           & 0x03FFU));
}
static constexpr WORD PrimaryLangId(LANGID language_id) noexcept {
    return static_cast<WORD>(
        static_cast<WORD>(language_id)
        & 0x03FFU
    );
}
static constexpr WORD SubLangId(LANGID language_id) noexcept {
    return static_cast<WORD>((
           static_cast<WORD>(language_id) >> 10 )
           & 0x003FU
    );
}

static inline const JitLocaleEntry *
JitFindLocaleByLcid(LCID locale_id) {
    size_t index;
    
    LANGID wanted_language = LangIdFromLcid(locale_id);
    for (index = 0; index < JIT_LOCALE_COUNT(); ++index) {
        LANGID entry_language = LangIdFromLcid(
            jit_locales[index].lcid
        );

        if (entry_language == wanted_language) {
            return &jit_locales[index];
        }
    }
    return nullptr;
}