pub mod ffi_boundary;
pub mod safe_core;

#[cfg(feature = "python")]
pub mod python_bindings;

pub use ffi_boundary::{
    rust_chunk_buffer, rust_chunk_buffer_v2, ChunkBoundary, ChunkBoundaryV2, CHUNKER_ERR_INVALID,
    CHUNKER_ERR_TRUNCATED, CHUNKER_MODE_COMPAT_C, CHUNKER_MODE_RAW, CHUNKER_MODE_SEMANTIC,
};
pub use safe_core::{
    blake3_128, cache_key, chunk_batch_with_config, chunk_slice, chunk_slice_compat,
    chunk_slice_semantic, chunk_with_config, chunker_fingerprint, validate_chunk_params, Chunk,
    ChunkerConfig, ChunkerError, ChunkingMode, ALGORITHM_VERSION, MAX_CHUNK_SIZE_LIMIT,
};
