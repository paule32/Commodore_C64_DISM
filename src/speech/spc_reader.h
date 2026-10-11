#ifndef D64_SPC_READER_H
#define D64_SPC_READER_H
#include <stdint.h>
#include <stddef.h>

typedef struct RS_Spc RS_Spc;
/* The container is indexed once; entries are fetched on demand.
 * All functions return 1 for success; 0 for failure.
 * Returned PCM belongs to the caller and must be freed with free().
 * No MP3/Ogg decoder is bundled; PCM16 and Microsoft IMA WAV are supported.
 */
RS_Spc *rs_spc_open(const char *path);
void rs_spc_close(RS_Spc *spc);
int rs_spc_decode(RS_Spc *spc, const char *name,
                  int16_t **pcm, uint32_t *frames, uint32_t *rate);
int rs_spc_entry_count(const RS_Spc *spc);
const char *rs_spc_entry_name(const RS_Spc *spc, int index);
const char *rs_spc_error(void);
#endif
