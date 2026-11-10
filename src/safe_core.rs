#![forbid(unsafe_code)]

//! # Safe Core: FastCDC (Fast Content-Defined Chunking) & Semantic Boundary Snapping
//!
//! Idiomatic, 100% memory-safe implementation of the FastCDC algorithm (USENIX ATC'16, Wen Xia et al.)
//! with a 256-entry GEAR table, window size normalization, dual-mask rolling hash, and
//! NLP/UTF-8 Semantic Boundary Snapping for Retrieval-Augmented Generation (RAG) pipelines.
//!
//! Contains zero unsafe code (`#![forbid(unsafe_code)]`) and no `libc` dependencies.

use thiserror::Error;

#[derive(Error, Debug, PartialEq, Eq)]
pub enum ChunkerError {
    #[error("min_chunk cannot be zero")]
    ZeroMinChunk,
    #[error("max_chunk ({max}) must be greater than or equal to min_chunk ({min})")]
    InvalidChunkSize { min: usize, max: usize },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Chunk {
    pub offset: usize,
    pub length: usize,
    pub hash: u64,
}

// FastCDC clamping constants matching c_legacy/fastcdc.c
const AVERAGE_MIN: u32 = 1 << 8; // 256
const AVERAGE_MAX: u32 = 1 << 28; // 268,435,456
const MINIMUM_MIN: u32 = AVERAGE_MIN >> 2; // 64
const MINIMUM_MAX: u32 = AVERAGE_MAX >> 2;
const MAXIMUM_MIN: u32 = AVERAGE_MIN << 2; // 1024
const MAXIMUM_MAX: u32 = AVERAGE_MAX << 2;

// FNV-1a 64-bit constants for deterministic chunk fingerprinting
const FNV_OFFSET_BASIS: u64 = 0xcbf29ce484222325;
const FNV_PRIME: u64 = 0x00000100000001B3;

// Standard 256-entry GEAR table from the USENIX ATC'16 FastCDC specification
const GEAR: [u32; 256] = [
    0x5C95C078, 0x22408989, 0x2D48A214, 0x12842087, 0x530F8AFB, 0x474536B9,
    0x2963B4F1, 0x44CB738B, 0x4EA7403D, 0x4D606B6E, 0x074EC5D3, 0x3AF39D18,
    0x726003CA, 0x37A62A74, 0x51A2F58E, 0x7506358E, 0x5D4AB128, 0x4D4AE17B,
    0x41E85924, 0x470C36F7, 0x4741CBE1, 0x01BB7F30, 0x617C1DE3, 0x2B0C3A1F,
    0x50C48F73, 0x21A82D37, 0x6095ACE0, 0x419167A0, 0x3CAF49B0, 0x40CEA62D,
    0x66BC1C66, 0x545E1DAD, 0x2BFA77CD, 0x6E85DA24, 0x5FB0BDC5, 0x652CFC29,
    0x3A0AE1AB, 0x2837E0F3, 0x6387B70E, 0x13176012, 0x4362C2BB, 0x66D8F4B1,
    0x37FCE834, 0x2C9CD386, 0x21144296, 0x627268A8, 0x650DF537, 0x2805D579,
    0x3B21EBBD, 0x7357ED34, 0x3F58B583, 0x7150DDCA, 0x7362225E, 0x620A6070,
    0x2C5EF529, 0x7B522466, 0x768B78C0, 0x4B54E51E, 0x75FA07E5, 0x06A35FC6,
    0x30B71024, 0x1C8626E1, 0x296AD578, 0x28D7BE2E, 0x1490A05A, 0x7CEE43BD,
    0x698B56E3, 0x09DC0126, 0x4ED6DF6E, 0x02C1BFC7, 0x2A59AD53, 0x29C0E434,
    0x7D6C5278, 0x507940A7, 0x5EF6BA93, 0x68B6AF1E, 0x46537276, 0x611BC766,
    0x155C587D, 0x301BA847, 0x2CC9DDA7, 0x0A438E2C, 0x0A69D514, 0x744C72D3,
    0x4F326B9B, 0x7EF34286, 0x4A0EF8A7, 0x6AE06EBE, 0x669C5372, 0x12402DCB,
    0x5FEAE99D, 0x76C7F4A7, 0x6ABDB79C, 0x0DFAA038, 0x20E2282C, 0x730ED48B,
    0x069DAC2F, 0x168ECF3E, 0x2610E61F, 0x2C512C8E, 0x15FB8C06, 0x5E62BC76,
    0x69555135, 0x0ADB864C, 0x4268F914, 0x349AB3AA, 0x20EDFDB2, 0x51727981,
    0x37B4B3D8, 0x5DD17522, 0x6B2CBFE4, 0x5C47CF9F, 0x30FA1CCD, 0x23DEDB56,
    0x13D1F50A, 0x64EDDEE7, 0x0820B0F7, 0x46E07308, 0x1E2D1DFD, 0x17B06C32,
    0x250036D8, 0x284DBF34, 0x68292EE0, 0x362EC87C, 0x087CB1EB, 0x76B46720,
    0x104130DB, 0x71966387, 0x482DC43F, 0x2388EF25, 0x524144E1, 0x44BD834E,
    0x448E7DA3, 0x3FA6EAF9, 0x3CDA215C, 0x3A500CF3, 0x395CB432, 0x5195129F,
    0x43945F87, 0x51862CA4, 0x56EA8FF1, 0x201034DC, 0x4D328FF5, 0x7D73A909,
    0x6234D379, 0x64CFBF9C, 0x36F6589A, 0x0A2CE98A, 0x5FE4D971, 0x03BC15C5,
    0x44021D33, 0x16C1932B, 0x37503614, 0x1ACAF69D, 0x3F03B779, 0x49E61A03,
    0x1F52D7EA, 0x1C6DDD5C, 0x062218CE, 0x07E7A11A, 0x1905757A, 0x7CE00A53,
    0x49F44F29, 0x4BCC70B5, 0x39FEEA55, 0x5242CEE8, 0x3CE56B85, 0x00B81672,
    0x46BEECCC, 0x3CA0AD56, 0x2396CEE8, 0x78547F40, 0x6B08089B, 0x66A56751,
    0x781E7E46, 0x1E2CF856, 0x3BC13591, 0x494A4202, 0x520494D7, 0x2D87459A,
    0x757555B6, 0x42284CC1, 0x1F478507, 0x75C95DFF, 0x35FF8DD7, 0x4E4757ED,
    0x2E11F88C, 0x5E1B5048, 0x420E6699, 0x226B0695, 0x4D1679B4, 0x5A22646F,
    0x161D1131, 0x125C68D9, 0x1313E32E, 0x4AA85724, 0x21DC7EC1, 0x4FFA29FE,
    0x72968382, 0x1CA8EEF3, 0x3F3B1C28, 0x39C2FB6C, 0x6D76493F, 0x7A22A62E,
    0x789B1C2A, 0x16E0CB53, 0x7DECEEEB, 0x0DC7E1C6, 0x5C75BF3D, 0x52218333,
    0x106DE4D6, 0x7DC64422, 0x65590FF4, 0x2C02EC30, 0x64A9AC67, 0x59CAB2E9,
    0x4A21D2F3, 0x0F616E57, 0x23B54EE8, 0x02730AAA, 0x2F3C634D, 0x7117FC6C,
    0x01AC6F05, 0x5A9ED20C, 0x158C4E2A, 0x42B699F0, 0x0C7C14B3, 0x02BD9641,
    0x15AD56FC, 0x1C722F60, 0x7DA1AF91, 0x23E0DBCB, 0x0E93E12B, 0x64B2791D,
    0x440D2476, 0x588EA8DD, 0x4665A658, 0x7446C418, 0x1877A774, 0x5626407E,
    0x7F63BD46, 0x32D2DBD8, 0x3C790F4A, 0x772B7239, 0x6F8B2826, 0x677FF609,
    0x0DC82C11, 0x23FFE354, 0x2EAC53A6, 0x16139E09, 0x0AFD0DBC, 0x2A4D4237,
    0x56A368C7, 0x234325E4, 0x2DCE9187, 0x32E8EA7E,
];

#[inline]
fn clamp(x: u32, a: u32, b: u32) -> u32 {
    x.clamp(a, b)
}

#[inline]
fn mask(bits: u32) -> u32 {
    (1u32 << clamp(bits, 1, 31)) - 1
}

#[inline]
fn normal_size(mi: u32, av: u32, len: u32) -> u32 {
    let off = (mi + (mi + 1) / 2).min(av);
    let sz = av - off;
    sz.min(len)
}

#[inline]
pub fn fnv1a_64(data: &[u8]) -> u64 {
    let mut hash = FNV_OFFSET_BASIS;
    for &byte in data {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

#[inline]
fn cut_fastcdc(src: &[u8], mi: usize, ma: usize, ns: usize, mask_s: u32, mask_l: u32) -> usize {
    let len = src.len();
    let mut fp: u32 = 0;
    let mut i = len.min(mi);

    let n1 = ns.min(len);
    while i < n1 {
        fp = (fp >> 1).wrapping_add(GEAR[src[i] as usize]);
        if (fp & mask_s) == 0 {
            return i + 1;
        }
        i += 1;
    }

    let n2 = ma.min(len);
    while i < n2 {
        fp = (fp >> 1).wrapping_add(GEAR[src[i] as usize]);
        if (fp & mask_l) == 0 {
            return i + 1;
        }
        i += 1;
    }

    i
}

/// Returns true if `byte` is the start of a new UTF-8 codepoint (ASCII or leading multi-byte).
/// In UTF-8, continuation bytes always match the bit pattern `10xxxxxx` (`0x80..=0xBF`).
#[inline]
fn is_utf8_char_boundary(byte: u8) -> bool {
    (byte & 0b1100_0000) != 0b1000_0000
}

/// Snaps a raw FastCDC cut index to the nearest natural language boundary:
/// 1. Newline (`\n`) or sentence punctuation (`.`, `!`, `?` followed by whitespace)
/// 2. Word whitespace (`' '`, `'\t'`)
/// 3. Valid UTF-8 codepoint boundary (never splits multi-byte characters)
#[inline]
fn snap_to_semantic_boundary(src: &[u8], raw_cut: usize, min_chunk: usize, max_chunk: usize) -> usize {
    let len = src.len();
    if raw_cut >= len {
        return len;
    }

    let limit = max_chunk.min(len);
    // Lookahead window of up to 64 bytes (bounded by max_chunk and buffer length)
    let lookahead_end = (raw_cut + 64).min(limit);

    // 1. Priority: Look ahead for newline or sentence end (. ! ?)
    for idx in raw_cut..lookahead_end {
        let b = src[idx];
        if b == b'\n' {
            return idx + 1;
        }
        if (b == b'.' || b == b'!' || b == b'?') && idx + 1 < limit && src[idx + 1].is_ascii_whitespace() {
            return idx + 2;
        }
    }

    // 2. Priority: Look ahead for standard whitespace
    for idx in raw_cut..lookahead_end {
        if src[idx].is_ascii_whitespace() {
            return idx + 1;
        }
    }

    // 3. Fallback: Look behind (down to min_chunk) for whitespace so we never split a word
    let lookbehind_start = min_chunk.min(raw_cut);
    for idx in (lookbehind_start..raw_cut).rev() {
        if src[idx].is_ascii_whitespace() {
            return idx + 1;
        }
    }

    // 4. Final guarantee: Ensure we do not split a multi-byte UTF-8 sequence
    let mut utf8_safe = raw_cut;
    while utf8_safe < limit && !is_utf8_char_boundary(src[utf8_safe]) {
        utf8_safe += 1;
    }
    if utf8_safe < limit && is_utf8_char_boundary(src[utf8_safe]) {
        return utf8_safe;
    }
    while utf8_safe > lookbehind_start && !is_utf8_char_boundary(src[utf8_safe]) {
        utf8_safe -= 1;
    }
    utf8_safe.max(1)
}

/// Executes raw FastCDC over a contiguous byte slice with 100% C ABI parity (`c_legacy/fastcdc.c`).
pub fn chunk_slice(
    data: &[u8],
    min_chunk: usize,
    max_chunk: usize,
    _mask: u32,
) -> Result<Vec<Chunk>, ChunkerError> {
    if min_chunk == 0 {
        return Err(ChunkerError::ZeroMinChunk);
    }
    if max_chunk < min_chunk {
        return Err(ChunkerError::InvalidChunkSize {
            min: min_chunk,
            max: max_chunk,
        });
    }
    if data.is_empty() {
        return Ok(Vec::new());
    }

    let raw_mi = min_chunk as u32;
    let raw_ma = max_chunk as u32;
    let raw_avg = ((min_chunk + max_chunk) / 2).max(AVERAGE_MIN as usize) as u32;

    // Clamping identical to fastcdc_init in c_legacy/fastcdc.c
    let mi = clamp(raw_mi, MINIMUM_MIN, MINIMUM_MAX) as usize;
    let av = clamp(raw_avg, AVERAGE_MIN, AVERAGE_MAX);
    let ma = clamp(raw_ma, MAXIMUM_MIN, MAXIMUM_MAX) as usize;

    let bits = (av as f64).log2().round() as u32;
    let ns = normal_size(raw_mi, raw_avg, raw_ma) as usize;
    let mask_s = mask(bits + 1);
    let mask_l = mask(bits.saturating_sub(1));

    let mut chunks = Vec::new();
    let mut offset = 0;

    while offset < data.len() {
        let remaining = &data[offset..];
        let chunk_len = cut_fastcdc(remaining, mi, ma, ns, mask_s, mask_l);
        let actual_len = chunk_len.max(1);

        chunks.push(Chunk {
            offset,
            length: actual_len,
            hash: 0,
        });

        offset += actual_len;
    }

    Ok(chunks)
}

/// Executes NLP/RAG-optimized FastCDC with Semantic Boundary Snapping and 64-bit FNV-1a hashing.
///
/// Guarantees:
/// - Never splits multi-byte UTF-8 codepoints.
/// - Snaps chunk boundaries to sentence endings (`.`, `\n`) or word whitespace whenever possible.
/// - Populates `Chunk.hash` with a deterministic 64-bit FNV-1a fingerprint for embedding cache lookup.
pub fn chunk_slice_semantic(
    data: &[u8],
    min_chunk: usize,
    max_chunk: usize,
) -> Result<Vec<Chunk>, ChunkerError> {
    if min_chunk == 0 {
        return Err(ChunkerError::ZeroMinChunk);
    }
    if max_chunk < min_chunk {
        return Err(ChunkerError::InvalidChunkSize {
            min: min_chunk,
            max: max_chunk,
        });
    }
    if data.is_empty() {
        return Ok(Vec::new());
    }

    let avg = ((min_chunk + max_chunk) / 2).max(64) as u32;
    let mi = min_chunk as u32;
    let ma = max_chunk as u32;
    let bits = (avg as f64).log2().round().max(2.0) as u32;
    let ns = normal_size(mi, avg, ma) as usize;
    let mask_s = mask(bits + 1);
    let mask_l = mask(bits.saturating_sub(1));

    let mut chunks = Vec::new();
    let mut offset = 0;

    while offset < data.len() {
        let remaining = &data[offset..];
        let raw_len = cut_fastcdc(remaining, min_chunk, max_chunk, ns, mask_s, mask_l);
        let snapped_len = snap_to_semantic_boundary(remaining, raw_len, min_chunk, max_chunk);
        let actual_len = snapped_len.max(1);
        let chunk_bytes = &remaining[..actual_len];

        chunks.push(Chunk {
            offset,
            length: actual_len,
            hash: fnv1a_64(chunk_bytes),
        });

        offset += actual_len;
    }

    Ok(chunks)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fastcdc_empty() {
        assert_eq!(chunk_slice(&[], 64, 512, 0), Ok(Vec::new()));
        assert_eq!(chunk_slice_semantic(&[], 64, 512), Ok(Vec::new()));
    }

    #[test]
    fn test_invalid_chunk_params() {
        assert_eq!(chunk_slice(b"abc", 0, 10, 0), Err(ChunkerError::ZeroMinChunk));
        assert_eq!(
            chunk_slice_semantic(b"abc", 100, 50),
            Err(ChunkerError::InvalidChunkSize { min: 100, max: 50 })
        );
    }

    #[test]
    fn test_fastcdc_chunking_bounds() {
        let sample = vec![42u8; 10000];
        let chunks = chunk_slice(&sample, 64, 1024, 0).unwrap();
        assert!(!chunks.is_empty());
        let total: usize = chunks.iter().map(|c| c.length).sum();
        assert_eq!(total, sample.len());

        for c in &chunks {
            assert!(c.length >= 64 || c.offset + c.length == sample.len());
            assert!(c.length <= 1024);
        }
    }

    #[test]
    fn test_semantic_snapping_utf8_and_words() {
        let text = "Arquitetura de Sistemas e Inteligência Artificial: pré-processamento semântico \
                    com FastCDC em Rust. Garante que palavras acentuadas como coração, ação, \
                    computação e eficiência nunca sejam cortadas ao meio durante a indexação RAG. "
            .repeat(20);
        let bytes = text.as_bytes();

        let chunks = chunk_slice_semantic(bytes, 64, 256).unwrap();
        assert!(chunks.len() > 5);

        let mut covered = 0;
        for c in &chunks {
            assert_eq!(c.offset, covered);
            let slice = &bytes[c.offset..c.offset + c.length];
            // Proof 1: Every single chunk must be valid UTF-8 (never cuts inside multi-byte chars)
            let decoded = std::str::from_utf8(slice)
                .expect("Semantic chunker must never split a multi-byte UTF-8 character");
            // Proof 2: Non-final chunks must end on whitespace or newline
            if c.offset + c.length < bytes.len() {
                assert!(
                    decoded.ends_with(char::is_whitespace),
                    "Chunk did not end on a semantic boundary: {:?}",
                    decoded
                );
            }
            // Proof 3: Content hash is populated
            assert_ne!(c.hash, 0);
            covered += c.length;
        }
        assert_eq!(covered, bytes.len());
    }

    #[test]
    fn test_shift_resilience_deduplication() {
        let mut base_doc = String::new();
        for i in 0..50 {
            base_doc.push_str(&format!(
                "Section {i}: Content-defined chunking synchronizes boundaries across document edits.\n"
            ));
        }

        let mut edited_doc = String::from("NEW PARAGRAPH INSERTED AT PAGE 1 TOP OF DOCUMENT.\n");
        edited_doc.push_str(&base_doc);

        let base_chunks = chunk_slice_semantic(base_doc.as_bytes(), 64, 256).unwrap();
        let edited_chunks = chunk_slice_semantic(edited_doc.as_bytes(), 64, 256).unwrap();

        let base_hashes: std::collections::HashSet<u64> =
            base_chunks.iter().map(|c| c.hash).collect();
        let matching_chunks = edited_chunks
            .iter()
            .filter(|c| base_hashes.contains(&c.hash))
            .count();

        // At least 85% of chunks must be preserved identically despite inserting text at offset 0
        let hit_ratio = (matching_chunks as f64) / (base_chunks.len() as f64);
        assert!(
            hit_ratio >= 0.85,
            "Expected high deduplication cache hit ratio, got {:.2}%",
            hit_ratio * 100.0
        );
    }
}
