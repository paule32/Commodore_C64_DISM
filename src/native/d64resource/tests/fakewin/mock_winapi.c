/* Test-only resource table: simulates Win32 API enumeration without Win32. */
#include "windows.h"
#include <stdint.h>
#include <string.h>
#define MAX_RECS 16
typedef struct Rec {
    uint16_t type, id, lang;
    const unsigned char *data;
    uint32_t size;
} Rec;
static Rec records[MAX_RECS];
static int count;
void TestReset(void) { count = 0; }
int TestAdd(uint16_t type, uint16_t id, uint16_t lang,
            const void *data, uint32_t length) {
    if (count >= MAX_RECS) return -1;
    records[count].type = type;
    records[count].id = id;
    records[count].lang = lang;
    records[count].data = (const unsigned char *)data;
    records[count].size = length;
    ++count;
    return 0;
}
HRSRC FindResourceExW(HMODULE module, LPCWSTR type, LPCWSTR name, WORD lang) {
    int i;
    (void)module;
    for (i = 0; i < count; ++i)
        if (records[i].type == (uint16_t)(uintptr_t)type &&
            records[i].id == (uint16_t)(uintptr_t)name && records[i].lang == lang)
            return &records[i];
    return NULL;
}
DWORD SizeofResource(HMODULE module, HRSRC resource) {
    (void)module;
    return ((Rec *)resource)->size;
}
HGLOBAL LoadResource(HMODULE module, HRSRC resource) {
    (void)module;
    return resource;
}
void *LockResource(HGLOBAL resource) { return (void*)((Rec *)resource)->data; }
BOOL EnumResourceLanguagesW(HMODULE module, LPCWSTR type, LPCWSTR name,
                            ENUMRESLANGPROCW callback, LONG_PTR context) {
    int i;
    for (i = 0; i < count; ++i) {
        if (records[i].type != (uint16_t)(uintptr_t)type ||
            records[i].id != (uint16_t)(uintptr_t)name) continue;
        if (!callback(module, type, name, records[i].lang, context)) return FALSE;
    }
    return TRUE;
}
BOOL EnumResourceNamesW(HMODULE module, LPCWSTR type,
                         ENUMRESNAMEPROCW callback, LONG_PTR context) {
    int i, j;
    for (i = 0; i < count; ++i) {
        if (records[i].type != (uint16_t)(uintptr_t)type) continue;
        for (j = 0; j < i; ++j)
            if (records[j].type == records[i].type && records[j].id == records[i].id)
                break;
        if (j != i) continue;
        if (!callback(module, type, (LPWSTR)(uintptr_t)records[i].id, context)) return FALSE;
    }
    return TRUE;
}
