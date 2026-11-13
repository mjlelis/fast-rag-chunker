#![forbid(unsafe_code)]

use std::collections::HashMap;

#[cfg(not(miri))]
use rayon::prelude::*;
use thiserror::Error;
use unicode_normalization::UnicodeNormalization;

/// Canonical algorithm and boundary-rule version identifier included in cache fingerprints.
pub const ALGORITHM_VERSION: &str = "fast-rag-chunker/v0.3.0";

const MINIMUM_MIN: u32 = 64;
const MINIMUM_MAX: u32 = 67_108_864;
const AVERAGE_MIN: u32 = 256;
const AVERAGE_MAX: u32 = 268_435_456;
const MAXIMUM_MIN: u32 = 1024;
const MAXIMUM_MAX: u32 = 1_073_741_824;

/// Maximum permitted `max_chunk` size (1 GiB), preventing `u32` truncation and arithmetic overflow.
pub const MAX_CHUNK_SIZE_LIMIT: usize = MAXIMUM_MAX as usize;

/// Curated English abbreviation whitelist to prevent false sentence cuts.
pub static EN_ABBREVIATIONS: &[&str] = &[
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "vs", "etc", "eg", "ie", "approx", "al", "jan",
    "feb", "mar", "apr", "aug", "sept", "sep", "oct", "nov", "dec", "fig", "no", "vol", "vols",
    "dept", "est", "div", "corp", "inc", "ltd", "co", "ave", "st", "rd", "blvd", "gen", "col",
    "capt", "lt", "sgt", "rev", "hon", "gov", "sen", "rep", "ph.d", "m.d", "b.a",
];

/// Curated Portuguese abbreviation whitelist to prevent false sentence cuts.
pub static PT_ABBREVIATIONS: &[&str] = &[
    "art", "arts", "av", "bl", "cap", "cia", "coord", "dr", "dra", "drs", "dras", "ed", "eng",
    "ex", "exmo", "exma", "fig", "hab", "ilmo", "ilma", "inc", "n", "num", "obs", "pag", "pags",
    "pág", "págs", "prof", "profa", "profs", "profas", "rod", "sec", "sr", "sra", "srs", "sras",
    "tel", "univ", "v", "vol", "vols", "adm", "cel", "ten", "maj", "des", "min", "dep",
];

/// CJK sentence terminators in UTF-8 byte sequences.
pub static CJK_PUNCTUATION_BYTES: &[&[u8]] = &[
    "。".as_bytes(),
    "！".as_bytes(),
    "？".as_bytes(),
    "．".as_bytes(),
    "…".as_bytes(),
    "‥".as_bytes(),
];

/// Represents a content-defined chunk with a 128-bit (16-byte) content digest and RAG metadata.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Chunk {
    pub offset: usize,
    pub length: usize,
    pub digest: [u8; 16],
    pub ordinal: usize,
    pub heading_path: Vec<String>,
    pub context_before: String,
    pub context_after: String,
}

impl Chunk {
    /// Returns the 128-bit digest encoded as a 32-character lowercase hexadecimal string.
    #[inline]
    pub fn hex(&self) -> String {
        encode_hex_16(&self.digest)
    }

    /// Alias for ordinal index.
    #[inline]
    pub fn index(&self) -> usize {
        self.ordinal
    }
}

/// Operating mode for the FastCDC engine.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChunkingMode {
    /// Unclamped raw byte-level FastCDC respecting caller `min_chunk`, `avg_chunk`, and `max_chunk`.
    Raw,
    /// FastCDC with multi-tier priority boundary snapping (Markdown headings, blank lines, sentences, words, codepoints).
    Boundary,
    /// Deprecated alias for Boundary mode.
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
            Self::Boundary | Self::Semantic => "boundary",
            Self::CompatC => "compat_c",
        }
    }

    /// Parses a mode string (`"boundary"`, `"boundary_aware"`, `"semantic"`, `"raw"`, or `"compat_c"`).
    pub fn parse(mode: &str) -> Result<Self, ChunkerError> {
        match mode.trim().to_ascii_lowercase().as_str() {
            "boundary" | "boundary_aware" => Ok(Self::Boundary),
            "semantic" => Ok(Self::Semantic),
            "raw" => Ok(Self::Raw),
            "compat_c" | "compat" => Ok(Self::CompatC),
            other => Err(ChunkerError::InvalidMode {
                mode: other.to_string(),
            }),
        }
    }
}

/// Pre-hash normalization modes applied to bytes before computing content digests.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NormalizationMode {
    /// No normalization; digest computed over verbatim chunk slice.
    None,
    /// Collapses whitespace and normalizes CRLF to LF.
    Whitespace,
    /// Unicode Normalization Form C (NFC) with whitespace normalization.
    Nfc,
}

