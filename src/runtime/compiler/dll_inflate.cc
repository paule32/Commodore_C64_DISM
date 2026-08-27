// ---------------------------------------------------------------------------
// File: dll_inflate.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#include "dll_inflate.h"

# define DB_MAX_BITS         15
# define DB_MAX_LITLEN       288
# define DB_MAX_DIST         32
# define DB_MAX_CODELEN      19
# define DB_MAX_LENGTHS      (286 + 32)

typedef struct DBBitReader {
    const uint8_t * current;
    const uint8_t * end;
    uint32_t        bits;
    unsigned int    bit_count;
    int             error;
    
}   DBBitReader;

typedef struct DBHuffman {
    uint16_t     count [ DB_MAX_BITS + 1];
    uint16_t     symbol[ DB_MAX_LITLEN  ];
    unsigned int symbol_count;
    
}   DBHuffman;

static int
db_read_bits(
    DBBitReader  *reader,
    unsigned int  count,
    uint32_t     *value
) {
    uint32_t mask;

    if (reader == nullptr || value == nullptr || count > 24) {
        return 0;
    }

    while (reader->bit_count < count) {
        if (reader->current >= reader->end) {
            reader->error = 1;
            return 0;
        }

        reader->bits |= (
            (uint32_t)(*reader->current++)
        ) << reader->bit_count;

        reader->bit_count += 8;
    }

    if (count == 0) {
        *value = 0;
        return 1;
    }

    mask = ((uint32_t)1u << count) - 1u;
    *value = reader->bits & mask;
    reader->bits >>= count;
    reader->bit_count -= count;

    return 1;
}

static void
db_align_to_byte(
    DBBitReader *reader
) {
    unsigned int discard;

    discard = reader->bit_count & 7u;
    reader->bits >>= discard;
    reader->bit_count -= discard;
}

static int
db_build_huffman(
    DBHuffman     *table,
    const uint8_t *lengths,
    unsigned int   symbol_count
) {
    uint16_t offsets[DB_MAX_BITS + 1];
    int left;
    unsigned int bits;
    unsigned int symbol;

    if (
        table   == nullptr ||
        lengths == nullptr ||
        symbol_count > DB_MAX_LITLEN
    ) {
        return 0;
    }

    for (bits = 0; bits <= DB_MAX_BITS; ++bits) {
        table->count[bits] = 0;
    }

    table->symbol_count = symbol_count;

    for (symbol = 0; symbol < symbol_count; ++symbol) {
        unsigned int length = lengths[symbol];

        if (length > DB_MAX_BITS) {
            return 0;
        }

        ++table->count[length];
    }

    if (table->count[0] == symbol_count) {
        return 1;
    }

    left = 1;

    for (bits = 1; bits <= DB_MAX_BITS; ++bits) {
        left <<= 1;
        left -= table->count[bits];

        if (left < 0) {
            return 0;
        }
    }

    offsets[1] = 0;

    for (bits = 1; bits < DB_MAX_BITS; ++bits) {
        offsets[bits + 1] = (
            uint16_t)(
                offsets[bits] +
                table->count[bits]
            );
    }

    for (symbol = 0; symbol < symbol_count; ++symbol) {
        unsigned int length = lengths[symbol];

        if (length != 0) {
            table->symbol[
                offsets[length]++
            ] = (uint16_t)symbol;
        }
    }

    return 1;
}

static int
db_decode_symbol(
    DBBitReader    *reader,
    const DBHuffman *table,
    unsigned int   *result
) {
    uint32_t code;
    uint32_t first;
    unsigned int index;
    unsigned int length;

    code = 0;
    first = 0;
    index = 0;

    for (length = 1; length <= DB_MAX_BITS; ++length) {
        uint32_t bit;
        unsigned int count;

        if (!db_read_bits(reader, 1, &bit)) {
            return 0;
        }

        code |= bit;
        count = table->count[length];

        if (code < first + count) {
            unsigned int slot = (
                index +
                (unsigned int)(code - first)
            );

            if (slot >= table->symbol_count) {
                return 0;
            }

            *result = table->symbol[slot];
            return 1;
        }

        index += count;
        first = (first + count) << 1;
        code <<= 1;
    }

    return 0;
}

