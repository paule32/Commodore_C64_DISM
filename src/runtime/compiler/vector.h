// ---------------------------------------------------------------------------
// File: vector.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_VECTOR_HH__
#define __DBASE2MANY_VECTOR_HH__

# pragma once
# include "stddef.h"

namespace std {

template<typename T>
class vector {
private:
    T* data_;
    unsigned int size_;
    unsigned int capacity_;

public:
     vector();
    ~vector();

    unsigned int size() const;

          T& operator[](unsigned int i);
    const T& operator[](unsigned int i) const;

    void push_back(const T& value);
};

}   // namespace: std
#endif
