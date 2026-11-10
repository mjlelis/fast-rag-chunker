"""Pytest suite for the compiled `fast_rag_chunker` wheel (v0.1.1)."""

from __future__ import annotations
import warnings
import pytest
import fast_rag_chunker


def test_empty_batch_and_empty_document() -> None:
    assert fast_rag_chunker.chunk_documents_batch([]) == []
    res = fast_rag_chunker.chunk_documents_batch([b""])
    assert len(res) == 1
    assert res[0] == []


def test_contiguous_offset_coverage_and_non_empty() -> None:
    doc = (
        "Deterministic content-defined chunking with UTF-8 boundary snapping "
        "preserves natural sentences across document edits.\n"
    ).encode("utf-8") * 40

    for semantic_snap in (True, False):
        batch = fast_rag_chunker.chunk_documents_batch(
            [doc], min_chunk=64, max_chunk=256, semantic_snap=semantic_snap
        )
        assert len(batch) == 1
        chunks = batch[0]
        assert len(chunks) > 0, "Non-empty document must never return an empty chunk list"

        expected_offset = 0
        for idx, c in enumerate(chunks):
            assert c.offset == expected_offset
            assert c.length > 0
            assert c.length <= 256, f"Chunk {idx} exceeded max_chunk=256 (got {c.length})"
            if c.offset + c.length < len(doc):
                assert c.length >= 64, f"Non-final chunk {idx} below min_chunk=64 (got {c.length})"
            expected_offset += c.length

        assert expected_offset == len(doc)


def test_raw_mode_respects_max_chunk_below_1024() -> None:
    """R1.4: Verify raw mode honors max_chunk=512 without applying legacy C 1024-byte clamp."""
    doc = bytes((i * 1103515245 + 12345) >> 16 & 0xFF for i in range(8192))
    chunks = fast_rag_chunker.chunk_documents_batch(
        [doc], min_chunk=64, max_chunk=512, semantic_snap=False
    )[0]
    assert len(chunks) >= 16
    for c in chunks:
        assert c.length <= 512
        if c.offset + c.length < len(doc):
            assert c.length >= 64


def test_valid_utf8_per_chunk() -> None:
    doc = (
        "Arquitetura de Sistemas e Inteligência Artificial: pré-processamento semântico "
        "com FastCDC em Rust. Garante que palavras acentuadas como coração, ação, "
        "computação, soluções e eficiência nunca sejam cortadas ao meio na indexação RAG. 🚀\n"
    ).encode("utf-8") * 30

    chunks = fast_rag_chunker.chunk_documents_batch(
        [doc], min_chunk=64, max_chunk=256, semantic_snap=True
    )[0]
    assert len(chunks) > 10

    for c in chunks:
        piece = doc[c.offset : c.offset + c.length]
        decoded = piece.decode("utf-8")
        assert len(decoded) > 0
        assert c.hash != 0


def test_determinism_across_executions() -> None:
    docs = [
        ("Document A: " + "repeatable content-defined boundaries. " * 60).encode("utf-8"),
        ("Document B: " + "parallel Rayon execution across threads. " * 60).encode("utf-8"),
    ]
    run1 = fast_rag_chunker.chunk_documents_batch(docs, min_chunk=64, max_chunk=256)
    run2 = fast_rag_chunker.chunk_documents_batch(docs, min_chunk=64, max_chunk=256)

    assert len(run1) == len(run2)
    for c_list_1, c_list_2 in zip(run1, run2):
        tuples_1 = [(c.offset, c.length, c.hash) for c in c_list_1]
        tuples_2 = [(c.offset, c.length, c.hash) for c in c_list_2]
        assert tuples_1 == tuples_2


def test_invalid_parameters_raise_value_error() -> None:
    """R1.5 & R1.6: Invalid parameters raise ValueError with ChunkerError message."""
    docs = [b"non-empty document payload"]

    with pytest.raises(ValueError, match="min_chunk cannot be zero"):
        fast_rag_chunker.chunk_documents_batch(docs, min_chunk=0, max_chunk=512)

    with pytest.raises(ValueError, match="must be greater than or equal to min_chunk"):
        fast_rag_chunker.chunk_documents_batch(docs, min_chunk=512, max_chunk=64)

    with pytest.raises(ValueError, match="exceeds maximum supported limit"):
        fast_rag_chunker.chunk_documents_batch(docs, min_chunk=64, max_chunk=(1 << 30) + 1)


def test_mask_parameter_emits_deprecation_warning() -> None:
    """R1.3: Passing mask emits DeprecationWarning."""
    docs = [b"testing deprecated mask parameter warning"]

    with pytest.warns(DeprecationWarning, match="mask"):
        res = fast_rag_chunker.chunk_documents_batch(
            docs, min_chunk=64, max_chunk=512, mask=0x1F
        )
    assert len(res) == 1
    assert len(res[0]) == 1

    # Calling without mask must not emit DeprecationWarning
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", DeprecationWarning)
        fast_rag_chunker.chunk_documents_batch(docs, min_chunk=64, max_chunk=512)
        dep_warnings = [w for w in recorded if issubclass(w.category, DeprecationWarning)]
        assert len(dep_warnings) == 0