impl NormalizationMode {
    #[inline]
    pub fn as_str(self) -> &'static str {
        match self {
            Self::None => "none",
            Self::Whitespace => "whitespace",
            Self::Nfc => "nfc",
        }
    }

    pub fn parse(mode: &str) -> Result<Self, ChunkerError> {
        match mode.trim().to_ascii_lowercase().as_str() {
            "none" => Ok(Self::None),
            "whitespace" => Ok(Self::Whitespace),
            "nfc" => Ok(Self::Nfc),
            other => Err(ChunkerError::InvalidNormalizationMode {
                mode: other.to_string(),
            }),
        }
    }
}

/// Unit of measurement for chunk size constraints.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SizeUnit {
    /// Sizes specified in UTF-8 bytes.
    Bytes,
    /// Sizes specified in whitespace-separated tokens (words).
    Tokens,
}

impl SizeUnit {
    #[inline]
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Bytes => "bytes",
            Self::Tokens => "tokens",
        }
    }

    pub fn parse(unit: &str) -> Result<Self, ChunkerError> {
        match unit.trim().to_ascii_lowercase().as_str() {
            "bytes" => Ok(Self::Bytes),
            "tokens" => Ok(Self::Tokens),
            other => Err(ChunkerError::InvalidSizeUnit {
                unit: other.to_string(),
            }),
        }
    }
}

/// Resolves the snap window: explicit user value or proportional default.
#[inline]
pub fn resolve_snap_window(
    avg_chunk: usize,
    min_chunk: usize,
    max_chunk: usize,
    user_snap: Option<usize>,
) -> usize {
    if let Some(w) = user_snap {
        return w;
    }
    let target = ((avg_chunk as f64) * 0.15).round() as usize;
    let max_allowed = (max_chunk.saturating_sub(min_chunk)) / 2;
    32.max(target.min(max_allowed.max(32)))
}

/// Complete configuration contract for content-defined chunking.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChunkerConfig {
    pub min_chunk: usize,
    pub avg_chunk: usize,
    pub max_chunk: usize,
    pub mode: ChunkingMode,
    pub compute_hash: bool,
    pub snap_window: Option<usize>,
    pub size_unit: SizeUnit,
    pub normalize: NormalizationMode,
    pub context_before: usize,
    pub context_after: usize,
}

impl ChunkerConfig {
    /// Validates and constructs a `ChunkerConfig` with default v0.3 parameters for compatibility.
    pub fn new(
        min_chunk: usize,
        avg_chunk: Option<usize>,
        max_chunk: usize,
        mode: ChunkingMode,
        compute_hash: bool,
    ) -> Result<Self, ChunkerError> {
        Self::new_full(
            min_chunk,
            avg_chunk,
            max_chunk,
            mode,
            compute_hash,
            None,
            SizeUnit::Bytes,
            NormalizationMode::None,
            0,
            0,
        )
    }

    /// Full constructor supporting all v0.3 parameters.
    #[allow(clippy::too_many_arguments)]
    pub fn new_full(
        min_chunk: usize,
        avg_chunk: Option<usize>,
        max_chunk: usize,
        mode: ChunkingMode,
        compute_hash: bool,
        snap_window: Option<usize>,
        size_unit: SizeUnit,
        normalize: NormalizationMode,
        context_before: usize,
        context_after: usize,
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

        let resolved_mode = match mode {
            ChunkingMode::Semantic => ChunkingMode::Boundary,
            other => other,
        };

        Ok(Self {
            min_chunk,
            avg_chunk: avg,
            max_chunk,
            mode: resolved_mode,
            compute_hash,
            snap_window,
            size_unit,
            normalize,
            context_before,
            context_after,
        })
    }

    /// Returns the deterministic configuration fingerprint string.
    pub fn fingerprint(&self) -> String {
        chunker_fingerprint(self)
    }
}

#[derive(Error, Debug, PartialEq, Eq)]
pub enum ChunkerError {
    #[error("Minimum chunk size must be greater than 0")]
    InvalidMinChunkSize,
    #[error("Minimum chunk size ({min}) cannot be greater than maximum chunk size ({max})")]
    MinGreaterThanMax { min: usize, max: usize },
    #[error("Average chunk size ({avg}) must be between minimum ({min}) and maximum ({max})")]
    InvalidAverageChunkSize { min: usize, avg: usize, max: usize },
    #[error("Chunk size ({size}) exceeds maximum supported limit ({max_allowed} bytes)")]
    ChunkSizeTooLarge { size: usize, max_allowed: usize },
    #[error(
        "Invalid mode: '{mode}'. Expected one of ['boundary', 'boundary_aware', 'compat_c', 'raw']"
    )]
    InvalidMode { mode: String },
    #[error("Invalid size_unit: '{unit}'. Expected 'bytes' or 'tokens'")]
    InvalidSizeUnit { unit: String },
    #[error("Invalid normalize: '{mode}'. Expected 'none', 'whitespace', or 'nfc'")]
    InvalidNormalizationMode { mode: String },
    #[error("Cannot generate a cache key when compute_hash is disabled")]
    HashDisabledForCacheKey,
    #[error("Cannot generate a cache key for a chunk with an empty (all-zero) digest")]
    EmptyDigestForCacheKey,
    #[error("Embedding model_id must not be empty when generating a cache key")]
    EmptyModelId,
    #[error("Invalid thread count ({count}): num_threads must be >= 1")]
    InvalidThreadCount { count: usize },
}

