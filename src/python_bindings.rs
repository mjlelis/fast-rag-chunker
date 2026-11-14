#![allow(clippy::useless_conversion)]

#[cfg(feature = "python")]
use pyo3::exceptions::{PyDeprecationWarning, PyTypeError, PyValueError};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::{PyBytes, PyDict};

#[cfg(feature = "python")]
use crate::safe_core::{
    cache_key as rust_cache_key, chunk_batch_with_config,
    chunker_fingerprint as rust_chunker_fingerprint, diff_chunks as rust_diff_chunks,
    encode_hex_16, resolve_snap_window as rust_resolve_snap_window, Chunk, ChunkerConfig,
    ChunkingMode, NormalizationMode, SizeUnit, ALGORITHM_VERSION,
};

#[cfg(feature = "python")]
#[pyclass(name = "ChunkResult")]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PyChunkResult {
    #[pyo3(get)]
    pub offset: usize,
    #[pyo3(get)]
    pub length: usize,
    pub digest_bytes: [u8; 16],
    #[pyo3(get)]
    pub ordinal: usize,
    #[pyo3(get)]
    pub heading_path: Vec<String>,
    #[pyo3(get)]
    pub context_before: String,
    #[pyo3(get)]
    pub context_after: String,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyChunkResult {
    #[new]
    #[pyo3(signature = (offset=0, length=0, digest=None, hex=None, ordinal=0, heading_path=None, context_before="", context_after=""))]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        offset: usize,
        length: usize,
        digest: Option<&Bound<'_, PyBytes>>,
        hex: Option<&str>,
        ordinal: usize,
        heading_path: Option<Vec<String>>,
        context_before: &str,
        context_after: &str,
    ) -> PyResult<Self> {
        let mut digest_bytes = [0u8; 16];
        if let Some(d) = digest {
            let b = d.as_bytes();
            if b.len() != 16 {
                return Err(PyValueError::new_err(format!(
                    "Digest must be exactly 16 bytes, got {}",
                    b.len()
                )));
            }
            digest_bytes.copy_from_slice(b);
        } else if let Some(h) = hex {
            if h.len() != 32 {
                return Err(PyValueError::new_err(format!(
                    "Hex string must be exactly 32 chars, got {}",
                    h.len()
                )));
            }
            if let Ok(vec) = (0..32)
                .step_by(2)
                .map(|i| u8::from_str_radix(&h[i..i + 2], 16))
                .collect::<Result<Vec<u8>, _>>()
            {
                digest_bytes.copy_from_slice(&vec);
            }
        }

        Ok(Self {
            offset,
            length,
            digest_bytes,
            ordinal,
            heading_path: heading_path.unwrap_or_default(),
            context_before: context_before.to_string(),
            context_after: context_after.to_string(),
        })
    }

    /// Returns the 128-bit (16-byte) BLAKE3 content digest as Python `bytes`.
    #[getter]
    pub fn digest<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
        PyBytes::new(py, &self.digest_bytes)
    }

    /// Returns the 128-bit (16-byte) BLAKE3 content digest as a 32-char lowercase hex string.
    #[getter]
    pub fn hex(&self) -> String {
        encode_hex_16(&self.digest_bytes)
    }

    /// Compatibility alias for ordinal index.
    #[getter]
    pub fn index(&self) -> usize {
        self.ordinal
    }

    pub fn __repr__(&self) -> String {
        format!(
            "ChunkResult(offset={}, length={}, hex='{}', ordinal={})",
            self.offset,
            self.length,
            self.hex(),
            self.ordinal
        )
    }
}

