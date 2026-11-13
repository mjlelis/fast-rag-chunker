"""Tier 4: Real-World Application Scenario Tests.

Exercises end-to-end production RAG workflows using real bilingual corpora:
1. Scenario 1: Bilingual Wikipedia technical revisions (EN and PT) verifying chunk reuse and diffing.
2. Scenario 2: Legal document indexing (LGPD legal articles, numbered incisos, heading paths).
3. Scenario 3: Technical Markdown manuals with tables, code blocks, and deep heading hierarchies.
4. Scenario 4: End-to-end Vector Database synchronization simulation (Pinecone/Qdrant pattern).
5. Scenario 5: High-throughput multilingual mixed-batch indexing pipeline (EN, PT, CJK).
6. Scenario 6: Content-defined localized edit resynchronization verification.
"""

from pathlib import Path
import pytest
from tests.e2e.adapter import (
    ChunkerConfig,
    ChunkResult,
    chunk_documents_batch,
    chunker_fingerprint,
    cache_key,
    diff_chunks,
)


def _load_corpus_file(corpus_dir: Path, filename: str) -> bytes:
    """Helper to load real text from bench/corpus/data/."""
    file_path = corpus_dir / filename
    if not file_path.is_file():
        pytest.skip(f"Corpus file not found: {file_path}")
    return file_path.read_bytes()


# ============================================================================
# Scenario 1: Bilingual Wikipedia Technical Revisions
# ============================================================================

def test_scenario1_bilingual_wikipedia_revisions(corpus_dir: Path):
    """Evaluates chunk reuse and diffing across English and Portuguese Wikipedia revisions."""
    # Load real English and Portuguese revision pairs
    en_old = _load_corpus_file(corpus_dir, "en_01_rolling_hash_rev_old.md")
    en_new = _load_corpus_file(corpus_dir, "en_01_rolling_hash_rev_new.md")
    pt_old = _load_corpus_file(corpus_dir, "pt_01_tabela_de_dispers_o_rev_old.md")
    pt_new = _load_corpus_file(corpus_dir, "pt_01_tabela_de_dispers_o_rev_new.md")

    cfg = ChunkerConfig(min_chunk=64, avg_chunk=256, max_chunk=512, mode="boundary")

    # Process English revision
    en_chunks_old = chunk_documents_batch([en_old], config=cfg)[0]
    en_chunks_new = chunk_documents_batch([en_new], config=cfg)[0]

    assert len(en_chunks_old) >= 10
    assert len(en_chunks_new) >= 10
    assert sum(c.length for c in en_chunks_old) == len(en_old)
    assert sum(c.length for c in en_chunks_new) == len(en_new)

    en_diff = diff_chunks(en_chunks_old, en_chunks_new)
    # Check that identical chunks were preserved
    old_digests = {c.digest for c in en_chunks_old}
    new_digests = {c.digest for c in en_chunks_new}
    shared_digests = old_digests & new_digests
    reuse_rate = len(shared_digests) / max(len(old_digests), 1)
    assert reuse_rate > 0.60, f"Expected >60% chunk reuse in English revisions, got {reuse_rate:.2%}"

    # Process Portuguese revision
    pt_chunks_old = chunk_documents_batch([pt_old], config=cfg)[0]
    pt_chunks_new = chunk_documents_batch([pt_new], config=cfg)[0]

    assert len(pt_chunks_old) >= 10
    assert len(pt_chunks_new) >= 10
    assert sum(c.length for c in pt_chunks_old) == len(pt_old)
    assert sum(c.length for c in pt_chunks_new) == len(pt_new)

    pt_diff = diff_chunks(pt_chunks_old, pt_chunks_new)
    pt_shared = {c.digest for c in pt_chunks_old} & {c.digest for c in pt_chunks_new}
    pt_reuse_rate = len(pt_shared) / max(len(pt_chunks_old), 1)
    assert pt_reuse_rate > 0.60, f"Expected >60% chunk reuse in Portuguese revisions, got {pt_reuse_rate:.2%}"


# ============================================================================
# Scenario 2: Legal Corpus Indexing (LGPD)
# ============================================================================

def test_scenario2_legal_corpus_lgpd_indexing(corpus_dir: Path):
    """Validates structural metadata extraction and abbreviation guards on Brazilian Data Protection Law (LGPD)."""
    lgpd_doc = _load_corpus_file(corpus_dir, "pt_15_lei_geral_de_prote_o_de_dados_pe_rev_new.md")

    cfg = ChunkerConfig(
        min_chunk=64,
        avg_chunk=256,
        max_chunk=512,
        mode="boundary",
        context_before=1,
        context_after=1,
    )
    chunks = chunk_documents_batch([lgpd_doc], config=cfg)[0]
    assert len(chunks) >= 20

    for idx, c in enumerate(chunks):
        assert c.ordinal == idx
        raw = lgpd_doc[c.offset : c.offset + c.length]
        text = raw.decode("utf-8")
        # Ensure no chunk ends abruptly on common legal abbreviations
        assert not text.endswith("art.")
        assert not text.endswith("inc.")
        assert not text.endswith("par.")

    # Verify heading paths captured structural legal divisions
    headings_found = set()
    for c in chunks:
        for h in c.heading_path:
            headings_found.add(h)
    assert len(headings_found) >= 3