/// 256-entry pseudo-random 32-bit Gear lookup table matching `c_legacy/fastcdc.c`.
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
pub fn encode_hex_16(bytes: &[u8; 16]) -> String {
    encode_hex_16_from_slice(bytes)
}

#[inline]
pub fn encode_hex_16_from_slice(bytes: &[u8]) -> String {
    const HEX_CHARS: &[u8; 16] = b"0123456789abcdef";
    let mut out = Vec::with_capacity(bytes.len() * 2);
    for &b in bytes {
        out.push(HEX_CHARS[(b >> 4) as usize]);
        out.push(HEX_CHARS[(b & 0x0f) as usize]);
    }
    String::from_utf8(out).unwrap_or_default()
}

/// Computes a 128-bit (16-byte) truncated BLAKE3 digest of `data`.
#[inline]
pub fn blake3_128(data: &[u8]) -> [u8; 16] {
    let hash = blake3::hash(data);
    let mut out = [0u8; 16];
    out.copy_from_slice(&hash.as_bytes()[..16]);
    out
}

/// Summarizes the algorithm version and `ChunkerConfig` parameters into a deterministic fingerprint.
pub fn chunker_fingerprint(config: &ChunkerConfig) -> String {
    let snap_str = match config.snap_window {
        Some(w) => w.to_string(),
        None => "None".to_string(),
    };
    let spec = format!(
        "{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}",
        ALGORITHM_VERSION,
        config.min_chunk,
        config.avg_chunk,
        config.max_chunk,
        config.mode.as_str(),
        if config.compute_hash { "True" } else { "False" },
        snap_str,
        config.size_unit.as_str(),
        config.normalize.as_str(),
        config.context_before,
        config.context_after,
    );
    let hash = blake3::hash(spec.as_bytes());
    encode_hex_16_from_slice(&hash.as_bytes()[..16])
}

/// Computes a complete, collision-resistant cache key.
pub fn cache_key(
    chunk: &Chunk,
    model_id: &str,
    config: &ChunkerConfig,
    with_context: bool,
) -> Result<String, ChunkerError> {
    if chunk.digest == [0u8; 16] {
        return Err(ChunkerError::EmptyDigestForCacheKey);
    }
    if !config.compute_hash {
        return Err(ChunkerError::HashDisabledForCacheKey);
    }
    let model_trimmed = model_id.trim();
    if model_trimmed.is_empty() {
        return Err(ChunkerError::EmptyModelId);
    }
    let fp = chunker_fingerprint(config);
    let payload = if !with_context {
        format!(
            "{}:{}:{}:{}",
            ALGORITHM_VERSION,
            model_trimmed,
            fp,
            chunk.hex()
        )
    } else {
        format!(
            "{}:{}:{}:{}:{}:{}",
            ALGORITHM_VERSION,
            model_trimmed,
            fp,
            chunk.hex(),
            chunk.context_before,
            chunk.context_after
        )
    };
    let hash = blake3::hash(payload.as_bytes());
    let hex_key = encode_hex_16_from_slice(&hash.as_bytes()[..16]);
    Ok(format!("frc:v0.3.0:{}", hex_key))
}

/// Applies pre-hash normalization without altering original byte offsets.
pub fn normalize_slice(raw_bytes: &[u8], mode: NormalizationMode) -> Vec<u8> {
    match mode {
        NormalizationMode::None => raw_bytes.to_vec(),
        NormalizationMode::Whitespace => {
            let text = String::from_utf8_lossy(raw_bytes);
            let unified = text.replace("\r\n", "\n").replace('\r', "\n");
            let mut result = String::with_capacity(unified.len());
            let mut in_space_run = false;
            for ch in unified.chars() {
                if ch == ' ' || ch == '\t' {
                    if !in_space_run {
                        result.push(' ');
                        in_space_run = true;
                    }
                } else {
                    in_space_run = false;
                    result.push(ch);
                }
            }
            result.trim().as_bytes().to_vec()
        }
        NormalizationMode::Nfc => {
            let text = String::from_utf8_lossy(raw_bytes);
            let nfc_text: String = text.nfc().collect();
            let unified = nfc_text.replace("\r\n", "\n").replace('\r', "\n");
            let mut result = String::with_capacity(unified.len());
            let mut in_space_run = false;
            for ch in unified.chars() {
                if ch.is_whitespace() {
                    if !in_space_run {
                        result.push(' ');
                        in_space_run = true;
                    }
                } else {
                    in_space_run = false;
                    result.push(ch);
                }
            }
            result.trim().as_bytes().to_vec()
        }
    }
}

