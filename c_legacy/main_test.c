#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "chunker.h"

int main(void) {
    const char *test_data = "Fast Content-Defined Chunking (FastCDC) stream processing and deduplication baseline. "
                            "Systems programming in C and Rust with zero-copy PyO3 bindings and Rayon parallelism. "
                            "Testing content-defined rolling hash boundary detection in legacy C.";
    size_t data_len = strlen(test_data);
    ChunkBoundary boundaries[16];

    int32_t count = chunk_buffer(
        (const uint8_t *)test_data,
        data_len,
        16,   // min_chunk
        64,   // max_chunk
        0x07, // mask (3 bits -> trigger on average every 8 bytes)
        boundaries,
        16
    );

    if (count < 0) {
        fprintf(stderr, "Erro ao processar chunking C legada!\n");
        return 1;
    }

    printf("[C Legacy] Total de chunks identificados: %d\n", count);
    for (int32_t i = 0; i < count; i++) {
        printf("  Chunk %d: offset=%zu, len=%zu, hash=0x%llx\n",
               i, boundaries[i].offset, boundaries[i].length, (unsigned long long)boundaries[i].hash);
    }

    return 0;
}