# ============================================================================
# Scenario 3: Technical Markdown Documentation with Code Blocks and Tables
# ============================================================================

def test_scenario3_technical_markdown_manual_with_tables_and_code():
    """Validates chunking of technical documents with code blocks, tables, and lists."""
    doc = (
        "# System Architecture Specification\n\n"
        "This specification outlines the technical design of the distributed storage engine.\n\n"
        "## Component Overview\n\n"
        "The architecture consists of three core subsystems:\n"
        "1. Ingestion gateway\n"
        "2. Chunking engine\n"
        "3. Vector store connector\n\n"
        "### API Interface\n\n"
        "The primary entry point is exposed via Python bindings:\n\n"
        "```python\n"
        "from fast_rag_chunker import ChunkerConfig, chunk_documents_batch\n"
        "cfg = ChunkerConfig(min_chunk=64, max_chunk=512, mode='boundary')\n"
        "chunks = chunk_documents_batch([doc_bytes], config=cfg)\n"
        "```\n\n"
        "### Benchmark Comparison Table\n\n"
        "| Engine | Throughput (MB/s) | Chunk Reuse (%) | Memory Footprint |\n"
        "|:-------|:-----------------:|:---------------:|:----------------:|\n"
        "| FastCDC | 850 MB/s | 82.5% | 12 MB |\n"
        "| Fixed Window | 920 MB/s | 12.0% | 8 MB |\n"
        "| Recursive | 140 MB/s | 28.4% | 45 MB |\n\n"
        "## Deployment Guidelines\n\n"
        "Deploy using multi-threaded batch mode to maximize multi-core utilization.\n"
    ).encode("utf-8")

    cfg = ChunkerConfig(min_chunk=32, avg_chunk=128, max_chunk=256, mode="boundary")
    chunks = chunk_documents_batch([doc], config=cfg)[0]
    assert len(chunks) >= 3

    # Offsets must be strictly contiguous and reassemble entire document
    reconstructed = bytearray()
    for c in chunks:
        reconstructed.extend(doc[c.offset : c.offset + c.length])
    assert bytes(reconstructed) == doc

    # Headings must track the hierarchy
    assert any("System Architecture Specification" in c.heading_path for c in chunks)
    assert any("Benchmark Comparison Table" in c.heading_path for c in chunks)


# ============================================================================
# Scenario 4: End-to-End Vector Database Synchronization Simulation
# ============================================================================

class MockVectorDatabase:
    """Simulates a vector database (e.g. Pinecone/Qdrant/Chroma)."""

    def __init__(self) -> None:
        self.vectors: dict[str, dict] = {}
        self.embed_calls: int = 0
        self.delete_calls: int = 0
        self.metadata_update_calls: int = 0

    def upsert(self, doc_id: str, digest_hex: str, metadata: dict) -> None:
        self.embed_calls += 1
        self.vectors[digest_hex] = {"doc_id": doc_id, "metadata": metadata}

    def delete(self, digest_hex: str) -> None:
        self.delete_calls += 1
        self.vectors.pop(digest_hex, None)

    def update_metadata(self, digest_hex: str, new_metadata: dict) -> None:
        self.metadata_update_calls += 1
        if digest_hex in self.vectors:
            self.vectors[digest_hex]["metadata"] = new_metadata


