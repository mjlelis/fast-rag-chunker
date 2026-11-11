import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
README_PATH = ROOT_DIR / "README.md"
DEDUP_JSON = ROOT_DIR / "results" / "dedup.json"
THROUGHPUT_JSON = ROOT_DIR / "results" / "throughput.json"


def build_dedup_table(dedup_data: dict) -> str:
    lines = [
        "| Splitter / Configuration | Top Insert | Mid-Sentence | Deletion | 5 Scattered | Moved Para | Whitespace | Real Wiki (EN+PT) | Mean Resync (Top Insert) |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for sp in dedup_data["splitters"]:
        sc = sp["scenarios"]
        top = sc["top_insert"]["byte_reuse_ratio"] * 100.0
        mid = sc["mid_sentence_insert"]["byte_reuse_ratio"] * 100.0
        dele = sc["deletion"]["byte_reuse_ratio"] * 100.0
        scat = sc["scattered_edits"]["byte_reuse_ratio"] * 100.0
        mov = sc["moved_paragraph"]["byte_reuse_ratio"] * 100.0
        ws = sc["whitespace_only"]["byte_reuse_ratio"] * 100.0
        real = sc["real_revisions"]["byte_reuse_ratio"] * 100.0
        resync = sc["top_insert"]["resync_distance_mean"]
        lines.append(
            f"| **{sp['label']}** | {top:.1f}% | {mid:.1f}% | {dele:.1f}% | {scat:.1f}% | {mov:.1f}% | {ws:.1f}% | **{real:.1f}%** | {resync:.2f} chunks |"
        )
    return "\n".join(lines)


def build_size_dist_table(dedup_data: dict) -> str:
    lines = [
        "| Splitter / Configuration | Variant | Total Chunks | Min (B) | p5 (B) | p50 / Median (B) | Mean (B) | p95 (B) | Max (B) |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for sp in dedup_data["splitters"]:
        sd = sp["size_distribution"]
        lines.append(
            f"| **{sp['label']}** | `{sp['config_variant']}` | {sd['total_chunks']} | {sd['min']} | {sd['p5']:.1f} | {sd['p50']:.1f} | {sd['mean']:.1f} | {sd['p95']:.1f} | {sd['max']} |"
        )
    return "\n".join(lines)


def build_throughput_table(tp_data: dict) -> str:
    hw = tp_data["hardware"]
    cfg = tp_data["config"]
    header_meta = (
        f"*Hardware environment: CPU `{hw['cpu_model']}` | Logical cores: `{hw['logical_cores']}` | "
        f"Rayon pool threads: `{hw['rayon_threads']}` | Config: `min={cfg['min_chunk']}, avg={cfg['avg_chunk']}, max={cfg['max_chunk']}` | "
        f"Command: `{tp_data['command']}`*\n\n"
    )
    lines = [
        "| Mode & Hashing Configuration | 1 MB (`num_threads=1`) | 100 MB (`num_threads=1`) | Batch 256x4KB (`num_threads=1`) | Batch 256x4KB (`Rayon` Multi-Thread) |",
        "| :--- | ---: | ---: | ---: | ---: |",
    ]
    for row in tp_data["results"]:
        lines.append(
            f"| **{row['label']}** | {row['single_thread_1mb_mb_s']:.2f} MB/s | {row['single_thread_100mb_mb_s']:.2f} MB/s | {row['batch_256x4kb_1_thread_mb_s']:.2f} MB/s | **{row['batch_256x4kb_rayon_mb_s']:.2f} MB/s** |"
        )
    return header_meta + "\n".join(lines)


def replace_section(content: str, marker_name: str, new_block: str) -> str:
    begin_tag = f"<!-- BEGIN_{marker_name} -->"
    end_tag = f"<!-- END_{marker_name} -->"
    start_idx = content.find(begin_tag)
    end_idx = content.find(end_tag)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise RuntimeError(f"Missing or malformed marker {begin_tag} .. {end_tag} in README.md")
    before = content[: start_idx + len(begin_tag)]
    after = content[end_idx:]
    return f"{before}\n{new_block}\n{after}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate README.md tables from results/dedup.json and results/throughput.json"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that README.md matches the generated tables without modifying the file",
    )
    args = parser.parse_args()

    dedup_data = json.loads(DEDUP_JSON.read_text(encoding="utf-8"))
    tp_data = json.loads(THROUGHPUT_JSON.read_text(encoding="utf-8"))

    original = README_PATH.read_text(encoding="utf-8")
    updated = original
    updated = replace_section(updated, "DEDUP_TABLE", build_dedup_table(dedup_data))
    updated = replace_section(updated, "SIZE_DIST_TABLE", build_size_dist_table(dedup_data))
    updated = replace_section(updated, "THROUGHPUT_TABLE", build_throughput_table(tp_data))

    if args.check:
        if updated != original:
            print(
                "ERROR: README.md tables are out of sync with results/*.json. Run `make readme-tables`.",
                file=sys.stderr,
            )
            sys.exit(1)
        print("OK: README.md tables are 100% synchronized with results/*.json.")
    else:
        README_PATH.write_text(updated, encoding="utf-8")
        print("Updated README.md tables from results/dedup.json and results/throughput.json.")


if __name__ == "__main__":
    main()
