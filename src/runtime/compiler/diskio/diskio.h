// ---------------------------------------------------------------------------
// File: diskio.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_BLAKE2_H__
#define __DBASE2MANY_BLAKE2_H__

# pragma once
# include "stddef.h"

extern "C" {
DLL_API char * _jit_disk_free         (const char *drive);
DLL_API char * _jit_disk_total        (const char *drive);
DLL_API char * _jit_disk_label        (const char *drive);
DLL_API char * _jit_disk_serial       (const char *drive);
DLL_API char * _jit_disk_filesystem   (const char *drive);
DLL_API char * _jit_disk_type         (const char *drive);
DLL_API char * _jit_disk_share        (const char *drive);
DLL_API char * _jit_disk_used         (const char *drive);

DLL_API char * _jit_disk_exists       (const char *drive);
DLL_API char * _jit_disk_ready        (const char *drive);
DLL_API char * _jit_disk_is_cdrom     (const char *drive);
DLL_API char * _jit_disk_is_network   (const char *drive);
DLL_API char * _jit_disk_is_removable (const char *drive);
DLL_API char * _jit_disk_is_fixed     (const char *drive);
};

# endif
