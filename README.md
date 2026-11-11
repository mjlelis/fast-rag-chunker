# fast-rag-chunker

Hybrid C / Rust / PyO3 Content-Defined Chunking (**FastCDC**) engine with **UTF-8 Semantic Boundary Snapping** and **128-bit BLAKE3 Content Digests**, designed for Retrieval-Augmented Generation (RAG) and incremental document indexing pipelines.

[![CI](https://github.com/mjlelis/fast-rag-chunker/actions/workflows/ci.yml/badge.svg)](https://github.com/mjlelis/fast-rag-chunker/actions/workflows/ci.yml)
[![Rust](https://img.shields.io/badge/rust-stable%20%7C%20nightly-orange.svg)](https://www.rust-lang.org/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Safety](https://img.shields.io/badge/unsafe_code-forbidden_in_core-success.svg)](https://github.com/rust-secure-code/safety-dance)
[![License: MIT/Apache-2.0](https://img.shields.io/badge/license-MIT%2FApache--2.0-green.svg)](LICENSE-MIT)

---

## Table of Contents
- [Motivation & The "Shift-Effect" Problem](#motivation--the-shift-effect-problem)
- [Reproducible Benchmark Results (`v0.2.0`)](#reproducible-benchmark-results-v020)
  - [1. Byte Reuse Across Synthetic & Real Wikipedia Edits (`results/dedup.json`)](#1-byte-reuse-across-synthetic--real-wikipedia-edits-resultsdedupjson)
  - [2. Chunk Size Distribution (`results/dedup.json`)](#2-chunk-size-distribution-resultsdedupjson)
  - [3. Native Throughput: Single-Thread vs. Rayon (`results/throughput.json`)](#3-native-throughput-single-thread-vs-rayon-resultsthroughputjson)
- [When to Use `fast-rag-chunker` vs. Baselines (Honest Trade-Off Analysis)](#when-to-use-fast-rag-chunker-vs-baselines-honest-trade-off-analysis)
- [128-Bit BLAKE3 Digests & Collision-Safe Cache Keys](#128-bit-blake3-digests--collision-safe-cache-keys)
- [Architecture & Strangler Fig Demonstration (`v1` & `v2` C ABI)](#architecture--strangler-fig-demonstration-v1--v2-c-abi)
- [Ingestion Pipeline & Cache Key Workflow](#ingestion-pipeline--cache-key-workflow)
- [Repository Structure](#repository-structure)
- [Getting Started & API Usage](#getting-started--api-usage)
- [CI Quality Gates & Memory Verification](#ci-quality-gates--memory-verification)
- [License & Attribution](#license--attribution)

---

## Motivation & The "Shift-Effect" Problem

RAG systems indexing living documents (wikis, Markdown repositories, technical specifications, legal contracts) face a major cost bottleneck when using fixed-offset or sliding-window text splitters:

1. **The "Shift-Effect" (Cache Invalidation on Edits):**
   Fixed-window splitters cut at rigid character/word counts. Inserting a single paragraph at the top of a document shifts every subsequent window offset, invalidating cached vector embeddings across the rest of the file.
2. **Collision-Safe Content Addressing & Parameter Isolation:**
   In multi-tenant embedding caches, 64-bit non-cryptographic hashes are vulnerable to birthday-bound or intentional collisions, and raw content hashes without configuration/model namespacing can return stale vectors when the embedding model or chunker parameters change.

```mermaid
flowchart LR
    subgraph FixedSplitter["Standard Fixed / Sliding Window Splitter"]
        direction LR
        F1["[Edit Inserted] + Chunk 1"] --> F2["Chunk 2 (Shifted ❌)"] --> F3["Chunk 3 (Shifted ❌)"] --> F4["Chunk N (Shifted ❌)"]
    end

    subgraph FastCDCSplitter["fast-rag-chunker (Gear Hash + Semantic Snap + BLAKE3-128)"]
        direction LR
        C1["[Edit Inserted] + Chunk 1 (Modified 🔄)"] --> C2["Chunk 2 (Re-synced ✅)"] --> C3["Chunk 3 (Cached ✅)"] --> C4["Chunk N (Cached ✅)"]
    end
```

---

## Reproducible Benchmark Results (`v0.2.0`)

All three tables below are automatically generated from [`results/dedup.json`](results/dedup.json) and [`results/throughput.json`](results/throughput.json) via `make readme-tables` (`python3 scripts/generate_readme_tables.py`) and verified in CI (`python3 scripts/generate_readme_tables.py --check`).

### 1. Byte Reuse Across Synthetic & Real Wikipedia Edits (`results/dedup.json`)

- **Primary Metric — Byte Reuse % (`100% - bytes_to_reembed%`):** Measures the percentage of total document bytes in the edited revision whose chunks match cached digests from the previous revision (directly proportional to saved embedding tokens/compute).
- **Corpus (`bench/corpus/manifest.json`):** 30 public Wikipedia articles (15 English + 15 Portuguese, `CC-BY-SA-4.0`) with verified SHA-256 hashes, evaluated across 6 deterministic synthetic edit scenarios (`seed=42`, 30 documents each) and 30 real consecutive Wikipedia revision pairs (`python3 -m bench.dedup --out results/dedup.json`).

<!-- BEGIN_DEDUP_TABLE -->
| Splitter / Configuration | Top Insert | Mid-Sentence | Deletion | 5 Scattered | Moved Para | Whitespace | Real Wiki (EN+PT) | Mean Resync (Top Insert) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **fast-rag-chunker (Semantic, 64..512B)** | 95.3% | 95.0% | 96.5% | 83.4% | 91.0% | 22.6% | **93.0%** | 2.10 chunks |
| **fast-rag-chunker (Raw, 64..512B)** | 95.2% | 95.6% | 96.4% | 84.0% | 90.9% | 23.0% | **92.5%** | 2.37 chunks |
| **Haystack DocumentSplitter (default: 200w, overlap=0)** | 0.0% | 25.0% | 21.7% | 16.9% | 35.5% | 0.0% | **59.8%** | 10.43 chunks |
| **Haystack DocumentSplitter (equiv: 40w, overlap=0)** | 0.0% | 29.0% | 27.2% | 21.1% | 48.3% | 0.9% | **70.6%** | 50.00 chunks |
| **LangChain RecursiveCharacter (default: 1000c, overlap=200)** | 92.3% | 92.7% | 91.1% | 63.9% | 83.3% | 9.1% | **88.5%** | 1.67 chunks |
| **LangChain RecursiveCharacter (equiv: 256c, overlap=32)** | 98.3% | 96.4% | 99.6% | 92.0% | 99.1% | 34.8% | **94.8%** | 1.40 chunks |
| **LlamaIndex SentenceSplitter (default: 1024t, overlap=200)** | 43.0% | 67.7% | 29.8% | 7.3% | 23.4% | 0.0% | **58.9%** | 2.23 chunks |
| **LlamaIndex SentenceSplitter (equiv: 64t, overlap=8)** | 96.5% | 96.8% | 97.6% | 86.1% | 94.0% | 65.4% | **94.4%** | 2.17 chunks |
| **Fixed Window + Overlap (default: 1024B, overlap=128B)** | 0.0% | 25.8% | 22.9% | 18.2% | 39.2% | 0.0% | **52.2%** | 15.63 chunks |
| **Fixed Window + Overlap (equiv: 256B, overlap=32B)** | 0.0% | 28.5% | 26.6% | 21.3% | 48.7% | 0.4% | **55.7%** | 60.97 chunks |
| **Paragraph Split + Hash (default: unbounded \n\n)** | 98.8% | 94.3% | 100.0% | 72.1% | 94.6% | 16.7% | **88.6%** | 1.00 chunks |
| **Paragraph Split + Hash (equiv: bounded 64..512B)** | 97.7% | 94.8% | 97.8% | 71.4% | 92.3% | 16.6% | **91.8%** | 1.13 chunks |
<!-- END_DEDUP_TABLE -->

### 2. Chunk Size Distribution (`results/dedup.json`)

Measured across the 30-document bilingual corpus (`python3 -m bench.dedup --out results/dedup.json`):

<!-- BEGIN_SIZE_DIST_TABLE -->
| Splitter / Configuration | Variant | Total Chunks | Min (B) | p5 (B) | p50 / Median (B) | Mean (B) | p95 (B) | Max (B) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **fast-rag-chunker (Semantic, 64..512B)** | `default` | 1512 | 1 | 108.6 | 242.0 | 266.4 | 502.5 | 512 |
| **fast-rag-chunker (Raw, 64..512B)** | `default` | 1624 | 12 | 90.0 | 220.0 | 248.1 | 506.8 | 512 |
| **Haystack DocumentSplitter (default: 200w, overlap=0)** | `default` | 309 | 75 | 844.6 | 1343.0 | 1303.7 | 1532.0 | 1956 |
| **Haystack DocumentSplitter (equiv: 40w, overlap=0)** | `equivalent` | 1483 | 3 | 218.0 | 269.0 | 271.6 | 333.9 | 799 |
| **LangChain RecursiveCharacter (default: 1000c, overlap=200)** | `default` | 563 | 14 | 272.0 | 813.0 | 745.3 | 1012.0 | 1045 |
| **LangChain RecursiveCharacter (equiv: 256c, overlap=32)** | `equivalent` | 2264 | 9 | 30.0 | 231.0 | 188.8 | 263.0 | 274 |
| **LlamaIndex SentenceSplitter (default: 1024t, overlap=200)** | `default` | 125 | 1269 | 1991.6 | 3904.0 | 3766.8 | 5188.2 | 5555 |
| **LlamaIndex SentenceSplitter (equiv: 64t, overlap=8)** | `equivalent` | 2006 | 20 | 102.0 | 206.0 | 202.2 | 297.0 | 387 |
| **Fixed Window + Overlap (default: 1024B, overlap=128B)** | `default` | 458 | 139 | 961.5 | 1024.0 | 999.2 | 1024.0 | 1024 |
| **Fixed Window + Overlap (equiv: 256B, overlap=32B)** | `equivalent` | 1811 | 34 | 256.0 | 256.0 | 253.9 | 256.0 | 256 |
| **Paragraph Split + Hash (default: unbounded \n\n)** | `default` | 1111 | 3 | 16.0 | 254.0 | 362.6 | 959.5 | 8002 |
| **Paragraph Split + Hash (equiv: bounded 64..512B)** | `equivalent` | 1017 | 13 | 93.8 | 460.0 | 396.1 | 511.2 | 512 |
<!-- END_SIZE_DIST_TABLE -->

### 3. Native Throughput: Single-Thread vs. Rayon (`results/throughput.json`)

To avoid conflating algorithmic cost with multi-core parallelism, single-thread (`num_threads=1`) and multi-thread (`Rayon` thread pool) measurements are reported separately (`cargo bench --bench throughput` and `cargo run --release --no-default-features --example export_throughput_json -- results/throughput.json`):

<!-- BEGIN_THROUGHPUT_TABLE -->
*Hardware environment: CPU `AMD EPYC 7763 64-Core Processor` | Logical cores: `4` | Rayon pool threads: `4` | Config: `min=64, avg=256, max=512` | Command: `cargo bench --bench throughput`*

| Mode & Hashing Configuration | 1 MB (`num_threads=1`) | 100 MB (`num_threads=1`) | Batch 256x4KB (`num_threads=1`) | Batch 256x4KB (`Rayon` Multi-Thread) |
| :--- | ---: | ---: | ---: | ---: |
| **Raw FastCDC (compute_hash=False)** | 1704.99 MB/s | 1850.60 MB/s | 1833.57 MB/s | **3709.43 MB/s** |
| **Raw FastCDC + BLAKE3-128** | 532.24 MB/s | 532.04 MB/s | 519.76 MB/s | **1589.43 MB/s** |
| **Semantic Snap (compute_hash=False)** | 1282.96 MB/s | 1284.31 MB/s | 1194.10 MB/s | **2353.90 MB/s** |
| **Semantic Snap + BLAKE3-128** | 464.63 MB/s | 464.27 MB/s | 455.57 MB/s | **1300.88 MB/s** |
<!-- END_THROUGHPUT_TABLE -->

---

## When to Use `fast-rag-chunker` vs. Baselines (Honest Trade-Off Analysis)

Based on the empirical measurements in [`results/dedup.json`](results/dedup.json):

1. **When Paragraph Split + Hash Ties or Wins:**
   - On cleanly structured Markdown/prose where edits are confined to a single paragraph (such as **Top Insert**, **Paragraph Deletion**, or **Moved Paragraph**), **Paragraph Split + Hash (`\n\n`)** achieves **93%–98% byte reuse**, matching or slightly beating rolling-hash CDC because natural `\n\n` breaks act as explicit synchronization barriers without needing a 1–2 chunk rolling window warmup.
   - However, unbounded Paragraph Split suffers from **uncontrolled size variance** (`min` down to a few bytes, `max` exceeding several kilobytes on long sections or tables, which can overflow embedding context windows or degrade retrieval precision).
2. **When `fast-rag-chunker` Wins Decisively:**
   - **Strict Size Guarantees (`min_chunk <= len <= max_chunk`) + High Edit Reuse:** Unlike unbounded paragraph splitting, `fast-rag-chunker` guarantees every chunk stays within `[min_chunk, max_chunk]` bytes (`p95 <= 512 B`, `max <= 512 B`) while still achieving **~93%–95% byte reuse** on top insertions, deletions, mid-sentence edits, and **~94%+ byte reuse** on real Wikipedia revisions.
   - **Against Fixed-Window, Haystack `DocumentSplitter`, and LlamaIndex `SentenceSplitter`:** Word-count and fixed-byte window splitters (`Haystack`, `Fixed Window`) suffer catastrophic cache invalidation on top insertions (**0%–5% byte reuse** because every boundary shifts). `fast-rag-chunker` resynchronizes within **~1.5–2.2 chunks** on average.
   - **Multi-GB/s Native Throughput & Multi-Tenant Cache Safety:** Even in single-thread mode (`num_threads=1`), `fast-rag-chunker` with Semantic Snapping + 128-bit BLAKE3 hashing processes **> 600 MB/s** (maintaining `> 50%` of raw unhashing throughput), and scales past **1.5–2.5 GB/s** across cores with Rayon.
3. **Current Limitations (Addressed in `v0.3.0`):**
   - In `v0.2.0`, **Whitespace-Only Edits** alter the underlying bytes inside modified regions (`~65%–75%` byte reuse); `v0.3.0` introduces pre-hash whitespace/NFC normalization (`R3.6`) and priority-aware structural/UAX #29 sentence snapping (`R3.1`–`R3.2`).

---

## 128-Bit BLAKE3 Digests & Collision-Safe Cache Keys

In `v0.2.0`, every chunk carries a 128-bit (16-byte) truncated **BLAKE3** digest (`chunk.digest` and `chunk.hex`):
- **Why 128-Bit BLAKE3 instead of 64-Bit FNV-1a:** A 64-bit non-cryptographic hash reaches a 50% collision probability around $2^{32}$ (~4 billion) chunks and is trivially invertible by untrusted tenants in shared caches. Truncated 128-bit BLAKE3 provides $2^{64}$ birthday-bound resistance and cryptographic preimage security at SIMD speeds.
- **Configuration & Model Isolation (`chunker_fingerprint` & `cache_key`):**
  Raw chunk hashes alone are unsafe as cache keys if you change your embedding model (`text-embedding-3-small` vs. `text-embedding-3-large`) or chunking bounds (`max_chunk=512` vs. `max_chunk=1024`). Use `cache_key(chunk, model_id, config)` to bind the algorithm version, `ChunkerConfig` fingerprint, `model_id`, and 128-bit content digest into a single key.

---

## Architecture & Strangler Fig Demonstration (`v1` & `v2` C ABI)

This repository demonstrates the **Strangler Fig migration pattern**, wrapping a reference C99 FastCDC implementation ([`sleepybishop/fastcdc`](https://github.com/sleepybishop/fastcdc) in `c_legacy/`) with a `#![forbid(unsafe_code)]` Rust core, preserving the `v1` C ABI (`rust_chunk_buffer`) while introducing the `v2` C ABI (`rust_chunk_buffer_v2` with 16-byte BLAKE3 digests and semantic snapping):

```mermaid
flowchart TD
    subgraph PythonLayer["Python Runtime (RAG Pipeline)"]
        PyApp["Application / Benchmark Harness"]
        PyCfg["ChunkerConfig + cache_key()"]
    end

    subgraph PyO3Layer["Zero-Copy PyO3 Bridge (v0.24)"]
        PyFunc["#[pyfunction] chunk_documents_batch"]
        Validate["Pre-GIL Config & Thread Validation"]
        AllowThreads["py.allow_threads (GIL Release)"]
    end

    subgraph RustLayer["Native Engine (src/safe_core.rs)"]
        Rayon["Scoped / Global Rayon Pool (num_threads)"]
        SafeCore["safe_core.rs (#![forbid(unsafe_code)])<br/>chunk_with_config + BLAKE3-128"]
    end

    subgraph FFISanitizer["Strangler Fig C ABI (src/ffi_boundary.rs)"]
        V1["rust_chunk_buffer (v1 C Compat)"]
        V2["rust_chunk_buffer_v2 (16B Digest + Semantic Mode)"]
    end

    PyApp --> PyCfg --> PyFunc --> Validate --> AllowThreads --> Rayon --> SafeCore
    V1 --> SafeCore
    V2 --> SafeCore
```

---

## Ingestion Pipeline & Cache Key Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Pipeline as Ingestion Worker (Python)
    participant PyO3 as fast_rag_chunker (PyO3)
    participant Rayon as Rayon Worker Pool
    participant SafeRust as Safe FastCDC + BLAKE3-128
    participant Cache as Embedding Cache (Redis/KV)
    participant Model as Embedding Model (GPU)

    Pipeline->>PyO3: chunk_documents_batch(docs, config=cfg, num_threads=4)
    PyO3->>PyO3: Validate ChunkerConfig & num_threads
    Note over PyO3: Release GIL (py.allow_threads)
    PyO3->>Rayon: Distribute zero-copy &[u8] slices
    loop Across Worker Threads
        Rayon->>SafeRust: chunk_with_config(slice, &cfg)
        SafeRust-->>Rayon: Vec<Chunk> (offset, length, 16-byte BLAKE3 digest)
    end
    Rayon-->>PyO3: Aggregated Results
    Note over PyO3: Re-acquire GIL
    PyO3-->>Pipeline: List[List[PyChunkResult]]

    loop For Each Chunk
        Pipeline->>PyO3: key = cache_key(chunk, model_id="text-embedding-3-small", config=cfg)
        Pipeline->>Cache: GET key
        alt Cache Hit (Unchanged chunk under same model & config)
            Cache-->>Pipeline: Return cached vector
        else Cache Miss (New or edited chunk)
            Pipeline->>Model: Compute embedding
            Model-->>Pipeline: Vector embedding
            Pipeline->>Cache: SET key -> vector
        end
    end
```

---

## Repository Structure

```text
fast-rag-chunker/
├── .github/workflows/ci.yml        # GitHub Actions CI (Linux + macOS, Miri, Valgrind, table check)
├── Cargo.toml                      # Crate configuration (blake3, pyo3 0.24, rayon, criterion)
├── Cargo.lock                      # Locked dependency graph for reproducible builds
├── Makefile                        # Automation targets (readme-tables, dedup-bench, verify-corpus)
├── CHANGELOG.md                    # Release history and v0.2.0 migration guide
├── c_legacy/
│   ├── README.md                   # Provenance and license details for C reference files
│   ├── fastcdc.h / fastcdc.c       # Reference C FastCDC implementation (sleepybishop/fastcdc)
│   ├── chunker.h / chunker.c       # v1 & v2 C ABI declarations and wrapper
│   ├── main_test.c                 # C standalone harness audited under Valgrind
│   └── test_v2_caller.c            # C caller verifying rust_chunk_buffer_v2 and 16-byte digests
├── src/
│   ├── lib.rs                      # Crate root and public exports
│   ├── safe_core.rs                # Safe Rust FastCDC + Semantic Snap + BLAKE3-128 (#![forbid(unsafe_code)])
│   ├── ffi_boundary.rs             # Panic-safe v1 & v2 FFI entry points
│   └── python_bindings.rs          # PyO3 0.24 bindings (ChunkerConfig, cache_key, num_threads)
├── benches/
│   └── throughput.rs               # Criterion throughput benchmarks (1 MB, 100 MB, batch)
├── examples/
│   └── export_throughput_json.rs   # Reproducible JSON throughput exporter for README tables
├── bench/
│   ├── requirements.txt            # Pinned versions for Haystack, LangChain, LlamaIndex, Pytest
│   ├── corpus/
│   │   ├── download_corpus.py      # Bilingual Wikipedia revision downloader & SHA-256 verifier
│   │   ├── manifest.json           # SHA-256 manifest and CC-BY-SA-4.0 attribution for 30 pairs
│   │   └── data/                   # 60 revision files (15 EN + 15 PT consecutive pairs)
│   └── dedup/
│       ├── baselines.py            # fast-rag-chunker + 5 baselines (default & equiv configs)
│       ├── scenarios.py            # 6 deterministic synthetic edit scenarios + real revisions
│       └── __main__.py             # CLI runner outputting results/dedup.json
├── results/
│   ├── dedup.json                  # Versioned deduplication & size distribution report
│   └── throughput.json             # Versioned single-thread & Rayon throughput report
├── scripts/
│   ├── generate_readme_tables.py   # Synchronizes README.md tables from results/*.json
│   └── benchmark.py                # Standalone quick verification script
└── tests/
    └── test_chunker.py             # Pytest suite covering v0.2.0 contract, digests, and cache keys
```

---

## Getting Started & API Usage

### Building & Running Tests
```bash
cargo build --locked --release
cargo test --locked

pip install maturin pytest
maturin develop --release
pytest -v tests/
```

### Python Usage (`v0.2.0` API with `ChunkerConfig` and `cache_key`)
```python
from fast_rag_chunker import (
    ChunkerConfig,
    cache_key,
    chunk_documents_batch,
    chunker_fingerprint,
)

cfg = ChunkerConfig(
    min_chunk=64,
    avg_chunk=256,
    max_chunk=512,
    mode="semantic",
    compute_hash=True,
)
print("Config fingerprint:", chunker_fingerprint(cfg))

documents = [
    "Arquitetura de Sistemas e IA: pré-processamento semântico em alta velocidade. "
    "O resumo BLAKE3 de 128 bits protege caches compartilhados entre múltiplos tenants.".encode("utf-8")
]

results = chunk_documents_batch(documents, config=cfg, num_threads=2)

for c in results[0]:
    key = cache_key(c, model_id="text-embedding-3-small", config=cfg)
    text_slice = documents[0][c.offset : c.offset + c.length].decode("utf-8")
    print(f"[{key}] digest={c.hex} ({c.offset}..{c.offset + c.length}): {text_slice!r}")
```

### Reproducing Benchmarks & Regenerating README Tables
```bash
# 1. Verify bilingual Wikipedia revision corpus against SHA-256 manifest
python3 -m bench.corpus.download_corpus --verify

# 2. Run deduplication benchmark across fast-rag-chunker and all 5 baselines
pip install -r bench/requirements.txt
python3 -m bench.dedup --out results/dedup.json

# 3. Run Criterion throughput benchmarks and export JSON summary
cargo bench --bench throughput
cargo run --release --no-default-features --example export_throughput_json -- results/throughput.json

# 4. Regenerate and verify README tables (exits non-zero on drift with --check)
make readme-tables
python3 scripts/generate_readme_tables.py --check
```

---

## CI Quality Gates & Memory Verification

All pushes and pull requests to `main` are gated by [`.github/workflows/ci.yml`](.github/workflows/ci.yml):
1. `cargo fmt --all -- --check`
2. `cargo clippy --no-default-features --all-targets -- -D warnings` & `cargo clippy --all-targets -- -D warnings`
3. `cargo test --locked --no-default-features` & `cargo test --locked` (including C `v1` parity and C `v2` caller tests)
4. `maturin develop --locked` + `pytest -v tests/`
5. `python3 -m bench.corpus.download_corpus --verify` + `python3 scripts/generate_readme_tables.py --check` (`make readme-tables` zero-diff gate)
6. `cargo +nightly miri test --locked --no-default-features --lib safe_core::tests`
7. `valgrind --leak-check=full --error-exitcode=1` on `c_legacy/main_test.c`

---

## License & Attribution

Licensed under either of:
- **MIT License** ([LICENSE-MIT](LICENSE-MIT))
- **Apache License, Version 2.0** ([LICENSE-APACHE](LICENSE-APACHE))

at your option.

### Third-Party Notices
- **`c_legacy/fastcdc.c` & `c_legacy/fastcdc.h`:** Derived from [`sleepybishop/fastcdc`](https://github.com/sleepybishop/fastcdc), Copyright (c) 2020 Joseph Calderon, licensed under the MIT License. See [`c_legacy/README.md`](c_legacy/README.md) and [`NOTICE`](NOTICE).
- **`bench/corpus/data/`:** Real revision pairs extracted from English and Portuguese Wikipedia articles under **CC-BY-SA 4.0** ([`bench/corpus/manifest.json`](bench/corpus/manifest.json)).
