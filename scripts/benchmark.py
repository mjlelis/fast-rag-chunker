"""Script de Benchmark Comparativo PEP 8 com Tipagem Estrita:
1. Python puro
2. C legado via ctypes
3. Rust PyO3 com Rayon (Zero-Copy)
"""

from __future__ import annotations
import ctypes
import os
import sys
import time
from typing import List, Tuple

# Carregamento da extensão C legada caso compilada
C_LIB_PATH = os.path.join(os.path.dirname(__file__), "..", "target", "release", "libfast_rag_chunker.so")
if sys.platform == "win32":
    C_LIB_PATH = os.path.join(os.path.dirname(__file__), "..", "target", "release", "fast_rag_chunker.dll")

class CChunkBoundary(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_size_t),
        ("length", ctypes.c_size_t),
        ("hash", ctypes.c_uint64),
    ]

def python_pure_chunker(data: bytes, min_chunk: int = 64, max_chunk: int = 512, mask: int = 0x1F) -> List[Tuple[int, int]]:
    chunks: List[Tuple[int, int]] = []
    start = 0
    total = len(data)
    while start < total:
        remaining = total - start
        if remaining <= min_chunk:
            chunks.append((start, remaining))
            break
        curr = min_chunk
        h = 0
        for i in range(min_chunk):
            h = (h * 31 + data[start + i]) & 0xFFFFFFFFFFFFFFFF
        limit = min(remaining, max_chunk)
        while curr < limit:
            if (h & mask) == 0:
                break
            h = (h * 31 + data[start + curr]) & 0xFFFFFFFFFFFFFFFF
            curr += 1
        chunks.append((start, curr))
        start += curr
    return chunks

def run_benchmark() -> None:
    print("=== Benchmark de Pré-Processamento de RAG / Content-Defined Chunking ===")
    sample_text = b"Engenharia de Sistemas e Infraestrutura de IA de Alta Performance. " * 50000 # ~3.3 MB
    num_docs = 10
    dataset: List[bytes] = [sample_text for _ in range(num_docs)]
    total_mb = (len(sample_text) * num_docs) / (1024 * 1024)

    print(f"Dataset de teste: {num_docs} documentos | Total: {total_mb:.2f} MB\n")

    # 1. Pure Python
    t0 = time.perf_counter()
    py_results = [python_pure_chunker(doc) for doc in dataset]
    t1 = time.perf_counter()
    py_duration = t1 - t0
    print(f"[1] Python Puro: {py_duration:.3f} s ({(total_mb / py_duration):.2f} MB/s) | Chunks por doc: {len(py_results[0])}")

    # 2. Rust PyO3 + Rayon
    try:
        import fast_rag_chunker
        t2 = time.perf_counter()
        rust_results = fast_rag_chunker.chunk_documents_batch(dataset, 64, 512, 0x1F)
        t3 = time.perf_counter()
        rust_duration = t3 - t2
        print(f"[2] Rust PyO3 + Rayon: {rust_duration:.3f} s ({(total_mb / rust_duration):.2f} MB/s) | Chunks por doc: {len(rust_results[0])}")
        print(f"--> Speedup Rust vs Python Puro: {py_duration / rust_duration:.2f}x mais rapido!")
    except ImportError:
        print("[!] Modulo fast_rag_chunker ainda nao instalado no ambiente Python. Execute 'maturin develop' para testar.")

if __name__ == "__main__":
    run_benchmark()
