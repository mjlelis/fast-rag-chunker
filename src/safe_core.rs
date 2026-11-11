#![forbid(unsafe_code)]

#[cfg(not(miri))]
use rayon::prelude::*;
use thiserror::Error;

/// Canonical algorithm and boundary-rule version identifier included in cache fingerprints.
pub const ALGORITHM_VERSION: &str = "fast-rag-chunker/v0.2.0";

const MINIMUM_MIN: u32 = 64;
const MINIMUM_MAX: u32 = 67_108_864;
const AVERAGE_MIN: u32 = 256;
const AVERAGE_MAX: u32 = 268_435_456;
const MAXIMUM_MIN: u32 = 1024;
const MAXIMUM_MAX: u32 = 1_073_741_824;

/// Maximum permitted `max_chunk` size (1 GiB), preventing `u32` truncation and arithmetic overflow.
pub const MAX_CHUNK_SIZE_LIMIT: usize = MAXIMUM_MAX as usize;

/// Represents a content-defined chunk with a 128-bit (16-byte) content digest.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Chunk {
    pub offset: usize,
    pub length: usize,
    pub digest: [u8; 16],
}

impl Chunk {
    /// Returns the 128-bit digest encoded as a 32-character lowercase hexadecimal string.
    #[inline]
    pub fn hex(&self) -> String {
        encode_hex_16(&self.digest)
    }
}

/// Operating mode for the FastCDC engine.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChunkingMode {
    /// Unclamped raw byte-level FastCDC respecting caller `min_chunk`, `avg_chunk`, and `max_chunk`.
    Raw,
    /// FastCDC with UTF-8 and natural-language boundary snapping.
    Semantic,
    /// Legacy C compatibility mode applying `c_legacy/fastcdc.c` parameter clamps.
    CompatC,
}

impl ChunkingMode {
    /// Returns the canonical lowercase identifier for this mode.
    #[inline]
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Raw => "raw",
            Self::Semantic => "semantic",
            Self::CompatC => "compat_c",
        }
    }

    /// Parses a mode string (`"raw"`, `"semantic"`, or `"compat_c"`).
    pub fn parse(mode: &str) -> Result<Self, ChunkerError> {
        match mode.trim().to_ascii_lowercase().as_str() {
            "raw" => Ok(Self::Raw),
            "semantic" => Ok(Self::Semantic),
            "compat_c" | "compat" => Ok(Self::CompatC),
            other => Err(ChunkerError::InvalidMode {
                mode: other.to_string(),
            }),
        }
    }
}

/// Complete configuration contract for content-defined chunking.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ChunkerConfig {
    pub min_chunk: usize,
    pub avg_chunk: usize,
    pub max_chunk: usize,
    pub mode: ChunkingMode,
    pub compute_hash: bool,
}

impl ChunkerConfig {
    /// Validates and constructs a `ChunkerConfig`.
    /// When `avg_chunk` is `None`, defaults to the overflow-safe midpoint `min + (max - min) / 2`.
    pub fn new(
        min_chunk: usize,
        avg_chunk: Option<usize>,
        max_chunk: usize,
        mode: ChunkingMode,
        compute_hash: bool,
    ) -> Result<Self, ChunkerError> {
        let (_, default_avg, _) = validate_chunk_params(min_chunk, max_chunk)?;
        let avg = match avg_chunk {
            Some(user_avg) => {
                if user_avg < min_chunk || user_avg > max_chunk {
                    return Err(ChunkerError::InvalidAverageChunkSize {
                        min: min_chunk,
                        avg: user_avg,
                        max: max_chunk,
                    });
                }
                user_avg
            }
            None => default_avg as usize,
        };
        Ok(Self {
            min_chunk,
            avg_chunk: avg,
            max_chunk,
            mode,
            compute_hash,
        })
    }
}

