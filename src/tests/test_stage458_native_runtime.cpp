#include "d64qt5/d64qt5_bridge.h"
#include "d64qt5/d64_dbase_runtime.hpp"
#include <string>
#include <cassert>
#include <cstdio>
#include <limits>
static std::string eval(const std::string& s, double from, const double* count, int mode) {
    unsigned char dst[512] = {};
    const unsigned char* src=reinterpret_cast<const unsigned char*>(s.data());
    unsigned int size = 0;
    if (mode==0) size=DBaseUtf8Substring(dst,sizeof dst,src,s.size(),&from,count);
    if (mode==1) size=DBaseUtf8SubstringUpper(dst,sizeof dst,src,s.size(),&from,count);
    if (mode==2) size=DBaseUtf8SubstringLower(dst,sizeof dst,src,s.size(),&from,count);
    assert(size != 0xFFFFFFFFu);
    return std::string(reinterpret_cast<char*>(dst),size);
}
int main() {
    const std::string original = u8"aÄßxö";
    double three=3;
    assert(eval(original,2,&three,0)==u8"Äßx");
    assert(eval(original,2,&three,1)==u8"ÄßX");
    assert(eval(original,2,&three,2)==u8"äßx");
    assert(eval(original,0,nullptr,0)==original);
    assert(eval(original,99,nullptr,0)=="");
    double zero=0;
    assert(eval(original,1,&zero,0)=="");
    double massive=1e20;
    assert(eval(original,1,&massive,0)==original);
    unsigned char dst[128];
    unsigned int n=DBaseUtf8Upper(dst,sizeof dst,
        reinterpret_cast<const unsigned char*>(original.data()),original.size());
    assert(std::string(reinterpret_cast<char*>(dst),n)==u8"AÄßXÖ");
    n=DBaseUtf8Lower(dst,sizeof dst,
        reinterpret_cast<const unsigned char*>(original.data()),original.size());
    assert(std::string(reinterpret_cast<char*>(dst),n)==u8"aäßxö");
    std::puts("Stage458 native UTF-8 bridge tests OK");
}
