// Stage 678: minimal C ABI previously emitted by runtime/string.cc.
// Avoids exposing freestanding std::string / std::cout in the Qt C++ DLL.
#include "stddef.h"
extern "C" DLL_API char* _jit_strncpy(char *dest,const char *src,unsigned int count) {
    if (!dest || !src) return dest;
    unsigned int i=0;
    for (;i<count && src[i];++i) dest[i]=src[i];
    for (;i<count;++i) dest[i]=0;
    return dest;
}

// Distinct internal names exported under the legacy names by the Qt5 DEF.
extern "C" DLL_API unsigned int D64NativeStrlen(const char *text) {
    unsigned int count=0;
    if (text) while (text[count]) ++count;
    return count;
}
extern "C" DLL_API void* D64NativeMemset(void *out,int value,unsigned int size) {
    unsigned char *p=static_cast<unsigned char*>(out);
    if (p) for (unsigned int i=0;i<size;++i) p[i]=static_cast<unsigned char>(value);
    return out;
}