#[inline]
pub fn compute_chunk_digest(
    raw_slice: &[u8],
    compute_hash: bool,
    normalize: NormalizationMode,
) -> [u8; 16] {
    if !compute_hash {
        return [0u8; 16];
    }
    let target_bytes = normalize_slice(raw_slice, normalize);
    blake3_128(&target_bytes)
}

/// Checks whether the byte at `period_byte_idx` is the dot of a known abbreviation.
pub fn is_sentence_abbreviation(data: &[u8], period_byte_idx: usize) -> bool {
    if period_byte_idx == 0 || period_byte_idx >= data.len() {
        return false;
    }
    let mut start = period_byte_idx - 1;
    while start > 0 {
        let b = data[start];
        if b.is_ascii_whitespace()
            || b == b','
            || b == b';'
            || b == b':'
            || b == b'('
            || b == b'['
            || b == b'"'
            || b == b'\''
        {
            start += 1;
            break;
        }
        start -= 1;
    }
    let word_bytes = &data[start..period_byte_idx];
    if let Ok(s) = std::str::from_utf8(word_bytes) {
        let lower = s.to_lowercase();
        let trimmed = lower.trim_matches('.');
        EN_ABBREVIATIONS.contains(&trimmed) || PT_ABBREVIATIONS.contains(&trimmed)
    } else {
        false
    }
}

/// Searches `data[window_start..window_end]` for the highest-priority semantic boundary.
pub fn find_priority_boundary(
    data: &[u8],
    window_start: usize,
    window_end: usize,
) -> Option<usize> {
    if window_start >= window_end || window_start >= data.len() {
        return None;
    }
    let actual_end = window_end.min(data.len());
    let span = &data[window_start..actual_end];

    // Priority 1: Markdown Heading (?:^|\n)(#{1,6}[ \t]+[^\n]+)
    let mut i = 0;
    while i < span.len() {
        let is_line_start = (i == 0 && (window_start == 0 || data[window_start - 1] == b'\n'))
            || (span[i] == b'\n');
        if is_line_start {
            let content_start = if span[i] == b'\n' { i + 1 } else { i };
            if content_start < span.len() && span[content_start] == b'#' {
                let mut h = content_start;
                while h < span.len() && span[h] == b'#' {
                    h += 1;
                }
                let count = h - content_start;
                if (1..=6).contains(&count)
                    && h < span.len()
                    && (span[h] == b' ' || span[h] == b'\t')
                {
                    return Some(window_start + content_start);
                }
            }
        }
        i += 1;
    }

    // Priority 2: Blank line / Paragraph (\n[ \t]*\r?\n)
    let mut j = 0;
    while j < span.len() {
        if span[j] == b'\n' {
            let mut k = j + 1;
            while k < span.len() && (span[k] == b' ' || span[k] == b'\t') {
                k += 1;
            }
            if k < span.len() && span[k] == b'\r' {
                k += 1;
            }
            if k < span.len() && span[k] == b'\n' {
                return Some(window_start + k + 1);
            }
        }
        j += 1;
    }

    // Priority 3: Sentence boundary
    // First check CJK punctuation sequences
    for &cjk_seq in CJK_PUNCTUATION_BYTES {
        if let Some(pos) = span.windows(cjk_seq.len()).position(|w| w == cjk_seq) {
            return Some(window_start + pos + cjk_seq.len());
        }
    }

    // Next check Latin sentence terminators (. ! ?)
    for (idx, &b) in span.iter().enumerate() {
        if b == b'.' || b == b'!' || b == b'?' {
            let global_idx = window_start + idx;
            if b != b'.' || !is_sentence_abbreviation(data, global_idx) {
                let mut cut = global_idx + 1;
                while cut < data.len() && (data[cut] == b' ' || data[cut] == b'\t') {
                    cut += 1;
                }
                return Some(cut);
            }
        }
    }

    // Priority 4: Word boundary (Unicode whitespace / ASCII whitespace)
    for idx in (0..span.len()).rev() {
        let b = span[idx];
        if b == b' ' || b == b'\t' || b == b'\r' || b == b'\n' {
            return Some(window_start + idx + 1);
        }
    }

    None
}

