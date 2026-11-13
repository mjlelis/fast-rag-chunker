use std::panic::catch_unwind;
use std::ptr;
use std::slice;

use crate::safe_core::{
    chunk_slice_compat, chunk_with_config, ChunkerConfig, ChunkingMode, NormalizationMode,
    SizeUnit,
};

/// Return code when input pointers or chunk size parameters are invalid.
pub const CHUNKER_ERR_INVALID: i32 = -1;

/// Return code when the buffer produces more chunks than `max_chunks`.
/// The first `max_chunks` items are written to `out_boundaries`.
pub const CHUNKER_ERR_TRUNCATED: i32 = -2;

/// Mode constant for C ABI: C-legacy clamped compatibility mode.
pub const CHUNKER_MODE_COMPAT_C: u32 = 0;

/// Mode constant for C ABI: unclamped raw FastCDC mode.
pub const CHUNKER_MODE_RAW: u32 = 1;

/// Mode constant for C ABI: UTF-8 and natural-language semantic boundary mode (deprecated alias).
pub const CHUNKER_MODE_SEMANTIC: u32 = 2;

/// Mode constant for C ABI: Priority boundary mode.
pub const CHUNKER_MODE_BOUNDARY: u32 = 3;

/// Normalization mode constants for `rust_chunk_buffer_v3`.
pub const CHUNKER_NORMALIZE_NONE: u32 = 0;
pub const CHUNKER_NORMALIZE_WHITESPACE: u32 = 1;
pub const CHUNKER_NORMALIZE_NFC: u32 = 2;

/// Size unit constants for `rust_chunk_buffer_v3`.
pub const CHUNKER_UNIT_BYTES: u32 = 0;
pub const CHUNKER_UNIT_TOKENS: u32 = 1;

#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ChunkBoundary {
    pub offset: usize,
    pub length: usize,
    pub hash: u64,
}

#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ChunkBoundaryV2 {
    pub offset: usize,
    pub length: usize,
    pub digest: [u8; 16],
}

#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ChunkBoundaryV3 {
    pub offset: usize,
    pub length: usize,
    pub digest: [u8; 16],
    pub ordinal: usize,
}

/// v1 C ABI compatible entry point demonstrating the Strangler Fig replacement pattern.
///
/// Retained unchanged in v0.3.0 to preserve v1 binary compatibility and C parity tests.
///
/// # Safety
///
/// - If `len > 0`, `buf` must be a valid, non-null pointer to at least `len` initialized
///   bytes that remain valid and unmutated for the duration of this call.
/// - `out_boundaries` must be a valid, properly aligned, non-overlapping mutable pointer
///   with capacity for at least `max_chunks` elements of `ChunkBoundary`.
#[no_mangle]
pub unsafe extern "C" fn rust_chunk_buffer(
    buf: *const u8,
    len: usize,
    min_chunk: usize,
    max_chunk: usize,
    _mask: u32,
    out_boundaries: *mut ChunkBoundary,
    max_chunks: usize,
) -> i32 {
    let result = catch_unwind(|| {
        if buf.is_null()
            || out_boundaries.is_null()
            || min_chunk == 0
            || max_chunk < min_chunk
            || max_chunks == 0
            || i32::try_from(max_chunks).is_err()
        {
            return CHUNKER_ERR_INVALID;
        }

        if len == 0 {
            return 0;
        }

        let slice_data = unsafe { slice::from_raw_parts(buf, len) };

        match chunk_slice_compat(slice_data, min_chunk, max_chunk) {
            Ok(chunks) => {
                let to_copy = chunks.len().min(max_chunks);
                for (i, chunk) in chunks.iter().take(to_copy).enumerate() {
                    unsafe {
                        ptr::write(
                            out_boundaries.add(i),
                            ChunkBoundary {
                                offset: chunk.offset,
                                length: chunk.length,
                                hash: 0,
                            },
                        );
                    }
                }
                if chunks.len() > max_chunks {
                    CHUNKER_ERR_TRUNCATED
                } else {
                    to_copy as i32
                }
            }
            Err(_) => CHUNKER_ERR_INVALID,
        }
    });

    result.unwrap_or(CHUNKER_ERR_INVALID)
}

