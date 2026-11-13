"""Retrieval Evaluation Harness for fast-rag-chunker (v0.3.0)."""

from bench.retrieval.metrics import is_chunk_relevant, ndcg_at_k, recall_at_k, reciprocal_rank
from bench.retrieval.pipeline import RetrievalHarnessPipeline
from bench.retrieval.splitters import ChunkerSpec, build_all_chunkers

__all__ = [
    "ChunkerSpec",
    "RetrievalHarnessPipeline",
    "build_all_chunkers",
    "is_chunk_relevant",
    "ndcg_at_k",
    "recall_at_k",
    "reciprocal_rank",
]
