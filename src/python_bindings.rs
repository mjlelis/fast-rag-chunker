#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyBytes;
#[cfg(feature = "python")]
use rayon::prelude::*;

#[cfg(feature = "python")]
use crate::safe_core::{chunk_slice, chunk_slice_semantic};

#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone)]
pub struct PyChunkResult {
    #[pyo3(get)]
    pub offset: usize,
    #[pyo3(get)]
    pub length: usize,
    #[pyo3(get)]
    pub hash: u64,
}

/// Processes document batches in parallel across all CPU cores, releasing Python's GIL via Rayon.
/// When `semantic_snap=True` (default), snaps cut points to UTF-8 and natural language boundaries
/// and populates each chunk's 64-bit FNV-1a content hash for embedding cache lookup.
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (documents, min_chunk=64, max_chunk=512, mask=0x1F, semantic_snap=true))]
pub fn chunk_documents_batch(
    py: Python<'_>,
    documents: Vec<Bound<'_, PyBytes>>,
    min_chunk: usize,
    max_chunk: usize,
    mask: u32,
    semantic_snap: bool,
) -> PyResult<Vec<Vec<PyChunkResult>>> {
    // 1. Zero-copy extraction of contiguous byte slice references (&[u8])
    let doc_slices: Vec<&[u8]> = documents.iter().map(|b| b.as_bytes()).collect();

    // 2. Explicit release of the Global Interpreter Lock (GIL) for multi-core Rayon execution
    let results = py.allow_threads(|| {
        doc_slices
            .into_par_iter()
            .map(|slice| {
                let chunks = if semantic_snap {
                    chunk_slice_semantic(slice, min_chunk, max_chunk)
                } else {
                    chunk_slice(slice, min_chunk, max_chunk, mask)
                };

                chunks
                    .unwrap_or_default()
                    .into_iter()
                    .map(|c| PyChunkResult {
                        offset: c.offset,
                        length: c.length,
                        hash: c.hash,
                    })
                    .collect::<Vec<_>>()
            })
            .collect::<Vec<_>>()
    });

    Ok(results)
}

#[cfg(feature = "python")]
#[pymodule]
fn fast_rag_chunker(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyChunkResult>()?;
    m.add_function(wrap_pyfunction!(chunk_documents_batch, m)?)?;
    Ok(())
}