/// 3-way incremental chunk diff result supporting property access and tuple unpacking.
#[cfg(feature = "python")]
#[pyclass(name = "ChunkDiffResult")]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PyChunkDiffResult {
    #[pyo3(get)]
    pub to_embed: Vec<PyChunkResult>,
    #[pyo3(get)]
    pub to_delete: Vec<PyChunkResult>,
    #[pyo3(get)]
    pub to_metadata_update: Vec<PyChunkResult>,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyChunkDiffResult {
    #[new]
    #[pyo3(signature = (to_embed=None, to_delete=None, to_metadata_update=None))]
    pub fn new(
        to_embed: Option<Vec<PyChunkResult>>,
        to_delete: Option<Vec<PyChunkResult>>,
        to_metadata_update: Option<Vec<PyChunkResult>>,
    ) -> Self {
        Self {
            to_embed: to_embed.unwrap_or_default(),
            to_delete: to_delete.unwrap_or_default(),
            to_metadata_update: to_metadata_update.unwrap_or_default(),
        }
    }

    pub fn __len__(&self) -> usize {
        3
    }

    pub fn __getitem__(&self, idx: isize) -> PyResult<Vec<PyChunkResult>> {
        match idx {
            0 | -3 => Ok(self.to_embed.clone()),
            1 | -2 => Ok(self.to_delete.clone()),
            2 | -1 => Ok(self.to_metadata_update.clone()),
            _ => Err(pyo3::exceptions::PyIndexError::new_err(
                "tuple index out of range",
            )),
        }
    }

    pub fn __repr__(&self) -> String {
        format!(
            "ChunkDiffResult(to_embed={}, to_delete={}, to_metadata_update={})",
            self.to_embed.len(),
            self.to_delete.len(),
            self.to_metadata_update.len()
        )
    }
}