#[derive(Error, Debug, PartialEq, Eq)]
pub enum ChunkerError {
    #[error("Minimum chunk size must be greater than 0")]
    InvalidMinChunkSize,
    #[error("Minimum chunk size ({min}) cannot be greater than maximum chunk size ({max})")]
    MinGreaterThanMax { min: usize, max: usize },
    #[error("Average chunk size ({avg}) must be between min_chunk ({min}) and max_chunk ({max})")]
    InvalidAverageChunkSize { min: usize, avg: usize, max: usize },
    #[error("Chunk size ({size}) exceeds maximum supported limit ({max_allowed} bytes)")]
    ChunkSizeTooLarge { size: usize, max_allowed: usize },
    #[error("Unsupported chunking mode '{mode}': expected 'semantic', 'raw', or 'compat_c'")]
    InvalidMode { mode: String },
    #[error("Cannot generate a cache key when compute_hash is disabled (digest is empty)")]
    HashDisabledForCacheKey,
    #[error("Embedding model_id must not be empty when generating a cache key")]
    EmptyModelId,
    #[error("Invalid thread count ({count}): num_threads must be >= 1")]
    InvalidThreadCount { count: usize },
}

/// 256-entry pseudo-random 32-bit Gear lookup table matching `c_legacy/fastcdc.c`
/// (derived from the sleepybishop/fastcdc C reference implementation, Copyright (c) 2020 Joseph Calderon, MIT License).
#[rustfmt::skip]
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

/// Validates `min_chunk` and `max_chunk` without risking integer overflow or `u32` truncation.
/// Returns `(min_u32, avg_u32, max_u32)` where `avg_u32 = min + (max - min) / 2`.
#[inline]
pub fn validate_chunk_params(
    min_chunk: usize,
    max_chunk: usize,
) -> Result<(u32, u32, u32), ChunkerError> {
    if min_chunk == 0 {
        return Err(ChunkerError::InvalidMinChunkSize);
    }
    if min_chunk > max_chunk {
        return Err(ChunkerError::MinGreaterThanMax {
            min: min_chunk,
            max: max_chunk,
        });
    }
    if max_chunk > MAX_CHUNK_SIZE_LIMIT {
        return Err(ChunkerError::ChunkSizeTooLarge {
            size: max_chunk,
            max_allowed: MAX_CHUNK_SIZE_LIMIT,
        });
    }

    let avg_chunk = min_chunk + (max_chunk - min_chunk) / 2;
    Ok((min_chunk as u32, avg_chunk as u32, max_chunk as u32))
}

#[inline]
fn encode_hex_16(bytes: &[u8; 16]) -> String {
    const HEX_CHARS: &[u8; 16] = b"0123456789abcdef";
    let mut out = Vec::with_capacity(32);
    for &b in bytes {
        out.push(HEX_CHARS[(b >> 4) as usize]);
        out.push(HEX_CHARS[(b & 0x0f) as usize]);
    }
    String::from_utf8(out).unwrap_or_default()
}

/// Computes a 128-bit (16-byte) truncated BLAKE3 digest of `data`.
///
/// BLAKE3 provides cryptographic collision resistance for multi-tenant embedding caches
/// while leveraging SIMD instruction sets for multi-GB/s throughput.
#[inline]
pub fn blake3_128(data: &[u8]) -> [u8; 16] {
    let hash = blake3::hash(data);
    let mut out = [0u8; 16];
    out.copy_from_slice(&hash.as_bytes()[..16]);
    out
}

/// Summarizes the algorithm version and `ChunkerConfig` parameters into a deterministic
/// fingerprint string suitable for namespacing embedding caches.
pub fn chunker_fingerprint(config: &ChunkerConfig) -> String {
    let canonical = format!(
        "{}|mode={}|min={}|avg={}|max={}",
        ALGORITHM_VERSION,
        config.mode.as_str(),
        config.min_chunk,
        config.avg_chunk,
        config.max_chunk
    );
    let digest = blake3_128(canonical.as_bytes());
    format!(
        "frc:v0.2.0:{}:{}:{}:{}:{}",
        config.mode.as_str(),
        config.min_chunk,
        config.avg_chunk,
        config.max_chunk,
        &encode_hex_16(&digest)[..16]
    )
}