/// v2 C ABI entry point supporting `CHUNKER_MODE_COMPAT_C` (0), `CHUNKER_MODE_RAW` (1),
/// `CHUNKER_MODE_SEMANTIC` (2), and `CHUNKER_MODE_BOUNDARY` (3), explicit `avg_chunk`,
/// and 128-bit (16-byte) BLAKE3 content digests in `ChunkBoundaryV2`.
///
/// # Safety
///
/// - If `len > 0`, `buf` must be a valid, non-null pointer to at least `len` initialized bytes.
/// - `out_boundaries` must be a valid, properly aligned mutable pointer for `max_chunks` elements.
#[no_mangle]
pub unsafe extern "C" fn rust_chunk_buffer_v2(
    buf: *const u8,
    len: usize,
    min_chunk: usize,
    avg_chunk: usize,
    max_chunk: usize,
    mode: u32,
    compute_hash: i32,
    out_boundaries: *mut ChunkBoundaryV2,
    max_chunks: usize,
) -> i32 {
    let result = catch_unwind(|| {
        if buf.is_null()
            || out_boundaries.is_null()
            || min_chunk == 0
            || max_chunk < min_chunk
            || max_chunks == 0
            || i32::try_from(max_chunks).is_err()
        {
            return CHUNKER_ERR_INVALID;
        }

        let chunking_mode = match mode {
            CHUNKER_MODE_COMPAT_C => ChunkingMode::CompatC,
            CHUNKER_MODE_RAW => ChunkingMode::Raw,
            CHUNKER_MODE_SEMANTIC | CHUNKER_MODE_BOUNDARY => ChunkingMode::Boundary,
            _ => return CHUNKER_ERR_INVALID,
        };

        let avg_opt = if avg_chunk == 0 {
            None
        } else {
            Some(avg_chunk)
        };
        let cfg = match ChunkerConfig::new(
            min_chunk,
            avg_opt,
            max_chunk,
            chunking_mode,
            compute_hash != 0,
        ) {
            Ok(c) => c,
            Err(_) => return CHUNKER_ERR_INVALID,
        };

        if len == 0 {
            return 0;
        }

        let slice_data = unsafe { slice::from_raw_parts(buf, len) };

        match chunk_with_config(slice_data, &cfg) {
            Ok(chunks) => {
                let to_copy = chunks.len().min(max_chunks);
                for (i, chunk) in chunks.iter().take(to_copy).enumerate() {
                    unsafe {
                        ptr::write(
                            out_boundaries.add(i),
                            ChunkBoundaryV2 {
                                offset: chunk.offset,
                                length: chunk.length,
                                digest: chunk.digest,
                            },
                        );
                    }
                }
                if chunks.len() > max_chunks {
                    CHUNKER_ERR_TRUNCATED
                } else {
                    to_copy as i32
                }
            }
            Err(_) => CHUNKER_ERR_INVALID,
        }
    });

    result.unwrap_or(CHUNKER_ERR_INVALID)
}

