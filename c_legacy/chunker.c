#include "chunker.h"
#include "fastcdc.h"

typedef struct {
    ChunkBoundary *out_boundaries;
    size_t max_chunks;
    size_t count;
} ChunkCollector;

static int collector_callback(void *arg, size_t offset, size_t len) {
    ChunkCollector *col = (ChunkCollector *)arg;
    if (col->count < col->max_chunks) {
        col->out_boundaries[col->count].offset = offset;
        col->out_boundaries[col->count].length = len;
        col->out_boundaries[col->count].hash = 0; // FastCDC utiliza gear hash interno
        col->count++;
        return 0; // continua
    }
    return 1; // atingiu o limite
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
    (void)mask;
    if (!buf || !out_boundaries || min_chunk == 0 || max_chunk < min_chunk || max_chunks == 0) {
        return -1;
    }

    if (len == 0) {
        return 0;
    }

    // Calcula tamanho médio geométrico para o FastCDC
    uint32_t avg = (uint32_t)((min_chunk + max_chunk) / 2);
    if (avg < 256) avg = 256; // FastCDC AVERAGE_MIN

    fcdc_ctx ctx = fastcdc_init((uint32_t)min_chunk, avg, (uint32_t)max_chunk);
    ChunkCollector collector = {
        .out_boundaries = out_boundaries,
        .max_chunks = max_chunks,
        .count = 0
    };

    fastcdc_update(&ctx, (uint8_t *)buf, len, 1, collector_callback, &collector);

    return (int32_t)collector.count;
}
