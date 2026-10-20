// Stage 208/209: dBase immutable case tables + buffer conversion.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cmath>
#include "d64_dbase_case_tables.inc"

namespace {
constexpr std::uint32_t DBASE_CASE_BUFFER_ERROR = 0xFFFFFFFFu;

static std::uint32_t dbase_read_u32_le(const std::uint8_t *p)
{
    return static_cast<std::uint32_t>(p[0])
        | (static_cast<std::uint32_t>(p[1]) << 8)
        | (static_cast<std::uint32_t>(p[2]) << 16)
        | (static_cast<std::uint32_t>(p[3]) << 24);
}

static const std::uint8_t *dbase_find_case_mapping(
    const std::uint8_t *table, std::uint32_t packedKey,
    std::uint8_t *mappedLength)
{
    if (mappedLength) *mappedLength = 0;
    if (!table || packedKey == 0) return nullptr;
    const std::uint8_t *row=table;
    for (;;) {
        const std::uint32_t key=dbase_read_u32_le(row);
        if (key == 0) return nullptr;
        const std::uint8_t length=row[4];
        if (key == packedKey) {
            if (mappedLength) *mappedLength=length;
            return row+5;
        }
        row += 5u + static_cast<std::size_t>(length);
    }
}

static std::uint32_t dbase_case_buffer(
    std::uint8_t *destination, std::uint32_t destinationCapacity,
    const std::uint8_t *source, std::uint32_t sourceLength,
    const std::uint8_t *table, bool upper)
{
    if (!destination || destinationCapacity == 0)
        return DBASE_CASE_BUFFER_ERROR;
    if (!source && sourceLength != 0) {
        destination[0]=0;
        return DBASE_CASE_BUFFER_ERROR;
    }
    std::uint32_t inOffset=0, outOffset=0;
    auto append_bytes=[&](const std::uint8_t *bytes,std::uint32_t count)->bool {
        if (outOffset >= destinationCapacity) return false;
        const std::uint32_t remaining=destinationCapacity-1u-outOffset;
        if (count > remaining) return false;
        if (count) std::memcpy(destination+outOffset,bytes,count);
        outOffset += count;
        return true;
    };
    while (inOffset < sourceLength) {
        const std::uint8_t first=source[inOffset];
        if (first < 0x80u) {
            std::uint8_t mapped=first;
            if (upper) {
                if (mapped >= 'a' && mapped <= 'z') mapped -= 32u;
            } else {
                if (mapped >= 'A' && mapped <= 'Z') mapped += 32u;
            }
            if (!append_bytes(&mapped,1u)) {
                destination[0]=0; return DBASE_CASE_BUFFER_ERROR;
            }
            ++inOffset; continue;
        }
        std::uint32_t charLength=1u;
        if (first >= 194u && first < 245u) {
            charLength=2u;
            if (first >= 224u) charLength=3u;
            if (first >= 240u) charLength=4u;
            if (charLength > sourceLength-inOffset) charLength=1u;
        }
        if (charLength > 1u) {
            std::uint32_t packedKey=0;
            for (std::uint32_t i=0;i<charLength;++i)
                packedKey |= static_cast<std::uint32_t>(source[inOffset+i]) << (8u*i);
            std::uint8_t mappedLength=0;
            const std::uint8_t *mapped=dbase_find_case_mapping(
                table,packedKey,&mappedLength);
            if (mapped) {
                if (!append_bytes(mapped,mappedLength)) {
                    destination[0]=0; return DBASE_CASE_BUFFER_ERROR;
                }
                inOffset += charLength; continue;
            }
        }
        if (!append_bytes(source+inOffset,charLength)) {
            destination[0]=0; return DBASE_CASE_BUFFER_ERROR;
        }
        inOffset += charLength;
    }
    destination[outOffset]=0;
    return outOffset;
}

static const DBaseRuntimeContext g_dbase_runtime_context = {
    1u,
    __dbase_upper_table,
    __dbase_lower_table,
    __dbase_upper_table_size,
    __dbase_lower_table_size
};
}

extern "C" D64QT5_API const DBaseRuntimeContext *DBaseGetRuntimeContext(void)
{ return &g_dbase_runtime_context; }

extern "C" D64QT5_API const unsigned char *DBaseGetUpperTable(void)
{ return g_dbase_runtime_context.upperTable; }

