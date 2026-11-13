"""Tier 1: Comprehensive Feature Coverage Tests (>= 5 tests per feature).

Covers:
- R2.8: 128-bit BLAKE3 hash, chunk.digest, chunk.hex, compute_hash=False
- R2.9: chunker_fingerprint(config), cache_key(chunk, model_id, config)
- R2.10: ChunkerConfig parameter validation
- R2.12: num_threads parameter and deterministic output
- R3.1: Priority boundaries (Heading > Blank line > Sentence > Word > Codepoint)
- R3.2: UAX #29 sentence segmentation with PT/EN abbreviation filtering and CJK
- R3.3: Configurable snap window proportional to avg_chunk
- R3.4: Tail remainder handling (< min_chunk) via merge or balanced redistribution
- R3.5: Size unit (bytes vs tokens) and hard max_tokens guarantee
- R3.6: Pre-hash normalization (none, whitespace, nfc) preserving verbatim offsets
- R3.7: Structural metadata (heading_path stack and ordinal indexing)
- R3.8: Sentence context windowing and context-aware cache keys
- R3.9: Incremental chunk diffing (diff_chunks)
- R3.11: Mode rename to boundary/boundary_aware and deprecation warnings
"""

import pytest
import warnings
from tests.e2e.adapter import (
    ChunkerConfig,
    ChunkResult,
    chunk_documents_batch,
    chunker_fingerprint,
    cache_key,
    diff_chunks,
    resolve_snap_window,
)


# ============================================================================
# R2.8: 128-bit BLAKE3 hash, chunk.digest, chunk.hex, compute_hash=False
# ============================================================================

def test_r2_8_digest_length_and_type():
    doc = b"Testing 128-bit truncated BLAKE3 digest type and byte length invariants."
    chunks = chunk_documents_batch([doc], min_chunk=16, max_chunk=64, compute_hash=True)[0]
    assert len(chunks) >= 1
    for c in chunks:
        assert isinstance(c.digest, bytes)
        assert len(c.digest) == 16, f"Expected 16-byte digest, got {len(c.digest)}"


def test_r2_8_hex_matches_digest_hexdigest():
    doc = b"Verifying hexadecimal string representation against digest.hex()."
    chunks = chunk_documents_batch([doc], min_chunk=16, max_chunk=64, compute_hash=True)[0]
    for c in chunks:
        assert isinstance(c.hex, str)
        assert len(c.hex) == 32
        assert c.hex == c.digest.hex()
        assert c.hex == c.hex.lower()


def test_r2_8_compute_hash_true_nonzero():
    doc = b"Non-trivial document content ensuring non-zero cryptographic digest generation." * 4
    chunks = chunk_documents_batch([doc], min_chunk=32, max_chunk=128, compute_hash=True)[0]
    for c in chunks:
        assert c.digest != b"\x00" * 16
        assert c.hex != "0" * 32


def test_r2_8_compute_hash_false_all_zeros():
    doc = b"When compute_hash is disabled, digest must be all zeros and hex 32 zeros." * 4
    chunks = chunk_documents_batch([doc], min_chunk=32, max_chunk=128, compute_hash=False)[0]
    for c in chunks:
        assert c.digest == b"\x00" * 16
        assert c.hex == "0" * 32


def test_r2_8_deterministic_digest_across_identical_chunks():
    doc = b"Deterministic chunk digest reproducibility check across isolated batch invocations."
    run1 = chunk_documents_batch([doc], min_chunk=16, max_chunk=64, compute_hash=True)[0]
    run2 = chunk_documents_batch([doc], min_chunk=16, max_chunk=64, compute_hash=True)[0]
    assert len(run1) == len(run2)
    for c1, c2 in zip(run1, run2):
        assert c1.digest == c2.digest
        assert c1.hex == c2.hex


def test_r2_8_different_content_produces_different_digest():
    doc_a = b"First distinct document slice for hash collision verification."
    doc_b = b"Second distinct document slice for hash collision verification."
    chunk_a = chunk_documents_batch([doc_a], min_chunk=16, max_chunk=128)[0][0]
    chunk_b = chunk_documents_batch([doc_b], min_chunk=16, max_chunk=128)[0][0]
    assert chunk_a.digest != chunk_b.digest
    assert chunk_a.hex != chunk_b.hex


# ============================================================================
# R2.9: Fingerprint & Cache Key
# ============================================================================

