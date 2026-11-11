use std::env;
use std::fs;
use std::hint::black_box;
use std::time::Instant;

use fast_rag_chunker::{chunk_batch_with_config, chunk_with_config, ChunkerConfig, ChunkingMode};

fn build_utf8_corpus(target_bytes: usize) -> Vec<u8> {
    let paragraph = "Arquitetura de Sistemas e Engenharia de Dados para RAG: \
        O algoritmo FastCDC aplica um rolling hash Gear de 64 bits sobre janelas de bytes, \
        permitindo ressincronizar fronteiras de chunks após edições locais no documento. \
        Em conjunto com o alinhamento semântico UTF-8 e resumos criptográficos BLAKE3-128, \
        pipelines de indexação vetorial evitam o re-embedding desnecessário de trechos inalterados.\n\n";
    let repeat_count = target_bytes.div_ceil(paragraph.len());
    let mut buf = paragraph.repeat(repeat_count).into_bytes();
    buf.truncate(target_bytes);
    buf
}

fn measure_mb_per_sec<F: FnMut() -> usize>(total_bytes: usize, iterations: u32, mut f: F) -> f64 {
    let _ = black_box(f());
    let start = Instant::now();
    for _ in 0..iterations {
        let count = f();
        black_box(count);
    }
    let elapsed = start.elapsed().as_secs_f64().max(1e-9);
    let total_mb = (total_bytes as f64 * f64::from(iterations)) / (1024.0 * 1024.0);
    total_mb / elapsed
}

fn detect_cpu_model() -> String {
    if let Ok(cpuinfo) = fs::read_to_string("/proc/cpuinfo") {
        for line in cpuinfo.lines() {
            if let Some((k, v)) = line.split_once(':') {
                if k.trim() == "model name" {
                    return v.trim().to_string();
                }
            }
        }
    }
    env::consts::ARCH.to_string()
}

fn main() {
    let out_path = env::args()
        .nth(1)
        .unwrap_or_else(|| String::from("results/throughput.json"));

    let logical_cores = std::thread::available_parallelism()
        .map(usize::from)
        .unwrap_or(4);
    let cpu_model = detect_cpu_model();

    let doc_1mb = build_utf8_corpus(1024 * 1024);
    let doc_100mb = build_utf8_corpus(100 * 1024 * 1024);
    let small_doc = build_utf8_corpus(4 * 1024);
    let small_batch_owned: Vec<Vec<u8>> = (0..256).map(|_| small_doc.clone()).collect();
    let small_batch_slices: Vec<&[u8]> = small_batch_owned.iter().map(Vec::as_slice).collect();
    let batch_total_bytes: usize = small_batch_slices.iter().map(|s| s.len()).sum();

    let modes = [
        (
            "raw_no_hash",
            "Raw FastCDC (compute_hash=False)",
            ChunkingMode::Raw,
            false,
        ),
        (
            "raw_with_hash",
            "Raw FastCDC + BLAKE3-128",
            ChunkingMode::Raw,
            true,
        ),
        (
            "semantic_no_hash",
            "Semantic Snap (compute_hash=False)",
            ChunkingMode::Semantic,
            false,
        ),
        (
            "semantic_with_hash",
            "Semantic Snap + BLAKE3-128",
            ChunkingMode::Semantic,
            true,
        ),
    ];

    let mut entries_json = Vec::new();

    for (mode_id, mode_label, mode, compute_hash) in modes {
        let cfg = ChunkerConfig::new(64, Some(256), 512, mode, compute_hash).unwrap();

        let st_1mb = measure_mb_per_sec(doc_1mb.len(), 25, || {
            chunk_with_config(black_box(&doc_1mb), black_box(&cfg))
                .unwrap()
                .len()
        });

        let st_100mb = measure_mb_per_sec(doc_100mb.len(), 2, || {
            chunk_with_config(black_box(&doc_100mb), black_box(&cfg))
                .unwrap()
                .len()
        });

        let batch_st = measure_mb_per_sec(batch_total_bytes, 25, || {
            chunk_batch_with_config(black_box(&small_batch_slices), black_box(&cfg), Some(1))
                .unwrap()
                .len()
        });

        let batch_rayon = measure_mb_per_sec(batch_total_bytes, 25, || {
            chunk_batch_with_config(black_box(&small_batch_slices), black_box(&cfg), None)
                .unwrap()
                .len()
        });

        entries_json.push(format!(
            "    {{\n      \"mode_id\": \"{mode_id}\",\n      \"label\": \"{mode_label}\",\n      \"compute_hash\": {compute_hash},\n      \"single_thread_1mb_mb_s\": {st_1mb:.2},\n      \"single_thread_100mb_mb_s\": {st_100mb:.2},\n      \"batch_256x4kb_1_thread_mb_s\": {batch_st:.2},\n      \"batch_256x4kb_rayon_mb_s\": {batch_rayon:.2}\n    }}"
        ));
    }

    let json_content = format!(
        "{{\n  \"benchmark\": \"criterion_throughput_v0.2.0\",\n  \"command\": \"cargo bench --bench throughput\",\n  \"hardware\": {{\n    \"cpu_model\": \"{cpu_model}\",\n    \"logical_cores\": {logical_cores},\n    \"rayon_threads\": {logical_cores}\n  }},\n  \"config\": {{\n    \"min_chunk\": 64,\n    \"avg_chunk\": 256,\n    \"max_chunk\": 512\n  }},\n  \"results\": [\n{}\n  ]\n}}\n",
        entries_json.join(",\n")
    );

    if let Some(parent) = std::path::Path::new(&out_path).parent() {
        let _ = fs::create_dir_all(parent);
    }
    fs::write(&out_path, json_content).expect("Failed to write throughput JSON");
    println!("Wrote throughput results to {out_path}");
}
