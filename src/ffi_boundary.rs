use std::panic::catch_unwind;
use std::slice;

use crate::safe_core::chunk_slice;

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct ChunkBoundary {
    pub offset: usize,
    pub length: usize,
    pub hash: u64,
}

/// Interface FFI de compatibilidade binária (ABI C) com substituição Strangler Fig.
///
/// Defesas implementadas:
/// 1. Verificação estrita de ponteiros nulos e limites de argumentos.
/// 2. Conversão imediata para slice Rust seguro com `std::slice::from_raw_parts`.
/// 3. Isolamento completo contra pânico com `std::panic::catch_unwind`.
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
        // 1. Defesa contra ponteiros nulos e argumentos inválidos
        if buf.is_null()
            || out_boundaries.is_null()
            || min_chunk == 0
            || max_chunk < min_chunk
            || max_chunks == 0
        {
            return -1;
        }

        if len == 0 {
            return 0;
        }

        // 2. Conversão imediata para slices seguros do Rust
        let slice_data = slice::from_raw_parts(buf, len);
        let out_slice = slice::from_raw_parts_mut(out_boundaries, max_chunks);

        // 3. Chamada ao núcleo seguro
        match chunk_slice(slice_data, min_chunk, max_chunk, mask) {
            Ok(chunks) => {
                let to_copy = chunks.len().min(max_chunks);
                for i in 0..to_copy {
                    out_slice[i] = ChunkBoundary {
                        offset: chunks[i].offset,
                        length: chunks[i].length,
                        hash: chunks[i].hash,
                    };
                }
                to_copy as i32
            }
            Err(_) => -1,
        }
    });

    match result {
        Ok(code) => code,
        Err(_) => -1, // Captura qualquer panic e impede vazamento de Unwind além da ABI C
    }
}

// Declaração externa para linkar e validar com o baseline C compilado pelo build.rs
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
            let res = rust_chunk_buffer(
                std::ptr::null(),
                10,
                4,
                16,
                0x07,
                std::ptr::null_mut(),
                10,
            );
            assert_eq!(res, -1);
        }
    }

    #[test]
    fn test_strangler_fig_c_vs_rust_parity() {
        let sample = b"Comparacao direta de baseline C versus implementacao Rust Strangler Fig!";
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

        for i in 0..(c_count as usize) {
            assert_eq!(c_out[i].offset, rust_out[i].offset);
            assert_eq!(c_out[i].length, rust_out[i].length);
            assert_eq!(c_out[i].hash, rust_out[i].hash);
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

        for i in 0..(c_count as usize) {
            assert_eq!(c_out[i].offset, rust_out[i].offset);
            assert_eq!(c_out[i].length, rust_out[i].length);
            assert_eq!(c_out[i].hash, rust_out[i].hash);
        }
    }
}
