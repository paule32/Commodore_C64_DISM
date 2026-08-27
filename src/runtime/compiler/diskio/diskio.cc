// ---------------------------------------------------------------------------
// File: diskio.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "stddef.h"
# include "diskio.h"
# include "memory.h"
# include "string.h"
# include "windows.h"

static char *str_alloc(const char *s)
{
    char *p;
    size_t len;

    if (!s)
        s = "";

    len = _jit_strlen(s);
    p = (char *)_jit_malloc(len + 1);

    if (!p)
        return nullptr;

    _jit_memcpy(p, s, len + 1);
    return p;
}

static void
build_root_path(char *buffer, const char *drive)
{
    char ch = 'C';

    if (drive && drive[0])
        ch = drive[0];

    if (ch >= 'a' && ch <= 'z')
        ch = ch - 'a' + 'A';

    buffer[0] = ch;
    buffer[1] = ':';
    buffer[2] = '\\';
    buffer[3] = '\0';
}

static char *uint64_to_string(unsigned long long value)
{
    char temp[64];

#if defined(_MSC_VER)
    _snprintf(temp, sizeof(temp), "%I64u", value);
#else
    _jit_snprintf(temp, sizeof(temp), "%llu", value);
#endif

    temp[sizeof(temp) - 1] = '\0';
    return str_alloc(temp);
}

static char *
uint32_to_dec(DWORD value)
{
    char temp[32];

#if defined(_MSC_VER)
    _snprintf(temp, sizeof(temp), "%lu", (unsigned long)value);
#else
    _jit_snprintf(temp, sizeof(temp), "%lu", (unsigned long)value);
#endif

    temp[sizeof(temp) - 1] = '\0';
    return str_alloc(temp);
}

static char *
uint32_to_hex(DWORD value)
{
    char temp[16];

#if defined(_MSC_VER)
    _snprintf(temp, sizeof(temp), "%08lX", (unsigned long)value);
#else
    _jit_snprintf(temp, sizeof(temp), "%08lX", (unsigned long)value);
#endif

    temp[sizeof(temp) - 1] = '\0';

    return str_alloc(temp);
}

DLL_API char *
_jit_disk_free(const char *drive)
{
    char root[4];
    ULARGE_INTEGER free_available;
    ULARGE_INTEGER total_bytes;
    ULARGE_INTEGER total_free;
    DWORD err;

    build_root_path(root, drive);

    if (!GetDiskFreeSpaceExA(
        root,
        &free_available,
        &total_bytes,
        &total_free))
    {
        err = GetLastError();

        if (err == ERROR_NOT_READY)
            return str_alloc("ERROR_NOT_READY");

        if (err == ERROR_PATH_NOT_FOUND)
            return str_alloc("ERROR_PATH_NOT_FOUND");

        if (err == ERROR_INVALID_DRIVE)
            return str_alloc("ERROR_INVALID_DRIVE");

        return uint32_to_dec(err);
    }

    return uint64_to_string(
        (unsigned long long)free_available.QuadPart
    );
}

DLL_API char *
_jit_disk_total(const char *drive)
{
    char root[4];

    DWORD sectors;
    DWORD bytes;
    DWORD free_clusters;
    DWORD total_clusters;

    build_root_path(root, drive);

    if (!GetDiskFreeSpaceA(
        root,
        &sectors,
        &bytes,
        &free_clusters,
        &total_clusters))
    {
        return _jit_strdup("");
    }

    unsigned long long total_bytes =
        (unsigned long long)total_clusters *
        sectors *
        bytes;

    return uint64_to_string(total_bytes);
}

DLL_API char *
_jit_disk_label(const char *drive)
{
    char root[4];

    char label[MAX_PATH];

    build_root_path(root, drive);

    if (!GetVolumeInformationA(
        root,
        label,
        sizeof(label),
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        0))
    {
        return _jit_strdup("");
    }

    return _jit_strdup(label);
}

DLL_API char *
_jit_disk_serial(const char *drive)
{
    char root[4];

    DWORD serial;

    build_root_path(root, drive);

    if (!GetVolumeInformationA(
        root,
        nullptr,
        0,
        &serial,
        nullptr,
        nullptr,
        nullptr,
        0))
    {
        return _jit_strdup("");
    }

    return uint32_to_hex(serial);
}

