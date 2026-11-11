import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
DATA_DIR = CORPUS_DIR / "data"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"

EN_ARTICLES = [
    "Content-defined_chunking",
    "Rolling_hash",
    "Retrieval-augmented_generation",
    "Vector_database",
    "Cryptographic_hash_function",
    "Distributed_hash_table",
    "B-tree",
    "Log-structured_merge-tree",
    "Write-ahead_logging",
    "Consensus_(computer_science)",
    "Raft_(algorithm)",
    "Paxos_(computer_science)",
    "Consistent_hashing",
    "Bloom_filter",
    "Locality-sensitive_hashing",
    "Information_retrieval",
    "Tf-idf",
    "Okapi_BM25",
    "Inverted_index",
    "PageRank",
]

PT_ARTICLES = [
    "Tabela_ de_dispersão",
    "Função_hash_criptográfica",
    "Árvore_B",
    "Sistema_distribuído",
    "Processamento_de_linguagem_natural",
    "Aprendizado_de_máquina",
    "Inteligência_artificial",
    "Banco_de_dados_relacional",
    "Compilador",
    "Sistema_operativo",
    "Memória_virtual",
    "Escalonamento_de_processos",
    "Protocolo_de_controle_de_transmissão",
    "Criptografia_de_chave_pública",
    " Lei_Geral_de_Proteção_de_Dados_Pessoais",
    "Constituição_brasileira_de_1988",
    "Direito_administrativo",
    "Engenharia_de_software",
    "Arquitetura_de_computadores",
    "Rede_neural_artificial",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_wikitext_to_markdown(raw: str) -> str:
    text = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/>]*/>", "", text)
    # Remove nested templates up to 3 levels
    for _ in range(3):
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"====\s*(.+?)\s*====", r"#### \1", text)
    text = re.sub(r"===\s*(.+?)\s*===", r"### \1", text)
    text = re.sub(r"==\s*(.+?)\s*==", r"## \1", text)
    text = re.sub(r"'{2,3}", "", text)
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines = []
    blank_streak = 0
    for line in lines:
        if not line or line.startswith("|") or line.startswith("{|") or line.startswith("|}"):
            blank_streak += 1
            if blank_streak <= 1 and cleaned_lines:
                cleaned_lines.append("")
            continue
        blank_streak = 0
        cleaned_lines.append(line)
    result = "\n".join(cleaned_lines).strip() + "\n"
    return result


