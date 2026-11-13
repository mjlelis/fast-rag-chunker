"""Tier 3: Cross-Feature Pairwise Interaction Tests.

Tests the orthogonal combination and interaction between independent features:
1. Boundary snapping + context windowing + cache_key
2. Unicode Normalization (NFC) + 128-bit BLAKE3 hash + heading metadata
3. Size unit (tokens) + tail redistribution + diff_chunks
4. Concurrency (num_threads=4) + boundary mode + structural metadata determinism
5. Whitespace normalization + boundary snapping + incremental diffing
6. Context windowing + normalization + cache key with context
7. Token sizing + heading hierarchy + context windowing
8. Abbreviation protection + dynamic snap window + tail merge
9. Diff chunks + context-aware cache keys + metadata shifts
10. Multi-threading + size unit (tokens) + multilingual CJK texts
"""

import pytest
import unicodedata
from tests.e2e.adapter import (
    ChunkerConfig,
    ChunkResult,
    chunk_documents_batch,
    chunker_fingerprint,
    cache_key,
    diff_chunks,
    resolve_snap_window,
)


def test_pairwise_boundary_context_and_cache_key():
    """Combines boundary snapping, sentence context extraction, and context-aware cache key."""
    doc = (
        "# Overview\n\n"
        "Initial sentence providing context. "
        "Second sentence acting as the core subject. "
        "Third sentence terminating the first section.\n\n"
        "## Details\n\n"
        "Fourth sentence introducing technical specifications. "
        "Fifth sentence concluding the document."
    ).encode("utf-8")

    cfg = ChunkerConfig(
        min_chunk=30,
        avg_chunk=60,
        max_chunk=120,
        mode="boundary",
        context_before=1,
        context_after=1,
    )
    chunks = chunk_documents_batch([doc], config=cfg)[0]
    assert len(chunks) >= 2

    # Verify that boundary snapping created a chunk starting with the heading line
    details_chunks = [
        c for c in chunks if doc[c.offset : c.offset + c.length].decode("utf-8").startswith("## Details")
    ]
    assert len(details_chunks) == 1
    details_chunk = details_chunks[0]
    assert "Details" in details_chunk.heading_path

    # Verify that context was captured
    assert len(chunks[1].context_before) > 0
    assert len(chunks[0].context_after) > 0

    # Verify cache key generation incorporates both chunk digest and context
    k_no_ctx = cache_key(chunks[1], "bge-m3", cfg, with_context=False)
    k_with_ctx = cache_key(chunks[1], "bge-m3", cfg, with_context=True)
    assert k_no_ctx != k_with_ctx
    assert k_with_ctx.startswith("frc:v0.3.0:")


def test_pairwise_nfc_normalization_blake3_and_headings():
    """Combines NFC normalization, 128-bit BLAKE3 content hash, and heading stack tracking."""
    # Compose text with both NFC and NFD representations under identical headings
    text_nfc = "# Seção de Verificação\n\nTexto com coração, ação e computação.\n"
    text_nfd = "# Seção de Verificação\n\n" + unicodedata.normalize("NFD", "Texto com coração, ação e computação.\n")

    doc_nfc = text_nfc.encode("utf-8")
    doc_nfd = text_nfd.encode("utf-8")

    cfg = ChunkerConfig(min_chunk=15, max_chunk=120, normalize="nfc")
    chunks_nfc = chunk_documents_batch([doc_nfc], config=cfg)[0]
    chunks_nfd = chunk_documents_batch([doc_nfd], config=cfg)[0]

    assert len(chunks_nfc) == 1
    assert len(chunks_nfd) == 1

    # Digests must match under NFC normalization despite different byte sequences
    assert chunks_nfc[0].digest == chunks_nfd[0].digest
    assert chunks_nfc[0].hex == chunks_nfd[0].hex

    # Verbatim offsets must match respective original byte arrays
    assert doc_nfc[chunks_nfc[0].offset : chunks_nfc[0].offset + chunks_nfc[0].length] == doc_nfc
    assert doc_nfd[chunks_nfd[0].offset : chunks_nfd[0].offset + chunks_nfd[0].length] == doc_nfd

    # Heading paths must be identical
    assert chunks_nfc[0].heading_path == ["Seção de Verificação"]
    assert chunks_nfd[0].heading_path == ["Seção de Verificação"]


def test_pairwise_token_size_unit_tail_redistribution_and_diff():
    """Combines token-based sizing, tail remainder redistribution, and 3-way vector diffing."""
    words_v1 = [f"word_{i}" for i in range(25)]
    words_v2 = [f"word_{i}" for i in range(25)]
    # Modify one word in v2
    words_v2[12] = "modified_word"

    doc_v1 = " ".join(words_v1).encode("utf-8")
    doc_v2 = " ".join(words_v2).encode("utf-8")

    cfg = ChunkerConfig(min_chunk=5, max_chunk=12, size_unit="tokens")
    chunks_v1 = chunk_documents_batch([doc_v1], config=cfg)[0]
    chunks_v2 = chunk_documents_batch([doc_v2], config=cfg)[0]

    # Verify hard token upper bound
    for c in chunks_v1 + chunks_v2:
        tok_count = len(doc_v1[c.offset : c.offset + c.length].decode("utf-8").split())
        assert tok_count <= 12

    # Perform diff
    diff = diff_chunks(chunks_v1, chunks_v2)
    # The modified chunk should appear in to_embed and old chunk in to_delete
    assert len(diff.to_embed) >= 1
    assert len(diff.to_delete) >= 1


