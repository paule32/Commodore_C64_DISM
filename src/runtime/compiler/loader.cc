// ---------------------------------------------------------------------------
// File: loader.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
// jit_loader.cpp
// Win32 / NT 3.x kompatibel, ohne kernel32.lib für LoadLibraryA/GetProcAddress
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "windows.h"

struct IMAGE_DOS_HEADER
{
    WORD e_magic;
    WORD unused1[29];
    LONG e_lfanew;
};

struct IMAGE_FILE_HEADER
{
    WORD  Machine;
    WORD  NumberOfSections;
    DWORD TimeDateStamp;
    DWORD PointerToSymbolTable;
    DWORD NumberOfSymbols;
    WORD  SizeOfOptionalHeader;
    WORD  Characteristics;
};

struct IMAGE_DATA_DIRECTORY
{
    DWORD VirtualAddress;
    DWORD Size;
};

struct IMAGE_OPTIONAL_HEADER32
{
    WORD  Magic;
    BYTE  MajorLinkerVersion;
    BYTE  MinorLinkerVersion;
    DWORD SizeOfCode;
    DWORD SizeOfInitializedData;
    DWORD SizeOfUninitializedData;
    DWORD AddressOfEntryPoint;
    DWORD BaseOfCode;
    DWORD BaseOfData;
    DWORD ImageBase;
    DWORD SectionAlignment;
    DWORD FileAlignment;

    WORD  MajorOperatingSystemVersion;
    WORD  MinorOperatingSystemVersion;
    WORD  MajorImageVersion;
    WORD  MinorImageVersion;
    WORD  MajorSubsystemVersion;
    WORD  MinorSubsystemVersion;

    DWORD Win32VersionValue;
    DWORD SizeOfImage;
    DWORD SizeOfHeaders;
    DWORD CheckSum;

    WORD  Subsystem;
    WORD  DllCharacteristics;

    DWORD SizeOfStackReserve;
    DWORD SizeOfStackCommit;
    DWORD SizeOfHeapReserve;
    DWORD SizeOfHeapCommit;
    DWORD LoaderFlags;
    DWORD NumberOfRvaAndSizes;

    IMAGE_DATA_DIRECTORY DataDirectory[16];
};

struct IMAGE_NT_HEADERS32
{
    DWORD Signature;
    IMAGE_FILE_HEADER FileHeader;
    IMAGE_OPTIONAL_HEADER32 OptionalHeader;
};

struct IMAGE_EXPORT_DIRECTORY
{
    DWORD Characteristics;
    DWORD TimeDateStamp;
    WORD  MajorVersion;
    WORD  MinorVersion;
    DWORD Name;
    DWORD Base;
    DWORD NumberOfFunctions;
    DWORD NumberOfNames;
    DWORD AddressOfFunctions;
    DWORD AddressOfNames;
    DWORD AddressOfNameOrdinals;
};

struct LIST_ENTRY32
{
    LIST_ENTRY32 *Flink;
    LIST_ENTRY32 *Blink;
};

struct UNICODE_STRING32
{
    WORD  Length;
    WORD  MaximumLength;
    WORD *Buffer;
};

struct PEB_LDR_DATA32
{
    DWORD Length;
    BYTE  Initialized;
    PVOID SsHandle;

    LIST_ENTRY32 InLoadOrderModuleList;
    LIST_ENTRY32 InMemoryOrderModuleList;
    LIST_ENTRY32 InInitializationOrderModuleList;
};

struct LDR_DATA_TABLE_ENTRY32
{
    LIST_ENTRY32 InLoadOrderLinks;
    LIST_ENTRY32 InMemoryOrderLinks;
    LIST_ENTRY32 InInitializationOrderLinks;

    PVOID DllBase;
    PVOID EntryPoint;
    DWORD SizeOfImage;

    UNICODE_STRING32 FullDllName;
    UNICODE_STRING32 BaseDllName;
};

struct PEB32
{
    BYTE Reserved1[12];
    PEB_LDR_DATA32 *Ldr;
};

PFN_LoadLibraryA p_LoadLibraryA = nullptr;

extern "C" PEB32* get_peb32()
{
    PEB32 *peb;
    asm volatile(
        "movl %%fs:0x30, %0"
        : "=r"(peb)
    );
    return peb;
}

int ascii_tolower(int c)
{
    if (c >= 'A' && c <= 'Z')
    return c + 32;
    return c;
}