static int
db_build_fixed_tables(
    DBHuffman *literal_length_table,
    DBHuffman *distance_table
) {
    uint8_t lengths[DB_MAX_LITLEN];
    unsigned int index;

    for (index = 0; index <= 143; ++index) {
        lengths[index] = 8;
    }

    for (; index <= 255; ++index) {
        lengths[index] = 9;
    }

    for (; index <= 279; ++index) {
        lengths[index] = 7;
    }

    for (; index <= 287; ++index) {
        lengths[index] = 8;
    }

    if (!db_build_huffman(
        literal_length_table,
        lengths,
        DB_MAX_LITLEN
    )) {
        return 0;
    }

    for (index = 0; index < DB_MAX_DIST; ++index) {
        lengths[index] = 5;
    }

    return db_build_huffman(
        distance_table,
        lengths,
        DB_MAX_DIST
    );
}

static int
db_build_dynamic_tables(
    DBBitReader *reader,
    DBHuffman   *literal_length_table,
    DBHuffman   *distance_table
) {
    static const uint8_t code_length_order[DB_MAX_CODELEN] = {
        16, 17, 18, 0, 8, 7, 9, 6, 10, 5,
        11, 4, 12, 3, 13, 2, 14, 1, 15
    };

    uint8_t code_lengths[DB_MAX_CODELEN];
    uint8_t lengths[DB_MAX_LENGTHS];
    DBHuffman code_length_table;
    uint32_t value;
    unsigned int literal_count;
    unsigned int distance_count;
    unsigned int code_length_count;
    unsigned int total;
    unsigned int index;

    if (!db_read_bits(reader, 5, &value)) {
        return DB_INFLATE_TRUNCATED;
    }

    literal_count = 257u + (unsigned int)value;

    if (!db_read_bits(reader, 5, &value)) {
        return DB_INFLATE_TRUNCATED;
    }

    distance_count = 1u + (unsigned int)value;

    if (!db_read_bits(reader, 4, &value)) {
        return DB_INFLATE_TRUNCATED;
    }

    code_length_count = 4u + (unsigned int)value;

    if (
        literal_count > 286 ||
        distance_count > 32
    ) {
        return DB_INFLATE_BAD_HUFFMAN;
    }

    for (index = 0; index < DB_MAX_CODELEN; ++index) {
        code_lengths[index] = 0;
    }

    for (index = 0; index < code_length_count; ++index) {
        if (!db_read_bits(reader, 3, &value)) {
            return DB_INFLATE_TRUNCATED;
        }

        code_lengths[
            code_length_order[index]
        ] = (uint8_t)value;
    }

    if (!db_build_huffman(
        &code_length_table,
        code_lengths,
        DB_MAX_CODELEN
    )) {
        return DB_INFLATE_BAD_HUFFMAN;
    }

    total = literal_count + distance_count;
    index = 0;

    while (index < total) {
        unsigned int symbol;

        if (!db_decode_symbol(
            reader,
            &code_length_table,
            &symbol
        )) {
            return (
                reader->error
                ? DB_INFLATE_TRUNCATED
                : DB_INFLATE_BAD_HUFFMAN
            );
        }

        if (symbol <= 15) {
            lengths[index++] = (uint8_t)symbol;
            continue;
        }

        if (symbol == 16) {
            unsigned int repeat;
            uint8_t previous;

            if (index == 0) {
                return DB_INFLATE_BAD_HUFFMAN;
            }

            if (!db_read_bits(reader, 2, &value)) {
                return DB_INFLATE_TRUNCATED;
            }

            repeat = 3u + (unsigned int)value;
            previous = lengths[index - 1];

            if (index + repeat > total) {
                return DB_INFLATE_BAD_HUFFMAN;
            }

            while (repeat-- != 0) {
                lengths[index++] = previous;
            }

            continue;
        }

        if (symbol == 17 || symbol == 18) {
            unsigned int repeat;
            unsigned int extra_bits;

            extra_bits = (
                symbol == 17
                ? 3u
                : 7u
            );

            if (!db_read_bits(
                reader,
                extra_bits,
                &value
            )) {
                return DB_INFLATE_TRUNCATED;
            }

            repeat = (
                symbol == 17
                ? 3u
                : 11u
            ) + (unsigned int)value;

            if (index + repeat > total) {
                return DB_INFLATE_BAD_HUFFMAN;
            }

            while (repeat-- != 0) {
                lengths[index++] = 0;
            }

            continue;
        }

        return DB_INFLATE_BAD_HUFFMAN;
    }

    if (lengths[256] == 0) {
        return DB_INFLATE_BAD_HUFFMAN;
    }

    if (!db_build_huffman(
        literal_length_table,
        lengths,
        literal_count
    )) {
        return DB_INFLATE_BAD_HUFFMAN;
    }

    if (!db_build_huffman(
        distance_table,
        lengths + literal_count,
        distance_count
    )) {
        return DB_INFLATE_BAD_HUFFMAN;
    }

    return DB_INFLATE_OK;
}

