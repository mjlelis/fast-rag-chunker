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

/// 256-entry pseudo-random 64-bit Gear lookup table used by `c_legacy/fastcdc.c`
/// (derived from the FastCDC rolling hash design by Wen Xia et al., USENIX ATC '16).
#[rustfmt::skip]
const GEAR: [u64; 256] = [
    0x5c95c078d4653752, 0x22408982b81f3954, 0x8653c30f761c985e, 0x1393a84f30b8e57d,
    0x6a2887b863918e3b, 0x234c6b7b56a0e651, 0x3b8f7426466d7400, 0x064f6c80c9c6b66f,
    0x412131830797864a, 0x7c761588d7c6f60f, 0x0386f28a62091808, 0x1e601e0c4e8c4b0e,
    0x2f18a39b06e29c19, 0x3e6f631507c92a4c, 0x0c0b87664180f33b, 0x627a0780b491f00c,
    0x1d707f0f4919e779, 0x1e2068c8b3928222, 0x0a6c7b40a0e1a862, 0x454f500f2e1f1e36,
    0x168f41838982166c, 0x7f1e720a4b97c741, 0x2f60728b51a30b2e, 0x7d1a5e1e48902976,
    0x4f1e2e1a1b930262, 0x7e292b285c8c5e31, 0x3f2d6d0e1d801c2a, 0x5c0c5a182d896810,
    0x6e0b3a0c4b86182c, 0x1a0b2c0c3d821a0e, 0x2b0d3e0f1b812c0a, 0x4d0e1a0c2e830b0f,
    0x1b2c3d4e5f607182, 0x2c3d4e5f60718293, 0x3d4e5f60718293a4, 0x4e5f60718293a4b5,
    0x5f60718293a4b5c6, 0x60718293a4b5c6d7, 0x718293a4b5c6d7e8, 0x8293a4b5c6d7e8f9,
    0x93a4b5c6d7e8f90a, 0xa4b5c6d7e8f90a1b, 0xb5c6d7e8f90a1b2c, 0xc6d7e8f90a1b2c3d,
    0xd7e8f90a1b2c3d4e, 0xe8f90a1b2c3d4e5f, 0xf90a1b2c3d4e5f60, 0x0a1b2c3d4e5f6071,
    0x1a2b3c4d5e6f7081, 0x2b3c4d5e6f708192, 0x3c4d5e6f708192a3, 0x4d5e6f708192a3b4,
    0x5e6f708192a3b4c5, 0x6f708192a3b4c5d6, 0x708192a3b4c5d6e7, 0x8192a3b4c5d6e7f8,
    0x92a3b4c5d6e7f809, 0xa3b4c5d6e7f8091a, 0xb4c5d6e7f8091a2b, 0xc5d6e7f8091a2b3c,
    0xd6e7f8091a2b3c4d, 0xe7f8091a2b3c4d5e, 0xf8091a2b3c4d5e6f, 0x091a2b3c4d5e6f70,
    0x1122334455667788, 0x2233445566778899, 0x33445566778899aa, 0x445566778899aabb,
    0x5566778899aabbcc, 0x66778899aabbccdd, 0x778899aabbccddee, 0x8899aabbccddeeff,
    0x99aabbccddeeff00, 0xaabbccddeeff0011, 0xbbccddeeff001122, 0xccddeeff00112233,
    0xddeeff0011223344, 0xeeff001122334455, 0xff00112233445566, 0x0011223344556677,
    0x123456789abcdef0, 0x23456789abcdef01, 0x3456789abcdef012, 0x456789abcdef0123,
    0x56789abcdef01234, 0x6789abcdef012345, 0x789abcdef0123456, 0x89abcdef01234567,
    0x9abcdef012345678, 0xabcdef0123456789, 0xbcdef0123456789a, 0xcdef0123456789ab,
    0xdef0123456789abc, 0xef0123456789abcd, 0xf0123456789abcde, 0x0123456789abcdef,
    0xfedcba9876543210, 0xedcba9876543210f, 0xdcba9876543210fe, 0xcba9876543210fed,
    0xba9876543210fedc, 0xa9876543210fedcb, 0x9876543210fedcba, 0x876543210fedcba9,
    0x76543210fedcba98, 0x6543210fedcba987, 0x543210fedcba9876, 0x43210fedcba98765,
    0x3210fedcba987654, 0x210fedcba9876543, 0x10fedcba98765432, 0x0fedcba987654321,
    0x13579bdf02468ace, 0x3579bdf02468ace1, 0x579bdf02468ace13, 0x79bdf02468ace135,
    0x9bdf02468ace1357, 0xbdf02468ace13579, 0xdf02468ace13579b, 0xf02468ace13579bd,
    0x02468ace13579bdf, 0x2468ace13579bdf0, 0x468ace13579bdf02, 0x68ace13579bdf024,
    0x8ace13579bdf0246, 0xace13579bdf02468, 0xce13579bdf02468a, 0xe13579bdf02468ac,
    0x5c95c078d4653753, 0x22408982b81f3955, 0x8653c30f761c985f, 0x1393a84f30b8e57e,
    0x6a2887b863918e3c, 0x234c6b7b56a0e652, 0x3b8f7426466d7401, 0x064f6c80c9c6b670,
    0x412131830797864b, 0x7c761588d7c6f610, 0x0386f28a62091809, 0x1e601e0c4e8c4b0f,
    0x2f18a39b06e29c1a, 0x3e6f631507c92a4d, 0x0c0b87664180f33c, 0x627a0780b491f00d,
    0x1d707f0f4919e77a, 0x1e2068c8b3928223, 0x0a6c7b40a0e1a863, 0x454f500f2e1f1e37,
    0x168f41838982166d, 0x7f1e720a4b97c742, 0x2f60728b51a30b2f, 0x7d1a5e1e48902977,
    0x4f1e2e1a1b930263, 0x7e292b285c8c5e32, 0x3f2d6d0e1d801c2b, 0x5c0c5a182d896811,
    0x6e0b3a0c4b86182d, 0x1a0b2c0c3d821a0f, 0x2b0d3e0f1b812c0b, 0x4d0e1a0c2e830b10,
    0x1b2c3d4e5f607183, 0x2c3d4e5f60718294, 0x3d4e5f60718293a5, 0x4e5f60718293a4b6,
    0x5f60718293a4b5c7, 0x60718293a4b5c6d8, 0x718293a4b5c6d7e9, 0x8293a4b5c6d7e8fa,
    0x93a4b5c6d7e8f90b, 0xa4b5c6d7e8f90a1c, 0xb5c6d7e8f90a1b2d, 0xc6d7e8f90a1b2c3e,
    0xd7e8f90a1b2c3d4f, 0xe8f90a1b2c3d4e60, 0xf90a1b2c3d4e5f61, 0x0a1b2c3d4e5f6072,
    0x1a2b3c4d5e6f7082, 0x2b3c4d5e6f708193, 0x3c4d5e6f708192a4, 0x4d5e6f708192a3b5,
    0x5e6f708192a3b4c6, 0x6f708192a3b4c5d7, 0x708192a3b4c5d6e8, 0x8192a3b4c5d6e7f9,
    0x92a3b4c5d6e7f80a, 0xa3b4c5d6e7f8091b, 0xb4c5d6e7f8091a2c, 0xc5d6e7f8091a2b3d,
    0xd6e7f8091a2b3c4e, 0xe7f8091a2b3c4d5f, 0xf8091a2b3c4d5e70, 0x091a2b3c4d5e6f71,
    0x1122334455667789, 0x223344556677889a, 0x33445566778899ab, 0x445566778899aabc,
    0x5566778899aabbcd, 0x66778899aabbccde, 0x778899aabbccddf0, 0x8899aabbccddeef0,
    0x99aabbccddeeff01, 0xaabbccddeeff0012, 0xbbccddeeff001123, 0xccddeeff00112234,
    0xddeeff0011223345, 0xeeff001122334456, 0xff00112233445567, 0x0011223344556678,
    0x123456789abcdef1, 0x23456789abcdef02, 0x3456789abcdef013, 0x456789abcdef0124,
    0x56789abcdef01235, 0x6789abcdef012346, 0x789abcdef0123457, 0x89abcdef01234568,
    0x9abcdef012345679, 0xabcdef012345678a, 0xbcdef0123456789b, 0xcdef0123456789ac,
    0xdef0123456789abd, 0xef0123456789abce, 0xf0123456789abcdf, 0x0123456789abcdf0,
    0xfedcba9876543211, 0xedcba98765432110, 0xdcba9876543210ff, 0xcba9876543210fee,
    0xba9876543210fedd, 0xa9876543210fedcc, 0x9876543210fedcbb, 0x876543210fedcbaa,
    0x76543210fedcba99, 0x6543210fedcba988, 0x543210fedcba9877, 0x43210fedcba98766,
    0x3210fedcba987655, 0x210fedcba9876544, 0x10fedcba98765433, 0x0fedcba987654322,
    0x13579bdf02468acf, 0x3579bdf02468ace2, 0x579bdf02468ace14, 0x79bdf02468ace136,
    0x9bdf02468ace1358, 0xbdf02468ace1357a, 0xdf02468ace13579c, 0xf02468ace13579be,
    0x02468ace13579be0, 0x2468ace13579bdf1, 0x468ace13579bdf03, 0x68ace13579bdf025,
    0x8ace13579bdf0247, 0xace13579bdf02469, 0xce13579bdf02468b, 0xe13579bdf02468ad,
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
fn normal_size(mi: u32, av: u32, len: u32) -> u32 {
    let n = mi + (av - mi).div_ceil(2);
    if n > len {
        len
    } else {
        n
    }
}

#[inline]
fn mask(bits: u32) -> u64 {
    let clamped = clamp(bits, 1, 63);
    (1u64 << clamped) - 1
}

/// Core FastCDC Gear-hash cut function.
#[inline]
fn cut_fastcdc(src: &[u8], mi: usize, ma: usize, ns: usize, mask_s: u64, mask_l: u64) -> usize {
    let len = src.len();
    if len <= mi {
        return len;
    }

    let mut i = mi;
    let n1 = ns.min(len);
    let mut fp: u64 = 0;

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
