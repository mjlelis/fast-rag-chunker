#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyBytes;
#[cfg(feature = "python")]
use rayon::prelude::*;

#[cfg(feature = "python")]
use crate::safe_core::chunk_slice;

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

/// Processa lotes de documentos em paralelo liberando o GIL do Python via Rayon
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (documents, min_chunk=64, max_chunk=512, mask=0x1F))]
pub fn chunk_documents_batch(
    py: Python<'_>,
    documents: Vec<Bound<'_, PyBytes>>,
    min_chunk: usize,
    max_chunk: usize,
    mask: u32,
) -> PyResult<Vec<Vec<PyChunkResult>>> {
    // 1. Extração de referências para fatias contíguas de memória (&[u8]) sem cópia
    let doc_slices: Vec<&[u8]> = documents.iter().map(|b| b.as_bytes()).collect();

    // 2. Liberação explícita do Global Interpreter Lock (GIL) para execução em paralelo multicore
    let results = py.allow_threads(|| {
        doc_slices
            .into_par_iter()
            .map(|slice| {
                chunk_slice(slice, min_chunk, max_chunk, mask)
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