/// Builds active hierarchical heading stack for the slice ending at `chunk_end`.
pub fn extract_heading_stack_at(data: &[u8], chunk_end: usize) -> Vec<String> {
    let prefix = &data[..chunk_end.min(data.len())];
    let text = String::from_utf8_lossy(prefix);
    let mut stack: Vec<(usize, String)> = Vec::new();

    for line in text.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with('#') {
            let hash_count = trimmed.bytes().take_while(|&b| b == b'#').count();
            if (1..=6).contains(&hash_count) {
                let rest = &trimmed[hash_count..];
                if rest.starts_with(' ') || rest.starts_with('\t') {
                    let title = rest.trim();
                    if !title.is_empty() {
                        while let Some((last_level, _)) = stack.last() {
                            if *last_level >= hash_count {
                                stack.pop();
                            } else {
                                break;
                            }
                        }
                        stack.push((hash_count, title.to_string()));
                    }
                }
            }
        }
    }
    stack.into_iter().map(|(_, t)| t).collect()
}

/// Segments text into sentences with character index spans.
fn extract_sentences(text: &str, data: &[u8]) -> Vec<(usize, usize, String)> {
    let mut sentences = Vec::new();
    let mut current_start = 0;
    let chars: Vec<(usize, usize, char)> = {
        let mut v = Vec::new();
        let mut byte_pos = 0;
        for (char_idx, ch) in text.chars().enumerate() {
            let ch_len = ch.len_utf8();
            v.push((char_idx, byte_pos, ch));
            byte_pos += ch_len;
        }
        v
    };

    let total_chars = chars.len();
    let mut i = 0;
    while i < total_chars {
        let (_char_idx, byte_pos, ch) = chars[i];
        let is_cjk_term = matches!(ch, '。' | '！' | '？' | '．' | '…' | '‥' | '；' | '：');
        let mut is_latin_term = matches!(ch, '.' | '!' | '?');

        if is_latin_term && ch == '.' && is_sentence_abbreviation(data, byte_pos) {
            is_latin_term = false;
        }

        if is_cjk_term || is_latin_term {
            let mut end_idx = i + 1;
            while end_idx < total_chars && matches!(chars[end_idx].2, ' ' | '\t' | '\r' | '\n') {
                end_idx += 1;
            }
            let sent_str: String = chars[current_start..end_idx]
                .iter()
                .map(|(_, _, c)| *c)
                .collect();
            let trimmed = sent_str.trim().to_string();
            if !trimmed.is_empty() {
                sentences.push((current_start, end_idx, trimmed));
            }
            current_start = end_idx;
            i = end_idx;
        } else {
            i += 1;
        }
    }

    if current_start < total_chars {
        let sent_str: String = chars[current_start..total_chars]
            .iter()
            .map(|(_, _, c)| *c)
            .collect();
        let trimmed = sent_str.trim().to_string();
        if !trimmed.is_empty() {
            sentences.push((current_start, total_chars, trimmed));
        }
    }

    sentences
}

fn attach_context_windows(
    doc: &[u8],
    chunks: &mut [Chunk],
    context_before: usize,
    context_after: usize,
) {
    let doc_text = String::from_utf8_lossy(doc);
    let sentences = extract_sentences(&doc_text, doc);

    for chunk in chunks.iter_mut() {
        let c_char_start = String::from_utf8_lossy(&doc[..chunk.offset])
            .chars()
            .count();
        let c_char_end = String::from_utf8_lossy(&doc[..chunk.offset + chunk.length])
            .chars()
            .count();

        if context_before > 0 {
            let mut ctx_before_list: Vec<&str> = Vec::new();
            for (_, s_end, s_text) in sentences.iter().rev() {
                if *s_end <= c_char_start {
                    ctx_before_list.push(s_text.as_str());
                    if ctx_before_list.len() >= context_before {
                        break;
                    }
                }
            }
            ctx_before_list.reverse();
            chunk.context_before = ctx_before_list.join(" ");
        }

        if context_after > 0 {
            let mut ctx_after_list: Vec<&str> = Vec::new();
            for (s_start, _, s_text) in &sentences {
                if *s_start >= c_char_end {
                    ctx_after_list.push(s_text.as_str());
                    if ctx_after_list.len() >= context_after {
                        break;
                    }
                }
            }
            chunk.context_after = ctx_after_list.join(" ");
        }
    }
}