def test_scenario4_end_to_end_rag_vector_db_sync():
    """Simulates realistic incremental synchronization with a vector database."""
    vdb = MockVectorDatabase()

    # Step 1: Initial document ingestion
    v1_text = (
        "# User Documentation\n\n"
        "Paragraph 1: Introduction to the content-defined chunking engine.\n\n"
        "Paragraph 2: Detailed explanation of FastCDC gear hashing.\n\n"
        "Paragraph 3: Description of 128-bit truncated BLAKE3 digests.\n\n"
        "Paragraph 4: Summary and conclusion of the initial release.\n"
    ).encode("utf-8")

    cfg = ChunkerConfig(min_chunk=20, avg_chunk=60, max_chunk=120, mode="boundary")
    v1_chunks = chunk_documents_batch([v1_text], config=cfg)[0]
    assert len(v1_chunks) >= 3

    for c in v1_chunks:
        vdb.upsert("doc_001", c.hex, {"ordinal": c.ordinal, "heading": c.heading_path})

    initial_embed_count = vdb.embed_calls
    assert initial_embed_count == len(v1_chunks)

    # Step 2: Revised document (Paragraph 2 edited, Paragraph 5 added)
    v2_text = (
        "# User Documentation\n\n"
        "Paragraph 1: Introduction to the content-defined chunking engine.\n\n"
        "Paragraph 2: MODIFIED EXPLANATION of boundary-aware priority models.\n\n"
        "Paragraph 3: Description of 128-bit truncated BLAKE3 digests.\n\n"
        "Paragraph 4: Summary and conclusion of the initial release.\n\n"
        "Paragraph 5: New section introducing vector database synchronization.\n"
    ).encode("utf-8")

    v2_chunks = chunk_documents_batch([v2_text], config=cfg)[0]
    diff = diff_chunks(v1_chunks, v2_chunks)

    # Step 3: Apply diff to vector database
    for c in diff.to_embed:
        vdb.upsert("doc_001", c.hex, {"ordinal": c.ordinal, "heading": c.heading_path})
    for c in diff.to_delete:
        vdb.delete(c.hex)
    for c in diff.to_metadata_update:
        vdb.update_metadata(c.hex, {"ordinal": c.ordinal, "heading": c.heading_path})

    # Verify that only the new/modified chunks required embedding
    assert len(diff.to_embed) < len(v2_chunks), "Incremental sync should embed fewer chunks than full re-index"
    assert vdb.embed_calls == initial_embed_count + len(diff.to_embed)


# ============================================================================
# Scenario 5: High-Throughput Multilingual Mixed-Batch Pipeline
# ============================================================================

def test_scenario5_multilingual_mixed_batch_indexing(corpus_dir: Path):
    """Validates multi-threaded batch ingestion of English, Portuguese, and CJK documents."""
    en_doc = _load_corpus_file(corpus_dir, "en_02_retrieval_augmented_generation_rev_new.md")
    pt_doc = _load_corpus_file(corpus_dir, "pt_15_lei_geral_de_prote_o_de_dados_pe_rev_new.md")
    cjk_doc = (
        "# 多语言混合处理测试\n\n"
        "自然语言检索系统必须能够同时高效处理多种语言的文档内容。"
        "全角标点符号与拉丁文字母能够共存于同一个索引管道中！\n\n"
        "## 性能与稳定性\n\n"
        "通过并行化处理可以充分利用多核处理器的计算能力……保证零冲突。\n"
    ).encode("utf-8")

    batch = [en_doc, pt_doc, cjk_doc]
    cfg = ChunkerConfig(min_chunk=32, avg_chunk=128, max_chunk=256, mode="boundary")

    results = chunk_documents_batch(batch, config=cfg, num_threads=4)
    assert len(results) == 3

    all_digests = set()
    for doc_idx, doc_chunks in enumerate(results):
        assert len(doc_chunks) >= 1
        original_doc = batch[doc_idx]
        assert sum(c.length for c in doc_chunks) == len(original_doc)
        for c in doc_chunks:
            all_digests.add(c.digest)

    # Ensure zero hash collisions across all multilingual chunks
    total_chunks = sum(len(doc_chunks) for doc_chunks in results)
    assert len(all_digests) == total_chunks, "Hash collision detected in multilingual batch"


# ============================================================================
# Scenario 6: Content-Defined Localized Edit Resynchronization
# ============================================================================

def test_scenario6_cache_resync_after_localized_edit():
    """Demonstrates FastCDC local content property: edits resynchronize boundary cuts downstream."""
    prefix = (
        "# Section 1: Invariant Prefix\n\n"
        "This long section of text establishes baseline boundaries that should remain "
        "completely identical before and after localized modifications downstream.\n\n"
    ).encode("utf-8") * 4

    middle_v1 = b"Original middle paragraph sentence.\n\n"
    middle_v2 = b"Completely rewritten middle paragraph sentence with different length.\n\n"

    suffix = (
        "## Section 2: Invariant Suffix\n\n"
        "This long trailing section tests whether the rolling hash and boundary model "
        "resynchronizes back to identical chunk cuts despite the change above.\n\n"
    ).encode("utf-8") * 4

    doc_v1 = prefix + middle_v1 + suffix
    doc_v2 = prefix + middle_v2 + suffix

    cfg = ChunkerConfig(min_chunk=32, avg_chunk=100, max_chunk=200, mode="boundary")
    chunks_v1 = chunk_documents_batch([doc_v1], config=cfg)[0]
    chunks_v2 = chunk_documents_batch([doc_v2], config=cfg)[0]

    # First few chunks in prefix must be 100% identical in offsets, lengths, and digests
    assert chunks_v1[0].digest == chunks_v2[0].digest
    assert chunks_v1[0].offset == chunks_v2[0].offset
    assert chunks_v1[0].length == chunks_v2[0].length

    # Verify that downstream suffix chunks share identical digests (resynchronization)
    v1_digests = {c.digest for c in chunks_v1}
    v2_digests = {c.digest for c in chunks_v2}
    common = v1_digests & v2_digests
    assert len(common) >= 3, "Failed to resynchronize downstream chunk digests"
