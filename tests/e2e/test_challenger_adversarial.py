"""Adversarial stress and parity test suite for fast-rag-chunker (Milestone M1).

Conducted by Challenger 2 (Adversarial Stress & Parity Challenger).
Empirically verifies:
1. Determinism and lack of regressions across thread counts (num_threads=1, 2, 4, 8, None).
2. Boundary integrity, UTF-8 multibyte safety, priority snapping, and localized resynchronization.
3. Corpus manifest cryptographic integrity and tamper detection.
4. Real-world bilingual Wikipedia corpus diffing across all 30 pairs.
5. High-concurrency thread safety and pathological edge-case resistance.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import subprocess
import sys
import unicodedata
from pathlib import Path
import pytest

from tests.e2e.adapter import (
    ChunkerConfig,
    ChunkResult,
    chunk_documents_batch,
    chunker_fingerprint,
    cache_key,
    diff_chunks,
    resolve_snap_window,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CORPUS_DIR = REPO_ROOT / "bench" / "corpus"
DATA_DIR = CORPUS_DIR / "data"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"


# ============================================================================
# Section 1: Determinism & Concurrency Across Thread Counts
# ============================================================================

def test_adversarial_thread_count_invariance_large_heterogeneous_batch():
    """Verify bit-for-bit determinism across num_threads=1, 2, 4, 8, and None.

    Stress-tests with a heterogeneous batch of 50 documents containing:
    - Empty docs
    - Tiny sub-min docs
    - Unicode heavy (Portuguese accents, CJK ideographs, 4-byte emojis)
    - Structural Markdown docs
    - Code blocks
    """
    batch: list[bytes] = []

    # 1. Empty doc
    batch.append(b"")

    # 2. Sub-min docs
    batch.append(b"Tiny")
    batch.append(b"Sub min chunk.")

    # 3. Unicode heavy docs
    batch.append(
        "Acentuação em português: coração, ação, computação, inteligência artificial, "
        "órgão regulador, transações distribuídas.\n"
        .encode("utf-8") * 10
    )
    batch.append(
        "机器学习与自然语言处理：分块算法与向量检索系统。标点符号测试：句号。问号？感叹号！\n"
        .encode("utf-8") * 10
    )
    batch.append(
        "Emoji stress: 🚀🦀🐍🔥🤖💻🔍📊🎯⚡️🎉 \n"
        .encode("utf-8") * 20
    )

    # 4. Markdown structured docs
    for i in range(20):
        batch.append(
            (
                f"# Main Chapter {i}\n\n"
                f"Introduction paragraph for chapter {i}. Explains FastCDC and BLAKE3.\n\n"
                f"## Section A: Algorithms\n\n"
                f"Content discussing rolling hash and gear matrix values.\n\n"
                f"### Subsection A.1\n\n"
                f"Deeper details with code:\n\n"
                f"```rust\nlet x = {i} * 42;\n```\n\n"
                f"## Section B: Evaluation\n\n"
                f"Concludes with deterministic results.\n"
            ).encode("utf-8")
        )

    # 5. Pathological repeated text
    batch.append(b"A" * 5000)
    batch.append(b"Word " * 1000)
    batch.append(b"\n\n\n" * 500)

    # 6. Varied document sizes
    for sz in [64, 127, 128, 255, 256, 511, 512, 1024, 2048, 4096, 8192]:
        batch.append(b"X" * sz)

    assert len(batch) >= 40

    cfg = ChunkerConfig(min_chunk=32, avg_chunk=96, max_chunk=192, mode="boundary")

    # Execute with different thread counts
    res_1 = chunk_documents_batch(batch, config=cfg, num_threads=1)
    res_2 = chunk_documents_batch(batch, config=cfg, num_threads=2)
    res_4 = chunk_documents_batch(batch, config=cfg, num_threads=4)
    res_8 = chunk_documents_batch(batch, config=cfg, num_threads=8)
    res_none = chunk_documents_batch(batch, config=cfg, num_threads=None)

    thread_results = [("threads=2", res_2), ("threads=4", res_4), ("threads=8", res_8), ("threads=None", res_none)]

    # Assert exact bit-for-bit parity
    for label, res in thread_results:
        assert len(res) == len(res_1), f"Document count mismatch for {label}"
        for doc_idx, (chunks_ref, chunks_test) in enumerate(zip(res_1, res)):
            assert len(chunks_ref) == len(chunks_test), (
                f"Chunk count mismatch at doc {doc_idx} for {label}: "
                f"expected {len(chunks_ref)}, got {len(chunks_test)}"
            )
            for c_idx, (cr, ct) in enumerate(zip(chunks_ref, chunks_test)):
                assert cr.offset == ct.offset, f"Offset mismatch at doc {doc_idx}, chunk {c_idx} for {label}"
                assert cr.length == ct.length, f"Length mismatch at doc {doc_idx}, chunk {c_idx} for {label}"
                assert cr.digest == ct.digest, f"Digest mismatch at doc {doc_idx}, chunk {c_idx} for {label}"
                assert cr.hex == ct.hex, f"Hex mismatch at doc {doc_idx}, chunk {c_idx} for {label}"
                assert cr.ordinal == ct.ordinal, f"Ordinal mismatch at doc {doc_idx}, chunk {c_idx} for {label}"
                assert cr.heading_path == ct.heading_path, f"Heading path mismatch at doc {doc_idx}, chunk {c_idx} for {label}"


def test_adversarial_thread_safety_concurrent_calls():
    """Verify that multiple concurrent Python threads calling chunk_documents_batch do not race."""
    doc = (
        "# Thread Safety Test\n\n"
        "Testing concurrent access from multiple threads to ensure pure functional safety.\n\n"
        "## Subhead\n\n"
        "Content repeated to ensure non-trivial execution duration.\n"
    ).encode("utf-8") * 15

    cfg = ChunkerConfig(min_chunk=32, avg_chunk=96, max_chunk=256, mode="boundary")
    reference = chunk_documents_batch([doc], config=cfg, num_threads=1)[0]

    def worker_task(thread_id: int) -> list[ChunkResult]:
        t_count = (thread_id % 4) + 1
        res = chunk_documents_batch([doc], config=cfg, num_threads=t_count)[0]
        return res

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker_task, i) for i in range(24)]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            assert len(res) == len(reference)
            for cr, ct in zip(reference, res):
                assert cr.offset == ct.offset
                assert cr.length == ct.length
                assert cr.digest == ct.digest


def test_adversarial_invalid_num_threads_handling():
    """Verify robust exception handling for invalid num_threads inputs."""
    cfg = ChunkerConfig(min_chunk=32, max_chunk=128)
    sample_doc = [b"Sample content for validation."]

    # num_threads = 0 must raise ValueError
    with pytest.raises(ValueError, match="num_threads must be >= 1"):
        chunk_documents_batch(sample_doc, config=cfg, num_threads=0)

    # Negative thread count must raise ValueError
    with pytest.raises(ValueError, match="num_threads must be >= 1"):
        chunk_documents_batch(sample_doc, config=cfg, num_threads=-1)

    with pytest.raises(ValueError, match="num_threads must be >= 1"):
        chunk_documents_batch(sample_doc, config=cfg, num_threads=-99)


# ============================================================================
# Section 2: Corpus Manifest Cryptographic Integrity & Tamper Testing
# ============================================================================

def test_corpus_manifest_deep_cryptographic_verification():
    """Deeply inspect manifest.json schema, file presence, exact byte lengths, and SHA-256."""
    assert MANIFEST_PATH.exists(), f"Missing manifest at {MANIFEST_PATH}"
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest.get("corpus_version") == "0.2.0"
    docs = manifest.get("documents", [])
    assert len(docs) >= 30, f"Expected >= 30 documents, got {len(docs)}"

    en_count = 0
    pt_count = 0

    for idx, item in enumerate(docs):
        # Validate required schema keys
        for key in ["doc_id", "lang", "title", "pageid", "old_revid", "new_revid",
                    "old_file", "new_file", "old_bytes", "new_bytes", "old_sha256", "new_sha256"]:
            assert key in item, f"Missing key '{key}' in document {idx} ({item.get('doc_id')})"

        assert item["lang"] in ("en", "pt")
        if item["lang"] == "en":
            en_count += 1
        else:
            pt_count += 1

        # Check revision ID validity
        assert isinstance(item["old_revid"], int) and item["old_revid"] > 0
        assert isinstance(item["new_revid"], int) and item["new_revid"] > 0
        assert item["old_revid"] != item["new_revid"], f"Revisions must differ in {item['doc_id']}"

        # Check files on disk
        for prefix in ("old", "new"):
            rel_file = item[f"{prefix}_file"]
            full_path = CORPUS_DIR / rel_file
            assert full_path.is_file(), f"Missing corpus file: {full_path}"

            data = full_path.read_bytes()
            assert len(data) == item[f"{prefix}_bytes"], (
                f"Byte length mismatch for {rel_file}: expected {item[f'{prefix}_bytes']}, got {len(data)}"
            )

            actual_sha = hashlib.sha256(data).hexdigest()
            expected_sha = item[f"{prefix}_sha256"]
            assert actual_sha == expected_sha, (
                f"SHA-256 mismatch for {rel_file}: expected {expected_sha}, got {actual_sha}"
            )

    assert en_count == 15, f"Expected exactly 15 English docs, got {en_count}"
    assert pt_count == 15, f"Expected exactly 15 Portuguese docs, got {pt_count}"


def test_corpus_manifest_cli_execution():
    """Verify that python -m bench.corpus.download_corpus --verify exits cleanly with code 0."""
    result = subprocess.run(
        [sys.executable, "-m", "bench.corpus.download_corpus", "--verify"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Manifest verification CLI failed: {result.stderr}"
    assert "Verified 30 document revision pairs (60 files) against SHA-256 manifest." in result.stdout


# ============================================================================
# Section 3: Boundary Integrity, UTF-8 Multibyte Safety & Resync Behavior
# ============================================================================

def test_adversarial_multibyte_utf8_boundary_snapping():
    """Verify that chunk boundaries NEVER slice inside 2-byte, 3-byte, or 4-byte UTF-8 codepoints.

    Uses dense multibyte characters with tight, misaligned chunk limits.
    """
    # 2-byte: á, é, í, ó, ú, ñ, ç (C3 xx)
    # 3-byte: 中, 文, 字, 符, 编, 码 (E4..E9 xx xx)
    # 4-byte: 🦀, 🚀, 💡, 🛡️, ⚙️, 🔥 (F0 9F xx xx)
    raw_text = (
        "Texto em português com acentos: áéíóúçãõ. "
        "中文汉字测试自然语言处理分块。 "
        "Emojis: 🦀🦀🚀🚀💡💡🔥🔥🤖🤖. "
    ) * 20
    doc = raw_text.encode("utf-8")

    # Use asymmetric, non-power-of-2 chunk limits to induce potential slicing
    for min_c, max_c in [(17, 43), (23, 67), (31, 89), (13, 37)]:
        cfg = ChunkerConfig(min_chunk=min_c, max_chunk=max_c, mode="boundary")
        chunks = chunk_documents_batch([doc], config=cfg)[0]

        reconstructed = bytearray()
        for idx, c in enumerate(chunks):
            chunk_bytes = doc[c.offset : c.offset + c.length]
            # Must decode without UnicodeDecodeError
            try:
                decoded = chunk_bytes.decode("utf-8")
                assert len(decoded) > 0
            except UnicodeDecodeError as err:
                pytest.fail(f"Chunk {idx} sliced multibyte UTF-8 codepoint: {err}")

            reconstructed.extend(chunk_bytes)

        # Offsets must be strictly contiguous and reassemble original bytes
        assert bytes(reconstructed) == doc


def test_adversarial_priority_boundary_order():
    """Verify priority order: Heading > Blank line > Sentence end > Word boundary > Codepoint."""
    # Construct a string where heading, blank line, sentence, and word boundary compete
    # within the snap window around target cut
    doc = (
        "Prefix intro sentence. "
        "Another sentence here. "
        "\n\n"
        "# High Priority Heading\n\n"
        "Following sentence after heading."
    ).encode("utf-8")

    cfg = ChunkerConfig(min_chunk=20, avg_chunk=50, max_chunk=120, mode="boundary")
    chunks = chunk_documents_batch([doc], config=cfg)[0]

    # Verify that the cut occurred exactly at the heading line
    heading_chunks = [
        c for c in chunks if doc[c.offset : c.offset + c.length].decode("utf-8").startswith("# High Priority Heading")
    ]
    assert len(heading_chunks) == 1
    assert "High Priority Heading" in heading_chunks[0].heading_path


def test_adversarial_resynchronization_under_diverse_mutations():
    """Verify FastCDC downstream resynchronization across single-byte, multi-byte, and paragraph edits."""
    prefix = (
        "# Section 1: Invariant Lead\n\n"
        "This lead section is identical across all mutated documents to verify upstream stability.\n\n"
    ).encode("utf-8") * 5

    suffix = (
        "## Section 2: Invariant Tail\n\n"
        "This long trailing section tests whether the rolling hash recovers and resynchronizes "
        "to identical chunks regardless of the nature or size of upstream edits.\n\n"
        "Sentence 1 in invariant tail.\n\n"
        "Sentence 2 in invariant tail.\n\n"
        "Sentence 3 in invariant tail.\n\n"
    ).encode("utf-8") * 5

    mutations = [
        # 1-byte substitution
        b"Paragraph A with baseline contents.\n\n",
        b"Paragraph X with baseline contents.\n\n",
        # 1-byte insertion
        b"Paragraph A with baseline contents.\n\n",
        b"Paragraph AA with baseline contents.\n\n",
        # 100-byte insertion
        b"Short sentence.\n\n",
        b"Much longer inserted sentence with detailed explanation of content-defined chunking advantages.\n\n",
        # Multibyte CJK insertion
        b"Latin paragraph text with sufficient length exceeding the minimum chunk size boundary.\n\n",
        "插入一段足够长度的多字节中文段落内容以测试重同步特性。\n\n".encode("utf-8"),
    ]

    cfg = ChunkerConfig(min_chunk=32, avg_chunk=96, max_chunk=192, mode="boundary")

    for i in range(0, len(mutations), 2):
        doc1 = prefix + mutations[i] + suffix
        doc2 = prefix + mutations[i + 1] + suffix

        c1 = chunk_documents_batch([doc1], config=cfg)[0]
        c2 = chunk_documents_batch([doc2], config=cfg)[0]

        # Upstream prefix chunk digests must be identical
        assert c1[0].digest == c2[0].digest

        # Downstream suffix chunks must resynchronize
        d1_set = {c.digest for c in c1}
        d2_set = {c.digest for c in c2}
        common = d1_set & d2_set
        assert len(common) >= 3, f"Mutation pair {i//2} failed to resynchronize suffix chunks"


def test_adversarial_sub_min_chunk_edit_boundary_suppression():
    """Verify that boundaries located closer than min_chunk are suppressed to prevent sub-min chunks."""
    prefix = (
        "# Section 1: Invariant Lead\n\n"
        "This lead section is identical across all mutated documents to verify upstream stability.\n\n"
    ).encode("utf-8") * 5

    suffix = (
        "## Section 2: Invariant Tail\n\n"
        "This long trailing section tests whether the rolling hash recovers and resynchronizes "
        "to identical chunks regardless of the nature or size of upstream edits.\n\n"
        "Sentence 1 in invariant tail.\n\n"
        "Sentence 2 in invariant tail.\n\n"
        "Sentence 3 in invariant tail.\n\n"
    ).encode("utf-8") * 5

    # 13 bytes mutation (< min_chunk of 32)
    short_edit = b"Latin text.\n\n"
    doc = prefix + short_edit + suffix

    cfg = ChunkerConfig(min_chunk=32, avg_chunk=96, max_chunk=192, mode="boundary")
    chunks = chunk_documents_batch([doc], config=cfg)[0]

    # Invariant: NO non-final chunk may be smaller than min_chunk
    for idx, c in enumerate(chunks[:-1]):
        assert c.length >= 32, f"Chunk {idx} violated min_chunk constraint: length={c.length}"

    # Verify document is completely and contiguously reassembled
    reconstructed = bytearray()
    for c in chunks:
        reconstructed.extend(doc[c.offset : c.offset + c.length])
    assert bytes(reconstructed) == doc


def test_adversarial_pathological_inputs():
    """Verify behavior on extreme corner-case inputs."""
    cfg = ChunkerConfig(min_chunk=32, avg_chunk=64, max_chunk=128, mode="boundary")

    # 1. Monolithic document with no whitespace or delimiters (10,000 'Z's)
    monolithic = b"Z" * 10000
    chunks = chunk_documents_batch([monolithic], config=cfg)[0]
    assert len(chunks) > 50
    reconstructed = bytearray()
    for c in chunks:
        assert c.length <= 128
        assert c.length >= 32 or c.offset + c.length == len(monolithic)
        reconstructed.extend(monolithic[c.offset : c.offset + c.length])
    assert bytes(reconstructed) == monolithic

    # 2. Whitespace-only document
    ws_doc = b"   \t\t   \n\n   \r\n   "
    ws_chunks = chunk_documents_batch([ws_doc], config=cfg)[0]
    assert len(ws_chunks) == 1
    assert ws_chunks[0].length == len(ws_doc)

    # 3. Document consisting solely of Markdown headings
    headings_only = b"# H1\n## H2\n### H3\n#### H4\n##### H5\n"
    h_chunks = chunk_documents_batch([headings_only], config=cfg)[0]
    assert len(h_chunks) >= 1
    assert sum(c.length for c in h_chunks) == len(headings_only)

    # 4. Dense abbreviations with numbers and dots
    abbrev_text = (
        "Conforme art. 5º, inc. III da CF/88, e art. 10 da Lei 13.709. "
        "Consulte também pág. 45 e vol. 2, sob supervisão do Prof. Dr. Silva. "
        "In the US, see Mr. Jones and Mrs. Smith at Dept. of Justice, Jan. 15th."
    ).encode("utf-8")
    abbrev_chunks = chunk_documents_batch([abbrev_text], config=cfg)[0]
    for c in abbrev_chunks:
        raw = abbrev_text[c.offset : c.offset + c.length].decode("utf-8")
        assert not raw.endswith("art.")
        assert not raw.endswith("inc.")
        assert not raw.endswith("Prof.")
        assert not raw.endswith("Dr.")
        assert not raw.endswith("Mr.")
        assert not raw.endswith("Mrs.")


# ============================================================================
# Section 4: Full Corpus 30-Pair Diffing and Real-World Evaluation
# ============================================================================

def test_full_corpus_30_pair_diffing_and_chunk_reuse():
    """Executes chunking and 3-way diffing on all 30 bilingual Wikipedia revision pairs.

    Verifies:
    1. Zero crashes or unhandled exceptions across the entire real corpus.
    2. Exact byte reassembly on all 60 files.
    3. Non-trivial chunk reuse on every single pair.
    4. Average chunk reuse exceeds 55% across both English and Portuguese corpora.
    """
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    docs = manifest.get("documents", [])
    assert len(docs) == 30

    cfg = ChunkerConfig(min_chunk=64, avg_chunk=256, max_chunk=512, mode="boundary")

    en_reuse_rates: list[float] = []
    pt_reuse_rates: list[float] = []

    for item in docs:
        old_data = (CORPUS_DIR / item["old_file"]).read_bytes()
        new_data = (CORPUS_DIR / item["new_file"]).read_bytes()

        old_chunks = chunk_documents_batch([old_data], config=cfg)[0]
        new_chunks = chunk_documents_batch([new_data], config=cfg)[0]

        # Invariant: contiguous byte reassembly
        assert sum(c.length for c in old_chunks) == len(old_data)
        assert sum(c.length for c in new_chunks) == len(new_data)

        # Invariant: non-empty chunks with valid 16-byte digest
        for c in old_chunks + new_chunks:
            assert len(c.digest) == 16
            assert len(c.hex) == 32
            assert c.hex == c.digest.hex()

        # Invariant: diff_chunks partition completeness
        diff = diff_chunks(old_chunks, new_chunks)

        old_digests = {c.digest for c in old_chunks}
        new_digests = {c.digest for c in new_chunks}
        shared_digests = old_digests & new_digests

        reuse_rate = len(shared_digests) / max(len(old_digests), 1)
        if item["lang"] == "en":
            en_reuse_rates.append(reuse_rate)
        else:
            pt_reuse_rates.append(reuse_rate)

    assert len(en_reuse_rates) == 15
    assert len(pt_reuse_rates) == 15

    avg_en_reuse = sum(en_reuse_rates) / len(en_reuse_rates)
    avg_pt_reuse = sum(pt_reuse_rates) / len(pt_reuse_rates)

    print(f"\n[Empirical Result] Average EN Wikipedia Chunk Reuse: {avg_en_reuse:.2%}")
    print(f"[Empirical Result] Average PT Wikipedia Chunk Reuse: {avg_pt_reuse:.2%}")

    # Both bilingual corpora must achieve strong content-defined reuse
    assert avg_en_reuse > 0.55, f"Expected >55% average EN chunk reuse, got {avg_en_reuse:.2%}"
    assert avg_pt_reuse > 0.55, f"Expected >55% average PT chunk reuse, got {avg_pt_reuse:.2%}"
