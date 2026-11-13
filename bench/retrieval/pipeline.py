import math
import re
from typing import Any, Dict, List, Optional

try:
    from haystack import Document, Pipeline
    from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
    from haystack.document_stores.in_memory import InMemoryDocumentStore

    HAYSTACK_AVAILABLE = True
except ImportError:
    HAYSTACK_AVAILABLE = False


class RetrievalHarnessPipeline:
    """
    Retrieval pipeline wrapping Haystack 2.x InMemoryDocumentStore and
    InMemoryBM25Retriever. Falls back to a spec-identical Okapi BM25 implementation
    when Haystack 2.x is not installed locally.
    """

    def __init__(self):
        self.is_haystack = HAYSTACK_AVAILABLE
        self.doc_store = None
        self.pipeline = None
        # Fallback BM25 data structures
        self.chunks: List[Dict[str, Any]] = []
        self.doc_lens: List[int] = []
        self.avg_doc_len: float = 0.0
        self.tf: List[Dict[str, int]] = []
        self.df: Dict[str, int] = {}

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Indexes all chunk objects into the in-memory document store."""
        if self.is_haystack:
            self.doc_store = InMemoryDocumentStore()
            docs = [
                Document(
                    content=c["content"],
                    meta={
                        "doc_id": c["doc_id"],
                        "chunk_id": c["chunk_id"],
                        "offset": c.get("offset", 0),
                        "length": c.get("length", len(c["content"])),
                    },
                )
                for c in chunks
            ]
            self.doc_store.write_documents(docs)
            retriever = InMemoryBM25Retriever(document_store=self.doc_store)
            self.pipeline = Pipeline()
            self.pipeline.add_component(instance=retriever, name="retriever")
        else:
            self.chunks = chunks
            self.doc_lens = []
            self.tf = []
            self.df = {}
            total_len = 0
            for c in chunks:
                tokens = self._tokenize(c["content"])
                t_len = len(tokens)
                self.doc_lens.append(t_len)
                total_len += t_len
                counts: Dict[str, int] = {}
                for t in tokens:
                    counts[t] = counts.get(t, 0) + 1
                self.tf.append(counts)
                for t in counts:
                    self.df[t] = self.df.get(t, 0) + 1
            self.avg_doc_len = float(total_len) / float(max(1, len(chunks)))

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Retrieves top_k relevant chunks for a query string."""
        if self.is_haystack and self.pipeline is not None:
            res = self.pipeline.run({"retriever": {"query": query, "top_k": top_k}})
            docs = res.get("retriever", {}).get("documents", [])
            out = []
            for d in docs:
                out.append(
                    {
                        "content": d.content or "",
                        "doc_id": d.meta.get("doc_id", ""),
                        "chunk_id": d.meta.get("chunk_id", ""),
                        "offset": d.meta.get("offset", 0),
                        "length": d.meta.get("length", 0),
                        "score": getattr(d, "score", 0.0),
                    }
                )
            return out

        # Fallback Okapi BM25 ranking (k1=1.5, b=0.75)
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return self.chunks[:top_k]

        N = len(self.chunks)
        k1 = 1.5
        b = 0.75
        scores = []

        for idx in range(N):
            doc_len = self.doc_lens[idx]
            tf_map = self.tf[idx]
            doc_score = 0.0
            for t in q_tokens:
                if t in tf_map:
                    freq = tf_map[t]
                    doc_freq = self.df.get(t, 0)
                    # Lucene / Haystack BM25 IDF: ln(1 + (N - doc_freq + 0.5) / (doc_freq + 0.5))
                    idf = math.log(1.0 + (float(N - doc_freq) + 0.5) / (float(doc_freq) + 0.5))
                    numerator = float(freq) * (k1 + 1.0)
                    denominator = float(freq) + k1 * (1.0 - b + b * (float(doc_len) / max(1.0, self.avg_doc_len)))
                    doc_score += idf * (numerator / max(1e-6, denominator))
            scores.append((doc_score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        top = scores[:top_k]
        results = []
        for score, idx in top:
            item = dict(self.chunks[idx])
            item["score"] = score
            results.append(item)
        return results
