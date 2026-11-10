use std::panic::catch_unwind;
use std::ptr;
use std::slice;

use crate::safe_core::chunk_slice_compat;

/// Return code when input pointers or chunk size parameters are invalid.
pub const CHUNKER_ERR_INVALID: i32 = -1;

/// Return code when the buffer produces more chunks than `max_chunks`.
/// The first `max_chunks` items are written to `out_boundaries`.
pub const CHUNKER_ERR_TRUNCATED: i32 = -2;

#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ChunkBoundary {
    pub offset: usize,
    pub length: usize,
    pub hash: u64,
}

/// C ABI compatible entry point demonstrating the Strangler Fig replacement pattern.
///
/// Defenses implemented at the boundary:
/// 1. Validates null pointers and parameter bounds before dereferencing.
/// 2. Promotes `buf` to an immutable slice (`slice::from_raw_parts`) and writes
///    output elements via `ptr::write` without creating `&mut [T]` over uninitialized memory.
/// 3. Isolates execution inside `std::panic::catch_unwind` so no Rust panic ever unwinds
///    across the C ABI boundary.
///
/// Note: `mask` is ignored (retained for ABI compatibility; scheduled for removal in v0.2.0).
///
/// # Safety
///
/// - If `len > 0`, `buf` must be a valid, non-null pointer to at least `len` initialized
///   bytes that remain valid and unmutated for the duration of this call (passing a null
///   `buf` is safely caught and returns `CHUNKER_ERR_INVALID`).
/// - `out_boundaries` must be a valid, properly aligned, non-overlapping mutable pointer
///   with capacity for at least `max_chunks` elements of `ChunkBoundary` (passing a null
///   `out_boundaries` is safely caught and returns `CHUNKER_ERR_INVALID`). The memory at
///   `out_boundaries` does not need to be initialized prior to calling this function.
#[no_mangle]
pub unsafe extern "C" fn rust_chunk_buffer(
    buf: *const u8,
    len: usize,
    min_chunk: usize,
    max_chunk: usize,
    mask: u32,
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

        match chunk_slice_compat(slice_data, min_chunk, max_chunk, mask) {
            Ok(chunks) => {
                let to_copy = chunks.len().min(max_chunks);
                for (i, chunk) in chunks.iter().take(to_copy).enumerate() {
                    unsafe {
                        ptr::write(
                            out_boundaries.add(i),
                            ChunkBoundary {
                                offset: chunk.offset,
                                length: chunk.length,
                                hash: chunk.hash,
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
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_null_pointer_handling() {
        unsafe {
            let res = rust_chunk_buffer(ptr::null(), 10, 64, 1024, 0x07, ptr::null_mut(), 10);
            assert_eq!(res, CHUNKER_ERR_INVALID);
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
}