/// Configuration object for `fast_rag_chunker`.
#[cfg(feature = "python")]
#[pyclass(name = "ChunkerConfig")]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PyChunkerConfig {
    #[pyo3(get)]
    pub min_chunk: usize,
    #[pyo3(get)]
    pub avg_chunk: usize,
    #[pyo3(get)]
    pub max_chunk: usize,
    #[pyo3(get)]
    pub mode: String,
    #[pyo3(get)]
    pub compute_hash: bool,
    #[pyo3(get)]
    pub snap_window: Option<usize>,
    #[pyo3(get)]
    pub size_unit: String,
    #[pyo3(get)]
    pub normalize: String,
    #[pyo3(get)]
    pub context_before: usize,
    #[pyo3(get)]
    pub context_after: usize,
    #[pyo3(get)]
    pub num_threads: Option<usize>,
    pub(crate) inner: ChunkerConfig,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyChunkerConfig {
    #[new]
    #[pyo3(signature = (min_chunk=64, max_chunk=512, avg_chunk=None, mode="boundary", compute_hash=true, snap_window=None, size_unit="bytes", normalize="none", context_before=0, context_after=0, num_threads=None, semantic_snap=None, **kwargs))]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        py: Python<'_>,
        min_chunk: i64,
        max_chunk: i64,
        avg_chunk: Option<i64>,
        mut mode: &str,
        compute_hash: bool,
        snap_window: Option<i64>,
        size_unit: &str,
        normalize: &str,
        context_before: i64,
        context_after: i64,
        num_threads: Option<i64>,
        semantic_snap: Option<bool>,
        kwargs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Self> {
        if let Some(dict) = kwargs {
            if dict.contains("mask")? {
                return Err(PyTypeError::new_err(
                    "ChunkerConfig.__init__() got an unexpected keyword argument 'mask'",
                ));
            }
            if !dict.is_empty() {
                let first_key = dict.keys().get_item(0)?;
                return Err(PyTypeError::new_err(format!(
                    "ChunkerConfig.__init__() got an unexpected keyword argument '{}'",
                    first_key
                )));
            }
        }

        if min_chunk <= 0 {
            return Err(PyValueError::new_err(
                "Minimum chunk size must be greater than 0",
            ));
        }
        if max_chunk <= 0 {
            return Err(PyValueError::new_err(
                "Maximum chunk size must be greater than 0",
            ));
        }
        if min_chunk > max_chunk {
            return Err(PyValueError::new_err(format!(
                "Minimum chunk size ({min_chunk}) cannot be greater than maximum chunk size ({max_chunk})"
            )));
        }
        if let Some(avg) = avg_chunk {
            if avg < min_chunk || avg > max_chunk {
                return Err(PyValueError::new_err(format!(
                    "Average chunk size ({avg}) must be between minimum ({min_chunk}) and maximum ({max_chunk})"
                )));
            }
        }
        if max_chunk as usize > MAX_CHUNK_SIZE_LIMIT {
            return Err(PyValueError::new_err(format!(
                "Chunk size ({max_chunk}) exceeds maximum supported limit ({MAX_CHUNK_SIZE_LIMIT} bytes)"
            )));
        }
        if let Some(w) = snap_window {
            if w <= 0 {
                return Err(PyValueError::new_err(
                    "Snap window must be greater than 0",
                ));
            }
        }
        if context_before < 0 {
            return Err(PyValueError::new_err("context_before must be >= 0"));
        }
        if context_after < 0 {
            return Err(PyValueError::new_err("context_after must be >= 0"));
        }
        if let Some(n) = num_threads {
            if n <= 0 {
                return Err(PyValueError::new_err(format!(
                    "Invalid thread count ({n}): num_threads must be >= 1"
                )));
            }
        }

        if let Some(snap) = semantic_snap {
            let warnings = py.import("warnings")?;
            let deprecation = py.get_type::<PyDeprecationWarning>();
            warnings.call_method1(
                "warn",
                (
                    "semantic_snap is deprecated since v0.3.0. Use mode='boundary' or mode='raw' instead.",
                    deprecation,
                ),
            )?;
            mode = if snap { "boundary" } else { "raw" };
        }

        let trimmed_mode = mode.trim().to_ascii_lowercase();
        if trimmed_mode == "semantic" {
            let warnings = py.import("warnings")?;
            let deprecation = py.get_type::<PyDeprecationWarning>();
            warnings.call_method1(
                "warn",
                (
                    "mode='semantic' is deprecated since v0.3.0 and will be removed in v1.0.0. Use mode='boundary' instead.",
                    deprecation,
                ),
            )?;
            mode = "boundary";
        }

        let parsed_mode =
            ChunkingMode::parse(mode).map_err(|err| PyValueError::new_err(err.to_string()))?;
        let parsed_unit =
            SizeUnit::parse(size_unit).map_err(|err| PyValueError::new_err(err.to_string()))?;
        let parsed_norm = NormalizationMode::parse(normalize)
            .map_err(|err| PyValueError::new_err(err.to_string()))?;

        let mode_str = if trimmed_mode == "boundary_aware" {
            "boundary_aware".to_string()
        } else {
            parsed_mode.as_str().to_string()
        };

        let inner = ChunkerConfig::new_full(
            min_chunk as usize,
            avg_chunk.map(|a| a as usize),
            max_chunk as usize,
            parsed_mode,
            compute_hash,
            snap_window.map(|w| w as usize),
            parsed_unit,
            parsed_norm,
            context_before as usize,
            context_after as usize,
        )
        .map_err(|err| PyValueError::new_err(err.to_string()))?;

        Ok(Self {
            min_chunk: inner.min_chunk,
            avg_chunk: inner.avg_chunk,
            max_chunk: inner.max_chunk,
            mode: mode_str,
            compute_hash: inner.compute_hash,
            snap_window: inner.snap_window,
            size_unit: inner.size_unit.as_str().to_string(),
            normalize: inner.normalize.as_str().to_string(),
            context_before: inner.context_before,
            context_after: inner.context_after,
            num_threads: num_threads.map(|n| n as usize),
            inner,
        })
    }

    /// Returns the deterministic configuration fingerprint string.
    pub fn fingerprint(&self) -> String {
        rust_chunker_fingerprint(&self.inner)
    }

    pub fn __repr__(&self) -> String {
        format!(
            "ChunkerConfig(min_chunk={}, avg_chunk={}, max_chunk={}, mode='{}', compute_hash={}, snap_window={:?}, size_unit='{}', normalize='{}', context_before={}, context_after={})",
            self.min_chunk,
            self.avg_chunk,
            self.max_chunk,
            self.mode,
            self.compute_hash,
            self.snap_window,
            self.size_unit,
            self.normalize,
            self.context_before,
            self.context_after
        )
    }
}