/// v3 C ABI entry point supporting priority boundary mode, snap window,
/// pre-hash normalization, token/byte units, and ordinal indexing.
///
/// # Safety
///
/// - If `len > 0`, `buf` must be a valid, non-null pointer to at least `len` initialized bytes.
/// - `out_boundaries` must be a valid, properly aligned mutable pointer for `max_chunks` elements.
#[no_mangle]
pub unsafe extern "C" fn rust_chunk_buffer_v3(
    buf: *const u8,
    len: usize,
    min_chunk: usize,
    avg_chunk: usize,
    max_chunk: usize,
    mode: u32,
    snap_window: u32,
    normalize: u32,
    size_unit: u32,
    compute_hash: i32,
    out_boundaries: *mut ChunkBoundaryV3,
    max_chunks: usize,
) -> i32 {
    let result = catch_unwind(|| {
        if buf.is_null()
            || out_boundaries.is_null()
            || min_chunk == 0
            || max_chunk < min_chunk
            || max_chunks == 0
            || i32::try_from(max_chunks).is_err()
        {
            return CHUNKER_ERR_INVALID;
        }

        let chunking_mode = match mode {
            CHUNKER_MODE_COMPAT_C => ChunkingMode::CompatC,
            CHUNKER_MODE_RAW => ChunkingMode::Raw,
            CHUNKER_MODE_SEMANTIC | CHUNKER_MODE_BOUNDARY => ChunkingMode::Boundary,
            _ => return CHUNKER_ERR_INVALID,
        };

        let norm_mode = match normalize {
            CHUNKER_NORMALIZE_NONE => NormalizationMode::None,
            CHUNKER_NORMALIZE_WHITESPACE => NormalizationMode::Whitespace,
            CHUNKER_NORMALIZE_NFC => NormalizationMode::Nfc,
            _ => return CHUNKER_ERR_INVALID,
        };

        let unit = match size_unit {
            CHUNKER_UNIT_BYTES => SizeUnit::Bytes,
            CHUNKER_UNIT_TOKENS => SizeUnit::Tokens,
            _ => return CHUNKER_ERR_INVALID,
        };

        let avg_opt = if avg_chunk == 0 {
            None
        } else {
            Some(avg_chunk)
        };

        let snap_opt = if snap_window == 0 {
            None
        } else {
            Some(snap_window as usize)
        };

        let cfg = match ChunkerConfig::new_full(
            min_chunk,
            avg_opt,
            max_chunk,
            chunking_mode,
            compute_hash != 0,
            snap_opt,
            unit,
            norm_mode,
            0,
            0,
        ) {
            Ok(c) => c,
            Err(_) => return CHUNKER_ERR_INVALID,
        };

        if len == 0 {
            return 0;
        }

        let slice_data = unsafe { slice::from_raw_parts(buf, len) };

        match chunk_with_config(slice_data, &cfg) {
            Ok(chunks) => {
                let to_copy = chunks.len().min(max_chunks);
                for (i, chunk) in chunks.iter().take(to_copy).enumerate() {
                    unsafe {
                        ptr::write(
                            out_boundaries.add(i),
                            ChunkBoundaryV3 {
                                offset: chunk.offset,
                                length: chunk.length,
                                digest: chunk.digest,
                                ordinal: chunk.ordinal,
                            },
                        );
                    }
                }
                if chunks.len() > max_chunks {
                    CHUNKER_ERR_TRUNCATED
                } else {
                    to_copy as i32
                }
            }
            Err(_) => CHUNKER_ERR_INVALID,
        }
    });

    result.unwrap_or(CHUNKER_ERR_INVALID)
}

