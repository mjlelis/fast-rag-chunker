import argparse
import json
import math
from pathlib import Path
from typing import Dict, List

from bench.dedup.baselines import ChunkSpan, SplitterSpec, build_all_splitters
from bench.dedup.scenarios import DocumentPair, build_all_scenarios, load_corpus_pairs


def percentile(sorted_vals: List[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    idx = (len(sorted_vals) - 1) * (p / 100.0)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return float(sorted_vals[lo])
    frac = idx - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


def compute_resync_distance(base_spans: List[ChunkSpan], new_spans: List[ChunkSpan]) -> int:
    """
    Measures how many chunks in `new_spans` are missed starting from the first
    diverged chunk until `new_spans` hits a digest present in `base_spans`.
    If `new_spans` never resynchronizes after diverging, returns the number of
    remaining chunks from the divergence point to the end of `new_spans`.
    """
    base_digests = {s.digest for s in base_spans}
    first_miss = None
    for idx, s in enumerate(new_spans):
        if s.digest not in base_digests:
            first_miss = idx
            break
    if first_miss is None:
        return 0
    for idx in range(first_miss + 1, len(new_spans)):
        if new_spans[idx].digest in base_digests:
            return idx - first_miss
    return len(new_spans) - first_miss


def evaluate_splitter_on_scenario(
    splitter: SplitterSpec, pairs: List[DocumentPair]
) -> Dict[str, object]:
    total_new_chunks = 0
    reused_new_chunks = 0
    total_new_bytes = 0
    reused_new_bytes = 0
    resync_distances: List[float] = []

    for pair in pairs:
        base_spans = splitter.split_fn(pair.old_bytes)
        new_spans = splitter.split_fn(pair.new_bytes)
        base_digests = {s.digest for s in base_spans}

        for s in new_spans:
            total_new_chunks += 1
            total_new_bytes += s.length
            if s.digest in base_digests:
                reused_new_chunks += 1
                reused_new_bytes += s.length

        resync_distances.append(float(compute_resync_distance(base_spans, new_spans)))

    resync_sorted = sorted(resync_distances)
    chunk_reuse_ratio = reused_new_chunks / max(1, total_new_chunks)
    byte_reuse_ratio = reused_new_bytes / max(1, total_new_bytes)
    bytes_to_reembed_ratio = 1.0 - byte_reuse_ratio

    return {
        "documents": len(pairs),
        "total_edited_chunks": total_new_chunks,
        "reused_chunks": reused_new_chunks,
        "chunk_reuse_ratio": round(chunk_reuse_ratio, 6),
        "total_edited_bytes": total_new_bytes,
        "reused_bytes": reused_new_bytes,
        "bytes_to_reembed": total_new_bytes - reused_new_bytes,
        "byte_reuse_ratio": round(byte_reuse_ratio, 6),
        "bytes_to_reembed_ratio": round(bytes_to_reembed_ratio, 6),
        "resync_distance_mean": round(sum(resync_distances) / max(1, len(resync_distances)), 2),
        "resync_distance_p50": round(percentile(resync_sorted, 50), 2),
        "resync_distance_p95": round(percentile(resync_sorted, 95), 2),
    }


def evaluate_size_distribution(
    splitter: SplitterSpec, base_pairs: List[DocumentPair]
) -> Dict[str, object]:
    lengths: List[float] = []
    for pair in base_pairs:
        spans = splitter.split_fn(pair.old_bytes)
        for s in spans:
            lengths.append(float(s.length))

    lengths_sorted = sorted(lengths)
    return {
        "total_chunks": len(lengths_sorted),
        "min": int(lengths_sorted[0]) if lengths_sorted else 0,
        "p5": round(percentile(lengths_sorted, 5), 1),
        "p50": round(percentile(lengths_sorted, 50), 1),
        "p95": round(percentile(lengths_sorted, 95), 1),
        "max": int(lengths_sorted[-1]) if lengths_sorted else 0,
        "mean": round(sum(lengths_sorted) / max(1, len(lengths_sorted)), 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deduplication benchmark across fast-rag-chunker and 5 RAG baselines."
    )
    parser.add_argument(
        "--out",
        default="results/dedup.json",
        help="Output JSON path (default: results/dedup.json)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic random seed for synthetic edit scenarios (default: 42)",
    )
    args = parser.parse_args()

    splitters = build_all_splitters()
    base_pairs = load_corpus_pairs()
    scenarios = build_all_scenarios(seed=args.seed)

    splitter_reports = []
    for sp in splitters:
        size_dist = evaluate_size_distribution(sp, base_pairs)
        scenario_metrics: Dict[str, Dict[str, object]] = {}
        for scen_id, scen_label, scen_pairs in scenarios:
            metrics = evaluate_splitter_on_scenario(sp, scen_pairs)
            metrics["scenario_label"] = scen_label
            scenario_metrics[scen_id] = metrics

        splitter_reports.append(
            {
                "splitter_id": sp.splitter_id,
                "family": sp.family,
                "config_variant": sp.config_variant,
                "label": sp.label,
                "size_distribution": size_dist,
                "scenarios": scenario_metrics,
            }
        )
        top_reuse = scenario_metrics["top_insert"]["byte_reuse_ratio"] * 100.0
        real_reuse = scenario_metrics["real_revisions"]["byte_reuse_ratio"] * 100.0
        print(
            f"[done] {sp.label:<58} | Top-Insert Reuse: {top_reuse:6.2f}% | Real-Wiki Reuse: {real_reuse:6.2f}%"
        )

    payload = {
        "benchmark": "dedup_v0.2.0",
        "command": "python -m bench.dedup --out results/dedup.json",
        "seed": args.seed,
        "corpus": {
            "manifest": "bench/corpus/manifest.json",
            "license": "CC-BY-SA-4.0",
            "total_documents": len(base_pairs),
            "languages": ["en", "pt"],
        },
        "scenarios": [
            {"id": scen_id, "label": scen_label, "documents": len(scen_pairs)}
            for scen_id, scen_label, scen_pairs in scenarios
        ],
        "splitters": splitter_reports,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote deduplication benchmark report to {out_path}")


if __name__ == "__main__":
    main()