def test_r2_9_fingerprint_deterministic():
    cfg1 = ChunkerConfig(min_chunk=64, avg_chunk=128, max_chunk=256, mode="boundary")
    cfg2 = ChunkerConfig(min_chunk=64, avg_chunk=128, max_chunk=256, mode="boundary")
    assert chunker_fingerprint(cfg1) == chunker_fingerprint(cfg2)
    assert cfg1.fingerprint() == cfg2.fingerprint()


def test_r2_9_fingerprint_changes_on_parameter_delta():
    base = ChunkerConfig(min_chunk=64, avg_chunk=128, max_chunk=256, mode="boundary")
    diff_min = ChunkerConfig(min_chunk=32, avg_chunk=128, max_chunk=256, mode="boundary")
    diff_avg = ChunkerConfig(min_chunk=64, avg_chunk=192, max_chunk=256, mode="boundary")
    diff_mode = ChunkerConfig(min_chunk=64, avg_chunk=128, max_chunk=256, mode="raw")

    fp_base = chunker_fingerprint(base)
    assert fp_base != chunker_fingerprint(diff_min)
    assert fp_base != chunker_fingerprint(diff_avg)
    assert fp_base != chunker_fingerprint(diff_mode)


def test_r2_9_cache_key_incorporates_model_id():
    doc = b"Verifying model_id namespace separation in cache keys."
    chunk = chunk_documents_batch([doc], min_chunk=16, max_chunk=128)[0][0]
    cfg = ChunkerConfig(min_chunk=16, max_chunk=128)

    k1 = cache_key(chunk, "text-embedding-3-small", cfg)
    k2 = cache_key(chunk, "text-embedding-3-large", cfg)
    k3 = cache_key(chunk, "bge-m3", cfg)

    assert k1 != k2
    assert k1 != k3
    assert k2 != k3
    assert k1.startswith("frc:v0.3.0:")


def test_r2_9_cache_key_incorporates_chunk_digest():
    doc1 = b"First chunk content for cache key generation."
    doc2 = b"Second chunk content for cache key generation."
    c1 = chunk_documents_batch([doc1], min_chunk=16, max_chunk=128)[0][0]
    c2 = chunk_documents_batch([doc2], min_chunk=16, max_chunk=128)[0][0]
    cfg = ChunkerConfig(min_chunk=16, max_chunk=128)

    k1 = cache_key(c1, "text-embedding-3-small", cfg)
    k2 = cache_key(c2, "text-embedding-3-small", cfg)
    assert k1 != k2


def test_r2_9_cache_key_raises_on_unhashed_chunk():
    doc = b"Document chunked without hash computation."
    chunk_no_hash = chunk_documents_batch([doc], min_chunk=16, max_chunk=128, compute_hash=False)[0][0]
    cfg = ChunkerConfig(min_chunk=16, max_chunk=128)

    with pytest.raises(ValueError, match="all-zero"):
        cache_key(chunk_no_hash, "text-embedding-3-small", cfg)


def test_r2_9_cache_key_raises_on_compute_hash_false_config():
    doc = b"Document chunked with hash, but evaluated under unhashed config."
    chunk = chunk_documents_batch([doc], min_chunk=16, max_chunk=128, compute_hash=True)[0][0]
    cfg_no_hash = ChunkerConfig(min_chunk=16, max_chunk=128, compute_hash=False)

    with pytest.raises(ValueError, match="compute_hash"):
        cache_key(chunk, "text-embedding-3-small", cfg_no_hash)


# ============================================================================
# R2.10: ChunkerConfig Parameter Validation
# ============================================================================

def test_r2_10_min_chunk_zero_or_negative_raises_error():
    with pytest.raises(ValueError, match="greater than 0"):
        ChunkerConfig(min_chunk=0, max_chunk=256)
    with pytest.raises(ValueError, match="greater than 0"):
        ChunkerConfig(min_chunk=-16, max_chunk=256)


def test_r2_10_min_greater_than_max_raises_error():
    with pytest.raises(ValueError, match="cannot be greater than maximum"):
        ChunkerConfig(min_chunk=512, max_chunk=256)


def test_r2_10_avg_chunk_out_of_bounds_raises_error():
    with pytest.raises(ValueError, match="Average chunk size"):
        ChunkerConfig(min_chunk=64, avg_chunk=32, max_chunk=256)
    with pytest.raises(ValueError, match="Average chunk size"):
        ChunkerConfig(min_chunk=64, avg_chunk=512, max_chunk=256)


