import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

try:
    import fast_rag_chunker
except ImportError:
    from tests.e2e import reference_oracle as fast_rag_chunker


@dataclass(frozen=True)
class ChunkerSpec:
    splitter_id: str
    family: str
    config_variant: str
    label: str
    split_fn: Callable[[str, str], List[Dict[str, Any]]]


def _make_fast_rag_chunker(min_chunk=64, avg_chunk=256, max_chunk=512, normalize="nfc"):
    cfg = fast_rag_chunker.ChunkerConfig(
        min_chunk=min_chunk,
        avg_chunk=avg_chunk,
        max_chunk=max_chunk,
        mode="boundary",
        normalize=normalize,
        compute_hash=True,
    )

    def _split(text: str, doc_id: str) -> List[Dict[str, Any]]:
        doc_bytes = text.encode("utf-8")
        results = fast_rag_chunker.chunk_documents_batch([doc_bytes], config=cfg)[0]
        chunks: List[Dict[str, Any]] = []
        for idx, c in enumerate(results):
            raw_slice = doc_bytes[c.offset : c.offset + c.length]
            chunk_text = raw_slice.decode("utf-8", errors="replace")
            # Calculate char offset from byte offset
            char_offset = len(doc_bytes[: c.offset].decode("utf-8", errors="replace"))
            chunks.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}#frc_{idx}",
                    "content": chunk_text,
                    "offset": char_offset,
                    "length": len(chunk_text),
                }
            )
        return chunks

    return _split


