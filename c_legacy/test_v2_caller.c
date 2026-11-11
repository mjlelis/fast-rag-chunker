#include <stdio.h>
#include <string.h>
#include "chunker.h"

int32_t c_call_and_verify_rust_v2(void) {
    const char *text =
        "Architectural verification of rust_chunk_buffer_v2 from C ABI! "
        "Semantic boundary snapping preserves UTF-8 words and populates "
        "128-bit BLAKE3 content digests in every ChunkBoundaryV2 entry. "
        "Repeating sentence to produce multiple chunks across the buffer.";

    ChunkBoundaryV2 chunks[16];
    memset(chunks, 0, sizeof(chunks));

    int32_t count = rust_chunk_buffer_v2(
        (const uint8_t *)text,
        strlen(text),
        32,
        64,
        128,
        CHUNKER_MODE_SEMANTIC,
        1,
        chunks,
        16
    );

    if (count < 2) {
        return -10;
    }

    size_t expected_offset = 0;
    for (int32_t i = 0; i < count; ++i) {
        if (chunks[i].offset != expected_offset || chunks[i].length == 0 || chunks[i].length > 128) {
            return -20;
        }
        int non_zero = 0;
        for (int b = 0; b < 16; ++b) {
            if (chunks[i].digest[b] != 0) {
                non_zero = 1;
                break;
            }
        }
        if (!non_zero) {
            return -30;
        }
        expected_offset += chunks[i].length;
    }

    if (expected_offset != strlen(text)) {
        return -40;
    }

    /* Verify truncation return code when max_chunks is smaller than total */
    ChunkBoundaryV2 trunc_chunks[1];
    int32_t trunc_rc = rust_chunk_buffer_v2(
        (const uint8_t *)text,
        strlen(text),
        32,
        64,
        128,
        CHUNKER_MODE_SEMANTIC,
        1,
        trunc_chunks,
        1
    );
    if (trunc_rc != CHUNKER_ERR_TRUNCATED) {
        return -50;
    }

    return count;
}

#ifdef STANDALONE_C_V2_MAIN
int main(void) {
    int32_t rc = c_call_and_verify_rust_v2();
    if (rc < 0) {
        fprintf(stderr, "c_call_and_verify_rust_v2 failed with status %d\n", (int)rc);
        return 1;
    }
    printf("c_call_and_verify_rust_v2 succeeded: %d semantic chunks verified with 128-bit BLAKE3 digests.\n", (int)rc);
    return 0;
}
#endif
