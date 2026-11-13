pub mod ffi_boundary;
pub mod safe_core;

#[cfg(feature = "python")]
pub mod python_bindings;

pub use ffi_boundary::{
    rust_chunk_buffer, rust_chunk_buffer_v2, rust_chunk_buffer_v3,
    ChunkBoundary, ChunkBoundaryV2, ChunkBoundaryV3,
    CHUNKER_ERR_INVALID, CHUNKER_ERR_TRUNCATED,
    CHUNKER_MODE_COMPAT_C, CHUNKER_MODE_RAW, CHUNKER_MODE_SEMANTIC, CHUNKER_MODE_BOUNDARY,
    CHUNKER_NORMALIZE_NONE, CHUNKER_NORMALIZE_WHITESPACE, CHUNKER_NORMALIZE_NFC,
    CHUNKER_UNIT_BYTES, CHUNKER_UNIT_TOKENS,
};
pub use safe_core::{
    blake3_128, cache_key, chunk_batch_with_config, chunk_slice, chunk_slice_compat,
    chunk_slice_semantic, chunk_with_config, chunker_fingerprint, diff_chunks,
    find_priority_boundary, resolve_snap_window, validate_chunk_params, Chunk,
    ChunkerConfig, ChunkerError, ChunkingMode, NormalizationMode, SizeUnit,
    ALGORITHM_VERSION, MAX_CHUNK_SIZE_LIMIT,
};
