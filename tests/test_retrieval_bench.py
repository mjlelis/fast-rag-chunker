import json
from pathlib import Path
import pytest

from bench.retrieval.metrics import is_chunk_relevant, ndcg_at_k, recall_at_k, reciprocal_rank
from bench.retrieval.pipeline import RetrievalHarnessPipeline
from bench.retrieval.splitters import build_all_chunkers


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "bench" / "retrieval" / "data"
RESULTS_FILE = REPO_ROOT / "results" / "retrieval.json"


def test_queries_and_qrels_datasets_exist_and_match():
    q_file = DATA_DIR / "queries.json"
    r_file = DATA_DIR / "qrels.json"
    assert q_file.exists(), "queries.json must exist"
    assert r_file.exists(), "qrels.json must exist"

    queries = json.loads(q_file.read_text(encoding="utf-8"))
    qrels = json.loads(r_file.read_text(encoding="utf-8"))

    assert len(queries) == 50, "Must contain exactly 50 evaluation queries"
    assert len(qrels) == 50, "Must contain exactly 50 qrels judgments"

    for q in queries:
        qid = q["query_id"]
        assert qid in qrels, f"Query {qid} missing in qrels"
        assert q["doc_id"] == qrels[qid]["doc_id"]
        assert len(qrels[qid]["key_terms"]) >= 2


def test_retrieval_metrics_exact_behavior():
    qrel = {
        "doc_id": "doc_test.md",
        "start_char": 100,
        "end_char": 200,
        "anchor": "A fast content-defined chunking engine optimizes cache reuse.",
        "key_terms": ["content-defined", "chunking", "engine", "cache", "reuse"],
    }

    # Relevant chunk (overlaps target span)
    relevant_chunk = {
        "doc_id": "doc_test.md",
        "chunk_id": "doc_test.md#chunk_1",
        "content": "A fast content-defined chunking engine optimizes cache reuse across document revisions.",
        "offset": 90,
        "length": 100,
    }

    # Irrelevant chunk (different doc or disjoint span)
    irrelevant_chunk_other_doc = {
        "doc_id": "other.md",
        "chunk_id": "other.md#chunk_0",
        "content": "A fast content-defined chunking engine optimizes cache reuse.",
        "offset": 100,
        "length": 100,
    }

    irrelevant_chunk_disjoint = {
        "doc_id": "doc_test.md",
        "chunk_id": "doc_test.md#chunk_99",
        "content": "Completely unrelated content about cooking recipes.",
        "offset": 5000,
        "length": 50,
    }

    assert is_chunk_relevant(relevant_chunk, qrel) is True
    assert is_chunk_relevant(irrelevant_chunk_other_doc, qrel) is False
    assert is_chunk_relevant(irrelevant_chunk_disjoint, qrel) is False

    # Test Recall@K
    retrieved_hit_at_1 = [relevant_chunk, irrelevant_chunk_disjoint]
    retrieved_miss = [irrelevant_chunk_disjoint]

    assert recall_at_k(retrieved_hit_at_1, qrel, k=1) == 1.0
    assert recall_at_k(retrieved_hit_at_1, qrel, k=5) == 1.0
    assert recall_at_k(retrieved_miss, qrel, k=5) == 0.0

    # Test MRR
    assert reciprocal_rank(retrieved_hit_at_1, qrel) == 1.0
    retrieved_hit_at_2 = [irrelevant_chunk_disjoint, relevant_chunk]
    assert reciprocal_rank(retrieved_hit_at_2, qrel) == 0.5
    assert reciprocal_rank(retrieved_miss, qrel) == 0.0

    # Test nDCG@10
    assert ndcg_at_k(retrieved_hit_at_1, qrel, k=10) == 1.0
    assert ndcg_at_k(retrieved_hit_at_2, qrel, k=10) == pytest.approx(0.6309, abs=0.01)
    assert ndcg_at_k(retrieved_miss, qrel, k=10) == 0.0


def test_all_six_chunkers_produce_valid_chunks():
    chunkers = build_all_chunkers()
    assert len(chunkers) == 6

    sample_doc = (
        "# Introduction to Distributed Computing\n\n"
        "Distributed systems achieve consensus by exchanging messages across network nodes. "
        "The Raft algorithm elects a leader to manage log replication.\n\n"
        "## Fault Tolerance\n\n"
        "Crash fault tolerance handles stopped processes without malicious behavior.\n"
    )

    for ch in chunkers:
        chunks = ch.split_fn(sample_doc, "sample.md")
        assert len(chunks) >= 1, f"Chunker {ch.label} emitted 0 chunks"
        for c in chunks:
            assert c["doc_id"] == "sample.md"
            assert "content" in c and len(c["content"]) > 0
            assert "offset" in c
            assert "length" in c


def test_retrieval_pipeline_indexing_and_scoring():
    chunks = [
        {
            "doc_id": "d1.md",
            "chunk_id": "d1.md#0",
            "content": "Raft is a consensus algorithm for distributed log replication.",
            "offset": 0,
            "length": 62,
        },
        {
            "doc_id": "d2.md",
            "chunk_id": "d2.md#0",
            "content": "A B-tree is a self-balancing search tree data structure.",
            "offset": 0,
            "length": 56,
        },
        {
            "doc_id": "d3.md",
            "chunk_id": "d3.md#0",
            "content": "LGPD regula o tratamento de dados pessoais no Brasil.",
            "offset": 0,
            "length": 53,
        },
    ]

    pipe = RetrievalHarnessPipeline()
    pipe.index_chunks(chunks)

    results_raft = pipe.retrieve("Raft consensus leader", top_k=2)
    assert len(results_raft) >= 1
    assert results_raft[0]["doc_id"] == "d1.md"

    results_lgpd = pipe.retrieve("dados pessoais LGPD", top_k=2)
    assert len(results_lgpd) >= 1
    assert results_lgpd[0]["doc_id"] == "d3.md"


def test_retrieval_results_json_schema_and_values():
    assert RESULTS_FILE.exists(), "results/retrieval.json must exist"
    data = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))

    assert data["benchmark"] == "retrieval_v0.3.0"
    assert data["corpus"]["total_documents"] == 30
    assert data["corpus"]["total_queries"] == 50
    assert "metrics" in data

    splitters = data["splitters"]
    assert len(splitters) == 6

    splitter_ids = {s["splitter_id"] for s in splitters}
    expected_ids = {
        "fast_rag_boundary",
        "haystack_doc_splitter",
        "langchain_recursive",
        "llamaindex_sentence",
        "fixed_window",
        "paragraph_split",
    }
    assert splitter_ids == expected_ids

    for sp in splitters:
        assert 0.0 <= sp["recall_at_5"] <= 1.0
        assert 0.0 <= sp["recall_at_10"] <= 1.0
        assert 0.0 <= sp["ndcg_at_10"] <= 1.0
        assert 0.0 <= sp["mrr"] <= 1.0
        assert sp["recall_at_5"] <= sp["recall_at_10"]
        assert sp["total_chunks"] > 0
        assert sp["avg_chunk_bytes"] > 0
