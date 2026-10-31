/* Test-only Windows API shim. NEVER use in a Windows production build. */
#ifndef D64_TEST_FAKE_WINDOWS_H
#define D64_TEST_FAKE_WINDOWS_H
#include <stdint.h>
#include <stddef.h>
#define __declspec(x)
#define __cdecl
#define CALLBACK
#ifndef NULL
#define NULL ((void*)0)
#endif
typedef void *HMODULE;
typedef void *HRSRC;
typedef void *HGLOBAL;
typedef const uint16_t *LPCWSTR;
typedef uint16_t *LPWSTR;
typedef uint16_t WORD;
typedef uint32_t DWORD;
typedef intptr_t LONG_PTR;
typedef int BOOL;
#define TRUE 1
#define FALSE 0
#define MAKEINTRESOURCEW(i) ((LPCWSTR)(uintptr_t)(uint16_t)(i))
#define IS_INTRESOURCE(i) ((((uintptr_t)(i)) >> 16) == 0)
typedef BOOL (CALLBACK *ENUMRESNAMEPROCW)(HMODULE,LPCWSTR,LPWSTR,LONG_PTR);
typedef BOOL (CALLBACK *ENUMRESLANGPROCW)(HMODULE,LPCWSTR,LPCWSTR,WORD,LONG_PTR);
HRSRC FindResourceExW(HMODULE,LPCWSTR,LPCWSTR,WORD);
DWORD SizeofResource(HMODULE,HRSRC);
HGLOBAL LoadResource(HMODULE,HRSRC);
void *LockResource(HGLOBAL);
BOOL EnumResourceLanguagesW(HMODULE,LPCWSTR,LPCWSTR,ENUMRESLANGPROCW,LONG_PTR);
BOOL EnumResourceNamesW(HMODULE,LPCWSTR,ENUMRESNAMEPROCW,LONG_PTR);
#endif