int wide_ascii_endswith_i(
    const WORD *wide,
    int wide_len_chars,
    const char *suffix)
{
    int suffix_len = 0;

    while (suffix[suffix_len])
        suffix_len++;

    if (wide_len_chars < suffix_len)
        return 0;

    int start = wide_len_chars - suffix_len;

    for (int i = 0; i < suffix_len; i++) {
        int a = ascii_tolower((char)wide[start + i]);
        int b = ascii_tolower(suffix[i]);

        if (a != b)
        return 0;
    }   return 1;
}

int str_equal(const char *a, const char *b)
{
    while (*a && *b) {
        if (*a != *b) return 0;
        a++;
        b++;
    }

    return *a == 0 && *b == 0;
}

FARPROC find_export(HMODULE module, const char *name)
{
    BYTE *base = (BYTE*)module;

    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER*)base;

    if (dos->e_magic != 0x5A4D) // MZ
        return 0;

    IMAGE_NT_HEADERS32 *nt = (IMAGE_NT_HEADERS32*)(base + dos->e_lfanew);

    if (nt->Signature != 0x00004550) // PE\0\0
        return 0;

    DWORD export_rva  = nt->OptionalHeader.DataDirectory[0].VirtualAddress;
    DWORD export_size = nt->OptionalHeader.DataDirectory[0].Size;

    if (!export_rva || !export_size)
    return 0;

    IMAGE_EXPORT_DIRECTORY *exp = (IMAGE_EXPORT_DIRECTORY*)(base + export_rva);

    DWORD * names     = (DWORD*)(base + exp->AddressOfNames);
    WORD  * ordinals  = ( WORD*)(base + exp->AddressOfNameOrdinals);
    DWORD * functions = (DWORD*)(base + exp->AddressOfFunctions);

    for (DWORD i = 0; i < exp->NumberOfNames; i++) {
        const char* func_name = (
        const char* )(base + names[i]);

        if (str_equal(func_name, name)) {
            WORD ordinal   = ordinals[i];
            DWORD func_rva = functions[ordinal];

            return (FARPROC)(base + func_rva);
        }
    }

    return 0;
}

HMODULE find_kernel32()
{
    PEB32 *peb = get_peb32();

    if (!peb || !peb->Ldr)
    return 0;

    LIST_ENTRY32 *head = &peb->Ldr->InLoadOrderModuleList;
    LIST_ENTRY32 *node = head->Flink;

    while (node && node != head) {
        LDR_DATA_TABLE_ENTRY32 *entry = (LDR_DATA_TABLE_ENTRY32*)node;
        int chars = entry->BaseDllName.Length / 2;

        if (entry->BaseDllName.Buffer &&
            wide_ascii_endswith_i(
                entry->BaseDllName.Buffer,
                chars,
                "kernel32.dll")) {
            return (HMODULE)entry->DllBase;
        }

        node = node->Flink;
    }

    return 0;
}

extern "C" int init_loader()
{
    HMODULE kernel32 = find_kernel32();

    if (!kernel32)
    return 0;

    p_LoadLibraryA   = (PFN_LoadLibraryA)   find_export(kernel32, "LoadLibraryA");
    p_GetProcAddress = (PFN_GetProcAddress) find_export(kernel32, "GetProcAddress");
    
    if (!p_LoadLibraryA || !p_GetProcAddress)
    return 0;

    p_GetStdHandle    = (PFN_GetStdHandle)    p_GetProcAddress(kernel32, "GetStdHandle");
    p_GetCommandLineA = (PFN_GetCommandLineA) p_GetProcAddress(kernel32, "GetCommandLineA");
    
    p_GetUserDefaultLCID   = (PFN_GetUserDefaultLCID  ) p_GetProcAddress(kernel32, "GetUserDefaultLCID");
    p_GetSystemDefaultLCID = (PFN_GetSystemDefaultLCID) p_GetProcAddress(kernel32, "GetSystemDefaultLCID");
    
    p_WriteFile       = (PFN_WriteFile)       p_GetProcAddress(kernel32, "WriteFile");
    p_ReadFile        = (PFN_ReadFile)        p_GetProcAddress(kernel32, "ReadFile");


    HMODULE user32 = p_LoadLibraryA("user32.dll");
    if (!user32)
    return 0;

    p_MessageBoxA = (PFN_MessageBoxA) p_GetProcAddress(user32, "MessageBoxA");
    if (!p_MessageBoxA)
    return 0;
    return 1;
}