#[cfg(feature = "python")]
#[allow(clippy::too_many_arguments)]
fn resolve_config(
    py: Python<'_>,
    config: Option<&PyChunkerConfig>,
    min_chunk: i64,
    avg_chunk: Option<i64>,
    max_chunk: i64,
    mut mode: &str,
    compute_hash: bool,
    snap_window: Option<i64>,
    size_unit: &str,
    normalize: &str,
    context_before: i64,
    context_after: i64,
    semantic_snap: Option<bool>,
) -> PyResult<ChunkerConfig> {
    if let Some(cfg) = config {
        return Ok(cfg.inner.clone());
    }

    if min_chunk <= 0 {
        return Err(PyValueError::new_err(
            "Minimum chunk size must be greater than 0",
        ));
    }
    if max_chunk <= 0 {
        return Err(PyValueError::new_err(
            "Maximum chunk size must be greater than 0",
        ));
    }
    if min_chunk > max_chunk {
        return Err(PyValueError::new_err(format!(
            "Minimum chunk size ({min_chunk}) cannot be greater than maximum chunk size ({max_chunk})"
        )));
    }
    if let Some(avg) = avg_chunk {
        if avg < min_chunk || avg > max_chunk {
            return Err(PyValueError::new_err(format!(
                "Average chunk size ({avg}) must be between minimum ({min_chunk}) and maximum ({max_chunk})"
            )));
        }
    }
    if max_chunk as usize > MAX_CHUNK_SIZE_LIMIT {
        return Err(PyValueError::new_err(format!(
            "Chunk size ({max_chunk}) exceeds maximum supported limit ({MAX_CHUNK_SIZE_LIMIT} bytes)"
        )));
    }
    if let Some(w) = snap_window {
        if w <= 0 {
            return Err(PyValueError::new_err(
                "Snap window must be greater than 0",
            ));
        }
    }
    if context_before < 0 {
        return Err(PyValueError::new_err("context_before must be >= 0"));
    }
    if context_after < 0 {
        return Err(PyValueError::new_err("context_after must be >= 0"));
    }

    if let Some(snap) = semantic_snap {
        let warnings = py.import("warnings")?;
        let deprecation = py.get_type::<PyDeprecationWarning>();
        warnings.call_method1(
            "warn",
            (
                "semantic_snap is deprecated since v0.3.0. Use mode='boundary' or mode='raw' instead.",
                deprecation,
            ),
        )?;
        mode = if snap { "boundary" } else { "raw" };
    }

    let trimmed_mode = mode.trim().to_ascii_lowercase();
    if trimmed_mode == "semantic" {
        let warnings = py.import("warnings")?;
        let deprecation = py.get_type::<PyDeprecationWarning>();
        warnings.call_method1(
            "warn",
            (
                "mode='semantic' is deprecated since v0.3.0 and will be removed in v1.0.0. Use mode='boundary' instead.",
                deprecation,
            ),
        )?;
        mode = "boundary";
    }

    let parsed_mode =
        ChunkingMode::parse(mode).map_err(|err| PyValueError::new_err(err.to_string()))?;
    let parsed_unit =
        SizeUnit::parse(size_unit).map_err(|err| PyValueError::new_err(err.to_string()))?;
    let parsed_norm = NormalizationMode::parse(normalize)
        .map_err(|err| PyValueError::new_err(err.to_string()))?;

    ChunkerConfig::new_full(
        min_chunk as usize,
        avg_chunk.map(|a| a as usize),
        max_chunk as usize,
        parsed_mode,
        compute_hash,
        snap_window.map(|w| w as usize),
        parsed_unit,
        parsed_norm,
        context_before as usize,
        context_after as usize,
    )
    .map_err(|err| PyValueError::new_err(err.to_string()))
}

/// Resolves the snap window: explicit user value or proportional default.
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (avg_chunk, min_chunk, max_chunk, user_snap=None))]
pub fn resolve_snap_window(
    avg_chunk: usize,
    min_chunk: usize,
    max_chunk: usize,
    user_snap: Option<usize>,
) -> usize {
    rust_resolve_snap_window(avg_chunk, min_chunk, max_chunk, user_snap)
}

