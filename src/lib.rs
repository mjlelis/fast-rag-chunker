pub mod ffi_boundary;
pub mod safe_core;

#[cfg(feature = "python")]
pub mod python_bindings;

pub use ffi_boundary::{
    rust_chunk_buffer, ChunkBoundary, CHUNKER_ERR_INVALID, CHUNKER_ERR_TRUNCATED,
};
pub use safe_core::{
    chunk_slice, chunk_slice_compat, chunk_slice_semantic, fnv1a_64, validate_chunk_params, Chunk,
    ChunkerError, MAX_CHUNK_SIZE_LIMIT,
};