def test_pairwise_threading_boundary_and_structural_determinism():
    """Combines multi-threaded batch execution, boundary snapping, and structural metadata determinism."""
    docs = [
        (
            f"# Document {i}\n\n"
            f"## Section Alpha\n\n"
            f"Paragraph content for document {i} with deterministic execution guarantees.\n\n"
            f"### Subsection Beta\n\n"
            f"Detailed content repeated to simulate substantial parallel payload size.\n\n"
        ).encode("utf-8")
        * 15
        for i in range(12)
    ]

    cfg = ChunkerConfig(min_chunk=32, avg_chunk=96, max_chunk=256, mode="boundary")

    res_single = chunk_documents_batch(docs, config=cfg, num_threads=1)
    res_multi = chunk_documents_batch(docs, config=cfg, num_threads=4)

    assert len(res_single) == len(res_multi) == 12

    for d_idx, (doc_s, doc_m) in enumerate(zip(res_single, res_multi)):
        assert len(doc_s) == len(doc_m)
        for c_idx, (cs, cm) in enumerate(zip(doc_s, doc_m)):
            assert cs.offset == cm.offset
            assert cs.length == cm.length
            assert cs.digest == cm.digest
            assert cs.hex == cm.hex
            assert cs.ordinal == cm.ordinal
            assert cs.heading_path == cm.heading_path


def test_pairwise_whitespace_normalization_and_diff_chunks():
    """Combines whitespace normalization with diffing: spacing edits should produce no new embeddings."""
    doc_clean = b"# Guide\n\nFirst paragraph here.\n\nSecond paragraph here.\n"
    doc_padded = b"# Guide\n\nFirst   paragraph   here.\r\n\r\nSecond  paragraph  here.\r\n"

    cfg = ChunkerConfig(min_chunk=10, max_chunk=80, normalize="whitespace")
    chunks_clean = chunk_documents_batch([doc_clean], config=cfg)[0]
    chunks_padded = chunk_documents_batch([doc_padded], config=cfg)[0]

    assert len(chunks_clean) == len(chunks_padded)
    for c1, c2 in zip(chunks_clean, chunks_padded):
        assert c1.digest == c2.digest

    # Diffing clean vs padded: identical digests mean zero to_embed calls!
    diff = diff_chunks(chunks_clean, chunks_padded)
    assert diff.to_embed == []
    assert diff.to_delete == []


def test_pairwise_context_window_and_normalization():
    """Combines context windowing with whitespace normalization and cache keys."""
    doc = (
        "First sentence context. "
        "Central chunk content   with   irregular   spaces. "
        "Trailing sentence context."
    ).encode("utf-8")

    cfg = ChunkerConfig(min_chunk=15, max_chunk=60, normalize="whitespace", context_before=1, context_after=1)
    chunks = chunk_documents_batch([doc], config=cfg)[0]
    assert len(chunks) >= 1
    target = chunks[0]
    k = cache_key(target, "embed-v1", cfg, with_context=True)
    assert k.startswith("frc:v0.3.0:")


def test_pairwise_token_sizing_and_nested_headings():
    """Combines token size units with deep heading paths."""
    doc = (
        "# Root\n\n"
        "## SubSection\n\n"
        "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu.\n"
    ).encode("utf-8")

    cfg = ChunkerConfig(min_chunk=3, max_chunk=8, size_unit="tokens")
    chunks = chunk_documents_batch([doc], config=cfg)[0]
    assert len(chunks) >= 1
    for c in chunks:
        assert "Root" in c.heading_path or "SubSection" in c.heading_path


def test_pairwise_abbreviations_and_proportional_snap_window():
    """Combines abbreviation guards with custom snap windows."""
    doc = (
        "The case referenced art. 5º and inc. I as key statutes. "
        "Furthermore, Dr. Watson corroborated the findings. "
        "The hearing was adjourned."
    ).encode("utf-8")

    # Set custom snap_window=45
    cfg = ChunkerConfig(min_chunk=20, avg_chunk=50, max_chunk=100, snap_window=45, mode="boundary")
    chunks = chunk_documents_batch([doc], config=cfg)[0]
    assert len(chunks) >= 1
    for c in chunks:
        t = doc[c.offset : c.offset + c.length].decode("utf-8")
        assert not t.endswith("art.")
        assert not t.endswith("inc.")
        assert not t.endswith("Dr.")


def test_pairwise_diff_chunks_with_context_aware_keys():
    """Combines 3-way diffing with context-aware cache keys."""
    c1_old = ChunkResult(
        offset=0, length=40, digest=b"\x01" * 16, hex="01" * 16, ordinal=0, context_after="Following A."
    )
    c1_new = ChunkResult(
        offset=0, length=40, digest=b"\x01" * 16, hex="01" * 16, ordinal=0, context_after="Following B."
    )
    cfg = ChunkerConfig(context_after=1)

    # Identical digest, but context shifted
    k_old = cache_key(c1_old, "model-x", cfg, with_context=True)
    k_new = cache_key(c1_new, "model-x", cfg, with_context=True)
    assert k_old != k_new


def test_pairwise_multithreading_tokens_and_cjk():
    """Combines multi-threading, token sizing, and CJK text processing."""
    cjk_docs = [
        (f"# 文档 {i}\n\n内容切分算法与自然语言处理系统测试。\n\n全角标点符号验证！").encode("utf-8")
        for i in range(8)
    ]
    cfg = ChunkerConfig(min_chunk=2, max_chunk=10, size_unit="tokens")
    res = chunk_documents_batch(cjk_docs, config=cfg, num_threads=4)
    assert len(res) == 8
    for doc_chunks in res:
        assert len(doc_chunks) >= 1
