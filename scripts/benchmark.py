"""Comparative Benchmark & Verification Suite (PEP 8 + Strict Type Hints).

Evaluates:
1. Algorithmic correctness: UTF-8 multi-byte safety and word/sentence boundary snapping.
2. Shift-Effect / Embedding Cache Deduplication Rate: Standard fixed/recursive chunker vs FastCDC Semantic.
3. Throughput & Latency overhead of Semantic Boundary Snapping + FNV-1a 64-bit fingerprinting.
"""

from __future__ import annotations
import math
import time
from typing import List, Set, Tuple

# 256-entry pseudo-random Gear lookup table derived from sleepybishop/fastcdc
# (Copyright (c) 2020 Joseph Calderon, MIT License).
GEAR: List[int] = [
    0x5C95C078, 0x22408989, 0x2D48A214, 0x12842087, 0x530F8AFB, 0x474536B9,
    0x2963B4F1, 0x44CB738B, 0x4EA7403D, 0x4D606B6E, 0x074EC5D3, 0x3AF39D18,
    0x726003CA, 0x37A62A74, 0x51A2F58E, 0x7506358E, 0x5D4AB128, 0x4D4AE17B,
    0x41E85924, 0x470C36F7, 0x4741CBE1, 0x01BB7F30, 0x617C1DE3, 0x2B0C3A1F,
    0x50C48F73, 0x21A82D37, 0x6095ACE0, 0x419167A0, 0x3CAF49B0, 0x40CEA62D,
    0x66BC1C66, 0x545E1DAD, 0x2BFA77CD, 0x6E85DA24, 0x5FB0BDC5, 0x652CFC29,
    0x3A0AE1AB, 0x2837E0F3, 0x6387B70E, 0x13176012, 0x4362C2BB, 0x66D8F4B1,
    0x37FCE834, 0x2C9CD386, 0x21144296, 0x627268A8, 0x650DF537, 0x2805D579,
    0x3B21EBBD, 0x7357ED34, 0x3F58B583, 0x7150DDCA, 0x7362225E, 0x620A6070,
    0x2C5EF529, 0x7B522466, 0x768B78C0, 0x4B54E51E, 0x75FA07E5, 0x06A35FC6,
    0x30B71024, 0x1C8626E1, 0x296AD578, 0x28D7BE2E, 0x1490A05A, 0x7CEE43BD,
    0x698B56E3, 0x09DC0126, 0x4ED6DF6E, 0x02C1BFC7, 0x2A59AD53, 0x29C0E434,
    0x7D6C5278, 0x507940A7, 0x5EF6BA93, 0x68B6AF1E, 0x46537276, 0x611BC766,
    0x155C587D, 0x301BA847, 0x2CC9DDA7, 0x0A438E2C, 0x0A69D514, 0x744C72D3,
    0x4F326B9B, 0x7EF34286, 0x4A0EF8A7, 0x6AE06EBE, 0x669C5372, 0x12402DCB,
    0x5FEAE99D, 0x76C7F4A7, 0x6ABDB79C, 0x0DFAA038, 0x20E2282C, 0x730ED48B,
    0x069DAC2F, 0x168ECF3E, 0x2610E61F, 0x2C512C8E, 0x15FB8C06, 0x5E62BC76,
    0x69555135, 0x0ADB864C, 0x4268F914, 0x349AB3AA, 0x20EDFDB2, 0x51727981,
    0x37B4B3D8, 0x5DD17522, 0x6B2CBFE4, 0x5C47CF9F, 0x30FA1CCD, 0x23DEDB56,
    0x13D1F50A, 0x64EDDEE7, 0x0820B0F7, 0x46E07308, 0x1E2D1DFD, 0x17B06C32,
    0x250036D8, 0x284DBF34, 0x68292EE0, 0x362EC87C, 0x087CB1EB, 0x76B46720,
    0x104130DB, 0x71966387, 0x482DC43F, 0x2388EF25, 0x524144E1, 0x44BD834E,
    0x448E7DA3, 0x3FA6EAF9, 0x3CDA215C, 0x3A500CF3, 0x395CB432, 0x5195129F,
    0x43945F87, 0x51862CA4, 0x56EA8FF1, 0x201034DC, 0x4D328FF5, 0x7D73A909,
    0x6234D379, 0x64CFBF9C, 0x36F6589A, 0x0A2CE98A, 0x5FE4D971, 0x03BC15C5,
    0x44021D33, 0x16C1932B, 0x37503614, 0x1ACAF69D, 0x3F03B779, 0x49E61A03,
    0x1F52D7EA, 0x1C6DDD5C, 0x062218CE, 0x07E7A11A, 0x1905757A, 0x7CE00A53,
    0x49F44F29, 0x4BCC70B5, 0x39FEEA55, 0x5242CEE8, 0x3CE56B85, 0x00B81672,
    0x46BEECCC, 0x3CA0AD56, 0x2396CEE8, 0x78547F40, 0x6B08089B, 0x66A56751,
    0x781E7E46, 0x1E2CF856, 0x3BC13591, 0x494A4202, 0x520494D7, 0x2D87459A,
    0x757555B6, 0x42284CC1, 0x1F478507, 0x75C95DFF, 0x35FF8DD7, 0x4E4757ED,
    0x2E11F88C, 0x5E1B5048, 0x420E6699, 0x226B0695, 0x4D1679B4, 0x5A22646F,
    0x161D1131, 0x125C68D9, 0x1313E32E, 0x4AA85724, 0x21DC7EC1, 0x4FFA29FE,
    0x72968382, 0x1CA8EEF3, 0x3F3B1C28, 0x39C2FB6C, 0x6D76493F, 0x7A22A62E,
    0x789B1C2A, 0x16E0CB53, 0x7DECEEEB, 0x0DC7E1C6, 0x5C75BF3D, 0x52218333,
    0x106DE4D6, 0x7DC64422, 0x65590FF4, 0x2C02EC30, 0x64A9AC67, 0x59CAB2E9,
    0x4A21D2F3, 0x0F616E57, 0x23B54EE8, 0x02730AAA, 0x2F3C634D, 0x7117FC6C,
    0x01AC6F05, 0x5A9ED20C, 0x158C4E2A, 0x42B699F0, 0x0C7C14B3, 0x02BD9641,
    0x15AD56FC, 0x1C722F60, 0x7DA1AF91, 0x23E0DBCB, 0x0E93E12B, 0x64B2791D,
    0x440D2476, 0x588EA8DD, 0x4665A658, 0x7446C418, 0x1877A774, 0x5626407E,
    0x7F63BD46, 0x32D2DBD8, 0x3C790F4A, 0x772B7239, 0x6F8B2826, 0x677FF609,
    0x0DC82C11, 0x23FFE354, 0x2EAC53A6, 0x16139E09, 0x0AFD0DBC, 0x2A4D4237,
    0x56A368C7, 0x234325E4, 0x2DCE9187, 0x32E8EA7E,
]