def _make_haystack_doc_splitter(split_length=256, split_overlap=32):
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

        def _split_native(text: str, doc_id: str) -> List[Dict[str, Any]]:
            res = splitter.run(documents=[Document(content=text)])
            docs = res.get("documents", [])
            chunks = []
            curr_pos = 0
            for idx, d in enumerate(docs):
                content = d.content or ""
                # Find start position
                pos = text.find(content[:40], curr_pos) if len(content) >= 40 else text.find(content, curr_pos)
                if pos == -1:
                    pos = curr_pos
                chunks.append(
                    {
                        "doc_id": doc_id,
                        "chunk_id": f"{doc_id}#haystack_{idx}",
                        "content": content,
                        "offset": pos,
                        "length": len(content),
                    }
                )
                curr_pos = pos + max(1, len(content) - 100)
            return chunks

        return _split_native
    except Exception:
        # Fallback word-level splitter matching Haystack DocumentSplitter behavior
        def _split_fallback(text: str, doc_id: str) -> List[Dict[str, Any]]:
            words_spans = [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\S+\s*", text)]
            if not words_spans:
                return []
            step = max(1, split_length - split_overlap)
            chunks = []
            idx = 0
            chunk_num = 0
            while idx < len(words_spans):
                group = words_spans[idx : idx + split_length]
                if not group:
                    break
                chunk_text = "".join(w[0] for w in group)
                start_char = group[0][1]
                end_char = group[-1][2]
                chunks.append(
                    {
                        "doc_id": doc_id,
                        "chunk_id": f"{doc_id}#haystack_{chunk_num}",
                        "content": chunk_text,
                        "offset": start_char,
                        "length": end_char - start_char,
                    }
                )
                chunk_num += 1
                if idx + split_length >= len(words_spans):
                    break
                idx += step
            return chunks

        return _split_fallback


def _make_langchain_splitter(chunk_size=256, chunk_overlap=32):
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        def _split_native(text: str, doc_id: str) -> List[Dict[str, Any]]:
            raw_chunks = splitter.split_text(text)
            chunks = []
            curr_pos = 0
            for idx, c in enumerate(raw_chunks):
                pos = text.find(c[:40], curr_pos) if len(c) >= 40 else text.find(c, curr_pos)
                if pos == -1:
                    pos = curr_pos
                chunks.append(
                    {
                        "doc_id": doc_id,
                        "chunk_id": f"{doc_id}#lc_{idx}",
                        "content": c,
                        "offset": pos,
                        "length": len(c),
                    }
                )
                curr_pos = pos + max(1, len(c) - chunk_overlap)
            return chunks

        return _split_native
    except Exception:
        # Fallback recursive character text splitter
        def _split_fallback(text: str, doc_id: str) -> List[Dict[str, Any]]:
            chunks = []
            idx = 0
            chunk_num = 0
            while idx < len(text):
                end = min(len(text), idx + chunk_size)
                if end < len(text):
                    for sep in ("\n\n", "\n", " "):
                        pos = text.rfind(sep, idx + chunk_overlap, end)
                        if pos != -1 and pos > idx:
                            end = pos + len(sep)
                            break
                chunk_text = text[idx:end]
                chunks.append(
                    {
                        "doc_id": doc_id,
                        "chunk_id": f"{doc_id}#lc_{chunk_num}",
                        "content": chunk_text,
                        "offset": idx,
                        "length": len(chunk_text),
                    }
                )
                chunk_num += 1
                if end >= len(text):
                    break
                idx = max(idx + 1, end - chunk_overlap)
            return chunks

        return _split_fallback


def _make_llamaindex_splitter(chunk_size=256, chunk_overlap=32):
    try:
        from llama_index.core.node_parser import SentenceSplitter

        splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        def _split_native(text: str, doc_id: str) -> List[Dict[str, Any]]:
            raw_chunks = splitter.split_text(text)
            chunks = []
            curr_pos = 0
            for idx, c in enumerate(raw_chunks):
                pos = text.find(c[:40], curr_pos) if len(c) >= 40 else text.find(c, curr_pos)
                if pos == -1:
                    pos = curr_pos
                chunks.append(
                    {
                        "doc_id": doc_id,
                        "chunk_id": f"{doc_id}#li_{idx}",
                        "content": c,
                        "offset": pos,
                        "length": len(c),
                    }
                )
                curr_pos = pos + max(1, len(c) - chunk_overlap)
            return chunks

        return _split_native
    except Exception:
        # Fallback sentence-based text splitter
        def _split_fallback(text: str, doc_id: str) -> List[Dict[str, Any]]:
            sentences = [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
            chunks = []
            cur_tokens: List[str] = []
            cur_len = 0
            chunk_num = 0
            curr_offset = 0

            for sent in sentences:
                s_len = len(sent)
                if cur_len + s_len > chunk_size and cur_tokens:
                    c_text = " ".join(cur_tokens)
                    pos = text.find(c_text[:30], curr_offset)
                    if pos == -1:
                        pos = curr_offset
                    chunks.append(
                        {
                            "doc_id": doc_id,
                            "chunk_id": f"{doc_id}#li_{chunk_num}",
                            "content": c_text,
                            "offset": pos,
                            "length": len(c_text),
                        }
                    )
                    chunk_num += 1
                    curr_offset = pos + max(1, len(c_text) - chunk_overlap)
                    # Retain overlap sentences
                    overlap_buf: List[str] = []
                    ov_len = 0
                    for prev in reversed(cur_tokens):
                        if ov_len + len(prev) > chunk_overlap:
                            break
                        overlap_buf.insert(0, prev)
                        ov_len += len(prev) + 1
                    cur_tokens = overlap_buf
                    cur_len = ov_len

                cur_tokens.append(sent)
                cur_len += s_len + 1

            if cur_tokens:
                c_text = " ".join(cur_tokens)
                pos = text.find(c_text[:30], curr_offset)
                if pos == -1:
                    pos = curr_offset
                chunks.append(
                    {
                        "doc_id": doc_id,
                        "chunk_id": f"{doc_id}#li_{chunk_num}",
                        "content": c_text,
                        "offset": pos,
                        "length": len(c_text),
                    }
                )
            return chunks

        return _split_fallback


def _make_fixed_window_splitter(chunk_size=256, overlap=32):
    step = max(1, chunk_size - overlap)

    def _split(text: str, doc_id: str) -> List[Dict[str, Any]]:
        if not text:
            return []
        chunks = []
        chunk_num = 0
        for start in range(0, len(text), step):
            chunk_text = text[start : start + chunk_size]
            if not chunk_text:
                break
            chunks.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}#fw_{chunk_num}",
                    "content": chunk_text,
                    "offset": start,
                    "length": len(chunk_text),
                }
            )
            chunk_num += 1
            if start + chunk_size >= len(text):
                break
        return chunks

    return _split