extern "C" D64QT5_API const unsigned char *DBaseGetLowerTable(void)
{ return g_dbase_runtime_context.lowerTable; }

extern "C" D64QT5_API unsigned int DBaseUpperBuffer(
    unsigned char *destination, unsigned int destinationCapacity,
    const unsigned char *source, unsigned int sourceLength)
{
    return dbase_case_buffer(destination,destinationCapacity,source,sourceLength,
        g_dbase_runtime_context.upperTable,true);
}

extern "C" D64QT5_API unsigned int DBaseLowerBuffer(
    unsigned char *destination, unsigned int destinationCapacity,
    const unsigned char *source, unsigned int sourceLength)
{
    return dbase_case_buffer(destination,destinationCapacity,source,sourceLength,
        g_dbase_runtime_context.lowerTable,false);
}


// Stage 458: UTF-8 span and case APIs, without per-call generated x87 loops.
// Start/count are pointers to the WFM numeric double slots (NULL count = end).
// Results are byte lengths; UINT32_MAX means an invalid buffer/capacity.
static std::uint32_t dbase_utf8_saturating_positive(const double *value)
{
    if (!value || !std::isfinite(*value) || *value <= 0.0) return 0;
    if (*value >= 2147483647.0) return 2147483647u;
    return static_cast<std::uint32_t>(*value);  // truncates towards zero
}

static std::uint32_t dbase_utf8_character_width(
    const std::uint8_t *bytes, std::uint32_t remaining)
{
    if (!remaining) return 0;
    const std::uint8_t first=bytes[0];
    std::uint32_t n=1;
    if (first >= 194u && first < 245u) {
        n=first < 224u ? 2u : first < 240u ? 3u : 4u;
    }
    return n <= remaining ? n : 1u;
}

static std::uint32_t dbase_utf8_substring_operation(
    unsigned char *destination, unsigned int capacity,
    const unsigned char *source, unsigned int sourceLength,
    const double *start, const double *count, int conversion)
{
    if (!destination || !capacity || (sourceLength && !source))
        return DBASE_CASE_BUFFER_ERROR;
    // Nonpositive positions refer to the first character (one-based dBase).
    const std::uint32_t pos=dbase_utf8_saturating_positive(start);
    std::uint32_t skip=pos > 0 ? pos-1u : 0u;
    std::uint32_t take=count ? dbase_utf8_saturating_positive(count) : 0xFFFFFFFFu;
    std::uint32_t index=0;
    while (index < sourceLength && skip) {
        index += dbase_utf8_character_width(source+index,sourceLength-index);
        --skip;
    }
    const std::uint32_t first=index;
    while (index < sourceLength && take) {
        index += dbase_utf8_character_width(source+index,sourceLength-index);
        --take;
    }
    const std::uint32_t byteCount=index-first;
    if (!conversion) {
        if (byteCount >= capacity) { destination[0]=0; return DBASE_CASE_BUFFER_ERROR; }
        if (byteCount) std::memcpy(destination,source+first,byteCount);
        destination[byteCount]=0;
        return byteCount;
    }
    return dbase_case_buffer(destination,capacity,
        byteCount ? source+first : nullptr,byteCount,
        conversion > 0 ? g_dbase_runtime_context.upperTable :
                         g_dbase_runtime_context.lowerTable,
        conversion > 0);
}

extern "C" D64QT5_API unsigned int DBaseUtf8Substring(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len, const double *start, const double *count)
{
    return dbase_utf8_substring_operation(dst,cap,src,len,start,count,0);
}
extern "C" D64QT5_API unsigned int DBaseUtf8SubstringUpper(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len, const double *start, const double *count)
{
    return dbase_utf8_substring_operation(dst,cap,src,len,start,count,1);
}
extern "C" D64QT5_API unsigned int DBaseUtf8SubstringLower(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len, const double *start, const double *count)
{
    return dbase_utf8_substring_operation(dst,cap,src,len,start,count,-1);
}
extern "C" D64QT5_API unsigned int DBaseUtf8Upper(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len)
{
    return DBaseUpperBuffer(dst,cap,src,len);
}
extern "C" D64QT5_API unsigned int DBaseUtf8Lower(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len)
{
    return DBaseLowerBuffer(dst,cap,src,len);
}