DLL_API char *
_jit_disk_filesystem(const char *drive)
{
    char root[4];

    char fs[MAX_PATH];

    build_root_path(root, drive);

    if (!GetVolumeInformationA(
        root,
        nullptr,
        0,
        nullptr,
        nullptr,
        nullptr,
        fs,
        sizeof(fs)))
    {
        return _jit_strdup("");
    }

    return _jit_strdup(fs);
}

DLL_API char *
_jit_disk_type(const char *drive)
{
    char root[4];

    build_root_path(root, drive);

    switch (GetDriveTypeA(root))
    {
        case DRIVE_UNKNOWN:     return _jit_strdup("UNKNOWN");
        case DRIVE_NO_ROOT_DIR: return _jit_strdup("INVALID");
        case DRIVE_REMOVABLE:   return _jit_strdup("REMOVABLE");
        case DRIVE_FIXED:       return _jit_strdup("FIXED");
        case DRIVE_REMOTE:      return _jit_strdup("REMOTE");
        case DRIVE_CDROM:       return _jit_strdup("CDROM");
        case DRIVE_RAMDISK:     return _jit_strdup("RAMDISK");
    }

    return _jit_strdup("UNKNOWN");
}

DLL_API char *
_jit_disk_share(const char *drive)
{
    char root[4];

    char remote[MAX_PATH];

    DWORD size = sizeof(remote);

    build_root_path(root, drive);

    if (WNetGetConnectionA(
        root,
        remote,
        &size) != NO_ERROR)
    {
        return _jit_strdup("");
    }

    return _jit_strdup(remote);
}

DLL_API char *
_jit_disk_exists(const char *drive)
{
    char root[4];

    build_root_path(root, drive);

    if (GetDriveTypeA(root) == DRIVE_NO_ROOT_DIR)
        return str_alloc("0");

    return str_alloc("1");
}

DLL_API char *
_jit_disk_ready(const char *drive)
{
    char root[4];
    DWORD sectors;
    DWORD bytes;
    DWORD free_clusters;
    DWORD total_clusters;

    build_root_path(root, drive);

    if (!GetDiskFreeSpaceA(
        root,
        &sectors,
        &bytes,
        &free_clusters,
        &total_clusters))
    {
        return str_alloc("0");
    }

    return str_alloc("1");
}

DLL_API char *
_jit_disk_is_cdrom(const char *drive)
{
    char root[4];

    build_root_path(root, drive);

    return str_alloc(
        GetDriveTypeA(root) == DRIVE_CDROM ? "1" : "0"
    );
}

DLL_API char *
_jit_disk_is_network(const char *drive)
{
    char root[4];

    build_root_path(root, drive);

    return str_alloc(
        GetDriveTypeA(root) == DRIVE_REMOTE ? "1" : "0"
    );
}

DLL_API char *
_jit_disk_is_removable(const char *drive)
{
    char root[4];

    build_root_path(root, drive);

    return str_alloc(
        GetDriveTypeA(root) == DRIVE_REMOVABLE ? "1" : "0"
    );
}

DLL_API char *
_jit_disk_is_fixed(const char *drive)
{
    char root[4];

    build_root_path(root, drive);

    return str_alloc(
        GetDriveTypeA(root) == DRIVE_FIXED ? "1" : "0"
    );
}

DLL_API char *
_jit_disk_used(const char *drive)
{
    char root[4];

    DWORD sectors;
    DWORD bytes;
    DWORD free_clusters;
    DWORD total_clusters;

    unsigned long long free_bytes;
    unsigned long long total_bytes;
    unsigned long long used_bytes;

    build_root_path(root, drive);

    if (!GetDiskFreeSpaceA(
        root,
        &sectors,
        &bytes,
        &free_clusters,
        &total_clusters))
    {
        return str_alloc("");
    }

    free_bytes =
        (unsigned long long)free_clusters *
        sectors *
        bytes;

    total_bytes =
        (unsigned long long)total_clusters *
        sectors *
        bytes;

    used_bytes = total_bytes - free_bytes;

    return uint64_to_string(used_bytes);
}
