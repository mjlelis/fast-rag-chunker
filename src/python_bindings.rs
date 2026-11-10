#![allow(clippy::useless_conversion)]

#[cfg(feature = "python")]
use pyo3::exceptions::{PyDeprecationWarning, PyValueError};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyBytes;
#[cfg(feature = "python")]
use rayon::prelude::*;

#[cfg(feature = "python")]
use crate::safe_core::{chunk_slice, chunk_slice_semantic, validate_chunk_params, ChunkerError};

#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PyChunkResult {
    #[pyo3(get)]
    pub offset: usize,
    #[pyo3(get)]
    pub length: usize,
    #[pyo3(get)]
    pub hash: u64,
}

/// Processes a batch of byte documents in parallel across all CPU cores, releasing Python's GIL.
///
/// Parameters:
/// - `documents`: Sequence of Python `bytes` objects.
/// - `min_chunk`: Minimum chunk length in bytes (must be >= 1).
/// - `max_chunk`: Maximum chunk length in bytes (must be >= `min_chunk` and <= 1 GiB).
/// - `mask`: Deprecated and ignored (has no effect; FastCDC derives its internal dual masks
///           from the average chunk size. Emits `DeprecationWarning` when passed and will be
///           removed in v0.2.0).
/// - `semantic_snap`: When `True` (default), snaps cut points to UTF-8 and natural language
///                    boundaries and populates each chunk's 64-bit FNV-1a content hash.
///                    When `False`, runs raw FastCDC strictly honoring `min_chunk` and `max_chunk`.
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (documents, min_chunk=64, max_chunk=512, mask=None, semantic_snap=true))]
pub fn chunk_documents_batch(
    py: Python<'_>,
    documents: Vec<Bound<'_, PyBytes>>,
    min_chunk: usize,
    max_chunk: usize,
    mask: Option<u32>,
    semantic_snap: bool,
) -> PyResult<Vec<Vec<PyChunkResult>>> {
    if mask.is_some() {
        let warnings = PyModule::import_bound(py, "warnings")?;
        let category = py.get_type_bound::<PyDeprecationWarning>();
        warnings.call_method1(
            "warn",
            (
                "The 'mask' parameter is ignored by FastCDC and will be removed in v0.2.0.",
                category,
                1,
            ),
        )?;
    }

    // Validate parameters before releasing the GIL so invalid inputs fail fast with ValueError
    validate_chunk_params(min_chunk, max_chunk)
        .map_err(|err| PyValueError::new_err(err.to_string()))?;

    let mask_val = mask.unwrap_or(0);
    let doc_slices: Vec<&[u8]> = documents.iter().map(|b| b.as_bytes()).collect();

    let results: Result<Vec<Vec<PyChunkResult>>, ChunkerError> = py.allow_threads(|| {
        doc_slices
            .into_par_iter()
            .map(|slice| {
                let chunks = if semantic_snap {
                    chunk_slice_semantic(slice, min_chunk, max_chunk)?
                } else {
                    chunk_slice(slice, min_chunk, max_chunk, mask_val)?
                };

                Ok(chunks
                    .into_iter()
                    .map(|c| PyChunkResult {
                        offset: c.offset,
                        length: c.length,
                        hash: c.hash,
                    })
                    .collect::<Vec<_>>())
            })
            .collect()
    });

    results.map_err(|err| PyValueError::new_err(err.to_string()))
}

#[cfg(feature = "python")]
#[pymodule]
fn fast_rag_chunker(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyChunkResult>()?;
    m.add_function(wrap_pyfunction!(chunk_documents_batch, m)?)?;
    Ok(())
}