def test_r2_10_max_chunk_exceeds_limit_raises_error():
    with pytest.raises(ValueError, match="exceeds maximum supported limit"):
        ChunkerConfig(min_chunk=64, max_chunk=1_073_741_825)


def test_r2_10_mask_parameter_removed_raises_type_error():
    with pytest.raises(TypeError, match="unexpected keyword argument 'mask'"):
        ChunkerConfig(min_chunk=64, max_chunk=256, mask=0x03)  # type: ignore[call-arg]


def test_r2_10_valid_config_constructs_properly():
    cfg = ChunkerConfig(min_chunk=64, avg_chunk=128, max_chunk=256, mode="boundary", compute_hash=True)
    assert cfg.min_chunk == 64
    assert cfg.avg_chunk == 128
    assert cfg.max_chunk == 256
    assert cfg.mode == "boundary"
    assert cfg.compute_hash is True


# ============================================================================
# R2.12: Concurrency & Rayon Determinism
# ============================================================================

def test_r2_12_single_thread_execution():
    docs = [f"Batch item {i} execution check.\n".encode("utf-8") * 20 for i in range(5)]
    res = chunk_documents_batch(docs, min_chunk=32, max_chunk=128, num_threads=1)
    assert len(res) == 5
    for doc_chunks in res:
        assert len(doc_chunks) >= 1


def test_r2_12_multi_thread_execution():
    docs = [f"Batch item {i} multi-thread check.\n".encode("utf-8") * 20 for i in range(8)]
    res = chunk_documents_batch(docs, min_chunk=32, max_chunk=128, num_threads=4)
    assert len(res) == 8
    for doc_chunks in res:
        assert len(doc_chunks) >= 1


def test_r2_12_thread_count_zero_raises_error():
    docs = [b"Invalid thread count check."]
    with pytest.raises(ValueError, match="num_threads must be >= 1"):
        chunk_documents_batch(docs, min_chunk=16, max_chunk=64, num_threads=0)


def test_r2_12_deterministic_output_across_thread_counts():
    docs = [f"Deterministic output check doc {i}.\n".encode("utf-8") * 30 for i in range(6)]
    res_t1 = chunk_documents_batch(docs, min_chunk=32, max_chunk=128, num_threads=1)
    res_t4 = chunk_documents_batch(docs, min_chunk=32, max_chunk=128, num_threads=4)
    res_def = chunk_documents_batch(docs, min_chunk=32, max_chunk=128, num_threads=None)

    assert len(res_t1) == len(res_t4) == len(res_def)
    for d1, d4, d_def in zip(res_t1, res_t4, res_def):
        assert len(d1) == len(d4) == len(d_def)
        for c1, c4, c_def in zip(d1, d4, d_def):
            assert (c1.offset, c1.length, c1.digest, c1.hex) == (c4.offset, c4.length, c4.digest, c4.hex)
            assert (c1.offset, c1.length, c1.digest, c1.hex) == (c_def.offset, c_def.length, c_def.digest, c_def.hex)


def test_r2_12_none_threads_uses_default_pool():
    docs = [b"Default thread pool behavior execution check." * 5]
    res = chunk_documents_batch(docs, min_chunk=16, max_chunk=64, num_threads=None)
    assert len(res) == 1
    assert len(res[0]) >= 1


# ============================================================================
# R3.1: Priority Boundary Model
# ============================================================================

def test_r3_1_priority1_markdown_heading_takes_precedence():
    doc = (
        "Paragraph body content before the section title. This is descriptive text.\n"
        "# New Major Heading\n"
        "This is the start of the next section."
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=32, avg_chunk=70, max_chunk=150, mode="boundary")[0]
    assert len(chunks) >= 2
    # The second chunk must start with the heading line
    second_chunk_text = doc[chunks[1].offset : chunks[1].offset + chunks[1].length].decode("utf-8")
    assert second_chunk_text.startswith("# New Major Heading")


def test_r3_1_priority2_blank_line_takes_precedence_over_sentence():
    doc = (
        "First sentence of paragraph. Second sentence of paragraph.\n\n"
        "Third sentence located in paragraph two. Fourth sentence follows."
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=30, avg_chunk=65, max_chunk=140, mode="boundary")[0]
    assert len(chunks) >= 2
    second_chunk_text = doc[chunks[1].offset : chunks[1].offset + chunks[1].length].decode("utf-8")
    assert second_chunk_text.startswith("Third sentence")


