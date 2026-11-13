import pytest

try:
    import fast_rag_chunker
    from fast_rag_chunker import ChunkerConfig, cache_key, chunk_documents_batch, chunker_fingerprint
except ImportError:
    from tests.e2e.adapter import (
        ChunkerConfig,
        cache_key,
        chunk_documents_batch,
        chunker_fingerprint,
    )


def test_contiguous_offsets_and_valid_utf8():
    doc = (
        "Arquitetura de Sistemas e Inteligência Artificial: pré-processamento semântico "
        "com FastCDC em Rust. Garante que palavras acentuadas como coração, ação, "
        "computação, ciência e eficiência nunca sejam cortadas ao meio durante a indexação RAG. "
        " emojis: 🚀🦀🐍 e caracteres CJK: 机器学习与人工智能。\n"
    ).encode("utf-8") * 25

    batch_results = chunk_documents_batch(
        [doc],
        min_chunk=64,
        max_chunk=256,
        mode="semantic",
    )
    assert len(batch_results) == 1
    chunks = batch_results[0]
    assert len(chunks) > 10

    expected_offset = 0
    reconstructed = bytearray()
    for idx, c in enumerate(chunks):
        assert c.offset == expected_offset, f"Gap or overlap at chunk {idx}"
        assert c.length > 0
        assert c.length <= 256, f"Chunk {idx} exceeded max_chunk: {c.length}"
        if c.offset + c.length < len(doc):
            assert c.length >= 64, f"Non-final chunk {idx} below min_chunk: {c.length}"

        raw_slice = doc[c.offset : c.offset + c.length]
        decoded = raw_slice.decode("utf-8")
        assert len(decoded) > 0
        assert isinstance(c.digest, bytes)
        assert len(c.digest) == 16
        assert c.digest != b"\x00" * 16
        assert c.hex == c.digest.hex()
        assert len(c.hex) == 32

        reconstructed.extend(raw_slice)
        expected_offset += c.length

    assert expected_offset == len(doc)
    assert bytes(reconstructed) == doc


def test_raw_mode_respects_bounds_and_computes_hash():
    doc = bytes((i * 73 + 19) % 256 for i in range(8192))
    batch_results = chunk_documents_batch(
        [doc],
        min_chunk=64,
        max_chunk=512,
        mode="raw",
        compute_hash=True,
    )
    chunks = batch_results[0]
    assert len(chunks) > 5

    expected_offset = 0
    for idx, c in enumerate(chunks):
        assert c.offset == expected_offset
        assert c.length <= 512, f"Raw chunk {idx} length {c.length} exceeded max_chunk=512"
        if c.offset + c.length < len(doc):
            assert c.length >= 64, f"Non-final raw chunk {idx} length {c.length} < min_chunk=64"
        assert isinstance(c.digest, bytes)
        assert len(c.digest) == 16
        assert c.digest != b"\x00" * 16
        assert c.hex == c.digest.hex()
        expected_offset += c.length

    assert expected_offset == len(doc)


def test_compute_hash_false_disables_digest():
    doc = b"Disabling hash computation sets 16-byte digest to all zeros. " * 20
    for mode in ("raw", "semantic"):
        chunks = chunk_documents_batch(
            [doc],
            min_chunk=64,
            max_chunk=256,
            mode=mode,
            compute_hash=False,
        )[0]
        assert len(chunks) >= 2
        for c in chunks:
            assert c.digest == b"\x00" * 16
            assert c.hex == "0" * 32


def test_mask_parameter_removed_raises_type_error():
    doc = b"Passing removed mask parameter must raise TypeError in v0.2.0."
    with pytest.raises(TypeError):
        chunk_documents_batch([doc], min_chunk=16, max_chunk=64, mask=0x03)


