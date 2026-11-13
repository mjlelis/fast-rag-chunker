import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List

from bench.retrieval.metrics import ndcg_at_k, recall_at_k, reciprocal_rank
from bench.retrieval.pipeline import RetrievalHarnessPipeline
from bench.retrieval.splitters import build_all_chunkers

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CORPUS_DIR = ROOT_DIR / "bench" / "corpus" / "data"
DATA_DIR = ROOT_DIR / "bench" / "retrieval" / "data"
DEFAULT_OUT = ROOT_DIR / "results" / "retrieval.json"


def load_corpus() -> Dict[str, str]:
    """Loads all 30 revised documents from bench/corpus/data/*_rev_new.md."""
    docs = {}
    for p in sorted(CORPUS_DIR.glob("*_rev_new.md")):
        docs[p.name] = p.read_text(encoding="utf-8")
    if not docs:
        raise RuntimeError(f"No corpus documents found in {CORPUS_DIR}")
    return docs


def load_queries_and_qrels() -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Loads evaluation queries and ground-truth relevance judgments."""
    q_path = DATA_DIR / "queries.json"
    r_path = DATA_DIR / "qrels.json"
    if not q_path.exists() or not r_path.exists():
        raise RuntimeError(f"Missing evaluation queries or qrels in {DATA_DIR}")
    queries = json.loads(q_path.read_text(encoding="utf-8"))
    qrels = json.loads(r_path.read_text(encoding="utf-8"))
    return queries, qrels


def evaluate_splitter(
    splitter, docs: Dict[str, str], queries: List[Dict[str, Any]], qrels: Dict[str, Any], top_k: int = 10
) -> Dict[str, Any]:
    # 1. Chunk all documents in corpus
    all_chunks: List[Dict[str, Any]] = []
    total_bytes = 0
    for doc_id, text in docs.items():
        doc_chunks = splitter.split_fn(text, doc_id)
        all_chunks.extend(doc_chunks)
        for c in doc_chunks:
            total_bytes += len(c["content"].encode("utf-8"))

    total_chunks = len(all_chunks)
    avg_chunk_bytes = round(float(total_bytes) / float(max(1, total_chunks)), 1)

    # 2. Build retrieval index
    pipeline = RetrievalHarnessPipeline()
    pipeline.index_chunks(all_chunks)

    # 3. Run queries through pipeline and compute metrics
    recalls_5 = []
    recalls_10 = []
    ndcgs_10 = []
    mrrs = []

    for q in queries:
        q_id = q["query_id"]
        q_text = q["query"]
        qrel = qrels.get(q_id, {})
        retrieved = pipeline.retrieve(q_text, top_k=top_k)

        r5 = recall_at_k(retrieved, qrel, k=5)
        r10 = recall_at_k(retrieved, qrel, k=10)
        n10 = ndcg_at_k(retrieved, qrel, k=10)
        mrr = reciprocal_rank(retrieved, qrel)

        recalls_5.append(r5)
        recalls_10.append(r10)
        ndcgs_10.append(n10)
        mrrs.append(mrr)

    mean_r5 = round(sum(recalls_5) / float(max(1, len(recalls_5))), 4)
    mean_r10 = round(sum(recalls_10) / float(max(1, len(recalls_10))), 4)
    mean_n10 = round(sum(ndcgs_10) / float(max(1, len(ndcgs_10))), 4)
    mean_mrr = round(sum(mrrs) / float(max(1, len(mrrs))), 4)

    return {
        "splitter_id": splitter.splitter_id,
        "family": splitter.family,
        "config_variant": splitter.config_variant,
        "label": splitter.label,
        "total_chunks": total_chunks,
        "avg_chunk_bytes": avg_chunk_bytes,
        "recall_at_5": mean_r5,
        "recall_at_10": mean_r10,
        "ndcg_at_10": mean_n10,
        "mrr": mean_mrr,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Haystack 2.x retrieval evaluation harness across fast-rag-chunker and 5 baselines."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output JSON path (default: results/retrieval.json)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of retrieved documents to evaluate (default: 10)",
    )
    args = parser.parse_args()

    print("Loading bilingual technical and legal corpus (30 documents)...")
    docs = load_corpus()
    print(f"Loaded {len(docs)} documents.")

    print("Loading queries and relevance judgments...")
    queries, qrels = load_queries_and_qrels()
    print(f"Loaded {len(queries)} queries and {len(qrels)} qrels.")

    splitters = build_all_chunkers()
    print(f"\nEvaluating {len(splitters)} chunkers with Haystack 2.x BM25 retrieval pipeline...")

    results = []
    for sp in splitters:
        print(f"\n--- Running evaluation for {sp.label} ---")
        metrics = evaluate_splitter(sp, docs, queries, qrels, top_k=args.top_k)
        print(
            f"  Total Chunks: {metrics['total_chunks']} | Avg Size: {metrics['avg_chunk_bytes']}B | "
            f"Recall@5: {metrics['recall_at_5']:.3f} | Recall@10: {metrics['recall_at_10']:.3f} | "
            f"nDCG@10: {metrics['ndcg_at_10']:.3f} | MRR: {metrics['mrr']:.3f}"
        )
        results.append(metrics)

    output_payload = {
        "benchmark": "retrieval_v0.3.0",
        "command": f"python -m bench.retrieval --out {args.out.as_posix()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "framework": "Haystack 2.12.0 (InMemoryDocumentStore + InMemoryBM25Retriever)",
        "corpus": {
            "total_documents": len(docs),
            "languages": ["en", "pt"],
            "total_queries": len(queries),
        },
        "metrics": ["recall_at_5", "recall_at_10", "ndcg_at_10", "mrr"],
        "splitters": results,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSuccessfully wrote retrieval evaluation results to {args.out}")


if __name__ == "__main__":
    main()