def test_r3_1_priority3_sentence_end_takes_precedence_over_word():
    doc = (
        "Sentence number one terminates here. Sentence number two continues with regular words."
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=20, avg_chunk=40, max_chunk=90, mode="boundary")[0]
    assert len(chunks) >= 2
    first_chunk_text = doc[chunks[0].offset : chunks[0].offset + chunks[0].length].decode("utf-8")
    assert first_chunk_text.endswith(".") or first_chunk_text.endswith(". ")


def test_r3_1_priority4_word_boundary_takes_precedence_over_codepoint():
    doc = b"Supercalifragilisticexpialidocious words should be kept intact whenever possible in chunking."
    chunks = chunk_documents_batch([doc], min_chunk=20, avg_chunk=40, max_chunk=80, mode="boundary")[0]
    assert len(chunks) >= 2
    first_chunk_slice = doc[chunks[0].offset : chunks[0].offset + chunks[0].length]
    assert not first_chunk_slice.endswith(b"Supercali")  # Shouldn't cut within long word if space available


def test_r3_1_priority5_utf8_codepoint_fallback_never_slices_multibyte():
    doc = "Emojis 🚀🦀🐍 e caracteres acentuados ação coração ciência.".encode("utf-8") * 5
    chunks = chunk_documents_batch([doc], min_chunk=32, avg_chunk=64, max_chunk=128, mode="boundary")[0]
    for c in chunks:
        raw_slice = doc[c.offset : c.offset + c.length]
        # Must decode without UnicodeDecodeError
        decoded = raw_slice.decode("utf-8")
        assert len(decoded) > 0


def test_r3_1_local_content_preservation():
    p1 = "First stable paragraph of the document that remains untouched across edits.\n\n"
    p2_v1 = "Second paragraph version A before modification was introduced.\n\n"
    p2_v2 = "Second paragraph version B with localized modifications applied.\n\n"
    p3 = "Third stable paragraph positioned downstream in the document.\n\n"

    doc_v1 = (p1 + p2_v1 + p3).encode("utf-8")
    doc_v2 = (p1 + p2_v2 + p3).encode("utf-8")

    chunks_v1 = chunk_documents_batch([doc_v1], min_chunk=32, avg_chunk=70, max_chunk=150)[0]
    chunks_v2 = chunk_documents_batch([doc_v2], min_chunk=32, avg_chunk=70, max_chunk=150)[0]

    # First chunk must match exactly
    assert chunks_v1[0].digest == chunks_v2[0].digest


# ============================================================================
# R3.2: UAX #29 Sentence Segmentation & Abbreviation Filtering
# ============================================================================

def test_r3_2_english_abbreviations_not_cut():
    doc = (
        "Dr. Smith visited the hospital yesterday. "
        "The committee reviewed e.g. financial statements and vs. competitors. "
        "All items were approved."
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=16, avg_chunk=45, max_chunk=95, mode="boundary")[0]
    first_chunk_text = doc[chunks[0].offset : chunks[0].offset + chunks[0].length].decode("utf-8")
    # Must not cut immediately after "Dr."
    assert "Dr. Smith" in first_chunk_text or not first_chunk_text.endswith("Dr.")


def test_r3_2_portuguese_abbreviations_not_cut():
    doc = (
        "O art. 5 da Constituição assegura direitos fundamentais. "
        "Conforme o inc. I, a igualdade é garantida. "
        "O Prof. Silva leciona direito constitucional."
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=16, avg_chunk=45, max_chunk=95, mode="boundary")[0]
    first_chunk_text = doc[chunks[0].offset : chunks[0].offset + chunks[0].length].decode("utf-8")
    assert not first_chunk_text.endswith("art.")
    assert not first_chunk_text.endswith("inc.")


def test_r3_2_cjk_punctuation_sentence_boundary():
    doc = "这是第一句中文内容。这是第二句中文内容！最后一句内容？".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, avg_chunk=30, max_chunk=60, mode="boundary")[0]
    assert len(chunks) >= 2
    first_chunk_text = doc[chunks[0].offset : chunks[0].offset + chunks[0].length].decode("utf-8")
    assert first_chunk_text.endswith("。") or first_chunk_text.endswith("！")


def test_r3_2_unicode_spaces_handled():
    # Non-breaking space \u00A0 and ideographic space \u3000
    doc = "Palavra1\u00a0Palavra2\u3000Palavra3\u2009Palavra4 termina aqui.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, avg_chunk=25, max_chunk=50, mode="boundary")[0]
    assert len(chunks) >= 1
    # Decodes without error
    for c in chunks:
        assert len(doc[c.offset : c.offset + c.length].decode("utf-8")) > 0