/// Summarizes the algorithm version and chunking parameters into a deterministic fingerprint.
#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (config=None, *, min_chunk=64, avg_chunk=None, max_chunk=512, mode="boundary", compute_hash=true, snap_window=None, size_unit="bytes", normalize="none", context_before=0, context_after=0))]
pub fn chunker_fingerprint(
    py: Python<'_>,
    config: Option<&PyChunkerConfig>,
    min_chunk: i64,
    avg_chunk: Option<i64>,
    max_chunk: i64,
    mode: &str,
    compute_hash: bool,
    snap_window: Option<i64>,
    size_unit: &str,
    normalize: &str,
    context_before: i64,
    context_after: i64,
) -> PyResult<String> {
    let resolved = resolve_config(
        py,
        config,
        min_chunk,
        avg_chunk,
        max_chunk,
        mode,
        compute_hash,
        snap_window,
        size_unit,
        normalize,
        context_before,
        context_after,
        None,
    )?;
    Ok(rust_chunker_fingerprint(&resolved))
}

/// Builds a collision-resistant embedding cache key.
#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (chunk, model_id, config=None, *, min_chunk=64, avg_chunk=None, max_chunk=512, mode="boundary", compute_hash=true, with_context=false, snap_window=None, size_unit="bytes", normalize="none", context_before=0, context_after=0))]
pub fn cache_key(
    py: Python<'_>,
    chunk: &PyChunkResult,
    model_id: &str,
    config: Option<&PyChunkerConfig>,
    min_chunk: i64,
    avg_chunk: Option<i64>,
    max_chunk: i64,
    mode: &str,
    compute_hash: bool,
    with_context: bool,
    snap_window: Option<i64>,
    size_unit: &str,
    normalize: &str,
    context_before: i64,
    context_after: i64,
) -> PyResult<String> {
    let resolved = resolve_config(
        py,
        config,
        min_chunk,
        avg_chunk,
        max_chunk,
        mode,
        compute_hash,
        snap_window,
        size_unit,
        normalize,
        context_before,
        context_after,
        None,
    )?;
    if chunk.digest_bytes == [0u8; 16] {
        return Err(PyValueError::new_err(
            "Cannot generate a cache key for a chunk with an empty (all-zero) digest",
        ));
    }
    if !resolved.compute_hash {
        return Err(PyValueError::new_err(
            "Cannot generate cache key when compute_hash is disabled",
        ));
    }
    let rust_chunk = Chunk {
        offset: chunk.offset,
        length: chunk.length,
        digest: chunk.digest_bytes,
        ordinal: chunk.ordinal,
        heading_path: chunk.heading_path.clone(),
        context_before: chunk.context_before.clone(),
        context_after: chunk.context_after.clone(),
    };
    rust_cache_key(&rust_chunk, model_id, &resolved, with_context)
        .map_err(|err| PyValueError::new_err(err.to_string()))
}