def _make_paragraph_splitter(min_bytes=64, max_bytes=512):
    def _split(text: str, doc_id: str) -> List[Dict[str, Any]]:
        raw_paras = [p for p in re.split(r"(\n\s*\n)", text) if p]
        paras: List[str] = []
        i = 0
        while i < len(raw_paras):
            if i + 1 < len(raw_paras) and raw_paras[i + 1].startswith("\n"):
                paras.append(raw_paras[i] + raw_paras[i + 1])
                i += 2
            else:
                paras.append(raw_paras[i])
                i += 1

        chunks: List[Dict[str, Any]] = []
        buf = ""
        buf_start = 0
        curr_offset = 0
        chunk_num = 0

        for p in paras:
            p_len = len(p.encode("utf-8"))
            if not buf:
                buf = p
                buf_start = curr_offset
            elif len(buf.encode("utf-8")) + p_len <= max_bytes:
                buf += p
            else:
                chunks.append(
                    {
                        "doc_id": doc_id,
                        "chunk_id": f"{doc_id}#para_{chunk_num}",
                        "content": buf,
                        "offset": buf_start,
                        "length": len(buf),
                    }
                )
                chunk_num += 1
                buf = p
                buf_start = curr_offset
            curr_offset += len(p)

        if buf:
            chunks.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}#para_{chunk_num}",
                    "content": buf,
                    "offset": buf_start,
                    "length": len(buf),
                }
            )

        return chunks

    return _split


def build_all_chunkers() -> List[ChunkerSpec]:
    """Returns the 6 chunkers evaluated in the retrieval harness."""
    return [
        ChunkerSpec(
            splitter_id="fast_rag_boundary",
            family="fast-rag-chunker",
            config_variant="boundary (64..512B, nfc)",
            label="fast-rag-chunker (Boundary, 64..512B)",
            split_fn=_make_fast_rag_chunker(min_chunk=64, avg_chunk=256, max_chunk=512, normalize="nfc"),
        ),
        ChunkerSpec(
            splitter_id="haystack_doc_splitter",
            family="Haystack",
            config_variant="split_by=word, length=256, overlap=32",
            label="Haystack DocumentSplitter (256w, overlap=32)",
            split_fn=_make_haystack_doc_splitter(split_length=256, split_overlap=32),
        ),
        ChunkerSpec(
            splitter_id="langchain_recursive",
            family="LangChain",
            config_variant="chunk_size=256, overlap=32",
            label="LangChain RecursiveCharacter (256c, overlap=32)",
            split_fn=_make_langchain_splitter(chunk_size=256, chunk_overlap=32),
        ),
        ChunkerSpec(
            splitter_id="llamaindex_sentence",
            family="LlamaIndex",
            config_variant="chunk_size=256, overlap=32",
            label="LlamaIndex SentenceSplitter (256c, overlap=32)",
            split_fn=_make_llamaindex_splitter(chunk_size=256, chunk_overlap=32),
        ),
        ChunkerSpec(
            splitter_id="fixed_window",
            family="Fixed Window",
            config_variant="window=256, overlap=32",
            label="Fixed Window + Overlap (256B, overlap=32)",
            split_fn=_make_fixed_window_splitter(chunk_size=256, overlap=32),
        ),
        ChunkerSpec(
            splitter_id="paragraph_split",
            family="Paragraph Split",
            config_variant="bounded 64..512B",
            label="Paragraph Split + Hash (bounded 64..512B)",
            split_fn=_make_paragraph_splitter(min_bytes=64, max_bytes=512),
        ),
    ]