def test_r3_2_trailing_quotes_and_brackets_preserved():
    doc = 'Ele declarou: "Esta é a regra." E depois saiu da sala.'.encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    assert len(chunks) >= 1


def test_r3_2_multilingual_mixed_sentence_segmentation():
    doc = (
        "First sentence in English. "
        "Segunda sentença em português do Brasil com acentuação. "
        "第三句是包含全角标点的中文。"
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=20, avg_chunk=50, max_chunk=100, mode="boundary")[0]
    assert len(chunks) >= 2


# ============================================================================
# R3.3: Configurable Snap Window
# ============================================================================

def test_r3_3_snap_window_none_resolves_proportional_default():
    # 15% of avg_chunk=512 is ~77
    resolved = resolve_snap_window(avg_chunk=512, min_chunk=64, max_chunk=1024, user_snap=None)
    assert 70 <= resolved <= 85


def test_r3_3_explicit_snap_window_respected():
    resolved = resolve_snap_window(avg_chunk=512, min_chunk=64, max_chunk=1024, user_snap=120)
    assert resolved == 120


def test_r3_3_snap_window_minimum_clamped_to_32():
    # 15% of avg_chunk=100 is 15 -> clamped to 32
    resolved = resolve_snap_window(avg_chunk=100, min_chunk=32, max_chunk=200, user_snap=None)
    assert resolved == 32


def test_r3_3_snap_window_upper_bound_clamped():
    # max allowed is (max - min) // 2 = (120 - 64) // 2 = 28 -> clamped to max(32, 28) = 32
    resolved = resolve_snap_window(avg_chunk=100, min_chunk=64, max_chunk=120, user_snap=None)
    assert resolved == 32


def test_r3_3_large_avg_chunk_scales_window_proportionally():
    # 15% of avg_chunk=2048 is ~307
    resolved = resolve_snap_window(avg_chunk=2048, min_chunk=256, max_chunk=4096, user_snap=None)
    assert 300 <= resolved <= 315


# ============================================================================
# R3.4: Tail Remainder Handling
# ============================================================================

def test_r3_4_zero_remainder_clean_termination():
    doc = b"a" * 256
    chunks = chunk_documents_batch([doc], min_chunk=64, avg_chunk=128, max_chunk=256, mode="raw")[0]
    total_len = sum(c.length for c in chunks)
    assert total_len == 256


def test_r3_4_remainder_greater_than_min_chunk_emits_independently():
    doc = b"x" * 150
    chunks = chunk_documents_batch([doc], min_chunk=40, avg_chunk=80, max_chunk=100, mode="raw")[0]
    assert len(chunks) == 2
    assert chunks[1].length >= 40


def test_r3_4_single_chunk_document_emitted_when_short():
    doc = b"Short document."
    chunks = chunk_documents_batch([doc], min_chunk=64, max_chunk=256)[0]
    assert len(chunks) == 1
    assert chunks[0].length == len(doc)
    assert chunks[0].offset == 0


def test_r3_4_small_remainder_merged_into_previous_chunk():
    # L_prev + remainder <= max_chunk
    doc = b"Initial body segment that fills most of the chunk. " + b"tiny tail"
    chunks = chunk_documents_batch([doc], min_chunk=32, avg_chunk=60, max_chunk=200, mode="raw")[0]
    assert len(chunks) == 1
    assert chunks[0].length == len(doc)


def test_r3_4_small_remainder_balanced_redistribution_when_merge_exceeds_max():
    # Construct input where prev chunk + tail > max_chunk
    # Combined length 140, max_chunk 100, min_chunk 30
    doc = b"a" * 135
    chunks = chunk_documents_batch([doc], min_chunk=30, avg_chunk=95, max_chunk=100, mode="raw")[0]
    assert len(chunks) == 2
    for c in chunks:
        assert c.length >= 30, f"Chunk below min_chunk: {c.length}"
        assert c.length <= 100, f"Chunk exceeded max_chunk: {c.length}"
    assert sum(c.length for c in chunks) == len(doc)


def test_r3_4_tail_merge_recomputes_digest():
    doc1 = b"Common initial body prefix. "
    doc2 = doc1 + b"small tail"
    c1 = chunk_documents_batch([doc1], min_chunk=32, max_chunk=200)[0][0]
    c2 = chunk_documents_batch([doc2], min_chunk=32, max_chunk=200)[0][0]
    assert c1.length != c2.length
    assert c1.digest != c2.digest