/// Computes the 3-way incremental chunk diff in O(N + M) time.
pub fn diff_chunks(
    old_chunks: &[Chunk],
    new_chunks: &[Chunk],
) -> (Vec<Chunk>, Vec<Chunk>, Vec<Chunk>) {
    let mut old_by_digest: HashMap<[u8; 16], Vec<&Chunk>> = HashMap::new();
    for c in old_chunks {
        old_by_digest.entry(c.digest).or_default().push(c);
    }

    let mut new_by_digest: HashMap<[u8; 16], Vec<&Chunk>> = HashMap::new();
    for c in new_chunks {
        new_by_digest.entry(c.digest).or_default().push(c);
    }

    let mut to_embed = Vec::new();
    let mut to_delete = Vec::new();
    let mut to_metadata_update = Vec::new();

    for c in new_chunks {
        match old_by_digest.get(&c.digest) {
            None => to_embed.push(c.clone()),
            Some(matches) => {
                let identical_metadata = matches.iter().any(|m| {
                    m.ordinal == c.ordinal
                        && m.heading_path == c.heading_path
                        && m.offset == c.offset
                });
                if !identical_metadata {
                    to_metadata_update.push(c.clone());
                }
            }
        }
    }

    for c in old_chunks {
        if !new_by_digest.contains_key(&c.digest) {
            to_delete.push(c.clone());
        }
    }

    (to_embed, to_delete, to_metadata_update)
}

fn count_tokens_in_slice(slice: &[u8]) -> usize {
    let text = String::from_utf8_lossy(slice);
    text.split_whitespace().count()
}