/// Processes a batch of byte documents in parallel across CPU cores, releasing Python's GIL.
#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (documents, min_chunk=64, max_chunk=512, avg_chunk=None, mode="boundary", compute_hash=true, num_threads=None, *, snap_window=None, size_unit="bytes", normalize="none", context_before=0, context_after=0, semantic_snap=None, config=None, **kwargs))]
pub fn chunk_documents_batch(
    py: Python<'_>,
    documents: Vec<Bound<'_, PyBytes>>,
    min_chunk: i64,
    max_chunk: i64,
    avg_chunk: Option<i64>,
    mode: &str,
    compute_hash: bool,
    num_threads: Option<i64>,
    snap_window: Option<i64>,
    size_unit: &str,
    normalize: &str,
    context_before: i64,
    context_after: i64,
    semantic_snap: Option<bool>,
    config: Option<&PyChunkerConfig>,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<Vec<Vec<PyChunkResult>>> {
    if let Some(dict) = kwargs {
        if dict.contains("mask")? {
            return Err(PyTypeError::new_err(
                "chunk_documents_batch() got an unexpected keyword argument 'mask'",
            ));
        }
        if !dict.is_empty() {
            let first_key = dict.keys().get_item(0)?;
            return Err(PyTypeError::new_err(format!(
                "chunk_documents_batch() got an unexpected keyword argument '{}'",
                first_key
            )));
        }
    }

    if let Some(n) = num_threads {
        if n <= 0 {
            return Err(PyValueError::new_err(format!(
                "Invalid thread count ({n}): num_threads must be >= 1"
            )));
        }
    }

    let resolved = resolve_config(
        py,
        config,
        min_chunk,
        avg_chunk,
        max_chunk,
        mode,
        compute_hash,
        snap_window,
        size_unit,
        normalize,
        context_before,
        context_after,
        semantic_snap,
    )?;

    let num_threads_resolved = if let Some(n) = num_threads {
        Some(n as usize)
    } else if let Some(cfg) = config {
        cfg.num_threads
    } else {
        None
    };

    let doc_slices: Vec<&[u8]> = documents.iter().map(|b| b.as_bytes()).collect();

    let batch_chunks = py
        .allow_threads(|| chunk_batch_with_config(&doc_slices, &resolved, num_threads_resolved))
        .map_err(|err| PyValueError::new_err(err.to_string()))?;

    let results = batch_chunks
        .into_iter()
        .map(|doc_chunks| {
            doc_chunks
                .into_iter()
                .map(|c| PyChunkResult {
                    offset: c.offset,
                    length: c.length,
                    digest_bytes: c.digest,
                    ordinal: c.ordinal,
                    heading_path: c.heading_path,
                    context_before: c.context_before,
                    context_after: c.context_after,
                })
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();

    Ok(results)
}

/// Computes the 3-way incremental chunk diff.
#[cfg(feature = "python")]
#[pyfunction]
pub fn diff_chunks(
    old_chunks: Vec<PyChunkResult>,
    new_chunks: Vec<PyChunkResult>,
) -> PyChunkDiffResult {
    let rust_old: Vec<Chunk> = old_chunks
        .iter()
        .map(|c| Chunk {
            offset: c.offset,
            length: c.length,
            digest: c.digest_bytes,
            ordinal: c.ordinal,
            heading_path: c.heading_path.clone(),
            context_before: c.context_before.clone(),
            context_after: c.context_after.clone(),
        })
        .collect();

    let rust_new: Vec<Chunk> = new_chunks
        .iter()
        .map(|c| Chunk {
            offset: c.offset,
            length: c.length,
            digest: c.digest_bytes,
            ordinal: c.ordinal,
            heading_path: c.heading_path.clone(),
            context_before: c.context_before.clone(),
            context_after: c.context_after.clone(),
        })
        .collect();

    let (to_embed, to_delete, to_metadata_update) = rust_diff_chunks(&rust_old, &rust_new);

    PyChunkDiffResult {
        to_embed: to_embed
            .into_iter()
            .map(|c| PyChunkResult {
                offset: c.offset,
                length: c.length,
                digest_bytes: c.digest,
                ordinal: c.ordinal,
                heading_path: c.heading_path,
                context_before: c.context_before,
                context_after: c.context_after,
            })
            .collect(),
        to_delete: to_delete
            .into_iter()
            .map(|c| PyChunkResult {
                offset: c.offset,
                length: c.length,
                digest_bytes: c.digest,
                ordinal: c.ordinal,
                heading_path: c.heading_path,
                context_before: c.context_before,
                context_after: c.context_after,
            })
            .collect(),
        to_metadata_update: to_metadata_update
            .into_iter()
            .map(|c| PyChunkResult {
                offset: c.offset,
                length: c.length,
                digest_bytes: c.digest,
                ordinal: c.ordinal,
                heading_path: c.heading_path,
                context_before: c.context_before,
                context_after: c.context_after,
            })
            .collect(),
    }
}

#[cfg(feature = "python")]
#[pymodule]
fn fast_rag_chunker(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("ALGORITHM_VERSION", ALGORITHM_VERSION)?;
    m.add_class::<PyChunkResult>()?;
    m.add("PyChunkResult", m.getattr("ChunkResult")?)?;
    m.add_class::<PyChunkerConfig>()?;
    m.add_class::<PyChunkDiffResult>()?;
    m.add("ChunkDiffResult", m.getattr("ChunkDiffResult")?)?;
    m.add_function(wrap_pyfunction!(chunk_documents_batch, m)?)?;
    m.add_function(wrap_pyfunction!(chunker_fingerprint, m)?)?;
    m.add_function(wrap_pyfunction!(cache_key, m)?)?;
    m.add_function(wrap_pyfunction!(diff_chunks, m)?)?;
    m.add_function(wrap_pyfunction!(resolve_snap_window, m)?)?;
    Ok(())
}
