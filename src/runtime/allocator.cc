// ---------------------------------------------------------------------------
// File: allocator.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "allocator.h"

# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wreturn-type"

# pragma GCC push_options
# pragma GCC optimize("no-stack-protector")

namespace std {

template<typename T>
__attribute__((naked, noinline, used))
T* Allocator<T>::alloc(uint32_t count) {
    __asm__ volatile(
        "pushl  4(%esp)         \n\t"
        "call   __jit_malloc    \n\t"
        "addl   $4, %esp        \n\t"
        "ret    $4              \n\t"
    );

/*! @brief the original code was:
 *  @code
 *  return (T*)_jit_malloc(sizeof(T) * count);
 *  @end
 */
}

template<typename T>
__attribute__((naked, noinline, used))
T* Allocator<T>::realloc(T* p, uint32_t count) {
/*!
 *  The example below shows the original -O1 optimized Compiler output.
 *  @example
 *  subl $8, %esp
 *  movl 16(%esp), %eax
 *  sall $3, %eax
 *  movl %eax, 4(%esp)
 *  movl 12(%esp), %eax
 *  movl %eax, (%esp)
 *  call __jit_realloc
 *  addl $8, %esp
 *  ret  $8
 *  @end
 */
    __asm__ volatile(
        "movl  8(%esp), %eax    \n\t"
        "sall  $3, %eax         \n\t"
        "pushl %eax             \n\t"
        "pushl 8(%esp)          \n\t"
        "call  __jit_realloc    \n\t"
        "addl  $8, %esp         \n\t"
        "ret   $8               \n\t"
    );

/*! @brief the original code was:
 *  @code
 *  return (T*)_jit_realloc(p, sizeof(T) * count);
 *  @end
 */
}

template<typename T>
__attribute__((naked, noinline, used))
void Allocator<T>::free(T* p) {
/*!
 *  The example below shows the original -O1 optimized Compiler output.
 *  @example
 *  subl $4, %esp          #    3 Byte's: 83 EC 04
 *  movl 8(%esp), %eax     # +  4 Byte's: 8B 44 24 08
 *  movl %eax, (%esp)      # +  3 Byte's: 89 04 24
 *  call __jit_free        # +  5 Byte's: E8 xx xx xx xx
 *  addl $4, %esp          # +  3 Byte's: 83 C4 04
 *  ret $4                 # +  3 Byte's: C2 04 00
 * ----------------------- # ----------------------------
 *  total                  # = 21 Byte's 
 *  @end
 */

/*! @brief The following assembly shows compacted code.
 *  @example
 *  pushl 4(%esp)          #    4 Byte's: FF 74 24 04
 *  call __jit_free        # +  5 Byte's
 *  addl $4, %esp          # +  3 Byte's
 *  ret $4                 # +  3 Byte's
 * ----------------------- # ----------------------------
 *  total                  # = 15 bytes
 *  @end
 */

/*! @brief 26.6 % lesser code for this member.
 */
    __asm__ volatile(
        "pushl 4(%esp)      \n\t"
        "call  __jit_free   \n\t"
        "addl  $4, %esp     \n\t"
        "ret   $4           \n\t"
    );

/*! @brief the original code was:
 *  @code
 *  _jit_free(p);
 *  @end
 */
}

template struct Allocator<char>;
template struct Allocator<int>;
template struct Allocator<double>;
 
}   // namespace: std

# pragma GCC pop_options
# pragma GCC diagnostic pop