# ============================================================================
# R3.5: Dual Size Units & Hard max_tokens Guarantee
# ============================================================================

def test_r3_5_size_unit_bytes_is_default():
    cfg = ChunkerConfig()
    assert cfg.size_unit == "bytes"


def test_r3_5_size_unit_tokens_accepted():
    cfg = ChunkerConfig(size_unit="tokens", min_chunk=10, max_chunk=50)
    assert cfg.size_unit == "tokens"


def test_r3_5_hard_max_tokens_guarantee():
    # 200 words document
    words = [f"token_{i}" for i in range(200)]
    doc = " ".join(words).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=30, size_unit="tokens")[0]
    assert len(chunks) >= 5
    for c in chunks:
        chunk_text = doc[c.offset : c.offset + c.length].decode("utf-8")
        tok_count = len(chunk_text.split())
        assert tok_count <= 30, f"Exceeded max_tokens limit: {tok_count} > 30"


def test_r3_5_invalid_size_unit_raises_error():
    with pytest.raises(ValueError, match="Invalid size_unit"):
        ChunkerConfig(size_unit="characters")


def test_r3_5_token_unit_chunks_align_with_word_spans():
    doc = b"One two three four five six seven eight nine ten."
    chunks = chunk_documents_batch([doc], min_chunk=2, max_chunk=5, size_unit="tokens")[0]
    assert len(chunks) >= 2
    for c in chunks:
        slice_text = doc[c.offset : c.offset + c.length].decode("utf-8")
        # Slices shouldn't split inside a token
        assert not slice_text.startswith("ne ")
        assert not slice_text.startswith("wo ")


# ============================================================================
# R3.6: Pre-Hash Normalization Preserving Verbatim Offsets
# ============================================================================

def test_r3_6_normalize_none_computes_raw_hash():
    doc = b"Raw text with \r\n and  multiple   spaces."
    chunk = chunk_documents_batch([doc], min_chunk=16, max_chunk=128, normalize="none")[0][0]
    assert chunk.offset == 0
    assert chunk.length == len(doc)
    assert doc[chunk.offset : chunk.offset + chunk.length] == doc


def test_r3_6_normalize_whitespace_collapses_spaces_and_crlf():
    doc1 = b"Text with standard spaces.\n"
    doc2 = b"Text   with   standard  spaces.\r\n"
    c1 = chunk_documents_batch([doc1], min_chunk=10, max_chunk=100, normalize="whitespace")[0][0]
    c2 = chunk_documents_batch([doc2], min_chunk=10, max_chunk=100, normalize="whitespace")[0][0]
    assert c1.digest == c2.digest


def test_r3_6_normalize_nfc_reconciles_canonical_decomposition():
    # Composed ç (\u00e7) vs decomposed c + combining cedilla (\u0063\u0327)
    doc_nfc = "Ação e computação.".encode("utf-8")
    doc_nfd = "Ac\u0327a\u0303o e computac\u0327a\u0303o.".encode("utf-8")
    c1 = chunk_documents_batch([doc_nfc], min_chunk=10, max_chunk=100, normalize="nfc")[0][0]
    c2 = chunk_documents_batch([doc_nfd], min_chunk=10, max_chunk=100, normalize="nfc")[0][0]
    assert c1.digest == c2.digest


def test_r3_6_offsets_strictly_invariant_to_normalization():
    doc = b"Prefix text.   Middle   padded   content.\r\nTrailing text."
    for norm in ("none", "whitespace", "nfc"):
        chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=40, normalize=norm)[0]
        reconstructed = bytearray()
        for c in chunks:
            assert doc[c.offset : c.offset + c.length]
            reconstructed.extend(doc[c.offset : c.offset + c.length])
        assert bytes(reconstructed) == doc


def test_r3_6_invalid_normalize_raises_error():
    with pytest.raises(ValueError, match="Invalid normalize"):
        ChunkerConfig(normalize="nfd")


def test_r3_6_normalize_none_vs_whitespace_difference():
    doc1 = b"Text with standard spacing."
    doc2 = b"Text   with   irregular   spacing."
    c1_raw = chunk_documents_batch([doc1], min_chunk=10, max_chunk=100, normalize="none")[0][0]
    c2_raw = chunk_documents_batch([doc2], min_chunk=10, max_chunk=100, normalize="none")[0][0]
    assert c1_raw.digest != c2_raw.digest


# ============================================================================
# R3.7: Structural Metadata (Heading Path & Ordinal)
# ============================================================================

