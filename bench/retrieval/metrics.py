import math
from typing import Any, Dict, List


def is_chunk_relevant(chunk: Dict[str, Any], qrel: Dict[str, Any]) -> bool:
    """
    Determines whether a candidate chunk contains or substantially overlaps
    the ground-truth target passage answering the query.
    """
    if chunk.get("doc_id") != qrel.get("doc_id"):
        return False

    # Check span overlap if offsets are provided
    c_off = chunk.get("offset")
    c_len = chunk.get("length")
    q_start = qrel.get("start_char")
    q_end = qrel.get("end_char")

    if c_off is not None and c_len is not None and q_start is not None and q_end is not None:
        c_end = c_off + c_len
        overlap_start = max(c_off, q_start)
        overlap_end = min(c_end, q_end)
        if overlap_end > overlap_start:
            overlap = overlap_end - overlap_start
            target_span = max(1, q_end - q_start)
            # If the chunk covers at least 30% of the target answer, or the target answer
            # constitutes at least 30% of the chunk, it is relevant
            if (overlap / target_span >= 0.25) or (overlap / max(1, c_len) >= 0.25):
                return True

    # Fallback text substring and keyword term matching
    content = chunk.get("content", "").lower()
    anchor = qrel.get("anchor", "").lower()
    if anchor and len(anchor) > 30:
        snippet = anchor[:min(60, len(anchor))]
        if snippet in content:
            return True

    key_terms = qrel.get("key_terms", [])
    if key_terms:
        matches = sum(1 for term in key_terms if term.lower() in content)
        if matches >= max(2, int(len(key_terms) * 0.7)):
            return True

    return False


def recall_at_k(retrieved: List[Dict[str, Any]], qrel: Dict[str, Any], k: int) -> float:
    """
    Computes Recall@K (HitRate@K): 1.0 if any relevant chunk is in the top K, else 0.0.
    """
    top_k = retrieved[:k]
    for c in top_k:
        if is_chunk_relevant(c, qrel):
            return 1.0
    return 0.0


def ndcg_at_k(retrieved: List[Dict[str, Any]], qrel: Dict[str, Any], k: int = 10) -> float:
    """
    Computes Normalized Discounted Cumulative Gain at rank K (nDCG@K).
    """
    top_k = retrieved[:k]
    dcg = 0.0
    rel_count = 0
    for idx, c in enumerate(top_k):
        if is_chunk_relevant(c, qrel):
            dcg += 1.0 / math.log2(idx + 2)  # rank is idx + 1, so log2(rank + 1) = log2(idx + 2)
            rel_count += 1

    if rel_count == 0:
        return 0.0

    # Ideal DCG with all relevant chunks at the very top
    idcg = 0.0
    for rank in range(1, rel_count + 1):
        idcg += 1.0 / math.log2(rank + 1)

    return dcg / idcg if idcg > 0.0 else 0.0


def reciprocal_rank(retrieved: List[Dict[str, Any]], qrel: Dict[str, Any]) -> float:
    """
    Computes Mean Reciprocal Rank (MRR): 1 / rank of the first relevant retrieved chunk.
    """
    for idx, c in enumerate(retrieved):
        if is_chunk_relevant(c, qrel):
            return 1.0 / float(idx + 1)
    return 0.0
