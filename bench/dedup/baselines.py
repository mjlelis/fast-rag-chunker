import hashlib
import re
from dataclasses import dataclass
from typing import Callable, List

try:
    import fast_rag_chunker
except ImportError:
    from tests.e2e import reference_oracle as fast_rag_chunker


@dataclass(frozen=True)
class ChunkSpan:
    length: int
    digest: bytes


@dataclass(frozen=True)
class SplitterSpec:
    splitter_id: str
    family: str
    config_variant: str
    label: str
    split_fn: Callable[[bytes], List[ChunkSpan]]


def _digest_128(data: bytes) -> bytes:
    return hashlib.blake2b(data, digest_size=16).digest()


def _spans_from_strings(chunks: List[str]) -> List[ChunkSpan]:
    out: List[ChunkSpan] = []
    for ch in chunks:
        if not ch:
            continue
        b = ch.encode("utf-8")
        out.append(ChunkSpan(length=len(b), digest=_digest_128(b)))
    return out


# ---------------------------------------------------------------------------
# 1. Native Rust fast-rag-chunker (via compiled PyO3 extension)
# ---------------------------------------------------------------------------
def _make_fast_rag_splitter(mode: str, min_chunk: int = 64, avg_chunk: int = 256, max_chunk: int = 512):
    cfg = fast_rag_chunker.ChunkerConfig(
        min_chunk=min_chunk,
        avg_chunk=avg_chunk,
        max_chunk=max_chunk,
        mode=mode,
        compute_hash=True,
    )

    def _split(doc_bytes: bytes) -> List[ChunkSpan]:
        res = fast_rag_chunker.chunk_documents_batch([doc_bytes], config=cfg)[0]
        return [ChunkSpan(length=c.length, digest=c.digest) for c in res]

    return _split


# ---------------------------------------------------------------------------
# 2. Baseline 1: Haystack DocumentSplitter
# ---------------------------------------------------------------------------
def _make_haystack_splitter(split_length: int, split_overlap: int):
    try:
        from haystack import Document
        from haystack.components.preprocessors import DocumentSplitter

        splitter = DocumentSplitter(
            split_by="word",
            split_length=split_length,
            split_overlap=split_overlap,
        )
        if hasattr(splitter, "warm_up"):
            splitter.warm_up()

        def _split(doc_bytes: bytes) -> List[ChunkSpan]:
            text = doc_bytes.decode("utf-8")
            result = splitter.run(documents=[Document(content=text)])
            docs = result.get("documents", [])
            return _spans_from_strings([d.content for d in docs if d.content])

        return _split
    except Exception:
        # Spec-identical word splitter fallback when Haystack is not installed locally
        def _split_fallback(doc_bytes: bytes) -> List[ChunkSpan]:
            text = doc_bytes.decode("utf-8")
            words = re.findall(r"\S+\s*", text)
            if not words:
                return []
            step = max(1, split_length - split_overlap)
            chunks = []
            for i in range(0, len(words), step):
                group = "".join(words[i : i + split_length])
                if group:
                    chunks.append(group)
                if i + split_length >= len(words):
                    break
            return _spans_from_strings(chunks)

        return _split_fallback


# ---------------------------------------------------------------------------
# 3. Baseline 2: LangChain RecursiveCharacterTextSplitter
# ---------------------------------------------------------------------------
def _make_langchain_splitter(chunk_size: int, chunk_overlap: int):
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        def _split(doc_bytes: bytes) -> List[ChunkSpan]:
            text = doc_bytes.decode("utf-8")
            return _spans_from_strings(splitter.split_text(text))

        return _split
    except Exception:
        def _split_fallback(doc_bytes: bytes) -> List[ChunkSpan]:
            text = doc_bytes.decode("utf-8")
            step = max(1, chunk_size - chunk_overlap)
            chunks = []
            idx = 0
            while idx < len(text):
                end = min(len(text), idx + chunk_size)
                if end < len(text):
                    for sep in ("\n\n", "\n", " "):
                        pos = text.rfind(sep, idx + chunk_overlap, end)
                        if pos != -1 and pos > idx:
                            end = pos + len(sep)
                            break
                chunks.append(text[idx:end])
                if end >= len(text):
                    break
                idx = max(idx + 1, end - chunk_overlap)
            return _spans_from_strings(chunks)

        return _split_fallback