extern "C" {
    pub fn chunk_buffer(
        buf: *const u8,
        len: usize,
        min_chunk: usize,
        max_chunk: usize,
        mask: u32,
        out_boundaries: *mut ChunkBoundary,
        max_chunks: usize,
    ) -> i32;

    pub fn c_call_and_verify_rust_v2() -> i32;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_null_pointer_handling() {
        unsafe {
            let res = rust_chunk_buffer(ptr::null(), 10, 64, 1024, 0x07, ptr::null_mut(), 10);
            assert_eq!(res, CHUNKER_ERR_INVALID);

            let res_v2 = rust_chunk_buffer_v2(
                ptr::null(),
                10,
                64,
                0,
                512,
                CHUNKER_MODE_SEMANTIC,
                1,
                ptr::null_mut(),
                10,
            );
            assert_eq!(res_v2, CHUNKER_ERR_INVALID);

            let res_v3 = rust_chunk_buffer_v3(
                ptr::null(),
                10,
                64,
                0,
                512,
                CHUNKER_MODE_BOUNDARY,
                0,
                0,
                0,
                1,
                ptr::null_mut(),
                10,
            );
            assert_eq!(res_v3, CHUNKER_ERR_INVALID);
        }
    }

    #[test]
    fn test_rust_chunk_buffer_v3_execution() {
        let text = b"# Header Title\n\nFirst paragraph content here. Second paragraph content follows.";
        let mut out = [ChunkBoundaryV3 {
            offset: 0,
            length: 0,
            digest: [0u8; 16],
            ordinal: 0,
        }; 8];

        let count = unsafe {
            rust_chunk_buffer_v3(
                text.as_ptr(),
                text.len(),
                16,
                32,
                64,
                CHUNKER_MODE_BOUNDARY,
                0,
                CHUNKER_NORMALIZE_NONE,
                CHUNKER_UNIT_BYTES,
                1,
                out.as_mut_ptr(),
                8,
            )
        };

        assert!(count >= 1);
        for i in 0..(count as usize) {
            assert_eq!(out[i].ordinal, i);
            assert!(out[i].length > 0);
            assert_ne!(out[i].digest, [0u8; 16]);
        }
    }

    #[test]
    fn test_strangler_fig_c_vs_rust_parity() {
        let sample = b"Direct comparison between legacy C baseline and Rust Strangler Fig FFI!";
        let mut c_out = [ChunkBoundary {
            offset: 0,
            length: 0,
            hash: 0,
        }; 16];
        let mut rust_out = [ChunkBoundary {
            offset: 0,
            length: 0,
            hash: 0,
        }; 16];

        let c_count = unsafe {
            chunk_buffer(
                sample.as_ptr(),
                sample.len(),
                64,
                1024,
                0x03,
                c_out.as_mut_ptr(),
                16,
            )
        };

        let rust_count = unsafe {
            rust_chunk_buffer(
                sample.as_ptr(),
                sample.len(),
                64,
                1024,
                0x03,
                rust_out.as_mut_ptr(),
                16,
            )
        };

        assert!(c_count > 0);
        assert_eq!(c_count, rust_count);

        for (c_item, r_item) in c_out.iter().zip(rust_out.iter()).take(c_count as usize) {
            assert_eq!(c_item, r_item);
        }
    }

    #[test]
    fn test_strangler_fig_c_vs_rust_multi_chunk_parity() {
        let mut sample = Vec::with_capacity(8192);
        for i in 0..8192u32 {
            sample.push(((i.wrapping_mul(1103515245).wrapping_add(12345)) >> 16) as u8);
        }

        let mut c_out = [ChunkBoundary {
            offset: 0,
            length: 0,
            hash: 0,
        }; 64];
        let mut rust_out = [ChunkBoundary {
            offset: 0,
            length: 0,
            hash: 0,
        }; 64];

        let c_count = unsafe {
            chunk_buffer(
                sample.as_ptr(),
                sample.len(),
                64,
                1024,
                0x1F,
                c_out.as_mut_ptr(),
                64,
            )
        };

        let rust_count = unsafe {
            rust_chunk_buffer(
                sample.as_ptr(),
                sample.len(),
                64,
                1024,
                0x1F,
                rust_out.as_mut_ptr(),
                64,
            )
        };

        assert!(c_count > 1);
        assert_eq!(c_count, rust_count);

        for (c_item, r_item) in c_out.iter().zip(rust_out.iter()).take(c_count as usize) {
            assert_eq!(c_item, r_item);
        }
    }

    #[test]
    fn test_truncation_signaling_and_parity() {
        let mut sample = Vec::with_capacity(8192);
        for i in 0..8192u32 {
            sample.push(((i.wrapping_mul(1103515245).wrapping_add(12345)) >> 16) as u8);
        }

        let max_chunks = 3usize;
        let mut c_out = [ChunkBoundary {
            offset: 0,
            length: 0,
            hash: 0,
        }; 3];
        let mut rust_out = [ChunkBoundary {
            offset: 0,
            length: 0,
            hash: 0,
        }; 3];

        let c_rc = unsafe {
            chunk_buffer(
                sample.as_ptr(),
                sample.len(),
                64,
                1024,
                0,
                c_out.as_mut_ptr(),
                max_chunks,
            )
        };

        let rust_rc = unsafe {
            rust_chunk_buffer(
                sample.as_ptr(),
                sample.len(),
                64,
                1024,
                0,
                rust_out.as_mut_ptr(),
                max_chunks,
            )
        };

        assert_eq!(c_rc, CHUNKER_ERR_TRUNCATED);
        assert_eq!(rust_rc, CHUNKER_ERR_TRUNCATED);
        assert_eq!(c_out, rust_out);
    }

    #[test]
    fn test_c_caller_invoking_rust_chunk_buffer_v2() {
        let count = unsafe { c_call_and_verify_rust_v2() };
        assert!(
            count >= 2,
            "C caller verification of rust_chunk_buffer_v2 failed with status {count}"
        );
    }
}