def fetch_wikipedia_revision_pair(lang: str, title: str):
    clean_title = title.strip().replace(" ", "_")
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "prop": "revisions",
            "titles": clean_title,
            "rvprop": "ids|timestamp|content",
            "rvslots": "main",
            "rvlimit": "10",
            "format": "json",
            "redirects": "1",
        }
    )
    url = f"https://{lang}.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "fast-rag-chunker-benchmark/0.2.0 (https://github.com/mjlelis/fast-rag-chunker)"
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    pages = payload.get("query", {}).get("pages", {})
    for page in pages.values():
        revs = page.get("revisions", [])
        if len(revs) < 2:
            continue
        cleaned_revs = []
        for r in revs:
            content = r.get("slots", {}).get("main", {}).get("*", "")
            md = clean_wikitext_to_markdown(content)
            if len(md.encode("utf-8")) >= 2500:
                cleaned_revs.append(
                    {
                        "revid": r["revid"],
                        "parentid": r.get("parentid", 0),
                        "timestamp": r["timestamp"],
                        "markdown": md[:18000] + "\n",
                    }
                )
        for i in range(len(cleaned_revs) - 1):
            newer = cleaned_revs[i]
            older = cleaned_revs[i + 1]
            if newer["markdown"] != older["markdown"]:
                return {
                    "lang": lang,
                    "title": page.get("title", clean_title),
                    "pageid": page.get("pageid", 0),
                    "old_revid": older["revid"],
                    "old_timestamp": older["timestamp"],
                    "new_revid": newer["revid"],
                    "new_timestamp": newer["timestamp"],
                    "old_text": older["markdown"],
                    "new_text": newer["markdown"],
                    "url": f"https://{lang}.wikipedia.org/w/index.php?title={urllib.parse.quote(clean_title)}&diff={newer['revid']}&oldid={older['revid']}",
                }
    return None


def download_all(target_per_lang: int = 15) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    entries = []

    for lang, candidates in [("en", EN_ARTICLES), ("pt", PT_ARTICLES)]:
        collected = 0
        for raw_title in candidates:
            if collected >= target_per_lang:
                break
            try:
                pair = fetch_wikipedia_revision_pair(lang, raw_title)
            except Exception as exc:
                print(f"[warn] skipping {lang}:{raw_title}: {exc}", file=sys.stderr)
                continue
            if pair is None:
                continue

            slug = re.sub(r"[^a-z0-9_]+", "_", pair["title"].lower()).strip("_")
            doc_id = f"{lang}_{collected + 1:02d}_{slug[:32]}"
            old_rel = f"data/{doc_id}_rev_old.md"
            new_rel = f"data/{doc_id}_rev_new.md"

            old_bytes = pair["old_text"].encode("utf-8")
            new_bytes = pair["new_text"].encode("utf-8")

            (CORPUS_DIR / old_rel).write_bytes(old_bytes)
            (CORPUS_DIR / new_rel).write_bytes(new_bytes)

            entries.append(
                {
                    "doc_id": doc_id,
                    "lang": lang,
                    "title": pair["title"],
                    "pageid": pair["pageid"],
                    "old_revid": pair["old_revid"],
                    "old_timestamp": pair["old_timestamp"],
                    "new_revid": pair["new_revid"],
                    "new_timestamp": pair["new_timestamp"],
                    "diff_url": pair["url"],
                    "license": "CC-BY-SA-4.0",
                    "old_file": old_rel,
                    "old_bytes": len(old_bytes),
                    "old_sha256": sha256_bytes(old_bytes),
                    "new_file": new_rel,
                    "new_bytes": len(new_bytes),
                    "new_sha256": sha256_bytes(new_bytes),
                }
            )
            collected += 1
            print(
                f"[ok] {doc_id}: rev {pair['old_revid']} -> {pair['new_revid']} ({len(old_bytes)} -> {len(new_bytes)} bytes)"
            )

    manifest = {
        "corpus_version": "0.2.0",
        "license": "CC-BY-SA-4.0 (Creative Commons Attribution-ShareAlike 4.0 International — Wikipedia Contributors)",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "total_documents": len(entries),
        "documents": entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote manifest with {len(entries)} revision pairs to {MANIFEST_PATH}")


def verify_manifest() -> bool:
    if not MANIFEST_PATH.exists():
        print(f"Manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        return False
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    docs = manifest.get("documents", [])
    if len(docs) < 30:
        print(f"Expected at least 30 documents in manifest, found {len(docs)}", file=sys.stderr)
        return False

    for item in docs:
        for prefix in ("old", "new"):
            rel_path = item[f"{prefix}_file"]
            expected_sha = item[f"{prefix}_sha256"]
            full_path = CORPUS_DIR / rel_path
            if not full_path.exists():
                print(f"Missing corpus file: {full_path}", file=sys.stderr)
                return False
            actual_sha = sha256_bytes(full_path.read_bytes())
            if actual_sha != expected_sha:
                print(
                    f"SHA-256 mismatch for {rel_path}: expected {expected_sha}, got {actual_sha}",
                    file=sys.stderr,
                )
                return False

    print(f"Verified {len(docs)} document revision pairs ({len(docs) * 2} files) against SHA-256 manifest.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download or verify the bilingual Wikipedia revision corpus."
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Download fresh revision pairs from en.wikipedia.org and pt.wikipedia.org",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing corpus files against bench/corpus/manifest.json SHA-256 hashes",
    )
    args = parser.parse_args()

    if args.fetch:
        download_all(target_per_lang=15)
    if args.verify or not args.fetch:
        ok = verify_manifest()
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
