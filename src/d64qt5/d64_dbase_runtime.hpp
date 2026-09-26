// Stage 208/209: dBase immutable case tables + buffer conversion.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
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
