.PHONY: readme-tables verify-corpus dedup-bench retrieval-bench throughput-bench

readme-tables:
	python3 scripts/generate_readme_tables.py

verify-corpus:
	python3 -m bench.corpus.download_corpus --verify

dedup-bench:
	python3 -m bench.dedup --out results/dedup.json

retrieval-bench:
	python3 -m bench.retrieval --out results/retrieval.json

throughput-bench:
	cargo run --release --no-default-features --example export_throughput_json -- results/throughput.json
	cargo bench --bench throughput