def test_r3_7_ordinal_is_strictly_sequential_zero_indexed():
    doc = b"Paragraph one.\n\nParagraph two.\n\nParagraph three.\n\nParagraph four." * 5
    chunks = chunk_documents_batch([doc], min_chunk=20, avg_chunk=40, max_chunk=80)[0]
    assert len(chunks) >= 4
    for expected_idx, c in enumerate(chunks):
        assert c.ordinal == expected_idx


def test_r3_7_single_top_level_heading_path():
    doc = "# User Guide\n\nThis is introductory content for users.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=16, max_chunk=128)[0]
    assert chunks[0].heading_path == ["User Guide"]


def test_r3_7_nested_heading_hierarchy_path():
    doc = (
        "# Engineering Manual\n\n"
        "## Architecture\n\n"
        "### Storage Engine\n\n"
        "Detailed storage engine specs go here.\n"
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=20, avg_chunk=60, max_chunk=200)[0]
    last_chunk = chunks[-1]
    assert "Engineering Manual" in last_chunk.heading_path
    assert "Architecture" in last_chunk.heading_path
    assert "Storage Engine" in last_chunk.heading_path


def test_r3_7_heading_stack_pops_on_equal_or_higher_level():
    doc = (
        "# Root\n\n"
        "## Section 1\n\n"
        "Content 1.\n\n"
        "## Section 2\n\n"
        "Content 2.\n"
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=30, max_chunk=60)[0]
    # Sibling Section 2 must not retain Section 1 in its heading path
    sec2_chunks = [c for c in chunks if "Section 2" in c.heading_path]
    assert len(sec2_chunks) >= 1
    assert "Section 1" not in sec2_chunks[0].heading_path


def test_r3_7_preamble_before_first_heading_has_empty_path():
    doc = "Preamble text without any heading.\n\n# First Heading\nBody text.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70)[0]
    assert chunks[0].heading_path == []


# ============================================================================
# R3.8: Sentence Context Windowing & Cache Keys
# ============================================================================

def test_r3_8_context_before_extracted_cleanly():
    doc = (
        "Zero sentence precedes. "
        "First sentence comes next. "
        "Second sentence is in the middle. "
        "Third sentence terminates the document."
    ).encode("utf-8")
    chunks = chunk_documents_batch(
        [doc], min_chunk=20, avg_chunk=45, max_chunk=90, context_before=1
    )[0]
    assert len(chunks) >= 2
    assert len(chunks[1].context_before) > 0


def test_r3_8_context_after_extracted_cleanly():
    doc = (
        "Zero sentence precedes. "
        "First sentence comes next. "
        "Second sentence is in the middle. "
        "Third sentence terminates the document."
    ).encode("utf-8")
    chunks = chunk_documents_batch(
        [doc], min_chunk=20, avg_chunk=45, max_chunk=90, context_after=1
    )[0]
    assert len(chunks) >= 2
    assert len(chunks[0].context_after) > 0


def test_r3_8_first_chunk_has_empty_context_before():
    doc = "Single starting sentence. Following sentence here.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, max_chunk=50, context_before=2)[0]
    assert chunks[0].context_before == ""


def test_r3_8_last_chunk_has_empty_context_after():
    doc = "First sentence here. Terminal sentence here.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, max_chunk=50, context_after=2)[0]
    assert chunks[-1].context_after == ""


def test_r3_8_cache_key_with_context_differs_from_without_context():
    doc = "Preceding sentence context. Target chunk sentence. Following sentence context.".encode("utf-8")
    chunk = chunk_documents_batch(
        [doc], min_chunk=15, max_chunk=50, context_before=1, context_after=1
    )[0][1]
    cfg = ChunkerConfig(min_chunk=15, max_chunk=50, context_before=1, context_after=1)

    k_no_ctx = cache_key(chunk, "model-a", cfg, with_context=False)
    k_with_ctx = cache_key(chunk, "model-a", cfg, with_context=True)
    assert k_no_ctx != k_with_ctx


def test_r3_8_modifying_context_invalidates_cache_key_with_context():
    c1 = ChunkResult(
        offset=50, length=40, digest=b"\x11" * 16, hex="11" * 16, context_before="Old context before."
    )
    c2 = ChunkResult(
        offset=50, length=40, digest=b"\x11" * 16, hex="11" * 16, context_before="New context before."
    )
    cfg = ChunkerConfig(min_chunk=16, max_chunk=64, context_before=1)

    k1 = cache_key(c1, "model-a", cfg, with_context=True)
    k2 = cache_key(c2, "model-a", cfg, with_context=True)
    assert k1 != k2


