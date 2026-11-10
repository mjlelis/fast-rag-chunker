#include "chunker.h"
#include "fastcdc.h"
#include <limits.h>

#define MAX_SUPPORTED_CHUNK_SIZE (1ULL << 30)

typedef struct {
    ChunkBoundary *out_boundaries;
    size_t max_chunks;
    size_t count;
    int truncated;
} ChunkCollector;

static int collector_callback(void *arg, size_t offset, size_t len) {
    ChunkCollector *col = (ChunkCollector *)arg;
    if (col->count < col->max_chunks) {
        col->out_boundaries[col->count].offset = offset;
        col->out_boundaries[col->count].length = len;
        col->out_boundaries[col->count].hash = 0;
        col->count++;
        return 0;
    }
    col->truncated = 1;
    return 1; /* Signal fastcdc_update to stop early */
}

int32_t chunk_buffer(
    const uint8_t *buf,
    size_t len,
    size_t min_chunk,
    size_t max_chunk,
    uint32_t mask,
    ChunkBoundary *out_boundaries,
    size_t max_chunks
) {
    (void)mask; /* Ignored; scheduled for removal in v0.2.0 */

    if (!buf || !out_boundaries || min_chunk == 0 || max_chunk < min_chunk ||
        max_chunk > MAX_SUPPORTED_CHUNK_SIZE || max_chunks == 0 ||
        max_chunks > (size_t)INT32_MAX) {
        return CHUNKER_ERR_INVALID;
    }

    if (len == 0) {
        return 0;
    }

    uint32_t mi = (uint32_t)min_chunk;
    uint32_t ma = (uint32_t)max_chunk;
    uint32_t avg = mi + (ma - mi) / 2;
    if (avg < 256) {
        avg = 256;
    }

    fcdc_ctx ctx = fastcdc_init(mi, avg, ma);
    ChunkCollector collector = {
        .out_boundaries = out_boundaries,
        .max_chunks = max_chunks,
        .count = 0,
        .truncated = 0
    };

    fastcdc_update(&ctx, (uint8_t *)buf, len, 1, collector_callback, &collector);

    if (collector.truncated) {
        return CHUNKER_ERR_TRUNCATED;
    }

    return (int32_t)collector.count;
}