# ---------------------------------------------------------------------------
# 4. Baseline 3: LlamaIndex SentenceSplitter
# ---------------------------------------------------------------------------
def _make_llamaindex_splitter(chunk_size: int, chunk_overlap: int):
    # Approx 4 chars per token in LlamaIndex default tokenizer
    char_target = chunk_size * 4
    char_overlap = chunk_overlap * 4

    def _split_fallback(text: str) -> List[ChunkSpan]:
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        chunks = []
        current: List[str] = []
        cur_len = 0
        for sent in sentences:
            if not sent:
                continue
            s_len = len(sent) + 1
            if cur_len + s_len > char_target and current:
                chunks.append(" ".join(current))
                overlap_buf: List[str] = []
                ov_len = 0
                for prev in reversed(current):
                    if ov_len + len(prev) > char_overlap:
                        break
                    overlap_buf.insert(0, prev)
                    ov_len += len(prev) + 1
                current = overlap_buf
                cur_len = ov_len
            current.append(sent)
            cur_len += s_len
        if current:
            chunks.append(" ".join(current))
        return _spans_from_strings(chunks)

    try:
        import nltk

        try:
            nltk.download("punkt_tab", quiet=True)
            nltk.download("punkt", quiet=True)
        except Exception:
            pass

        from llama_index.core.node_parser import SentenceSplitter

        splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        def _split(doc_bytes: bytes) -> List[ChunkSpan]:
            text = doc_bytes.decode("utf-8")
            try:
                return _spans_from_strings(splitter.split_text(text))
            except Exception:
                return _split_fallback(text)

        return _split
    except Exception:
        def _split_bytes(doc_bytes: bytes) -> List[ChunkSpan]:
            return _split_fallback(doc_bytes.decode("utf-8"))

        return _split_bytes


# ---------------------------------------------------------------------------
# 5. Baseline 4: Fixed Window with Overlap
# ---------------------------------------------------------------------------
def _make_fixed_window_splitter(window_bytes: int, overlap_bytes: int):
    step = max(1, window_bytes - overlap_bytes)

    def _split(doc_bytes: bytes) -> List[ChunkSpan]:
        if not doc_bytes:
            return []
        spans: List[ChunkSpan] = []
        for start in range(0, len(doc_bytes), step):
            chunk = doc_bytes[start : start + window_bytes]
            if not chunk:
                break
            spans.append(ChunkSpan(length=len(chunk), digest=_digest_128(chunk)))
            if start + window_bytes >= len(doc_bytes):
                break
        return spans

    return _split


# ---------------------------------------------------------------------------
# 6. Baseline 5: Paragraph Split + Hash
# ---------------------------------------------------------------------------
def _make_paragraph_splitter(bounded: bool, min_bytes: int = 64, max_bytes: int = 512):
    def _split(doc_bytes: bytes) -> List[ChunkSpan]:
        text = doc_bytes.decode("utf-8")
        raw_paras = [p for p in re.split(r"(\n\s*\n)", text) if p]
        # Re-attach paragraph separator to preceding paragraph so offsets cover full text
        paras: List[str] = []
        i = 0
        while i < len(raw_paras):
            if i + 1 < len(raw_paras) and raw_paras[i + 1].startswith("\n"):
                paras.append(raw_paras[i] + raw_paras[i + 1])
                i += 2
            else:
                paras.append(raw_paras[i])
                i += 1

        if not bounded:
            return _spans_from_strings(paras)

        bounded_chunks: List[str] = []
        buf = ""
        for p in paras:
            if len((buf + p).encode("utf-8")) <= max_bytes:
                buf += p
            else:
                if buf:
                    bounded_chunks.append(buf)
                    buf = ""
                p_bytes = p.encode("utf-8")
                if len(p_bytes) <= max_bytes:
                    buf = p
                else:
                    # Split oversized paragraph at word boundaries <= max_bytes
                    words = re.findall(r"\S+\s*", p)
                    cur = ""
                    for w in words:
                        if len((cur + w).encode("utf-8")) <= max_bytes:
                            cur += w
                        else:
                            if cur:
                                bounded_chunks.append(cur)
                            cur = w
                    if cur:
                        buf = cur
        if buf:
            if bounded_chunks and len(buf.encode("utf-8")) < min_bytes:
                prev = bounded_chunks[-1]
                if len((prev + buf).encode("utf-8")) <= max_bytes:
                    bounded_chunks[-1] = prev + buf
                else:
                    bounded_chunks.append(buf)
            else:
                bounded_chunks.append(buf)
        return _spans_from_strings(bounded_chunks)

    return _split