static int
db_inflate_compressed_block(
    DBBitReader     *reader,
    const DBHuffman *literal_length_table,
    const DBHuffman *distance_table,
    uint8_t         *destination,
    size_t           destination_capacity,
    size_t          *position
) {
    static const uint16_t length_base[29] = {
        3, 4, 5, 6, 7, 8, 9, 10,
        11, 13, 15, 17, 19, 23, 27, 31,
        35, 43, 51, 59, 67, 83, 99, 115,
        131, 163, 195, 227, 258
    };

    static const uint8_t length_extra[29] = {
        0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 1, 1, 2, 2, 2, 2,
        3, 3, 3, 3, 4, 4, 4, 4,
        5, 5, 5, 5, 0
    };

    static const uint16_t distance_base[30] = {
        1, 2, 3, 4, 5, 7, 9, 13,
        17, 25, 33, 49, 65, 97, 129, 193,
        257, 385, 513, 769, 1025, 1537,
        2049, 3073, 4097, 6145, 8193,
        12289, 16385, 24577
    };

    static const uint8_t distance_extra[30] = {
        0, 0, 0, 0, 1, 1, 2, 2,
        3, 3, 4, 4, 5, 5, 6, 6,
        7, 7, 8, 8, 9, 9, 10, 10,
        11, 11, 12, 12, 13, 13
    };

    for (;;) {
        unsigned int symbol;

        if (!db_decode_symbol(
            reader,
            literal_length_table,
            &symbol
        )) {
            return (
                reader->error
                ? DB_INFLATE_TRUNCATED
                : DB_INFLATE_BAD_HUFFMAN
            );
        }

        if (symbol < 256) {
            if (*position >= destination_capacity) {
                return DB_INFLATE_OUTPUT_OVERFLOW;
            }

            destination[(*position)++] = (uint8_t)symbol;
            continue;
        }

        if (symbol == 256) {
            return DB_INFLATE_OK;
        }

        if (symbol < 257 || symbol > 285) {
            return DB_INFLATE_BAD_HUFFMAN;
        }

        {
            unsigned int length_index = symbol - 257;
            unsigned int length = length_base[length_index];
            unsigned int extra = length_extra[length_index];
            uint32_t value;
            unsigned int distance_symbol;
            unsigned int distance;
            size_t source_position;

            if (extra != 0) {
                if (!db_read_bits(
                    reader,
                    extra,
                    &value
                )) {
                    return DB_INFLATE_TRUNCATED;
                }

                length += (unsigned int)value;
            }

            if (!db_decode_symbol(
                reader,
                distance_table,
                &distance_symbol
            )) {
                return (
                    reader->error
                    ? DB_INFLATE_TRUNCATED
                    : DB_INFLATE_BAD_HUFFMAN
                );
            }

            if (distance_symbol >= 30) {
                return DB_INFLATE_BAD_DISTANCE;
            }

            distance = distance_base[distance_symbol];
            extra = distance_extra[distance_symbol];

            if (extra != 0) {
                if (!db_read_bits(
                    reader,
                    extra,
                    &value
                )) {
                    return DB_INFLATE_TRUNCATED;
                }

                distance += (unsigned int)value;
            }

            if (
                distance == 0 ||
                (size_t)distance > *position
            ) {
                return DB_INFLATE_BAD_DISTANCE;
            }

            if (
                (size_t)length >
                destination_capacity - *position
            ) {
                return DB_INFLATE_OUTPUT_OVERFLOW;
            }

            source_position = *position - distance;

            while (length-- != 0) {
                destination[*position] =
                    destination[source_position];

                ++(*position);
                ++source_position;
            }
        }
    }
}