def fnv1a_64(data: bytes) -> int:
    h = 0xCBF29CE484222325
    for b in data:
        h ^= b
        h = (h * 0x00000100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def is_utf8_char_boundary(byte: int) -> bool:
    return (byte & 0b1100_0000) != 0b1000_0000


def snap_to_semantic_boundary(
    src: bytes, raw_cut: int, min_chunk: int, max_chunk: int
) -> int:
    length = len(src)
    if raw_cut >= length:
        return length

    limit = min(max_chunk, length)
    lookahead_end = min(raw_cut + 64, limit)

    # 1. Priority: Newline or sentence punctuation (. ! ?)
    for idx in range(raw_cut, lookahead_end):
        b = src[idx]
        if b == 10:  # '\n'
            return idx + 1
        if b in (46, 33, 63) and idx + 1 < limit and src[idx + 1] in (32, 9, 10, 13):
            return idx + 2

    # 2. Priority: Whitespace
    for idx in range(raw_cut, lookahead_end):
        if src[idx] in (32, 9, 10, 13):
            return idx + 1

    # 3. Lookbehind for whitespace
    lookbehind_start = min(min_chunk, raw_cut)
    for idx in range(raw_cut - 1, lookbehind_start - 1, -1):
        if src[idx] in (32, 9, 10, 13):
            return idx + 1

    # 4. UTF-8 safe boundary
    utf8_safe = raw_cut
    while utf8_safe < limit and not is_utf8_char_boundary(src[utf8_safe]):
        utf8_safe += 1
    if utf8_safe < limit and is_utf8_char_boundary(src[utf8_safe]):
        return utf8_safe
    while utf8_safe > lookbehind_start and not is_utf8_char_boundary(src[utf8_safe]):
        utf8_safe -= 1
    return max(utf8_safe, 1)


def fastcdc_cut(
    src: bytes, mi: int, ma: int, ns: int, mask_s: int, mask_l: int
) -> int:
    length = len(src)
    fp = 0
    i = min(length, mi)
    n1 = min(ns, length)
    while i < n1:
        fp = ((fp >> 1) + GEAR[src[i]]) & 0xFFFFFFFF
        if (fp & mask_s) == 0:
            return i + 1
        i += 1
    n2 = min(ma, length)
    while i < n2:
        fp = ((fp >> 1) + GEAR[src[i]]) & 0xFFFFFFFF
        if (fp & mask_l) == 0:
            return i + 1
        i += 1
    return i


def python_fastcdc_raw(
    data: bytes, min_chunk: int = 64, max_chunk: int = 512
) -> List[Tuple[int, int, int]]:
    avg = max((min_chunk + max_chunk) // 2, 64)
    bits = max(int(round(math.log2(avg))), 2)
    off = min(min_chunk + (min_chunk + 1) // 2, avg)
    ns = min(avg - off, max_chunk)
    mask_s = (1 << min(max(bits + 1, 1), 31)) - 1
    mask_l = (1 << min(max(bits - 1, 1), 31)) - 1

    chunks: List[Tuple[int, int, int]] = []
    offset = 0
    total = len(data)
    while offset < total:
        rem = data[offset : offset + max_chunk]
        c_len = max(fastcdc_cut(rem, min_chunk, max_chunk, ns, mask_s, mask_l), 1)
        chunks.append((offset, c_len, 0))
        offset += c_len
    return chunks


def python_fastcdc_semantic(
    data: bytes, min_chunk: int = 64, max_chunk: int = 512
) -> List[Tuple[int, int, int]]:
    avg = max((min_chunk + max_chunk) // 2, 64)
    bits = max(int(round(math.log2(avg))), 2)
    off = min(min_chunk + (min_chunk + 1) // 2, avg)
    ns = min(avg - off, max_chunk)
    mask_s = (1 << min(max(bits + 1, 1), 31)) - 1
    mask_l = (1 << min(max(bits - 1, 1), 31)) - 1

    chunks: List[Tuple[int, int, int]] = []
    offset = 0
    total = len(data)
    while offset < total:
        rem = data[offset : offset + max_chunk]
        raw_len = fastcdc_cut(rem, min_chunk, max_chunk, ns, mask_s, mask_l)
        snapped_len = max(
            snap_to_semantic_boundary(rem, raw_len, min_chunk, max_chunk), 1
        )
        chunk_bytes = rem[:snapped_len]
        chunks.append((offset, snapped_len, fnv1a_64(chunk_bytes)))
        offset += snapped_len
    return chunks


def fixed_recursive_splitter(
    data: bytes, chunk_size: int = 256, chunk_overlap: int = 32
) -> List[Tuple[int, int, int]]:
    """Simulates standard framework fixed/recursive sliding window text splitters."""
    chunks: List[Tuple[int, int, int]] = []
    offset = 0
    total = len(data)
    step = max(chunk_size - chunk_overlap, 1)
    while offset < total:
        end = min(offset + chunk_size, total)
        chunk_bytes = data[offset:end]
        chunks.append((offset, end - offset, fnv1a_64(chunk_bytes)))
        if end == total:
            break
        offset += step
    return chunks


def run_verification_and_benchmarks() -> None:
    print("=====================================================================")
    print(" 1. ALGORITHMIC VERIFICATION: UTF-8 & SEMANTIC BOUNDARY SNAPPING")
    print("=====================================================================")
    utf8_corpus = (
        "Arquitetura de Sistemas e Inteligência Artificial: pré-processamento semântico "
        "com FastCDC em Rust. Garante que palavras acentuadas como coração, ação, "
        "computação, soluções e eficiência nunca sejam cortadas ao meio na indexação RAG.\n"
    ).encode("utf-8") * 50

    sem_chunks = python_fastcdc_semantic(utf8_corpus, min_chunk=64, max_chunk=256)
    broken_utf8 = 0
    mid_word_cuts = 0
    for offset, length, chash in sem_chunks:
        piece = utf8_corpus[offset : offset + length]
        try:
            decoded = piece.decode("utf-8")
            if offset + length < len(utf8_corpus) and not decoded[-1].isspace():
                mid_word_cuts += 1
        except UnicodeDecodeError:
            broken_utf8 += 1

    print(f"Total UTF-8 chunks tested : {len(sem_chunks)}")
    print(f"Broken UTF-8 codepoints   : {broken_utf8} (Expected: 0)")
    print(f"Mid-word cuts             : {mid_word_cuts} (Expected: 0)")
    assert broken_utf8 == 0, "UTF-8 boundary violation detected!"
    assert mid_word_cuts == 0, "Mid-word cut detected!"
    print("[PASS] 100% UTF-8 safe and aligned to natural language boundaries.\n")

    print("=====================================================================")
    print(" 2. SHIFT-EFFECT BENCHMARK: INCREMENTAL EDIT DEDUPLICATION RATE")
    print("=====================================================================")
    sections = [
        f"Section {i:04d}: Enterprise RAG architecture requires deterministic content-defined "
        f"chunking to prevent embedding cache invalidation on incremental document edits.\n"
        for i in range(500)
    ]
    base_doc = "".join(sections).encode("utf-8")
    edited_doc = (
        b"NEW EXECUTIVE SUMMARY PARAGRAPH INSERTED AT TOP OF PAGE 1.\n" + base_doc
    )

    fixed_base = fixed_recursive_splitter(base_doc, chunk_size=256, chunk_overlap=32)
    fixed_edit = fixed_recursive_splitter(edited_doc, chunk_size=256, chunk_overlap=32)
    fixed_base_hashes: Set[int] = {h for _, _, h in fixed_base}
    fixed_hits = sum(1 for _, _, h in fixed_edit if h in fixed_base_hashes)
    fixed_hit_pct = (fixed_hits / len(fixed_edit)) * 100.0

    cdc_base = python_fastcdc_semantic(base_doc, min_chunk=64, max_chunk=256)
    cdc_edit = python_fastcdc_semantic(edited_doc, min_chunk=64, max_chunk=256)
    cdc_base_hashes: Set[int] = {h for _, _, h in cdc_base}
    cdc_hits = sum(1 for _, _, h in cdc_edit if h in cdc_base_hashes)
    cdc_hit_pct = (cdc_hits / len(cdc_edit)) * 100.0

    print(f"Document size             : {len(base_doc) / 1024:.1f} KB (500 sections)")
    print("Edit applied              : +59 bytes inserted at byte offset 0 (Page 1)")
    print(f"Fixed/Sliding Splitter    : {fixed_hits}/{len(fixed_edit)} chunks reused ({fixed_hit_pct:.2f}% Embedding Cache Hit Rate)")
    print(f"FastCDC Semantic Chunker  : {cdc_hits}/{len(cdc_edit)} chunks reused ({cdc_hit_pct:.2f}% Embedding Cache Hit Rate)\n")

    print("=====================================================================")
    print(" 3. THROUGHPUT BENCHMARK: RAW FASTCDC vs SEMANTIC SNAPPING")
    print("=====================================================================")
    sample_doc = utf8_corpus * 20  # ~290 KB per doc
    dataset: List[bytes] = [sample_doc for _ in range(10)]
    total_mb = (len(sample_doc) * len(dataset)) / (1024 * 1024)
    print(f"Corpus size: {len(dataset)} documents | Total: {total_mb:.2f} MB")

    t0 = time.perf_counter()
    raw_res = [python_fastcdc_raw(doc, 64, 512) for doc in dataset]
    t1 = time.perf_counter()
    raw_dur = t1 - t0

    t2 = time.perf_counter()
    sem_res = [python_fastcdc_semantic(doc, 64, 512) for doc in dataset]
    t3 = time.perf_counter()
    sem_dur = t3 - t2

    print(f"[Baseline Raw FastCDC]      {raw_dur:.3f} s ({total_mb / raw_dur:.2f} MB/s) | {len(raw_res[0])} chunks/doc")
    print(f"[Semantic Snapping + FNV1a] {sem_dur:.3f} s ({total_mb / sem_dur:.2f} MB/s) | {len(sem_res[0])} chunks/doc")

    try:
        import fast_rag_chunker
        t4 = time.perf_counter()
        rust_raw = fast_rag_chunker.chunk_documents_batch(
            dataset, min_chunk=64, max_chunk=512, semantic_snap=False
        )
        t5 = time.perf_counter()
        t6 = time.perf_counter()
        rust_sem = fast_rag_chunker.chunk_documents_batch(
            dataset, min_chunk=64, max_chunk=512, semantic_snap=True
        )
        t7 = time.perf_counter()
        print(
            f"[Rust PyO3 Raw FastCDC]     {t5 - t4:.4f} s ({total_mb / (t5 - t4):.2f} MB/s) | {len(rust_raw[0])} chunks/doc"
        )
        print(
            f"[Rust PyO3 Semantic Snap]   {t7 - t6:.4f} s ({total_mb / (t7 - t6):.2f} MB/s) | {len(rust_sem[0])} chunks/doc"
        )
    except ImportError:
        print("[Info] Native Rust extension not installed in current venv (run `maturin develop --release`).")


if __name__ == "__main__":
    run_verification_and_benchmarks()
