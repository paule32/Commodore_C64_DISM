// ---------------------------------------------------------------------------
// File: vector.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "memory.h"
# include "allocator.h"
# include "vector.h"

namespace std {

template<typename T>
vector<T>::vector()
    : data_(0)
    , size_(0)
    , capacity_(0)
    { }

template<typename T>
vector<T>::~vector() {
    Allocator<T> alloc;
    alloc.free(data_);
}

template<typename T>
unsigned int vector<T>::size() const {
    return size_;
}

template<typename T>
T& vector<T>::operator[](unsigned int i) {
    return data_[i];
}

template<typename T>
const T& vector<T>::operator[](unsigned int i) const {
    return data_[i];
}

template<typename T>
void vector<T>::push_back(const T& value) {
    if (size_ >= capacity_) {
        unsigned int new_capacity = capacity_ ? capacity_ * 2 : 4;
        Allocator<T> alloc;
        data_     = alloc.realloc(data_, new_capacity);
        capacity_ = new_capacity;
    }
    data_[size_++] = value;
}

template class vector<int>;
template class vector<char>;

}   // namespace: std