static int
db_inflate_deflate(
    const uint8_t *source,
    size_t         source_size,
    uint8_t       *destination,
    size_t         destination_capacity,
    size_t        *destination_size
) {
    DBBitReader reader = { source, source + source_size, 0, 0, 0 };
    size_t position = 0;
    unsigned int final_block = 0;

    while (!final_block) {
        uint32_t value;
        unsigned int block_type;

        if (!db_read_bits(&reader, 1, &value)) {
            return DB_INFLATE_TRUNCATED;
        }

        final_block = (unsigned int)value;

        if (!db_read_bits(&reader, 2, &value)) {
            return DB_INFLATE_TRUNCATED;
        }

        block_type = (unsigned int)value;

        if (block_type == 0) {
            uint32_t length;
            uint32_t inverse_length;
            uint32_t byte_value;
            unsigned int index;

            db_align_to_byte(
                &reader
            );

            if (
                !db_read_bits(&reader, 16, &length) ||
                !db_read_bits(&reader, 16, &inverse_length)
            ) {
                return DB_INFLATE_TRUNCATED;
            }

            if (
                ((length ^ 0xFFFFu) & 0xFFFFu) !=
                (inverse_length & 0xFFFFu)
            ) {
                return DB_INFLATE_BAD_BLOCK_TYPE;
            }

            if (
                (size_t)length >
                destination_capacity - position
            ) {
                return DB_INFLATE_OUTPUT_OVERFLOW;
            }

            for (index = 0; index < length; ++index) {
                if (!db_read_bits(
                    &reader,
                    8,
                    &byte_value
                )) {
                    return DB_INFLATE_TRUNCATED;
                }

                destination[position++] =
                    (uint8_t)byte_value;
            }

            continue;
        }

        if (block_type == 1 || block_type == 2) {
            DBHuffman literal_length_table;
            DBHuffman distance_table;
            int result;

            if (block_type == 1) {
                if (!db_build_fixed_tables(
                    &literal_length_table,
                    &distance_table
                )) {
                    return DB_INFLATE_BAD_HUFFMAN;
                }
            }
            else {
                result = db_build_dynamic_tables(
                    &reader,
                    &literal_length_table,
                    &distance_table
                );

                if (result != DB_INFLATE_OK) {
                    return result;
                }
            }

            result = db_inflate_compressed_block(
                &reader,
                &literal_length_table,
                &distance_table,
                destination,
                destination_capacity,
                &position
            );

            if (result != DB_INFLATE_OK) {
                return result;
            }

            continue;
        }

        return DB_INFLATE_BAD_BLOCK_TYPE;
    }

    *destination_size = position;
    return DB_INFLATE_OK;
}

uint32_t
db_crc32(
    const void *data,
    size_t      size
) {
    const uint8_t *bytes;
    uint32_t crc;

    bytes = (const uint8_t *)data;
    crc = 0xFFFFFFFFu;

    while (size-- != 0) {
        unsigned int bit;

        crc ^= *bytes++;

        for (bit = 0; bit < 8; ++bit) {
            uint32_t mask = (
                (uint32_t)0 -
                (crc & 1u)
            );

            crc = (
                crc >> 1
            ) ^ (
                0xEDB88320u & mask
            );
        }
    }

    return crc ^ 0xFFFFFFFFu;
}

int
db_inflate_raw(
    const uint8_t *source,
    size_t         source_size,
    uint8_t       *destination,
    size_t         destination_capacity,
    size_t        *destination_size
) {
    if (
        source           == nullptr ||
        destination      == nullptr ||
        destination_size == nullptr
    ) {
        return DB_INFLATE_BAD_ARGUMENT;
    }

    *destination_size = 0;

    return db_inflate_deflate(
        source,
        source_size,
        destination,
        destination_capacity,
        destination_size
    );
}