fn find_token_end(slice: &[u8], max_tokens: usize) -> usize {
    let text = String::from_utf8_lossy(slice);
    let mut count = 0;
    let mut byte_end = slice.len();
    let mut in_token = false;

    for (byte_idx, ch) in text.char_indices() {
        if ch.is_whitespace() {
            if in_token {
                count += 1;
                in_token = false;
                if count >= max_tokens {
                    byte_end = byte_idx;
                    break;
                }
            }
        } else {
            in_token = true;
        }
    }
    byte_end
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
    let mut off = mi + mi.div_ceil(2);
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

/// Core FastCDC Gear-hash cut function for C legacy compatibility.
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

/// Executes content-defined chunking according to a validated `ChunkerConfig`.
pub fn chunk_with_config(data: &[u8], config: &ChunkerConfig) -> Result<Vec<Chunk>, ChunkerError> {
    let validated = ChunkerConfig::new_full(
        config.min_chunk,
        Some(config.avg_chunk),
        config.max_chunk,
        config.mode,
        config.compute_hash,
        config.snap_window,
        config.size_unit,
        config.normalize,
        config.context_before,
        config.context_after,
    )?;

    if data.is_empty() {
        return Ok(Vec::new());
    }

    let doc_len = data.len();

    if validated.mode == ChunkingMode::CompatC {
        let raw_mi = validated.min_chunk as u32;
        let raw_av = validated.avg_chunk as u32;
        let raw_ma = validated.max_chunk as u32;

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
        let mut ordinal = 0;

        while offset < doc_len {
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
                ordinal,
                heading_path: Vec::new(),
                context_before: String::new(),
                context_after: String::new(),
            });

            offset += actual_len;
            ordinal += 1;
        }

        return Ok(chunks);
    }

    // Token mode early single-chunk check
    if validated.size_unit == SizeUnit::Tokens {
        let total_tokens = count_tokens_in_slice(data);
        if total_tokens <= validated.max_chunk {
            let digest = compute_chunk_digest(data, validated.compute_hash, validated.normalize);
            let heading_path = extract_heading_stack_at(data, doc_len);
            return Ok(vec![Chunk {
                offset: 0,
                length: doc_len,
                digest,
                ordinal: 0,
                heading_path,
                context_before: String::new(),
                context_after: String::new(),
            }]);
        }
    }

    let min_limit = validated.min_chunk;
    let max_limit = validated.max_chunk;
    let avg_limit = validated.avg_chunk;
    let snap_win = resolve_snap_window(avg_limit, min_limit, max_limit, validated.snap_window);

    let mut chunks: Vec<Chunk> = Vec::new();
    let mut offset = 0;
    let mut ordinal = 0;

    while offset < doc_len {
        let remaining = doc_len - offset;

        // Tail remainder handling (< min_limit)
        if remaining < min_limit {
            if chunks.is_empty() {
                let digest = compute_chunk_digest(
                    &data[offset..],
                    validated.compute_hash,
                    validated.normalize,
                );
                let heading_path = extract_heading_stack_at(data, doc_len);
                chunks.push(Chunk {
                    offset,
                    length: remaining,
                    digest,
                    ordinal,
                    heading_path,
                    context_before: String::new(),
                    context_after: String::new(),
                });
                break;
            }

            let last_idx = chunks.len() - 1;
            let prev_offset = chunks[last_idx].offset;
            let combined_len = chunks[last_idx].length + remaining;

            if combined_len <= max_limit {
                // Merge into previous chunk
                let merged_slice = &data[prev_offset..prev_offset + combined_len];
                let digest =
                    compute_chunk_digest(merged_slice, validated.compute_hash, validated.normalize);
                chunks[last_idx].length = combined_len;
                chunks[last_idx].digest = digest;
                break;
            } else {
                // Balanced midpoint redistribution
                let midpoint = prev_offset + combined_len / 2;
                let split_start = (prev_offset + min_limit).max(midpoint.saturating_sub(snap_win));
                let split_end = (prev_offset + combined_len - min_limit).min(midpoint + snap_win);
                let bound = if validated.mode == ChunkingMode::Boundary {
                    find_priority_boundary(data, split_start, split_end).unwrap_or(midpoint)
                } else {
                    midpoint
                };

                let first_len = bound - prev_offset;
                let second_len = combined_len - first_len;

                let d1 = compute_chunk_digest(
                    &data[prev_offset..bound],
                    validated.compute_hash,
                    validated.normalize,
                );
                chunks[last_idx].length = first_len;
                chunks[last_idx].digest = d1;

                let d2 = compute_chunk_digest(
                    &data[bound..bound + second_len],
                    validated.compute_hash,
                    validated.normalize,
                );
                let h_path2 = extract_heading_stack_at(data, bound + second_len);
                chunks.push(Chunk {
                    offset: bound,
                    length: second_len,
                    digest: d2,
                    ordinal: chunks[last_idx].ordinal + 1,
                    heading_path: h_path2,
                    context_before: String::new(),
                    context_after: String::new(),
                });
                break;
            }
        }

        let target_cut = (offset + avg_limit).min(doc_len);
        let mut cut_point = (offset + max_limit).min(doc_len);

        if validated.mode == ChunkingMode::Boundary {
            let w_start = (offset + min_limit).max(target_cut.saturating_sub(snap_win));
            let w_end = (offset + max_limit).min(target_cut + snap_win);
            if let Some(chosen) = find_priority_boundary(data, w_start, w_end) {
                if chosen > offset {
                    cut_point = chosen;
                } else {
                    cut_point = (offset + avg_limit).min(offset + max_limit);
                }
            } else {
                cut_point = (offset + avg_limit).min(offset + max_limit);
            }
        } else {
            cut_point = (offset + avg_limit).min(offset + max_limit);
        }

        // UTF-8 codepoint boundary fallback
        while cut_point < doc_len && (data[cut_point] & 0xC0) == 0x80 {
            cut_point += 1;
        }

        let mut length = (cut_point - offset).min(doc_len - offset);
        if length == 0 {
            length = remaining.min(max_limit);
        }

        // Token hard upper bound check
        if validated.size_unit == SizeUnit::Tokens {
            let tok_count = count_tokens_in_slice(&data[offset..offset + length]);
            if tok_count > max_limit {
                length = find_token_end(&data[offset..offset + length], max_limit);
            }
        }

        let raw_slice = &data[offset..offset + length];
        let digest = compute_chunk_digest(raw_slice, validated.compute_hash, validated.normalize);
        let heading_path = extract_heading_stack_at(data, offset + length);

        chunks.push(Chunk {
            offset,
            length,
            digest,
            ordinal,
            heading_path,
            context_before: String::new(),
            context_after: String::new(),
        });

        offset += length;
        ordinal += 1;
    }

    if validated.context_before > 0 || validated.context_after > 0 {
        attach_context_windows(
            data,
            &mut chunks,
            validated.context_before,
            validated.context_after,
        );
    }

    Ok(chunks)
}

