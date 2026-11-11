use std::time::Duration;

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
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

fn bench_single_document(c: &mut Criterion) {
    let modes = [
        ("raw_no_hash", ChunkingMode::Raw, false),
        ("raw_with_hash", ChunkingMode::Raw, true),
        ("semantic_no_hash", ChunkingMode::Semantic, false),
        ("semantic_with_hash", ChunkingMode::Semantic, true),
    ];

    // 1. 1 MB single-thread benchmark
    let doc_1mb = build_utf8_corpus(1024 * 1024);
    let mut group_1mb = c.benchmark_group("single_thread_1mb");
    group_1mb.throughput(Throughput::Bytes(doc_1mb.len() as u64));
    group_1mb.measurement_time(Duration::from_secs(3));

    for (label, mode, compute_hash) in modes {
        let cfg = ChunkerConfig::new(64, Some(256), 512, mode, compute_hash).unwrap();
        group_1mb.bench_with_input(BenchmarkId::from_parameter(label), &doc_1mb, |b, data| {
            b.iter(|| {
                let res = chunk_with_config(black_box(data), black_box(&cfg)).unwrap();
                black_box(res.len())
            });
        });
    }
    group_1mb.finish();

    // 2. 100 MB single-thread benchmark
    let doc_100mb = build_utf8_corpus(100 * 1024 * 1024);
    let mut group_100mb = c.benchmark_group("single_thread_100mb");
    group_100mb.throughput(Throughput::Bytes(doc_100mb.len() as u64));
    group_100mb.sample_size(10);
    group_100mb.measurement_time(Duration::from_secs(5));

    for (label, mode, compute_hash) in modes {
        let cfg = ChunkerConfig::new(64, Some(256), 512, mode, compute_hash).unwrap();
        group_100mb.bench_with_input(BenchmarkId::from_parameter(label), &doc_100mb, |b, data| {
            b.iter(|| {
                let res = chunk_with_config(black_box(data), black_box(&cfg)).unwrap();
                black_box(res.len())
            });
        });
    }
    group_100mb.finish();
}

fn bench_batch_documents(c: &mut Criterion) {
    let modes = [
        ("raw_no_hash", ChunkingMode::Raw, false),
        ("raw_with_hash", ChunkingMode::Raw, true),
        ("semantic_no_hash", ChunkingMode::Semantic, false),
        ("semantic_with_hash", ChunkingMode::Semantic, true),
    ];

    // 3. Batch of 256 small documents (4 KB each = 1 MB total): single-thread vs Rayon multi-thread
    let small_doc = build_utf8_corpus(4 * 1024);
    let small_batch_owned: Vec<Vec<u8>> = (0..256).map(|_| small_doc.clone()).collect();
    let small_batch_slices: Vec<&[u8]> = small_batch_owned.iter().map(Vec::as_slice).collect();
    let total_small_bytes: u64 = small_batch_slices.iter().map(|s| s.len() as u64).sum();

    let mut group_batch = c.benchmark_group("small_batch_256x4kb");
    group_batch.throughput(Throughput::Bytes(total_small_bytes));
    group_batch.measurement_time(Duration::from_secs(3));

    for (label, mode, compute_hash) in modes {
        let cfg = ChunkerConfig::new(64, Some(256), 512, mode, compute_hash).unwrap();
        group_batch.bench_with_input(
            BenchmarkId::new("single_thread", label),
            &small_batch_slices,
            |b, docs| {
                b.iter(|| {
                    let res =
                        chunk_batch_with_config(black_box(docs), black_box(&cfg), Some(1)).unwrap();
                    black_box(res.len())
                });
            },
        );
        group_batch.bench_with_input(
            BenchmarkId::new("rayon_pool", label),
            &small_batch_slices,
            |b, docs| {
                b.iter(|| {
                    let res =
                        chunk_batch_with_config(black_box(docs), black_box(&cfg), None).unwrap();
                    black_box(res.len())
                });
            },
        );
    }
    group_batch.finish();
}

criterion_group!(benches, bench_single_document, bench_batch_documents);
criterion_main!(benches);
