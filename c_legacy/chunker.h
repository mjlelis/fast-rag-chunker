#ifndef CHUNKER_H
#define CHUNKER_H

#include <stddef.h>
#include <stdint.h>
#include "fastcdc.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    size_t offset;
    size_t length;
    uint64_t hash;
} ChunkBoundary;

/**
 * FastCDC production content-defined chunking over a byte buffer.
 * Powered by the official FastCDC algorithm (Wen Xia et al.).
 * Fills up to max_chunks boundaries into out_boundaries.
 * Returns number of chunks identified, or -1 on error.
 */
int32_t chunk_buffer(
    const uint8_t *buf,
    size_t len,
    size_t min_chunk,
    size_t max_chunk,
    uint32_t mask,
    ChunkBoundary *out_boundaries,
    size_t max_chunks
);

#ifdef __cplusplus
}
#endif

#endif /* CHUNKER_H */