/// Processes a batch of documents using the specified `ChunkerConfig` and optional thread count.
pub fn chunk_batch_with_config(
    documents: &[&[u8]],
    config: &ChunkerConfig,
    num_threads: Option<usize>,
) -> Result<Vec<Vec<Chunk>>, ChunkerError> {
    let validated = ChunkerConfig::new_full(
        config.min_chunk,
        Some(config.avg_chunk),
        config.max_chunk,
        config.mode,
        config.compute_hash,
        config.snap_window,
        config.size_unit,
        config.normalize,
        config.context_before,
        config.context_after,
    )?;

    if num_threads == Some(0) {
        return Err(ChunkerError::InvalidThreadCount { count: 0 });
    }

    #[cfg(miri)]
    {
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

/// Executes raw FastCDC with C-legacy parameter clamping.
pub fn chunk_slice_compat(
    data: &[u8],
    min_chunk: usize,
    max_chunk: usize,
) -> Result<Vec<Chunk>, ChunkerError> {
    let config = ChunkerConfig::new(min_chunk, None, max_chunk, ChunkingMode::CompatC, false)?;
    chunk_with_config(data, &config)
}

/// Executes raw FastCDC strictly respecting caller-supplied bounds and computing 128-bit BLAKE3 digests.
pub fn chunk_slice(
    data: &[u8],
    min_chunk: usize,
    max_chunk: usize,
) -> Result<Vec<Chunk>, ChunkerError> {
    let config = ChunkerConfig::new(min_chunk, None, max_chunk, ChunkingMode::Raw, true)?;
    chunk_with_config(data, &config)
}

/// Executes FastCDC with boundary snapping and 128-bit BLAKE3 hashing.
pub fn chunk_slice_semantic(
    data: &[u8],
    min_chunk: usize,
    max_chunk: usize,
) -> Result<Vec<Chunk>, ChunkerError> {
    let config = ChunkerConfig::new(min_chunk, None, max_chunk, ChunkingMode::Boundary, true)?;
    chunk_with_config(data, &config)
}

#[cfg(test)]
mod tests {
    use super::*;

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
            ChunkerConfig::new(64, Some(32), 512, ChunkingMode::Boundary, true),
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
    }

    #[test]
    fn test_priority_boundaries_headings() {
        let doc = b"Preamble text before the heading.\n# Title\nBody of section.";
        let config = ChunkerConfig::new(16, Some(35), 70, ChunkingMode::Boundary, true).unwrap();
        let chunks = chunk_with_config(doc, &config).unwrap();
        assert!(chunks.len() >= 2);
        let sec2 = &doc[chunks[1].offset..chunks[1].offset + chunks[1].length];
        assert!(sec2.starts_with(b"# Title"));
    }

    #[test]
    fn test_sentence_abbreviations_no_split() {
        let doc = b"Dr. Watson visited the hospital. All items approved.";
        let config = ChunkerConfig::new(15, Some(30), 60, ChunkingMode::Boundary, true).unwrap();
        let chunks = chunk_with_config(doc, &config).unwrap();
        let first_text =
            String::from_utf8_lossy(&doc[chunks[0].offset..chunks[0].offset + chunks[0].length]);
        assert!(!first_text.ends_with("Dr."));
    }

    #[test]
    fn test_tail_merge_and_redistribution() {
        let doc = b"A".repeat(50);
        let config = ChunkerConfig::new(10, Some(20), 40, ChunkingMode::Raw, true).unwrap();
        let chunks = chunk_with_config(&doc, &config).unwrap();
        let total: usize = chunks.iter().map(|c| c.length).sum();
        assert_eq!(total, 50);
        for c in &chunks {
            assert!(c.length >= 10);
            assert!(c.length <= 40);
        }
    }

    #[test]
    fn test_normalization_modes() {
        let raw = b"hello   world \r\n";
        let norm_ws = normalize_slice(raw, NormalizationMode::Whitespace);
        assert_eq!(norm_ws, b"hello world");

        let nfd_str = "coração".nfd().collect::<String>();
        let norm_nfc = normalize_slice(nfd_str.as_bytes(), NormalizationMode::Nfc);
        assert_eq!(String::from_utf8_lossy(&norm_nfc), "coração");
    }

    #[test]
    fn test_diff_chunks() {
        let c1 = Chunk {
            offset: 0,
            length: 10,
            digest: [1u8; 16],
            ordinal: 0,
            heading_path: vec![],
            context_before: String::new(),
            context_after: String::new(),
        };
        let c2 = Chunk {
            offset: 10,
            length: 10,
            digest: [2u8; 16],
            ordinal: 1,
            heading_path: vec![],
            context_before: String::new(),
            context_after: String::new(),
        };
        let c3 = Chunk {
            offset: 20,
            length: 10,
            digest: [3u8; 16],
            ordinal: 2,
            heading_path: vec![],
            context_before: String::new(),
            context_after: String::new(),
        };

        let (to_embed, to_delete, to_meta) =
            diff_chunks(&[c1.clone(), c2.clone()], &[c1.clone(), c3.clone()]);
        assert_eq!(to_embed.len(), 1);
        assert_eq!(to_embed[0].digest, [3u8; 16]);
        assert_eq!(to_delete.len(), 1);
        assert_eq!(to_delete[0].digest, [2u8; 16]);
        assert_eq!(to_meta.len(), 0);
    }

    #[test]
    fn test_shift_resilience_deduplication() {
        use std::collections::HashSet;

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

        let hit_ratio = (matching_chunks as f64) / (base_chunks.len() as f64);
        assert!(
            hit_ratio >= 0.90,
            "Expected >= 90.00% deduplication cache hit ratio, got {:.2}% ({matching_chunks}/{})",
            hit_ratio * 100.0,
            base_chunks.len()
        );
    }

    #[test]
    fn test_resynchronization_distance_ceiling() {
        use std::collections::HashSet;

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
