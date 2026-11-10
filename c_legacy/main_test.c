#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "chunker.h"

int main(void) {
    const char *test_data =
        "Fast Content-Defined Chunking (FastCDC) stream processing and deduplication baseline. "
        "Systems programming in C and Rust with zero-copy PyO3 bindings and Rayon parallelism. "
        "Testing content-defined rolling hash boundary detection in legacy C.";
    size_t data_len = strlen(test_data);
    ChunkBoundary boundaries[16];

    /* 1. Normal execution test */
    int32_t count = chunk_buffer(
        (const uint8_t *)test_data,
        data_len,
        64,
        1024,
        0x07,
        boundaries,
        16
    );

    if (count < 0) {
        fprintf(stderr, "Error executing legacy C chunk_buffer: %d\n", count);
        return 1;
    }

    printf("[C Legacy] Total chunks identified: %d\n", count);
    for (int32_t i = 0; i < count; i++) {
        printf(
            "  Chunk %d: offset=%zu, len=%zu, hash=0x%llx\n",
            i,
            boundaries[i].offset,
            boundaries[i].length,
            (unsigned long long)boundaries[i].hash
        );
    }

    /* 2. Invalid parameter test */
    int32_t err_null = chunk_buffer(NULL, data_len, 64, 1024, 0, boundaries, 16);
    assert(err_null == CHUNKER_ERR_INVALID);

    /* 3. Truncation test on a larger heap-allocated buffer */
    size_t large_len = 8192;
    uint8_t *large_buf = (uint8_t *)malloc(large_len);
    if (!large_buf) {
        return 1;
    }
    for (size_t i = 0; i < large_len; i++) {
        large_buf[i] = (uint8_t)((i * 1103515245U + 12345U) >> 16);
    }

    ChunkBoundary small_out[2];
    int32_t trunc_rc = chunk_buffer(large_buf, large_len, 64, 1024, 0, small_out, 2);
    assert(trunc_rc == CHUNKER_ERR_TRUNCATED);
    free(large_buf);

    printf("[C Legacy] All assertions and memory checks passed.\n");
    return 0;
}
