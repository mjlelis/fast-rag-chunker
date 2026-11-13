import pytest

try:
    import fast_rag_chunker
    from fast_rag_chunker import (
        ChunkerConfig,
        cache_key,
        chunk_documents_batch,
        chunker_fingerprint,
        diff_chunks,
        resolve_snap_window,
    )
except ImportError:
    from tests.e2e.adapter import (
        ChunkerConfig,
        cache_key,
        chunk_documents_batch,
        chunker_fingerprint,
        diff_chunks,
        resolve_snap_window,
    )


def test_v03_priority_boundary_headings_and_context():
    doc = (
        "# Executive Summary\n\n"
        "First sentence of summary. Second sentence explaining architecture.\n\n"
        "## Technical Details\n\n"
        "Third sentence describing FastCDC. Fourth sentence with details.\n"
    ).encode("utf-8")

    cfg = ChunkerConfig(
        min_chunk=20,
        avg_chunk=60,
        max_chunk=120,
        mode="boundary",
        context_before=1,
        context_after=1,
    )
    results = chunk_documents_batch([doc], config=cfg)
    assert len(results) == 1
    chunks = results[0]
    assert len(chunks) >= 2

    # Verify sequential ordinals
    for idx, c in enumerate(chunks):
        assert c.ordinal == idx
        assert c.length > 0
        assert len(c.digest) == 16
        assert len(c.hex) == 32

    # Verify heading hierarchy
    tech_chunks = [c for c in chunks if "Technical Details" in c.heading_path]
    assert len(tech_chunks) >= 1
    assert tech_chunks[0].heading_path == ["Executive Summary", "Technical Details"]

    # Verify context windows
    assert chunks[0].context_before == ""
    assert len(chunks[0].context_after) > 0


def test_v03_diff_chunks_full_workflow():
    doc1 = (
        "# Section 1\n\n"
        "Stable paragraph 1 in document.\n\n"
        "# Section 2\n\n"
        "Paragraph 2 to be deleted.\n"
    ).encode("utf-8")

    doc2 = (
        "# Section 1\n\n"
        "Stable paragraph 1 in document.\n\n"
        "# Section 2\n\n"
        "Newly inserted replacement paragraph.\n"
    ).encode("utf-8")

    cfg = ChunkerConfig(min_chunk=16, avg_chunk=40, max_chunk=80, mode="boundary")
    chunks1 = chunk_documents_batch([doc1], config=cfg)[0]
    chunks2 = chunk_documents_batch([doc2], config=cfg)[0]

    diff = diff_chunks(chunks1, chunks2)
    to_embed, to_delete, to_meta = diff

    assert len(to_embed) >= 1
    assert len(to_delete) >= 1
    assert len(diff) == 3


def test_v03_pre_hash_normalization():
    doc_raw = b"Sample text with  multiple    spaces.\r\n"
    cfg_raw = ChunkerConfig(min_chunk=10, max_chunk=50, normalize="none")
    cfg_ws = ChunkerConfig(min_chunk=10, max_chunk=50, normalize="whitespace")

    c_raw = chunk_documents_batch([doc_raw], config=cfg_raw)[0][0]
    c_ws = chunk_documents_batch([doc_raw], config=cfg_ws)[0][0]

    # Offsets must reference original unnormalized text verbatim
    assert c_raw.offset == c_ws.offset == 0
    assert c_raw.length == c_ws.length == len(doc_raw)
    assert c_raw.digest != c_ws.digest


def test_v03_snap_window_resolution():
    assert resolve_snap_window(512, 64, 1024, None) == 77
    assert resolve_snap_window(512, 64, 1024, 128) == 128
