#![allow(clippy::useless_conversion)]

#[cfg(feature = "python")]
use pyo3::exceptions::PyValueError;
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyBytes;

#[cfg(feature = "python")]
use crate::safe_core::{
    cache_key as rust_cache_key, chunk_batch_with_config,
    chunker_fingerprint as rust_chunker_fingerprint, Chunk, ChunkerConfig, ChunkingMode,
    ALGORITHM_VERSION,
};

#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PyChunkResult {
    #[pyo3(get)]
    pub offset: usize,
    #[pyo3(get)]
    pub length: usize,
    pub digest_bytes: [u8; 16],
}

#[cfg(feature = "python")]
#[pymethods]
impl PyChunkResult {
    /// Returns the 128-bit (16-byte) BLAKE3 content digest as Python `bytes`.
    #[getter]
    pub fn digest<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
        PyBytes::new(py, &self.digest_bytes)
    }

    /// Returns the 128-bit (16-byte) BLAKE3 content digest as a 32-char lowercase hex string.
    #[getter]
    pub fn hex(&self) -> String {
        let chunk = Chunk {
            offset: self.offset,
            length: self.length,
            digest: self.digest_bytes,
        };
        chunk.hex()
    }

    pub fn __repr__(&self) -> String {
        format!(
            "PyChunkResult(offset={}, length={}, hex='{}')",
            self.offset,
            self.length,
            self.hex()
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
    pub(crate) inner: ChunkerConfig,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyChunkerConfig {
    #[new]
    #[pyo3(signature = (min_chunk=64, max_chunk=512, avg_chunk=None, mode="semantic", compute_hash=true))]
    pub fn new(
        min_chunk: usize,
        max_chunk: usize,
        avg_chunk: Option<usize>,
        mode: &str,
        compute_hash: bool,
    ) -> PyResult<Self> {
        let parsed_mode =
            ChunkingMode::parse(mode).map_err(|err| PyValueError::new_err(err.to_string()))?;
        let inner = ChunkerConfig::new(min_chunk, avg_chunk, max_chunk, parsed_mode, compute_hash)
            .map_err(|err| PyValueError::new_err(err.to_string()))?;
        Ok(Self {
            min_chunk: inner.min_chunk,
            avg_chunk: inner.avg_chunk,
            max_chunk: inner.max_chunk,
            mode: inner.mode.as_str().to_string(),
            compute_hash: inner.compute_hash,
            inner,
        })
    }

    /// Returns the deterministic configuration fingerprint string.
    pub fn fingerprint(&self) -> String {
        rust_chunker_fingerprint(&self.inner)
    }

    pub fn __repr__(&self) -> String {
        format!(
            "ChunkerConfig(min_chunk={}, avg_chunk={}, max_chunk={}, mode='{}', compute_hash={})",
            self.min_chunk, self.avg_chunk, self.max_chunk, self.mode, self.compute_hash
        )
    }
}

#[cfg(feature = "python")]
fn resolve_config(
    config: Option<&PyChunkerConfig>,
    min_chunk: usize,
    avg_chunk: Option<usize>,
    max_chunk: usize,
    mode: &str,
    compute_hash: bool,
    semantic_snap: Option<bool>,
) -> PyResult<ChunkerConfig> {
    if let Some(cfg) = config {
        return Ok(cfg.inner);
    }
    let parsed_mode = match semantic_snap {
        Some(true) => ChunkingMode::Semantic,
        Some(false) => ChunkingMode::Raw,
        None => ChunkingMode::parse(mode).map_err(|err| PyValueError::new_err(err.to_string()))?,
    };
    ChunkerConfig::new(min_chunk, avg_chunk, max_chunk, parsed_mode, compute_hash)
        .map_err(|err| PyValueError::new_err(err.to_string()))
}

/// Summarizes the algorithm version and chunking parameters into a deterministic fingerprint.
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (config=None, *, min_chunk=64, avg_chunk=None, max_chunk=512, mode="semantic", compute_hash=true))]
pub fn chunker_fingerprint(
    config: Option<&PyChunkerConfig>,
    min_chunk: usize,
    avg_chunk: Option<usize>,
    max_chunk: usize,
    mode: &str,
    compute_hash: bool,
) -> PyResult<String> {
    let resolved = resolve_config(
        config,
        min_chunk,
        avg_chunk,
        max_chunk,
        mode,
        compute_hash,
        None,
    )?;
    Ok(rust_chunker_fingerprint(&resolved))
}

/// Builds a collision-resistant embedding cache key combining `chunk.digest`, `model_id`,
/// and the `ChunkerConfig` fingerprint.
#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (chunk, model_id, config=None, *, min_chunk=64, avg_chunk=None, max_chunk=512, mode="semantic", compute_hash=true))]
pub fn cache_key(
    chunk: &PyChunkResult,
    model_id: &str,
    config: Option<&PyChunkerConfig>,
    min_chunk: usize,
    avg_chunk: Option<usize>,
    max_chunk: usize,
    mode: &str,
    compute_hash: bool,
) -> PyResult<String> {
    let resolved = resolve_config(
        config,
        min_chunk,
        avg_chunk,
        max_chunk,
        mode,
        compute_hash,
        None,
    )?;
    if chunk.digest_bytes == [0u8; 16] {
        return Err(PyValueError::new_err(
            "Cannot generate a cache key for a chunk with an empty (all-zero) digest",
        ));
    }
    let rust_chunk = Chunk {
        offset: chunk.offset,
        length: chunk.length,
        digest: chunk.digest_bytes,
    };
    rust_cache_key(&rust_chunk, model_id, &resolved)
        .map_err(|err| PyValueError::new_err(err.to_string()))
}

/// Processes a batch of byte documents in parallel across CPU cores, releasing Python's GIL.
#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (documents, min_chunk=64, max_chunk=512, avg_chunk=None, mode="semantic", compute_hash=true, num_threads=None, *, semantic_snap=None, config=None))]
pub fn chunk_documents_batch(
    py: Python<'_>,
    documents: Vec<Bound<'_, PyBytes>>,
    min_chunk: usize,
    max_chunk: usize,
    avg_chunk: Option<usize>,
    mode: &str,
    compute_hash: bool,
    num_threads: Option<usize>,
    semantic_snap: Option<bool>,
    config: Option<&PyChunkerConfig>,
) -> PyResult<Vec<Vec<PyChunkResult>>> {
    let resolved = resolve_config(
        config,
        min_chunk,
        avg_chunk,
        max_chunk,
        mode,
        compute_hash,
        semantic_snap,
    )?;
    if num_threads == Some(0) {
        return Err(PyValueError::new_err(
            "Invalid thread count (0): num_threads must be >= 1",
        ));
    }

    let doc_slices: Vec<&[u8]> = documents.iter().map(|b| b.as_bytes()).collect();

    let batch_chunks = py
        .allow_threads(|| chunk_batch_with_config(&doc_slices, &resolved, num_threads))
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
                })
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();

    Ok(results)
}

#[cfg(feature = "python")]
#[pymodule]
fn fast_rag_chunker(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("ALGORITHM_VERSION", ALGORITHM_VERSION)?;
    m.add_class::<PyChunkResult>()?;
    m.add_class::<PyChunkerConfig>()?;
    m.add_function(wrap_pyfunction!(chunk_documents_batch, m)?)?;
    m.add_function(wrap_pyfunction!(chunker_fingerprint, m)?)?;
    m.add_function(wrap_pyfunction!(cache_key, m)?)?;
    Ok(())
}
