# Legacy C Reference (`c_legacy/`)

## Origin and License

The files [`fastcdc.c`](fastcdc.c) and [`fastcdc.h`](fastcdc.h) in this directory are derived from the open-source C99 reference implementation of FastCDC by Joseph Calderon:

- **Source Repository:** <https://github.com/sleepybishop/fastcdc>
- **Copyright:** Copyright (c) 2020 Joseph Calderon
- **License:** MIT License (see [`../NOTICE`](../NOTICE))

The underlying Content-Defined Chunking algorithm was introduced by Wen Xia et al. in:
> *"FastCDC: a Fast and Efficient Content-Defined Chunking Approach for Data Deduplication"*, USENIX Annual Technical Conference (USENIX ATC '16), 2016.

Note that while the USENIX ATC '16 paper specifies the use of a 256-entry pre-generated array of pseudo-random 32-bit integers for Gear hashing, the specific hexadecimal constants in `GEAR[]` originate from `sleepybishop/fastcdc`.

## Local Modifications (v0.1.1)

1. **Early Callback Termination (`fastcdc.c`):** `fastcdc_update` now inspects the integer return value of the `on_chunk` callback (`cb`) and stops iteration early when a non-zero status is returned.
2. **ABI Adapter (`chunker.h` / `chunker.c`):** Provides the `chunk_buffer` entry point and `ChunkBoundary` struct used to demonstrate the Strangler Fig FFI migration pattern and run C-vs-Rust parity tests, including explicit truncation reporting (`CHUNKER_ERR_TRUNCATED = -2`).
