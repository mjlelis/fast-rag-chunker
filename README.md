# fast-rag-chunker

High-performance hybrid C / Rust / PyO3 Content-Defined Chunking (**FastCDC**) engine designed for high-throughput Retrieval-Augmented Generation (RAG) and document indexing pipelines.

[![Rust](https://img.shields.io/badge/rust-stable%20%7C%20nightly-orange.svg)](https://www.rust-lang.org/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-green.svg)](LICENSE)

## Overview

Traditional RAG ingestion pipelines implemented in pure Python suffer from significant CPU bottlenecks and GIL contention when processing large document corpora. `fast-rag-chunker` solves this using a **Strangler Fig** migration architecture:

1. **Legacy C Baseline:** Uses the official FastCDC (Wen Xia et al., USENIX ATC'16) algorithm implementation (`c_legacy/`).
2. **Memory-Safe Rust Core:** Re-implements the gear-hashing chunking logic under `#![forbid(unsafe_code)]` with zero dynamic allocations in the hot loop.
3. **Hardened FFI Boundary:** Exposes a drop-in C ABI compatible interface using `std::panic::catch_unwind` and immediate pointer-to-slice conversions.
4. **Zero-Copy PyO3 Bindings:** Exposes multi-threaded batch chunking to Python via Rayon, releasing the GIL during computation.

## Repository Architecture

```text
fast-rag-chunker/
├── Cargo.toml                  # cdylib, staticlib & rlib configuration
├── pyproject.toml              # Maturin build system
├── build.rs                    # C compilation and binding integration
├── Dockerfile                  # Isolated CI/build container
├── c_legacy/
│   ├── fastcdc.h               # Production C FastCDC header
│   ├── fastcdc.c               # Production C FastCDC implementation
│   ├── chunker.h               # Legacy C ABI interface
│   ├── chunker.c               # C wrapper
│   └── main_test.c             # C test harness
├── src/
│   ├── lib.rs                  # Crate root
│   ├── safe_core.rs            # 100% Safe Rust core (#![forbid(unsafe_code)])
│   ├── ffi_boundary.rs         # Panic-safe FFI layer (catch_unwind)
│   └── python_bindings.rs      # PyO3 module with Rayon parallelism
└── scripts/
    └── benchmark.py            # Comparative benchmark harness
```

## Quick Start

### Building the Rust Crate
```bash
cargo build --release
cargo test
```

### Python Extension (Maturin)
```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development build
pip install maturin
maturin develop --release
```

### Running Benchmarks
```bash
python scripts/benchmark.py
```

## Safety & Quality Gates
- **Zero Unsafe in Core:** `safe_core.rs` enforces `#![forbid(unsafe_code)]`.
- **FFI Boundary Defenses:** Validates null pointers, asserts slice bounds, and isolates panics from crossing the C ABI boundary.
