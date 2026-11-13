#ifndef CHUNKER_H
#define CHUNKER_H

#include <stddef.h>
#include <stdint.h>

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

/** Mode constants for `rust_chunk_buffer_v2` and `rust_chunk_buffer_v3`. */
#define CHUNKER_MODE_COMPAT_C 0U
#define CHUNKER_MODE_RAW      1U
#define CHUNKER_MODE_SEMANTIC 2U  /* deprecated alias for CHUNKER_MODE_BOUNDARY */
#define CHUNKER_MODE_BOUNDARY 3U

/** Normalization mode constants for `rust_chunk_buffer_v3`. */
#define CHUNKER_NORMALIZE_NONE       0U
#define CHUNKER_NORMALIZE_WHITESPACE 1U
#define CHUNKER_NORMALIZE_NFC        2U

/** Size unit constants for `rust_chunk_buffer_v3`. */
#define CHUNKER_UNIT_BYTES  0U
#define CHUNKER_UNIT_TOKENS 1U

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
 * v3 chunk boundary structure carrying a 128-bit BLAKE3 digest and ordinal index.
 */
typedef struct {
    size_t offset;
    size_t length;
    uint8_t digest[16];
    size_t ordinal;
} ChunkBoundaryV3;

/**
 * v1 C reference implementation over a contiguous byte buffer using FastCDC.
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

/**
 * v3 Rust FFI entry point supporting priority boundary mode, configurable snap window,
 * pre-hash normalization, token/byte units, and ordinal indexing.
 */
int32_t rust_chunk_buffer_v3(
    const uint8_t *buf,
    size_t len,
    size_t min_chunk,
    size_t avg_chunk,
    size_t max_chunk,
    uint32_t mode,
    uint32_t snap_window,
    uint32_t normalize,
    uint32_t size_unit,
    int32_t compute_hash,
    ChunkBoundaryV3 *out_boundaries,
    size_t max_chunks
);

#ifdef __cplusplus
}
#endif

#endif /* CHUNKER_H */