/// Computes a complete, collision-resistant cache key combining the chunk's 128-bit digest,
/// the embedding `model_id`, and the `ChunkerConfig` fingerprint.
///
/// Changing `model_id` or any boundary-affecting parameter in `config` produces a distinct key.
pub fn cache_key(
    chunk: &Chunk,
    model_id: &str,
    config: &ChunkerConfig,
) -> Result<String, ChunkerError> {
    if !config.compute_hash {
        return Err(ChunkerError::HashDisabledForCacheKey);
    }
    let model_trimmed = model_id.trim();
    if model_trimmed.is_empty() {
        return Err(ChunkerError::EmptyModelId);
    }
    let fp = chunker_fingerprint(config);
    let mut hasher = blake3::Hasher::new();
    hasher.update(ALGORITHM_VERSION.as_bytes());
    hasher.update(b"|model=");
    hasher.update(model_trimmed.as_bytes());
    hasher.update(b"|fp=");
    hasher.update(fp.as_bytes());
    hasher.update(b"|chunk=");
    hasher.update(&chunk.digest);
    let full = hasher.finalize();
    let mut key_bytes = [0u8; 16];
    key_bytes.copy_from_slice(&full.as_bytes()[..16]);
    Ok(format!("frc:v0.2.0:{}", encode_hex_16(&key_bytes)))
}

#[inline]
fn clamp(x: u32, a: u32, b: u32) -> u32 {
    if x < a {
        a
    } else if x > b {
        b
    } else {
        x
    }
}

#[inline]
fn div_ceil(a: u32, b: u32) -> u32 {
    a / b + if a % b != 0 { 1 } else { 0 }
}

#[inline]
fn normal_size(mi: u32, av: u32, len: u32) -> u32 {
    let mut off = mi + div_ceil(mi, 2);
    if off > av {
        off = av;
    }
    let sz = av - off;
    if sz > len {
        len
    } else {
        sz
    }
}

#[inline]
fn mask(bits: u32) -> u32 {
    let clamped = clamp(bits, 1, 31);
    (1u32 << clamped) - 1
}