# ============================================================================
# R3.9: Incremental Chunk Diffing (diff_chunks)
# ============================================================================

def test_r3_9_identical_chunk_lists_produce_empty_diff():
    c1 = ChunkResult(offset=0, length=50, digest=b"\x01" * 16, hex="01" * 16, ordinal=0)
    c2 = ChunkResult(offset=50, length=50, digest=b"\x02" * 16, hex="02" * 16, ordinal=1)
    diff = diff_chunks([c1, c2], [c1, c2])
    assert diff.to_embed == []
    assert diff.to_delete == []
    assert diff.to_metadata_update == []


def test_r3_9_inserted_chunk_categorized_as_to_embed():
    c1 = ChunkResult(offset=0, length=50, digest=b"\x01" * 16, hex="01" * 16, ordinal=0)
    c_new = ChunkResult(offset=50, length=50, digest=b"\x99" * 16, hex="99" * 16, ordinal=1)
    diff = diff_chunks([c1], [c1, c_new])
    assert len(diff.to_embed) == 1
    assert diff.to_embed[0].digest == b"\x99" * 16
    assert diff.to_delete == []


def test_r3_9_deleted_chunk_categorized_as_to_delete():
    c1 = ChunkResult(offset=0, length=50, digest=b"\x01" * 16, hex="01" * 16, ordinal=0)
    c2 = ChunkResult(offset=50, length=50, digest=b"\x02" * 16, hex="02" * 16, ordinal=1)
    diff = diff_chunks([c1, c2], [c1])
    assert diff.to_embed == []
    assert len(diff.to_delete) == 1
    assert diff.to_delete[0].digest == b"\x02" * 16


def test_r3_9_shifted_metadata_categorized_as_to_metadata_update():
    # Same digest, but ordinal shifted due to insertion elsewhere
    c_old = ChunkResult(offset=100, length=50, digest=b"\x05" * 16, hex="05" * 16, ordinal=1)
    c_new = ChunkResult(offset=150, length=50, digest=b"\x05" * 16, hex="05" * 16, ordinal=2)
    diff = diff_chunks([c_old], [c_new])
    assert diff.to_embed == []
    assert diff.to_delete == []
    assert len(diff.to_metadata_update) == 1
    assert diff.to_metadata_update[0].ordinal == 2


def test_r3_9_complete_document_replacement():
    old = [ChunkResult(offset=0, length=50, digest=b"\x01" * 16, hex="01" * 16)]
    new = [ChunkResult(offset=0, length=60, digest=b"\x02" * 16, hex="02" * 16)]
    diff = diff_chunks(old, new)
    assert len(diff.to_delete) == 1
    assert len(diff.to_embed) == 1
    assert diff.to_metadata_update == []


def test_r3_9_tuple_unpacking_compatibility():
    old = [ChunkResult(offset=0, length=50, digest=b"\x01" * 16, hex="01" * 16)]
    new = [ChunkResult(offset=0, length=50, digest=b"\x02" * 16, hex="02" * 16)]
    to_embed, to_delete, to_meta = diff_chunks(old, new)
    assert len(to_embed) == 1
    assert len(to_delete) == 1
    assert len(to_meta) == 0


# ============================================================================
# R3.11: Mode Rename to boundary/boundary_aware & Deprecation Warnings
# ============================================================================

def test_r3_11_mode_boundary_is_primary():
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        cfg = ChunkerConfig(mode="boundary")
        assert cfg.mode == "boundary"
        assert len(recorded) == 0


def test_r3_11_mode_boundary_aware_alias_accepted():
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        cfg = ChunkerConfig(mode="boundary_aware")
        assert cfg.mode == "boundary_aware"
        assert len(recorded) == 0


def test_r3_11_mode_semantic_emits_deprecation_warning():
    with pytest.deprecated_call(match="mode='semantic' is deprecated"):
        cfg = ChunkerConfig(mode="semantic")
        assert cfg.mode == "boundary"


def test_r3_11_semantic_snap_true_emits_deprecation_warning():
    with pytest.deprecated_call(match="semantic_snap is deprecated"):
        cfg = ChunkerConfig(semantic_snap=True)
        assert cfg.mode == "boundary"


def test_r3_11_semantic_snap_false_emits_deprecation_warning():
    with pytest.deprecated_call(match="semantic_snap is deprecated"):
        cfg = ChunkerConfig(semantic_snap=False)
        assert cfg.mode == "raw"
