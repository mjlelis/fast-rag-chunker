# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-10

### Breaking Changes & Migration Guide
- **128-Bit BLAKE3 Content Digest (`R2.8`):** Replaced the 64-bit `FNV-1a` (`chunk.hash: int`) with a 128-bit (16-byte) truncated **BLAKE3** digest (`chunk.digest: bytes` and `chunk.hex: str` in Python; `Chunk.digest: [u8; 16]` and `Chunk::hex()` in Rust) to protect multi-tenant embedding caches against intentional hash collisions. Raw mode (`mode="raw"`) now also computes content digests by default; pass `compute_hash=False` to disable hashing.
  ```python
  # v0.1.x:
  # key = f"emb:{chunk.hash:016x}"
  #
  # v0.2.0:
  from fast_rag_chunker import ChunkerConfig, cache_key, chunk_documents_batch
  cfg = ChunkerConfig(min_chunk=64, avg_chunk=256, max_chunk=512, mode="semantic")
  chunks = chunk_documents_batch([doc_bytes], config=cfg)[0]
  key = cache_key(chunks[0], model_id="text-embedding-3-small", config=cfg)
  raw_16_bytes = chunks[0].digest
  hex_32_chars = chunks[0].hex
  ```
- **Removed `mask` Parameter & Introduced `ChunkerConfig` (`R2.10`):** Removed the deprecated `mask` parameter from Rust (`chunk_slice`, `chunk_slice_compat`) and Python (`chunk_documents_batch`). Passing `mask=...` in Python now raises `TypeError`. Added `ChunkerConfig { min_chunk, avg_chunk, max_chunk, mode, compute_hash }` in Rust and `ChunkerConfig` in Python with optional `avg_chunk` (defaulting to the midpoint of `min_chunk` and `max_chunk`).

### Added
- **Deduplication Benchmark Harness (`R2.1`):** Added `bench/dedup/` (`python -m bench.dedup --out results/dedup.json`) executing the compiled Rust extension and outputting reproducible JSON metrics.
- **Five Real RAG Framework Baselines (`R2.2`):** Added default and size-equivalent (`~256B`) baselines for Haystack `DocumentSplitter`, LangChain `RecursiveCharacterTextSplitter`, LlamaIndex `SentenceSplitter`, Fixed Window with Overlap, and Paragraph Split + Hash, with pinned dependency versions in `bench/requirements.txt`.
- **Synthetic Edit Scenarios Over Real Prose (`R2.3`):** Added 6 deterministic edit scenarios (`seed=42`, 30 documents each): top insertion, mid-sentence insertion, paragraph/span deletion, 5 scattered inline edits, moved paragraph, and whitespace-only formatting changes.
- **Real Bilingual Revision Pairs Corpus (`R2.4`):** Added `bench/corpus/download_corpus.py` and `bench/corpus/manifest.json` with SHA-256 verification and `CC-BY-SA-4.0` license registration over 30 consecutive revision pairs (15 English + 15 Portuguese articles).
- **Byte-Level Re-Embedding Cost & Size Distribution Metrics (`R2.5`):** Recorded byte reuse ratio (`1 - bytes_to_reembed / total_bytes`), chunk reuse ratio, mean/p50/p95 resynchronization distance, and chunk size percentiles (`min`, `p5`, `p50`, `mean`, `p95`, `max`, `total_chunks`) in `results/dedup.json`.
- **Criterion Throughput Benchmarks (`R2.6`):** Added `benches/throughput.rs` (`cargo bench`) and `examples/export_throughput_json.rs` measuring `raw` and `semantic` modes with and without BLAKE3-128 hashing across `1 MB`, `100 MB`, and `256 x 4 KB` document batches in both single-thread (`num_threads=1`) and multi-thread Rayon modes.
- **Automated README Table Generation (`R2.7`):** Added `scripts/generate_readme_tables.py` and `Makefile` target `make readme-tables`, verified in CI to fail on any drift between `results/*.json` and `README.md`.
- **Complete Cache Key Helpers (`R2.9`):** Added `chunker_fingerprint(config)` and `cache_key(chunk, model_id, config)` in Rust and Python so changing the embedding model or chunker parameters automatically namespaces cached vectors.
- **v2 C ABI Entry Point (`R2.11`):** Added `rust_chunk_buffer_v2` and `ChunkBoundaryV2` (with 16-byte `digest`, `avg_chunk`, `mode`, and `compute_hash` support) in `c_legacy/chunker.h` and `src/ffi_boundary.rs` while keeping `v1` (`rust_chunk_buffer`) unchanged.
- **Parallelism Control & PyO3 Upgrade (`R2.12`):** Added `num_threads` parameter to `chunk_documents_batch` and `chunk_batch_with_config` (verifying deterministic output between `1` and `N` threads) and upgraded PyO3 to `0.24`.

