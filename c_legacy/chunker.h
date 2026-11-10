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
 * `out_boundaries` before returning this status.
 */
#define CHUNKER_ERR_TRUNCATED (-2)

typedef struct {
    size_t offset;
    size_t length;
    uint64_t hash;
} ChunkBoundary;

/**
 * Content-defined chunking over a contiguous byte buffer using FastCDC.
 *
 * Parameters:
 * - `buf`: Input byte buffer (must not be NULL).
 * - `len`: Length of `buf` in bytes.
 * - `min_chunk`: Minimum chunk length (clamped to [64, 67108864] in C ABI compat mode).
 * - `max_chunk`: Maximum chunk length (must be >= `min_chunk` and <= 1073741824).
 * - `mask`: Ignored (has no effect; FastCDC derives its internal dual masks from
 *           the average chunk size. Retained for ABI compatibility and scheduled
 *           for removal in v0.2.0).
 * - `out_boundaries`: Output buffer with capacity for at least `max_chunks` entries.
 * - `max_chunks`: Capacity of `out_boundaries` (must be > 0 and <= INT32_MAX).
 *
 * Returns:
 * - `>= 0`: Number of chunks identified and written to `out_boundaries`.
 * - `CHUNKER_ERR_INVALID` (-1): Invalid pointer or parameter bounds.
 * - `CHUNKER_ERR_TRUNCATED` (-2): Output truncated at `max_chunks` entries.
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
