#ifndef CHUNKER_H
#define CHUNKER_H

#include <stddef.h>
#include <stdint.h>
#include "fastcdc.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Error code returned when input pointers or size parameters are invalid. */
#define CHUNKER_ERR_INVALID   (-1)

/**
 * Error code returned when the input buffer produces more chunks than
 * `max_chunks`. The first `max_chunks` boundaries are written to
 * the output buffer before returning this status.
 */
#define CHUNKER_ERR_TRUNCATED (-2)

/** Mode constants for `rust_chunk_buffer_v2`. */
#define CHUNKER_MODE_COMPAT_C 0U
#define CHUNKER_MODE_RAW      1U
#define CHUNKER_MODE_SEMANTIC 2U

/**
 * v1 chunk boundary structure (retained unchanged for C ABI compatibility).
 */
typedef struct {
    size_t offset;
    size_t length;
    uint64_t hash;
} ChunkBoundary;

/**
 * v2 chunk boundary structure carrying a 128-bit (16-byte) BLAKE3 content digest.
 */
typedef struct {
    size_t offset;
    size_t length;
    uint8_t digest[16];
} ChunkBoundaryV2;

/**
 * v1 C reference implementation over a contiguous byte buffer using FastCDC.
 *
 * Note: `mask` is ignored (FastCDC derives its internal dual masks from the
 * average chunk size) and is retained solely for v1 ABI compatibility.
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

/**
 * v1 Rust FFI entry point (drop-in replacement for `chunk_buffer`).
 */
int32_t rust_chunk_buffer(
    const uint8_t *buf,
    size_t len,
    size_t min_chunk,
    size_t max_chunk,
    uint32_t mask,
    ChunkBoundary *out_boundaries,
    size_t max_chunks
);

/**
 * v2 Rust FFI entry point supporting raw, semantic, and C-compat modes,
 * explicit `avg_chunk` (pass 0 to use the midpoint `(min + max) / 2`),
 * and optional 128-bit (16-byte) BLAKE3 content digests.
 *
 * Parameters:
 * - `buf`: Input byte buffer (must not be NULL).
 * - `len`: Length of `buf` in bytes.
 * - `min_chunk`: Minimum chunk length in bytes (>= 1).
 * - `avg_chunk`: Target average chunk length in bytes (0 defaults to midpoint).
 * - `max_chunk`: Maximum chunk length in bytes (>= `min_chunk`, <= 1 GiB).
 * - `mode`: One of `CHUNKER_MODE_COMPAT_C` (0), `CHUNKER_MODE_RAW` (1),
 *           or `CHUNKER_MODE_SEMANTIC` (2).
 * - `compute_hash`: Non-zero to populate `out_boundaries[i].digest` with
 *                   128-bit BLAKE3; 0 to zero-fill `digest`.
 * - `out_boundaries`: Output buffer with capacity for at least `max_chunks` items.
 * - `max_chunks`: Capacity of `out_boundaries` (> 0 and <= INT32_MAX).
 *
 * Returns:
 * - `>= 0`: Number of chunks written to `out_boundaries`.
 * - `CHUNKER_ERR_INVALID` (-1): Invalid pointer, mode, or size parameters.
 * - `CHUNKER_ERR_TRUNCATED` (-2): Output truncated at `max_chunks` entries.
 */
int32_t rust_chunk_buffer_v2(
    const uint8_t *buf,
    size_t len,
    size_t min_chunk,
    size_t avg_chunk,
    size_t max_chunk,
    uint32_t mode,
    int32_t compute_hash,
    ChunkBoundaryV2 *out_boundaries,
    size_t max_chunks
);

#ifdef __cplusplus
}
#endif

#endif /* CHUNKER_H */