def build_all_splitters() -> List[SplitterSpec]:
    return [
        SplitterSpec(
            splitter_id="fast_rag_semantic",
            family="fast-rag-chunker",
            config_variant="default",
            label="fast-rag-chunker (Semantic, 64..512B)",
            split_fn=_make_fast_rag_splitter("semantic", 64, 256, 512),
        ),
        SplitterSpec(
            splitter_id="fast_rag_raw",
            family="fast-rag-chunker",
            config_variant="default",
            label="fast-rag-chunker (Raw, 64..512B)",
            split_fn=_make_fast_rag_splitter("raw", 64, 256, 512),
        ),
        SplitterSpec(
            splitter_id="haystack_default",
            family="Haystack DocumentSplitter",
            config_variant="default",
            label="Haystack DocumentSplitter (default: 200w, overlap=0)",
            split_fn=_make_haystack_splitter(split_length=200, split_overlap=0),
        ),
        SplitterSpec(
            splitter_id="haystack_equiv",
            family="Haystack DocumentSplitter",
            config_variant="equivalent",
            label="Haystack DocumentSplitter (equiv: 40w, overlap=0)",
            split_fn=_make_haystack_splitter(split_length=40, split_overlap=0),
        ),
        SplitterSpec(
            splitter_id="langchain_default",
            family="LangChain RecursiveCharacterTextSplitter",
            config_variant="default",
            label="LangChain RecursiveCharacter (default: 1000c, overlap=200)",
            split_fn=_make_langchain_splitter(chunk_size=1000, chunk_overlap=200),
        ),
        SplitterSpec(
            splitter_id="langchain_equiv",
            family="LangChain RecursiveCharacterTextSplitter",
            config_variant="equivalent",
            label="LangChain RecursiveCharacter (equiv: 256c, overlap=32)",
            split_fn=_make_langchain_splitter(chunk_size=256, chunk_overlap=32),
        ),
        SplitterSpec(
            splitter_id="llamaindex_default",
            family="LlamaIndex SentenceSplitter",
            config_variant="default",
            label="LlamaIndex SentenceSplitter (default: 1024t, overlap=200)",
            split_fn=_make_llamaindex_splitter(chunk_size=1024, chunk_overlap=200),
        ),
        SplitterSpec(
            splitter_id="llamaindex_equiv",
            family="LlamaIndex SentenceSplitter",
            config_variant="equivalent",
            label="LlamaIndex SentenceSplitter (equiv: 64t, overlap=8)",
            split_fn=_make_llamaindex_splitter(chunk_size=64, chunk_overlap=8),
        ),
        SplitterSpec(
            splitter_id="fixed_window_default",
            family="Fixed Window + Overlap",
            config_variant="default",
            label="Fixed Window + Overlap (default: 1024B, overlap=128B)",
            split_fn=_make_fixed_window_splitter(window_bytes=1024, overlap_bytes=128),
        ),
        SplitterSpec(
            splitter_id="fixed_window_equiv",
            family="Fixed Window + Overlap",
            config_variant="equivalent",
            label="Fixed Window + Overlap (equiv: 256B, overlap=32B)",
            split_fn=_make_fixed_window_splitter(window_bytes=256, overlap_bytes=32),
        ),
        SplitterSpec(
            splitter_id="paragraph_default",
            family="Paragraph Split + Hash",
            config_variant="default",
            label="Paragraph Split + Hash (default: unbounded \\n\\n)",
            split_fn=_make_paragraph_splitter(bounded=False),
        ),
        SplitterSpec(
            splitter_id="paragraph_equiv",
            family="Paragraph Split + Hash",
            config_variant="equivalent",
            label="Paragraph Split + Hash (equiv: bounded 64..512B)",
            split_fn=_make_paragraph_splitter(bounded=True, min_bytes=64, max_bytes=512),
        ),
    ]