/// Core FastCDC Gear-hash cut function.
#[inline]
fn cut_fastcdc(src: &[u8], mi: usize, ma: usize, ns: usize, mask_s: u32, mask_l: u32) -> usize {
    let len = src.len();
    if len <= mi {
        return len;
    }

    let mut i = mi;
    let n1 = ns.min(len);
    let mut fp: u32 = 0;

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

/// Returns `true` if `byte` is the start of a UTF-8 codepoint (ASCII or multi-byte leading byte).
/// In UTF-8, continuation bytes always have the bit pattern `10xxxxxx` (`0x80..=0xBF`).
#[inline]
fn is_utf8_char_boundary(byte: u8) -> bool {
    (byte & 0b1100_0000) != 0b1000_0000
}

/// Snaps a raw FastCDC cut index to the nearest natural language boundary:
/// 1. Newline (`\n`) or sentence punctuation (`.`, `!`, `?` followed by whitespace)
/// 2. Word whitespace (`' '`, `'\t'`)
/// 3. Valid UTF-8 codepoint boundary (never splits multi-byte characters)
#[inline]
fn snap_to_semantic_boundary(
    src: &[u8],
    raw_cut: usize,
    min_chunk: usize,
    max_chunk: usize,
) -> usize {
    let len = src.len();
    if raw_cut >= len {
        return len;
    }

    let limit = max_chunk.min(len);
    let lookahead_end = (raw_cut + 64).min(limit);

    // Single-pass lookahead for Tier 1 (sentence/newline) and Tier 2 (first whitespace)
    let mut first_whitespace: Option<usize> = None;
    for (offset, &b) in src[raw_cut..lookahead_end].iter().enumerate() {
        let idx = raw_cut + offset;
        if b == b'\n' {
            return idx + 1;
        }
        if (b == b'.' || b == b'!' || b == b'?')
            && idx + 1 < limit
            && src[idx + 1].is_ascii_whitespace()
        {
            return idx + 2;
        }
        if first_whitespace.is_none() && b.is_ascii_whitespace() {
            first_whitespace = Some(idx + 1);
        }
    }

    if let Some(ws_cut) = first_whitespace {
        return ws_cut;
    }

    // 3. Fallback: Look behind (down to min_chunk) for whitespace so we never split a word
    let lookbehind_start = min_chunk.min(raw_cut);
    if let Some(offset) = src[lookbehind_start..raw_cut]
        .iter()
        .rposition(u8::is_ascii_whitespace)
    {
        return lookbehind_start + offset + 1;
    }

    // 4. Final guarantee: Ensure we do not split a multi-byte UTF-8 sequence
    let mut utf8_safe = raw_cut.min(limit);
    while utf8_safe < limit && !is_utf8_char_boundary(src[utf8_safe]) {
        utf8_safe += 1;
    }
    if utf8_safe < limit && is_utf8_char_boundary(src[utf8_safe]) {
        return utf8_safe;
    }
    let mut utf8_back = raw_cut.min(limit.saturating_sub(1));
    while utf8_back > lookbehind_start && !is_utf8_char_boundary(src[utf8_back]) {
        utf8_back -= 1;
    }
    utf8_back.max(lookbehind_start).max(1)
}

/// Executes content-defined chunking according to a validated `ChunkerConfig`.
pub fn chunk_with_config(data: &[u8], config: &ChunkerConfig) -> Result<Vec<Chunk>, ChunkerError> {
    let validated = ChunkerConfig::new(
        config.min_chunk,
        Some(config.avg_chunk),
        config.max_chunk,
        config.mode,
        config.compute_hash,
    )?;
    if data.is_empty() {
        return Ok(Vec::new());
    }

    let raw_mi = validated.min_chunk as u32;
    let raw_av = validated.avg_chunk as u32;
    let raw_ma = validated.max_chunk as u32;

    match validated.mode {
        ChunkingMode::CompatC => {
            let clamped_avg = raw_av.max(AVERAGE_MIN);
            let mi = clamp(raw_mi, MINIMUM_MIN, MINIMUM_MAX) as usize;
            let av = clamp(clamped_avg, AVERAGE_MIN, AVERAGE_MAX);
            let ma = clamp(raw_ma, MAXIMUM_MIN, MAXIMUM_MAX) as usize;

            let bits = f64::from(av).log2().round() as u32;
            let ns = normal_size(raw_mi, clamped_avg, raw_ma) as usize;
            let mask_s = mask(bits + 1);
            let mask_l = mask(bits.saturating_sub(1));

            let mut chunks = Vec::new();
            let mut offset = 0;

            while offset < data.len() {
                let remaining = &data[offset..];
                let chunk_len = cut_fastcdc(remaining, mi, ma, ns, mask_s, mask_l);
                let actual_len = chunk_len.max(1);
                let digest = if validated.compute_hash {
                    blake3_128(&remaining[..actual_len])
                } else {
                    [0u8; 16]
                };

                chunks.push(Chunk {
                    offset,
                    length: actual_len,
                    digest,
                });

                offset += actual_len;
            }

            Ok(chunks)
        }
        ChunkingMode::Raw => {
            let bits = f64::from(raw_av.max(4)).log2().round().max(2.0) as u32;
            let ns = normal_size(raw_mi, raw_av, raw_ma) as usize;
            let mask_s = mask(bits + 1);
            let mask_l = mask(bits.saturating_sub(1));

            let mut chunks = Vec::new();
            let mut offset = 0;

            while offset < data.len() {
                let remaining = &data[offset..];
                let chunk_len = cut_fastcdc(
                    remaining,
                    validated.min_chunk,
                    validated.max_chunk,
                    ns,
                    mask_s,
                    mask_l,
                );
                let actual_len = chunk_len.max(1);
                let digest = if validated.compute_hash {
                    blake3_128(&remaining[..actual_len])
                } else {
                    [0u8; 16]
                };

                chunks.push(Chunk {
                    offset,
                    length: actual_len,
                    digest,
                });

                offset += actual_len;
            }

            Ok(chunks)
        }
        ChunkingMode::Semantic => {
            let avg = raw_av.max(64.min(raw_ma));
            let bits = f64::from(avg.max(4)).log2().round().max(2.0) as u32;
            let ns = normal_size(raw_mi, avg, raw_ma) as usize;
            let mask_s = mask(bits + 1);
            let mask_l = mask(bits.saturating_sub(1));

            let mut chunks = Vec::new();
            let mut offset = 0;

            while offset < data.len() {
                let remaining = &data[offset..];
                let raw_len = cut_fastcdc(
                    remaining,
                    validated.min_chunk,
                    validated.max_chunk,
                    ns,
                    mask_s,
                    mask_l,
                );
                let snapped_len = snap_to_semantic_boundary(
                    remaining,
                    raw_len,
                    validated.min_chunk,
                    validated.max_chunk,
                );
                let actual_len = snapped_len.max(1);
                let digest = if validated.compute_hash {
                    blake3_128(&remaining[..actual_len])
                } else {
                    [0u8; 16]
                };

                chunks.push(Chunk {
                    offset,
                    length: actual_len,
                    digest,
                });

                offset += actual_len;
            }

            Ok(chunks)
        }
    }
}

/// Processes a batch of documents using the specified `ChunkerConfig` and optional thread count.
///
/// - `num_threads = None`: Uses Rayon's global thread pool.
/// - `num_threads = Some(1)`: Executes sequentially on the calling thread without pool overhead.
/// - `num_threads = Some(n)` (`n > 1`): Executes on a scoped Rayon pool with `n` worker threads.
/// - `num_threads = Some(0)`: Returns `Err(ChunkerError::InvalidThreadCount { count: 0 })`.
pub fn chunk_batch_with_config(
    documents: &[&[u8]],
    config: &ChunkerConfig,
    num_threads: Option<usize>,
) -> Result<Vec<Vec<Chunk>>, ChunkerError> {
    let validated = ChunkerConfig::new(
        config.min_chunk,
        Some(config.avg_chunk),
        config.max_chunk,
        config.mode,
        config.compute_hash,
    )?;

    #[cfg(miri)]
    {
        if num_threads == Some(0) {
            return Err(ChunkerError::InvalidThreadCount { count: 0 });
        }
        return documents
            .iter()
            .map(|slice| chunk_with_config(slice, &validated))
            .collect();
    }

    #[cfg(not(miri))]
    match num_threads {
        Some(0) => Err(ChunkerError::InvalidThreadCount { count: 0 }),
        Some(1) => documents
            .iter()
            .map(|slice| chunk_with_config(slice, &validated))
            .collect(),
        Some(n) => {
            let pool = rayon::ThreadPoolBuilder::new()
                .num_threads(n)
                .build()
                .map_err(|_| ChunkerError::InvalidThreadCount { count: n })?;
            pool.install(|| {
                documents
                    .par_iter()
                    .map(|slice| chunk_with_config(slice, &validated))
                    .collect()
            })
        }
        None => documents
            .par_iter()
            .map(|slice| chunk_with_config(slice, &validated))
            .collect(),
    }
}

/// Executes raw FastCDC with C-legacy parameter clamping (`min >= 64`, `avg >= 256`, `max >= 1024`)
/// to maintain 100% binary compatibility with `c_legacy/fastcdc.c` across the v1 FFI boundary.
pub fn chunk_slice_compat(
    data: &[u8],
    min_chunk: usize,
    max_chunk: usize,
) -> Result<Vec<Chunk>, ChunkerError> {
    let config = ChunkerConfig::new(min_chunk, None, max_chunk, ChunkingMode::CompatC, false)?;
    chunk_with_config(data, &config)
}

/// Executes raw FastCDC strictly respecting caller-supplied `min_chunk` and `max_chunk` bounds
/// and computing 128-bit BLAKE3 chunk digests.
pub fn chunk_slice(
    data: &[u8],
    min_chunk: usize,
    max_chunk: usize,
) -> Result<Vec<Chunk>, ChunkerError> {
    let config = ChunkerConfig::new(min_chunk, None, max_chunk, ChunkingMode::Raw, true)?;
    chunk_with_config(data, &config)
}

/// Executes NLP/RAG-optimized FastCDC with Semantic Boundary Snapping and 128-bit BLAKE3 hashing.
pub fn chunk_slice_semantic(
    data: &[u8],
    min_chunk: usize,
    max_chunk: usize,
) -> Result<Vec<Chunk>, ChunkerError> {
    let config = ChunkerConfig::new(min_chunk, None, max_chunk, ChunkingMode::Semantic, true)?;
    chunk_with_config(data, &config)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn test_fastcdc_empty() {
        assert_eq!(chunk_slice(&[], 64, 512), Ok(Vec::new()));
        assert_eq!(chunk_slice_compat(&[], 64, 512), Ok(Vec::new()));
        assert_eq!(chunk_slice_semantic(&[], 64, 512), Ok(Vec::new()));
    }

    #[test]
    fn test_invalid_chunk_params() {
        assert_eq!(
            chunk_slice(b"test", 0, 512),
            Err(ChunkerError::InvalidMinChunkSize)
        );
        assert_eq!(
            chunk_slice(b"test", 1024, 512),
            Err(ChunkerError::MinGreaterThanMax {
                min: 1024,
                max: 512
            })
        );
        assert_eq!(
            chunk_slice_semantic(b"test", 0, 512),
            Err(ChunkerError::InvalidMinChunkSize)
        );
        assert_eq!(
            ChunkerConfig::new(64, Some(32), 512, ChunkingMode::Semantic, true),
            Err(ChunkerError::InvalidAverageChunkSize {
                min: 64,
                avg: 32,
                max: 512,
            })
        );
    }

    #[test]
    fn test_arithmetic_overflow_usize_max() {
        assert_eq!(
            chunk_slice(b"overflow test", usize::MAX, usize::MAX),
            Err(ChunkerError::ChunkSizeTooLarge {
                size: usize::MAX,
                max_allowed: MAX_CHUNK_SIZE_LIMIT,
            })
        );
        assert_eq!(
            chunk_slice_semantic(b"overflow test", usize::MAX / 2, usize::MAX),
            Err(ChunkerError::ChunkSizeTooLarge {
                size: usize::MAX,
                max_allowed: MAX_CHUNK_SIZE_LIMIT,
            })
        );
        assert_eq!(
            chunk_slice_compat(b"overflow test", 64, MAX_CHUNK_SIZE_LIMIT + 1),
            Err(ChunkerError::ChunkSizeTooLarge {
                size: MAX_CHUNK_SIZE_LIMIT + 1,
                max_allowed: MAX_CHUNK_SIZE_LIMIT,
            })
        );
    }

    #[test]
    fn test_blake3_digest_and_compute_hash_toggle() {
        let data = b"Deterministic 128-bit BLAKE3 content digest verification across modes.";
        let cfg_on = ChunkerConfig::new(16, None, 64, ChunkingMode::Raw, true).unwrap();
        let cfg_off = ChunkerConfig::new(16, None, 64, ChunkingMode::Raw, false).unwrap();

        let chunks_on = chunk_with_config(data, &cfg_on).unwrap();
        let chunks_off = chunk_with_config(data, &cfg_off).unwrap();
        assert_eq!(chunks_on.len(), chunks_off.len());

        for (c_on, c_off) in chunks_on.iter().zip(chunks_off.iter()) {
            assert_eq!(c_on.offset, c_off.offset);
            assert_eq!(c_on.length, c_off.length);
            assert_ne!(c_on.digest, [0u8; 16]);
            assert_eq!(c_on.hex().len(), 32);
            assert_eq!(c_off.digest, [0u8; 16]);
        }
    }

    #[test]
    fn test_fingerprint_and_cache_key_isolation() {
        let data = b"Sample paragraph for testing cache key isolation across models and configs.";
        let cfg_a = ChunkerConfig::new(32, Some(64), 128, ChunkingMode::Semantic, true).unwrap();
        let cfg_b = ChunkerConfig::new(32, Some(96), 128, ChunkingMode::Semantic, true).unwrap();
        let cfg_raw = ChunkerConfig::new(32, Some(64), 128, ChunkingMode::Raw, true).unwrap();
        let cfg_no_hash =
            ChunkerConfig::new(32, Some(64), 128, ChunkingMode::Semantic, false).unwrap();

        assert_ne!(chunker_fingerprint(&cfg_a), chunker_fingerprint(&cfg_b));
        assert_ne!(chunker_fingerprint(&cfg_a), chunker_fingerprint(&cfg_raw));

        let chunk = chunk_with_config(data, &cfg_a).unwrap()[0];
        let key_model_1 = cache_key(&chunk, "text-embedding-3-small", &cfg_a).unwrap();
        let key_model_2 = cache_key(&chunk, "text-embedding-3-large", &cfg_a).unwrap();
        let key_cfg_b = cache_key(&chunk, "text-embedding-3-small", &cfg_b).unwrap();

        assert_ne!(key_model_1, key_model_2);
        assert_ne!(key_model_1, key_cfg_b);
        assert_eq!(
            cache_key(&chunk, "text-embedding-3-small", &cfg_no_hash),
            Err(ChunkerError::HashDisabledForCacheKey)
        );
        assert_eq!(
            cache_key(&chunk, "   ", &cfg_a),
            Err(ChunkerError::EmptyModelId)
        );
    }

    #[test]
    fn test_num_threads_determinism() {
        let doc1 =
            b"Document one with natural sentences for parallel determinism check. ".repeat(8);
        let doc2 =
            b"Document two with UTF-8 accents: acao, coracao, semantica, ciencia. ".repeat(8);
        let docs: Vec<&[u8]> = vec![doc1.as_slice(), doc2.as_slice()];
        let cfg = ChunkerConfig::new(64, None, 256, ChunkingMode::Semantic, true).unwrap();

        let res_1 = chunk_batch_with_config(&docs, &cfg, Some(1)).unwrap();
        let res_2 = chunk_batch_with_config(&docs, &cfg, Some(2)).unwrap();
        let res_default = chunk_batch_with_config(&docs, &cfg, None).unwrap();

        assert_eq!(res_1, res_2);
        assert_eq!(res_1, res_default);
        assert_eq!(
            chunk_batch_with_config(&docs, &cfg, Some(0)),
            Err(ChunkerError::InvalidThreadCount { count: 0 })
        );
    }

    #[test]
    fn test_property_chunk_bounds_raw_and_semantic() {
        #[cfg(miri)]
        let raw_len = 512usize;
        #[cfg(not(miri))]
        let raw_len = 4096usize;

        let mut pseudo_random = Vec::with_capacity(raw_len);
        for i in 0..raw_len as u32 {
            pseudo_random.push(((i.wrapping_mul(1664525).wrapping_add(1013904223)) >> 16) as u8);
        }

        #[cfg(miri)]
        let repeat_factor = 6usize;
        #[cfg(not(miri))]
        let repeat_factor = 30usize;

        let prose = "Deterministic content-defined chunking with UTF-8 boundary snapping \
                     preserves natural sentences across document edits.\n"
            .repeat(repeat_factor);
        let utf8_heavy =
            "Ação, coração, pré-processamento semântico e eficiência em IA! ".repeat(repeat_factor);
        let uniform = vec![0x80u8; raw_len / 2];

        let corpora: [&[u8]; 5] = [
            b"short",
            &pseudo_random,
            prose.as_bytes(),
            utf8_heavy.as_bytes(),
            &uniform,
        ];
        let param_pairs: [(usize, usize); 5] =
            [(8, 32), (64, 256), (64, 512), (128, 512), (256, 256)];

        for data in corpora {
            for (min_c, max_c) in param_pairs {
                let raw_cfg =
                    ChunkerConfig::new(min_c, None, max_c, ChunkingMode::Raw, false).unwrap();
                let raw_chunks = chunk_with_config(data, &raw_cfg).unwrap();
                let mut offset = 0;
                for (idx, c) in raw_chunks.iter().enumerate() {
                    assert_eq!(c.offset, offset);
                    assert!(
                        c.length <= max_c,
                        "Raw chunk {idx} length {} exceeded max_chunk {max_c}",
                        c.length
                    );
                    if c.offset + c.length < data.len() {
                        assert!(
                            c.length >= min_c,
                            "Non-final raw chunk {idx} length {} below min_chunk {min_c}",
                            c.length
                        );
                    }
                    offset += c.length;
                }
                assert_eq!(offset, data.len());

                let sem_cfg =
                    ChunkerConfig::new(min_c, None, max_c, ChunkingMode::Semantic, false).unwrap();
                let sem_chunks = chunk_with_config(data, &sem_cfg).unwrap();
                let mut sem_offset = 0;
                for (idx, c) in sem_chunks.iter().enumerate() {
                    assert_eq!(c.offset, sem_offset);
                    assert!(
                        c.length <= max_c,
                        "Semantic chunk {idx} length {} exceeded max_chunk {max_c}",
                        c.length
                    );
                    if c.offset + c.length < data.len() {
                        assert!(
                            c.length >= min_c,
                            "Non-final semantic chunk {idx} length {} below min_chunk {min_c}",
                            c.length
                        );
                    }
                    sem_offset += c.length;
                }
                assert_eq!(sem_offset, data.len());
            }
        }
    }

    #[test]
    fn test_semantic_snapping_utf8_and_words() {
        let text =
            "Arquitetura de Sistemas e Inteligência Artificial: pré-processamento semântico \
                    com FastCDC em Rust. Garante que palavras acentuadas como coração, ação, \
                    computação e eficiência nunca sejam cortadas ao meio durante a indexação RAG. "
                .repeat(10);
        let bytes = text.as_bytes();

        let chunks = chunk_slice_semantic(bytes, 64, 256).unwrap();
        assert!(chunks.len() > 5);

        let mut covered = 0;
        for c in &chunks {
            assert_eq!(c.offset, covered);
            let slice = &bytes[c.offset..c.offset + c.length];
            let decoded = std::str::from_utf8(slice)
                .expect("Semantic chunker must never split a multi-byte UTF-8 character");
            if c.offset + c.length < bytes.len() {
                assert!(
                    decoded.ends_with(char::is_whitespace),
                    "Chunk did not end on a semantic boundary: {decoded:?}"
                );
            }
            assert_ne!(c.digest, [0u8; 16]);
            covered += c.length;
        }
        assert_eq!(covered, bytes.len());
    }

    #[test]
    fn test_shift_resilience_deduplication() {
        let mut base_doc = String::with_capacity(500 * 90);
        for i in 0..500 {
            base_doc.push_str(&format!(
                "Section {i:04}: Content-defined chunking synchronizes boundaries across document edits.\n"
            ));
        }

        let mut edited_doc = String::from("NEW PARAGRAPH INSERTED AT PAGE 1 TOP OF DOCUMENT.\n");
        edited_doc.push_str(&base_doc);

        let base_chunks = chunk_slice_semantic(base_doc.as_bytes(), 64, 256).unwrap();
        let edited_chunks = chunk_slice_semantic(edited_doc.as_bytes(), 64, 256).unwrap();

        let base_hashes: HashSet<[u8; 16]> = base_chunks.iter().map(|c| c.digest).collect();
        let matching_chunks = edited_chunks
            .iter()
            .filter(|c| base_hashes.contains(&c.digest))
            .count();

        // With 500 lines (~270 chunks), at least 95% of chunks must be reused identically
        let hit_ratio = (matching_chunks as f64) / (base_chunks.len() as f64);
        assert!(
            hit_ratio >= 0.95,
            "Expected >= 95.00% deduplication cache hit ratio, got {:.2}% ({matching_chunks}/{})",
            hit_ratio * 100.0,
            base_chunks.len()
        );
    }

    #[test]
    fn test_resynchronization_distance_ceiling() {
        // Measured baseline resynchronization distance on this 500-line corpus is 3 chunks.
        // Ceiling is set to 4 chunks so any regression in boundary synchronization fails immediately.
        const RESYNC_DISTANCE_CEILING: usize = 4;

        let mut base_doc = String::with_capacity(500 * 90);
        for i in 0..500 {
            base_doc.push_str(&format!(
                "Section {i:04}: Content-defined chunking synchronizes boundaries across document edits.\n"
            ));
        }

        let mut edited_doc = String::from("NEW PARAGRAPH INSERTED AT PAGE 1 TOP OF DOCUMENT.\n");
        edited_doc.push_str(&base_doc);

        let base_chunks = chunk_slice_semantic(base_doc.as_bytes(), 64, 256).unwrap();
        let edited_chunks = chunk_slice_semantic(edited_doc.as_bytes(), 64, 256).unwrap();

        let base_hashes: HashSet<[u8; 16]> = base_chunks.iter().map(|c| c.digest).collect();
        let first_hit_index = edited_chunks
            .iter()
            .position(|c| base_hashes.contains(&c.digest))
            .expect("Edited document must resynchronize with base document chunks");

        assert!(
            first_hit_index <= RESYNC_DISTANCE_CEILING,
            "Resynchronization distance ({first_hit_index} chunks) exceeded ceiling ({RESYNC_DISTANCE_CEILING} chunks)"
        );
    }
}
