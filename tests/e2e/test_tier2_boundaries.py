"""Tier 2: Comprehensive Boundary and Corner Case Tests (>= 5 tests per feature domain).

Covers:
- Extreme inputs: empty, single-byte, two-byte, odd lengths
- Exact sizing boundaries: exactly min_chunk, max_chunk, avg_chunk, min-1, max+1
- Deep heading stacks (H1 through H6), consecutive headings, trailing headings
- Sentence segmentation corner cases: missing terminal punctuation, repeated punctuation, ellipses
- Abbreviation boundary stress: legal abbreviations (art., inc., Dr., e.g., i.e.) at cut points
- Unicode & Multilingual stress: pure CJK, mixed scripts, emojis, Unicode spaces
- Tail remainder stress: 1-byte remainder, min-1 remainder, merge vs split boundaries
- Normalization & token sizing edge cases
- Diffing and cache key edge cases
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


# ============================================================================
# 1. Extreme Length & Capacity Boundaries
# ============================================================================

def test_tier2_empty_bytes_document():
    res = chunk_documents_batch([b""], min_chunk=64, max_chunk=256)
    assert res == [[]]


def test_tier2_single_byte_document():
    res = chunk_documents_batch([b"Z"], min_chunk=64, max_chunk=256)[0]
    assert len(res) == 1
    assert res[0].offset == 0
    assert res[0].length == 1
    assert res[0].ordinal == 0


def test_tier2_two_byte_document():
    res = chunk_documents_batch([b"OK"], min_chunk=64, max_chunk=256)[0]
    assert len(res) == 1
    assert res[0].length == 2


def test_tier2_odd_length_document():
    doc = b"OddLength13B!"
    res = chunk_documents_batch([doc], min_chunk=64, max_chunk=256)[0]
    assert len(res) == 1
    assert res[0].length == 13


def test_tier2_exactly_min_chunk_bytes():
    doc = b"M" * 64
    res = chunk_documents_batch([doc], min_chunk=64, max_chunk=256)[0]
    assert len(res) == 1
    assert res[0].length == 64


def test_tier2_min_chunk_minus_one_bytes():
    doc = b"M" * 63
    res = chunk_documents_batch([doc], min_chunk=64, max_chunk=256)[0]
    assert len(res) == 1
    assert res[0].length == 63


def test_tier2_min_chunk_plus_one_bytes():
    doc = b"M" * 65
    res = chunk_documents_batch([doc], min_chunk=64, max_chunk=256)[0]
    assert len(res) == 1
    assert res[0].length == 65


def test_tier2_exactly_max_chunk_bytes():
    doc = b"X" * 256
    res = chunk_documents_batch([doc], min_chunk=64, avg_chunk=128, max_chunk=256, mode="raw")[0]
    assert sum(c.length for c in res) == 256


def test_tier2_max_chunk_plus_one_bytes():
    doc = b"X" * 257
    res = chunk_documents_batch([doc], min_chunk=64, avg_chunk=128, max_chunk=256, mode="raw")[0]
    assert len(res) >= 2
    assert sum(c.length for c in res) == 257


def test_tier2_exactly_avg_chunk_bytes():
    doc = b"A" * 128
    res = chunk_documents_batch([doc], min_chunk=64, avg_chunk=128, max_chunk=256)[0]
    assert sum(c.length for c in res) == 128


# ============================================================================
# 2. Structural Document Extremes (Headings & Nesting)
# ============================================================================

def test_tier2_deep_headings_h1_to_h6():
    doc = (
        "# L1\n\n## L2\n\n### L3\n\n#### L4\n\n##### L5\n\n###### L6\n\nDeep nested content here.\n"
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=20, avg_chunk=50, max_chunk=200)[0]
    last_chunk = chunks[-1]
    assert last_chunk.heading_path == ["L1", "L2", "L3", "L4", "L5", "L6"]


def test_tier2_consecutive_headings_without_body():
    doc = "# H1\n## H2\n### H3\nActual body text follows.\n".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, max_chunk=100)[0]
    assert len(chunks) >= 1
    assert "H3" in chunks[0].heading_path


def test_tier2_trailing_heading_at_eof():
    doc = "Body text preceding trailing heading.\n\n# Trailing Heading".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, max_chunk=80)[0]
    assert len(chunks) >= 1
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_heading_without_space_is_not_heading():
    doc = "#NotAHeading text follows.\n".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=50)[0]
    assert chunks[0].heading_path == []


def test_tier2_heading_level_7_is_not_markdown_heading():
    doc = "####### Heading 7 is not recognized in standard Markdown.\n".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=80)[0]
    assert chunks[0].heading_path == []


def test_tier2_heading_with_trailing_hashes():
    doc = "# Clean Heading ##\n\nBody paragraph text.\n".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, max_chunk=60)[0]
    assert any("Clean Heading" in h for h in chunks[0].heading_path)


# ============================================================================
# 3. Punctuation & Whitespace Extremes
# ============================================================================

def test_tier2_multiple_consecutive_blank_lines():
    doc = "Paragraph one.\n\n\n\n\nParagraph two.\n\n\nParagraph three.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=30, max_chunk=60, mode="boundary")[0]
    assert len(chunks) >= 2
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_mixed_crlf_and_lf_blank_lines():
    doc = "Paragraph A.\r\n\r\nParagraph B.\n\nParagraph C.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=30, max_chunk=60)[0]
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_blank_lines_with_spaces_and_tabs():
    doc = "Para 1.\n  \t  \nPara 2.\n\t\t\nPara 3.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, avg_chunk=25, max_chunk=50)[0]
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_sentences_without_terminal_punctuation():
    doc = "First sentence without terminal Second sentence also unpunctuated Third sentence".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=20, avg_chunk=40, max_chunk=70, mode="boundary")[0]
    assert len(chunks) >= 1
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_repeated_punctuation_marks():
    doc = "What happened??? Truly amazing!!! Really... fascinating.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    assert len(chunks) >= 1


def test_tier2_ellipses_in_sentence():
    doc = "Thinking about the issue… then resolving it… final statement.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    assert len(chunks) >= 1


# ============================================================================
# 4. Abbreviation Boundary Stress Tests
# ============================================================================

def test_tier2_abbreviation_dr_at_boundary():
    doc = "The meeting was led by Dr. Watson and his team of researchers.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=30, max_chunk=60, mode="boundary")[0]
    for c in chunks:
        chunk_text = doc[c.offset : c.offset + c.length].decode("utf-8")
        assert not chunk_text.endswith("Dr.")


def test_tier2_portuguese_abbreviation_art_and_inc():
    doc = "De acordo com o art. 14, inc. II, do Código Civil brasileiro.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    for c in chunks:
        chunk_text = doc[c.offset : c.offset + c.length].decode("utf-8")
        assert not chunk_text.endswith("art.")
        assert not chunk_text.endswith("inc.")


def test_tier2_english_abbreviation_eg_and_ie():
    doc = "Specific examples, e.g. databases, i.e. distributed storage, were presented.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    for c in chunks:
        chunk_text = doc[c.offset : c.offset + c.length].decode("utf-8")
        assert not chunk_text.endswith("e.g.")
        assert not chunk_text.endswith("i.e.")


def test_tier2_repeated_abbreviations_in_succession():
    doc = "Mr. and Mrs. Smith met Dr. Jones and Prof. Davis at the conference.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    assert len(chunks) >= 1


def test_tier2_abbreviation_followed_by_newline():
    doc = "The presiding officer was\nDr.\nWatson.\n".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=50, mode="boundary")[0]
    assert len(chunks) >= 1


# ============================================================================
# 5. Multilingual & Unicode Invariant Tests
# ============================================================================

def test_tier2_pure_cjk_without_spaces():
    doc = "机器学习算法在自然语言处理领域有着广泛的应用。深度学习模型正在重塑信息检索系统。".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=20, avg_chunk=50, max_chunk=100, mode="boundary")[0]
    assert len(chunks) >= 2
    for c in chunks:
        raw = doc[c.offset : c.offset + c.length]
        assert raw.decode("utf-8")  # No split codepoints


def test_tier2_cjk_fullwidth_question_and_exclamation():
    doc = "这是一个测试吗？当然是！请确认结果。".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=12, avg_chunk=25, max_chunk=50, mode="boundary")[0]
    assert len(chunks) >= 1


def test_tier2_unicode_whitespace_quads_and_spaces():
    doc = "Alpha\u2000Beta\u2001Gamma\u2002Delta\u2003Epsilon.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, avg_chunk=25, max_chunk=50, mode="boundary")[0]
    assert len(chunks) >= 1


def test_tier2_unicode_zero_width_space():
    doc = "WordA\u200bWordB\u200bWordC\u200bWordD.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, avg_chunk=25, max_chunk=50, mode="boundary")[0]
    assert len(chunks) >= 1


def test_tier2_null_bytes_in_payload():
    doc = b"Header\x00Binary\x00Payload\x00Footer"
    chunks = chunk_documents_batch([doc], min_chunk=8, max_chunk=24, mode="raw")[0]
    assert len(chunks) >= 1
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_control_characters_in_payload():
    doc = b"Line1\x01\x02\x03\nLine2\x04\x05\x06\nLine3"
    chunks = chunk_documents_batch([doc], min_chunk=8, max_chunk=24, mode="raw")[0]
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_4byte_utf8_emojis():
    doc = "🦀 🚀 🐍 🎉 🔥 💡 📚 🔍 🧩 🤖".encode("utf-8") * 5
    chunks = chunk_documents_batch([doc], min_chunk=16, avg_chunk=40, max_chunk=80, mode="boundary")[0]
    for c in chunks:
        decoded = doc[c.offset : c.offset + c.length].decode("utf-8")
        assert len(decoded) > 0


def test_tier2_mixed_cyrillic_and_greek():
    doc = "Текст на русском языке. Ελληνικό κείμενο για δοκιμή.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    for c in chunks:
        assert doc[c.offset : c.offset + c.length].decode("utf-8")


# ============================================================================
# 6. Tail Remainder & Redistribution Extremes
# ============================================================================

def test_tier2_tail_remainder_one_byte():
    # Previous chunk + 1 byte
    doc = b"A" * 70 + b"B"
    chunks = chunk_documents_batch([doc], min_chunk=64, avg_chunk=70, max_chunk=150, mode="raw")[0]
    assert len(chunks) == 1
    assert chunks[0].length == 71


def test_tier2_tail_remainder_min_minus_one():
    # min_chunk=64, remainder=63
    doc = b"A" * 80 + b"B" * 63
    chunks = chunk_documents_batch([doc], min_chunk=64, avg_chunk=80, max_chunk=200, mode="raw")[0]
    assert len(chunks) == 1
    assert chunks[0].length == 143


def test_tier2_tail_merge_boundary_exact_max():
    # min_chunk=50, max_chunk=100. Previous=80, remainder=20 -> sum=100 (exact merge)
    doc = b"A" * 80 + b"B" * 20
    chunks = chunk_documents_batch([doc], min_chunk=50, avg_chunk=80, max_chunk=100, mode="raw")[0]
    assert len(chunks) == 1
    assert chunks[0].length == 100


def test_tier2_tail_split_boundary_max_plus_one():
    # Previous=80, remainder=21 -> sum=101 > max_chunk=100 -> forces balanced redistribution
    doc = b"A" * 80 + b"B" * 21
    chunks = chunk_documents_batch([doc], min_chunk=40, avg_chunk=80, max_chunk=100, mode="raw")[0]
    assert len(chunks) == 2
    for c in chunks:
        assert c.length >= 40
        assert c.length <= 100
    assert sum(c.length for c in chunks) == 101


# ============================================================================
# 7. Context Windowing Edge Cases
# ============================================================================

def test_tier2_context_window_single_sentence():
    doc = "Only single sentence in document.".encode("utf-8")
    chunks = chunk_documents_batch(
        [doc], min_chunk=10, max_chunk=50, context_before=5, context_after=5
    )[0]
    assert len(chunks) == 1
    assert chunks[0].context_before == ""
    assert chunks[0].context_after == ""


def test_tier2_context_window_empty_document():
    chunks = chunk_documents_batch([b""], context_before=3, context_after=3)[0]
    assert chunks == []


def test_tier2_context_window_multiline_sentence():
    doc = (
        "First sentence here.\n"
        "Second sentence spans across\n"
        "multiple lines before ending.\n"
        "Third sentence here."
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, max_chunk=60, context_before=1)[0]
    assert len(chunks) >= 2


# ============================================================================
# 8. Token Mode & Normalization Edge Cases
# ============================================================================

def test_tier2_token_mode_single_token():
    doc = b"SingleWord"
    chunks = chunk_documents_batch([doc], min_chunk=1, max_chunk=10, size_unit="tokens")[0]
    assert len(chunks) == 1
    assert chunks[0].length == len(doc)


def test_tier2_token_mode_punctuation_heavy():
    doc = b"word1, (word2) [word3] {word4}; word5: word6!"
    chunks = chunk_documents_batch([doc], min_chunk=2, max_chunk=4, size_unit="tokens")[0]
    assert len(chunks) >= 2


def test_tier2_normalization_mixed_nfc_nfd_equivalence():
    composed = "José e João foram à praça pública.".encode("utf-8")
    decomposed = unicodedata.normalize("NFD", "José e João foram à praça pública.").encode("utf-8")
    assert composed != decomposed
    c1 = chunk_documents_batch([composed], min_chunk=10, max_chunk=100, normalize="nfc")[0][0]
    c2 = chunk_documents_batch([decomposed], min_chunk=10, max_chunk=100, normalize="nfc")[0][0]
    assert c1.digest == c2.digest


def test_tier2_normalization_tabs_spaces_newlines():
    doc1 = b"Text\twith\ttabs and   multiple   spaces.\r\n"
    doc2 = b"Text with tabs and multiple spaces.\n"
    c1 = chunk_documents_batch([doc1], min_chunk=10, max_chunk=100, normalize="whitespace")[0][0]
    c2 = chunk_documents_batch([doc2], min_chunk=10, max_chunk=100, normalize="whitespace")[0][0]
    assert c1.digest == c2.digest


# ============================================================================
# 9. Diffing & Cache Key Edge Cases
# ============================================================================

def test_tier2_diff_chunks_empty_old_and_new():
    diff = diff_chunks([], [])
    assert diff.to_embed == []
    assert diff.to_delete == []
    assert diff.to_metadata_update == []


def test_tier2_diff_chunks_empty_old_nonempty_new():
    new = [ChunkResult(offset=0, length=20, digest=b"\x01" * 16, hex="01" * 16)]
    diff = diff_chunks([], new)
    assert len(diff.to_embed) == 1
    assert diff.to_delete == []


def test_tier2_diff_chunks_nonempty_old_empty_new():
    old = [ChunkResult(offset=0, length=20, digest=b"\x01" * 16, hex="01" * 16)]
    diff = diff_chunks(old, [])
    assert diff.to_embed == []
    assert len(diff.to_delete) == 1


def test_tier2_diff_chunks_only_offset_changed():
    c_old = ChunkResult(offset=0, length=50, digest=b"\x0a" * 16, hex="0a" * 16, ordinal=0)
    c_new = ChunkResult(offset=10, length=50, digest=b"\x0a" * 16, hex="0a" * 16, ordinal=0)
    diff = diff_chunks([c_old], [c_new])
    assert len(diff.to_metadata_update) == 1
    assert diff.to_embed == []
    assert diff.to_delete == []


def test_tier2_cache_key_special_chars_in_model_id():
    c = ChunkResult(offset=0, length=30, digest=b"\x33" * 16, hex="33" * 16)
    cfg = ChunkerConfig()
    k1 = cache_key(c, "openai/text-embedding-3-small@2024", cfg)
    k2 = cache_key(c, "cohere/embed-multilingual-v3.0", cfg)
    assert k1 != k2
    assert k1.startswith("frc:v0.3.0:")


def test_tier2_cache_key_long_model_id():
    c = ChunkResult(offset=0, length=30, digest=b"\x44" * 16, hex="44" * 16)
    cfg = ChunkerConfig()
    long_id = "org/model-variant-with-extremely-long-hierarchical-namespace-identifier-" + "x" * 200
    k = cache_key(c, long_id, cfg)
    assert len(k) == len("frc:v0.3.0:") + 32


# ============================================================================
# 10. Large Payload & Batch Robustness
# ============================================================================

def test_tier2_large_document_throughput():
    # 50 KB document
    doc = (
        "# High-Throughput Test Section\n\n"
        "Paragraph content repeated to verify that memory allocation and boundary "
        "scanning scales linearly without exponential backtracking or stack overflow.\n\n"
    ).encode("utf-8") * 250
    assert len(doc) > 35_000
    chunks = chunk_documents_batch([doc], min_chunk=64, avg_chunk=256, max_chunk=1024)[0]
    assert len(chunks) > 20
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_batch_with_empty_and_nonempty_docs():
    batch = [b"", b"Document one payload.", b"", b"Document two payload.", b""]
    res = chunk_documents_batch(batch, min_chunk=10, max_chunk=50)
    assert len(res) == 5
    assert res[0] == []
    assert len(res[1]) == 1
    assert res[2] == []
    assert len(res[3]) == 1
    assert res[4] == []


# ============================================================================
# 11. Additional Structural, Abbreviation & Boundary Stress Tests
# ============================================================================

def test_tier2_whitespace_only_document():
    doc = b"   \t  \r\n  \n   "
    res = chunk_documents_batch([doc], min_chunk=8, max_chunk=32)[0]
    assert len(res) >= 1
    assert sum(c.length for c in res) == len(doc)


def test_tier2_leading_blank_lines_before_heading():
    doc = "\n\n\n# Preamble Heading\nBody content follows.\n".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=80)[0]
    assert len(chunks) >= 1
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_heading_with_multiple_internal_spaces():
    doc = "##    Widely    Spaced    Heading   \n\nBody content.\n".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=80)[0]
    assert any("Widely    Spaced    Heading" in h for h in chunks[0].heading_path)


def test_tier2_heading_hierarchy_sibling_and_ascendant_pop():
    # Test L1 -> L2 -> L3 -> L2 (pops L3) -> L1 (pops L2, L1) -> New L1
    doc = (
        "# Root\n\n"
        "## Sub1\n\n"
        "### Sub1_Deep\n\nContent A.\n\n"
        "## Sub2\n\nContent B.\n\n"
        "# Root2\n\nContent C.\n"
    ).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=30, max_chunk=60)[0]
    # Check that Sub2 does not contain Sub1_Deep
    sub2_chunks = [c for c in chunks if "Sub2" in c.heading_path]
    for sc in sub2_chunks:
        assert "Sub1_Deep" not in sc.heading_path
    # Check that Root2 does not contain Root or Sub1 or Sub2
    root2_chunks = [c for c in chunks if "Root2" in c.heading_path]
    for rc in root2_chunks:
        assert "Root" not in rc.heading_path
        assert "Sub1" not in rc.heading_path
        assert "Sub2" not in rc.heading_path


def test_tier2_legal_abbreviation_paragrafo_unico():
    doc = "Conforme o parágrafo único e o art. 10 da legislação específica.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    assert len(chunks) >= 1


def test_tier2_legal_abbreviation_incisos_numerals():
    doc = "Disposto no art. 7º, inc. III e inc. IV, da referida norma jurídica.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    for c in chunks:
        text = doc[c.offset : c.offset + c.length].decode("utf-8")
        assert not text.endswith("art.")
        assert not text.endswith("inc.")


def test_tier2_english_abbreviation_at_start_of_chunk():
    doc = "Dr. Smith opened the conference session. He introduced the guest speaker.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=20, max_chunk=100)[0]
    assert len(chunks) >= 1
    assert doc[chunks[0].offset : chunks[0].offset + chunks[0].length].decode("utf-8").startswith("Dr. Smith")


def test_tier2_english_abbreviation_al_in_citations():
    doc = "Research by Johnson et al. demonstrated high throughput in chunking pipelines.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    for c in chunks:
        text = doc[c.offset : c.offset + c.length].decode("utf-8")
        assert not text.endswith("al.")


def test_tier2_portuguese_abbreviation_ed_and_pag():
    doc = "Publicado na 2ª ed., pág. 145, da revista especializada em computação.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    for c in chunks:
        text = doc[c.offset : c.offset + c.length].decode("utf-8")
        assert not text.endswith("ed.")
        assert not text.endswith("pág.")


def test_tier2_mixed_punctuation_interrobang():
    doc = "Is this result acceptable?! Of course it is! Next phase commences.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=15, avg_chunk=35, max_chunk=70, mode="boundary")[0]
    assert len(chunks) >= 1


def test_tier2_context_window_multi_sentence_limit():
    doc = (
        "Sent 1. Sent 2. Sent 3. Sent 4. Sent 5. "
        "Target sentence chunk in middle. "
        "Sent 6. Sent 7. Sent 8. Sent 9. Sent 10."
    ).encode("utf-8")
    chunks = chunk_documents_batch(
        [doc], min_chunk=20, avg_chunk=40, max_chunk=60, context_before=3, context_after=3
    )[0]
    assert len(chunks) >= 3
    middle_chunk = chunks[1]
    # Context before must not exceed 3 sentences
    before_sents = middle_chunk.context_before.split(". ")
    assert len(before_sents) <= 3


def test_tier2_diff_chunks_interleaved_insertions_and_deletions():
    c1 = ChunkResult(offset=0, length=20, digest=b"\x01" * 16, hex="01" * 16, ordinal=0)
    c2 = ChunkResult(offset=20, length=20, digest=b"\x02" * 16, hex="02" * 16, ordinal=1)
    c3 = ChunkResult(offset=40, length=20, digest=b"\x03" * 16, hex="03" * 16, ordinal=2)

    # c2 is deleted, c_new is inserted, c3 moves ordinal
    c_new = ChunkResult(offset=20, length=20, digest=b"\x99" * 16, hex="99" * 16, ordinal=1)
    c3_moved = ChunkResult(offset=40, length=20, digest=b"\x03" * 16, hex="03" * 16, ordinal=2)

    diff = diff_chunks([c1, c2, c3], [c1, c_new, c3_moved])
    assert len(diff.to_delete) == 1
    assert diff.to_delete[0].digest == b"\x02" * 16
    assert len(diff.to_embed) == 1
    assert diff.to_embed[0].digest == b"\x99" * 16
    assert diff.to_metadata_update == []


def test_tier2_snap_window_equal_min_and_max():
    # Boundary condition where min_chunk == max_chunk
    resolved = resolve_snap_window(avg_chunk=100, min_chunk=100, max_chunk=100, user_snap=None)
    assert resolved == 32


def test_tier2_boundary_mode_unbreakable_string_falls_back():
    # Long contiguous ASCII string without any whitespace or punctuation
    doc = b"A" * 300
    chunks = chunk_documents_batch([doc], min_chunk=32, avg_chunk=64, max_chunk=128, mode="boundary")[0]
    assert len(chunks) >= 3
    assert sum(c.length for c in chunks) == 300


def test_tier2_repeated_cjk_punctuation():
    doc = "这是测试文章。。这是第二句话！！这是第三句话？？".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, avg_chunk=25, max_chunk=50, mode="boundary")[0]
    assert len(chunks) >= 1
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_bom_utf8_prefix():
    doc = b"\xef\xbb\xbf# Title with UTF-8 BOM\nBody content."
    chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=50)[0]
    assert len(chunks) >= 1
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_single_long_sentence_exceeding_max_chunk():
    doc = ("Word " * 150 + "terminates here.").encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=32, avg_chunk=64, max_chunk=128, mode="boundary")[0]
    assert len(chunks) >= 4
    for c in chunks:
        assert c.length <= 128
    assert sum(c.length for c in chunks) == len(doc)


def test_tier2_heading_at_start_of_document_offset_zero():
    doc = "# Root Title\n\nBody content.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=50)[0]
    assert chunks[0].offset == 0
    assert chunks[0].heading_path == ["Root Title"]


def test_tier2_empty_headings_in_markdown():
    doc = "# \n## \nBody content.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=10, max_chunk=50)[0]
    assert len(chunks) >= 1


def test_tier2_tokens_mode_tail_redistribution():
    # 25 tokens with max_tokens=10, min_tokens=3
    tokens = [f"t{i}" for i in range(25)]
    doc = " ".join(tokens).encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=3, max_chunk=10, size_unit="tokens")[0]
    assert len(chunks) >= 3
    for c in chunks:
        tok_count = len(doc[c.offset : c.offset + c.length].decode("utf-8").split())
        assert tok_count <= 10


def test_tier2_raw_mode_ignores_headings_and_newlines():
    doc = "# Heading\n\nParagraph with sentences. Another sentence.".encode("utf-8")
    chunks = chunk_documents_batch([doc], min_chunk=20, avg_chunk=40, max_chunk=80, mode="raw")[0]
    assert len(chunks) >= 1
    assert sum(c.length for c in chunks) == len(doc)