def test_chunker_config_and_cache_key_isolation():
    doc = b"Paragraph for verifying ChunkerConfig, chunker_fingerprint, and cache_key. " * 10
    cfg_a = ChunkerConfig(min_chunk=64, avg_chunk=128, max_chunk=256, mode="semantic")
    cfg_b = ChunkerConfig(min_chunk=64, avg_chunk=192, max_chunk=256, mode="semantic")
    cfg_raw = ChunkerConfig(min_chunk=64, avg_chunk=128, max_chunk=256, mode="raw")

    fp_a = chunker_fingerprint(cfg_a)
    fp_b = chunker_fingerprint(cfg_b)
    fp_raw = chunker_fingerprint(cfg_raw)
    assert fp_a == cfg_a.fingerprint()
    assert fp_a != fp_b
    assert fp_a != fp_raw

    chunks = chunk_documents_batch([doc], config=cfg_a)[0]
    first_chunk = chunks[0]

    k1 = cache_key(first_chunk, "text-embedding-3-small", cfg_a)
    k2 = cache_key(first_chunk, "text-embedding-3-large", cfg_a)
    k3 = cache_key(first_chunk, "text-embedding-3-small", cfg_b)
    k4 = cache_key(first_chunk, "text-embedding-3-small", cfg_raw)

    assert k1 != k2, "Changing embedding model_id must change cache_key"
    assert k1 != k3, "Changing avg_chunk must change cache_key"
    assert k1 != k4, "Changing mode must change cache_key"

    # Calling cache_key when compute_hash=False must raise ValueError
    cfg_no_hash = ChunkerConfig(
        min_chunk=64, avg_chunk=128, max_chunk=256, mode="semantic", compute_hash=False
    )
    unhashed_chunk = chunk_documents_batch([doc], config=cfg_no_hash)[0][0]
    with pytest.raises(ValueError, match="digest"):
        cache_key(unhashed_chunk, "text-embedding-3-small", cfg_a)
    with pytest.raises(ValueError, match="compute_hash"):
        cache_key(first_chunk, "text-embedding-3-small", cfg_no_hash)


def test_invalid_parameters_raise_value_error():
    doc = b"Valid non-empty document payload."

    with pytest.raises(ValueError, match="greater than 0"):
        chunk_documents_batch([doc], min_chunk=0, max_chunk=512)

    with pytest.raises(ValueError, match="cannot be greater than maximum"):
        chunk_documents_batch([doc], min_chunk=1024, max_chunk=512)

    with pytest.raises(ValueError, match="Average chunk size"):
        chunk_documents_batch([doc], min_chunk=64, avg_chunk=32, max_chunk=512)

    with pytest.raises(ValueError, match="exceeds maximum supported limit"):
        chunk_documents_batch([doc], min_chunk=64, max_chunk=(1 << 30) + 1)

    with pytest.raises(ValueError, match="num_threads"):
        chunk_documents_batch([doc], min_chunk=64, max_chunk=256, num_threads=0)


def test_num_threads_and_determinism():
    docs = [
        f"Document {i}: Deterministic parallel Rayon execution check across runs.\n".encode("utf-8")
        * 40
        for i in range(8)
    ]

    run_single = chunk_documents_batch(docs, min_chunk=64, max_chunk=256, num_threads=1)
    run_multi = chunk_documents_batch(docs, min_chunk=64, max_chunk=256, num_threads=4)
    run_default = chunk_documents_batch(docs, min_chunk=64, max_chunk=256, num_threads=None)

    assert len(run_single) == len(docs)
    for d_single, d_multi, d_def in zip(run_single, run_multi, run_default):
        assert len(d_single) == len(d_multi) == len(d_def)
        for c1, c2, c3 in zip(d_single, d_multi, d_def):
            assert (c1.offset, c1.length, c1.digest, c1.hex) == (
                c2.offset,
                c2.length,
                c2.digest,
                c2.hex,
            )
            assert (c1.offset, c1.length, c1.digest, c1.hex) == (
                c3.offset,
                c3.length,
                c3.digest,
                c3.hex,
            )


def test_empty_batch_and_empty_document():
    assert chunk_documents_batch([]) == []
    assert chunk_documents_batch([b""]) == [[]]
    non_empty = chunk_documents_batch([b"single chunk"])
    assert len(non_empty) == 1
    assert len(non_empty[0]) == 1
    assert non_empty[0][0].offset == 0
    assert non_empty[0][0].length == len(b"single chunk")
