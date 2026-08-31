// ---------------------------------------------------------------------------
// File: allocator.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_ALLOCATOR_HH__
#define __DBASE2MANY_ALLOCATOR_HH__

# pragma once
# include "stddef.h"
# include "memory.h"

namespace std {
template<typename T>
struct Allocator {
    T*   alloc(uint32_t count);
    T* realloc(T* p, uint32_t count);

    void free(T* p);
};

extern template struct Allocator<char>;
extern template struct Allocator<int>;
extern template struct Allocator<double>;

}   // namespace: std
#endif
