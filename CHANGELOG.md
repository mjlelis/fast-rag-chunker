# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-11-10 — Credibility & Contract Hardening

This patch release does not alter the semantic chunking boundaries (existing embedding caches remain 100% valid). It fixes parameter contracts, hardens the FFI and Python error paths, resolves all linter warnings, and enforces quality gates in CI.

### Fixed & Changed
- **R1.1 (Shift-Resilience & Resynchronization Tests):** Rewrote `test_shift_resilience_deduplication` in `src/safe_core.rs` with a 500-line corpus and a strict `>= 95%` cache hit ratio threshold (achieving `99.26%`, `268/270` chunks reused). Added `test_resynchronization_distance_ceiling` to measure and bound the resynchronization distance (3 chunks until the first cache hit, ceiling set to 4 chunks).
- **R1.2 (Zero Clippy Warnings):** Eliminated all 5 `cargo clippy --all-targets -- -D warnings` diagnostics across default and `--no-default-features` builds (replaced manual ceiling division with `u32::div_ceil`, replaced indexed range loops with iterator combinators, replaced manual `match` unwrap with `Result::unwrap_or`, added `# Safety` documentation to `rust_chunk_buffer`, and suppressed macro-generated `useless_conversion` in PyO3 bindings).
- **R1.3 (`mask` Parameter Deprecation):** Documented in `c_legacy/chunker.h`, `src/safe_core.rs`, `src/python_bindings.rs`, and `README.md` that `mask` has no effect (FastCDC derives its internal dual masks from the average chunk size). Passing `mask` in Python now emits a `DeprecationWarning` prior to its removal in `v0.2.0`.
- **R1.4 (`max_chunk` Contract in Raw Mode):** Split raw FastCDC into `chunk_slice_compat` (retaining legacy C clamps `[64, 256, 1024]` for FFI parity with `c_legacy/fastcdc.c`) and `chunk_slice` (unclamped, strictly honoring caller-supplied `min_chunk` and `max_chunk` in Python raw mode). Added property tests verifying `length <= max_chunk` for all chunks and `length >= min_chunk` for all non-final chunks across both raw and semantic modes.
- **R1.5 (Python Error Propagation):** Replaced `.unwrap_or_default()` in `src/python_bindings.rs` with explicit `ValueError` propagation carrying the `ChunkerError` message. Parameter validation now executes before releasing the Python GIL (`py.allow_threads`), ensuring non-empty documents never silently return an empty list.
- **R1.6 (Checked Parameter Arithmetic):** Added `validate_chunk_params` and `ChunkerError::ChunkSizeTooLarge` (`MAX_CHUNK_SIZE_LIMIT = 1 GiB`) using overflow-free midpoint arithmetic (`mi + (ma - mi) / 2`), preventing debug panics or release wrap-arounds on large `usize` inputs such as `usize::MAX`.
- **R1.7 (FFI Safety & Truncation Signaling):**
  - Added `CHUNKER_ERR_TRUNCATED (-2)` and `CHUNKER_ERR_INVALID (-1)` to `c_legacy/chunker.h` and `src/ffi_boundary.rs`.
  - Replaced `slice::from_raw_parts_mut` over potentially uninitialized output buffers in `rust_chunk_buffer` with `std::ptr::write`.
  - Added a `# Safety` contract section to `rust_chunk_buffer`.
  - Updated `c_legacy/fastcdc.c` (`fastcdc_update`) and `c_legacy/chunker.c` to honor non-zero callback return codes, stopping early and returning `CHUNKER_ERR_TRUNCATED` when output capacity `max_chunks` is exceeded.
- **R1.8 (Licensing & Attribution):** Added `LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE`, and `c_legacy/README.md` crediting Joseph Calderon's `sleepybishop/fastcdc` (MIT License) for the C reference implementation and the 256-entry `GEAR` lookup table constants alongside the USENIX ATC '16 paper by Wen Xia et al.
- **R1.9 (GitHub Actions CI Quality Gates):** Added `.github/workflows/ci.yml` running on Linux and macOS with `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings` (with and without `python`), `cargo test --locked`, `maturin` wheel build + `pytest`, Miri (`cargo +nightly miri test` on `safe_core`), and Valgrind (`valgrind --leak-check=full` on `c_legacy/main_test`).
- **R1.10 (Pytest Integration Suite):** Added `tests/test_chunker.py` covering contiguous offset coverage, per-chunk UTF-8 validity, `ValueError` and `DeprecationWarning` contracts, multi-run determinism, raw vs. semantic bounds, and empty batch handling.
- **R1.11 (Evidence-Aligned Documentation):** Updated `README.md` to remove unmeasured `ctypes` rows, document the exact commands and synthetic 500-line corpus structure behind every benchmark figure, mark throughput numbers as preliminary, include the CI status badge, and describe the Strangler Fig setup as an architectural demonstration over the reference C implementation.
- **R1.12 (Repository Hygiene):** Committed `Cargo.lock` for reproducible `--locked` builds, removed unused `criterion` dev-dependency until `v0.2.0`, standardized all code comments to English, and added this `CHANGELOG.md`.

## [0.1.0] - 2026-11-10

### Added
- Initial hybrid C / Rust / PyO3 FastCDC implementation with UTF-8 Semantic Boundary Snapping and FNV-1a 64-bit chunk fingerprinting.