## [0.1.1] - 2026-11-10

### Fixed
- **R1.1 — Shift-Resilience Deduplication & Resynchronization Ceiling:** Rewrote `test_shift_resilience_deduplication` in `src/safe_core.rs` using a 500-line multi-chunk document with a strict `>= 95%` cache hit threshold (`99.26%` measured), and added `test_resynchronization_distance_ceiling` enforcing a maximum resynchronization distance of 4 chunks (`3` chunks measured).
- **R1.2 — Zero Clippy Warnings:** Resolved all 5 Clippy lints (`manual_div_ceil`, `needless_range_loop`, `manual_unwrap_or`, `missing_safety_doc`, and `useless_conversion`) so `cargo clippy --all-targets -- -D warnings` passes both with and without the `python` feature.
- **R1.4 — Raw Mode `max_chunk` Contract:** Separated C-clamped FastCDC (`chunk_slice_compat`, used by FFI and C parity tests) from unclamped raw FastCDC (`chunk_slice`, used by Python when `semantic_snap=False`), and added property tests asserting `length <= max_chunk` for all chunks and `length >= min_chunk` for all non-final chunks across raw and semantic modes.
- **R1.5 — Python Error Propagation:** Replaced silent `.unwrap_or_default()` fallback in `src/python_bindings.rs` with explicit `ValueError` exceptions raised prior to releasing the GIL (`py.allow_threads`).
- **R1.6 — Checked Parameter Arithmetic:** Added `validate_chunk_params` and `ChunkerError::ChunkSizeTooLarge` (`MAX_CHUNK_SIZE_LIMIT = 1 GiB`) using overflow-safe midpoint calculation `min + (max - min) / 2` and verified against `usize::MAX`.
- **R1.7 — FFI Safety & Truncation Signaling:** Updated `rust_chunk_buffer` (`src/ffi_boundary.rs`) and `chunk_buffer` (`c_legacy/chunker.c`, `c_legacy/fastcdc.c`, `c_legacy/chunker.h`) to return `CHUNKER_ERR_TRUNCATED (-2)` when chunks exceed `max_chunks`, stop early in the C streaming callback, write output via `std::ptr::write` without creating `&mut [T]` over uninitialized memory, and document `# Safety` preconditions.

### Changed
- **R1.3 — `mask` Parameter Deprecation:** Documented `mask` as ignored in `c_legacy/chunker.h`, Rust docstrings, and `README.md`, and emitted a `DeprecationWarning` in Python when `mask` is explicitly supplied.
- **R1.8 — Licensing & C Reference Attribution:** Added `LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE`, and `c_legacy/README.md` attributing `c_legacy/fastcdc.c` and `c_legacy/fastcdc.h` to [`sleepybishop/fastcdc`](https://github.com/sleepybishop/fastcdc) (Copyright (c) 2020 Joseph Calderon, MIT License), and clarified the `GEAR` table comment.
- **R1.9 & R1.10 — CI Quality Gates & Pytest Suite:** Added `.github/workflows/ci.yml` running `rustfmt`, `clippy`, `cargo test` (with and without `python`), `maturin` wheel build + `pytest` (`tests/test_chunker.py`), `Miri` on `safe_core`, and `Valgrind` on `c_legacy/main_test` across Linux and macOS.
- **R1.11 & R1.12 — Documentation & Repository Hygiene:** Aligned `README.md` strictly to reproducible repository evidence, versioned `Cargo.lock`, and standardized source comments in English.
