import json
import re
from pathlib import Path

CORPUS_DIR = Path("bench/corpus/data")
DATA_DIR = Path("bench/retrieval/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Define 50 high-quality query definitions.
# For each, we provide distinctive keywords to find the exact target paragraph in the document.
QUERY_SPECS = [
    # --- English (25 queries across 15 documents) ---
    {
        "query_id": "q_en_01_1",
        "doc_id": "en_01_rolling_hash_rev_new.md",
        "query": "What is a rolling hash and how does its sliding window work?",
        "search_pattern": "A rolling hash (also known as recursive hashing or rolling checksum)",
    },
    {
        "query_id": "q_en_01_2",
        "doc_id": "en_01_rolling_hash_rev_new.md",
        "query": "How is the rolling hash used in the Rabin-Karp string search algorithm?",
        "search_pattern": "Rabin–Karp string search algorithm",
    },
    {
        "query_id": "q_en_02_1",
        "doc_id": "en_02_retrieval_augmented_generation_rev_new.md",
        "query": "How does retrieval-augmented generation augment large language models with external data?",
        "search_pattern": "Retrieval-augmented generation (RAG) is a technique that enables",
    },
    {
        "query_id": "q_en_02_2",
        "doc_id": "en_02_retrieval_augmented_generation_rev_new.md",
        "query": "What is the distinction between dense and sparse vectors in RAG retrieval encoders?",
        "search_pattern": "Sparse vectors, which encode the identity of a word",
    },
    {
        "query_id": "q_en_03_1",
        "doc_id": "en_03_cryptographic_hash_function_rev_new.md",
        "query": "What security properties define an ideal cryptographic hash function?",
        "search_pattern": "A cryptographic hash function (CHF) is a hash algorithm",
    },
    {
        "query_id": "q_en_03_2",
        "doc_id": "en_03_cryptographic_hash_function_rev_new.md",
        "query": "Why is collision resistance crucial for cryptographic hash functions?",
        "search_pattern": "In practice, collision resistance is insufficient for many practical uses",
    },
    {
        "query_id": "q_en_04_1",
        "doc_id": "en_04_distributed_hash_table_rev_new.md",
        "query": "What service does a distributed hash table provide across participating nodes?",
        "search_pattern": "A distributed hash table (DHT) is a distributed system that provides a lookup service",
    },
    {
        "query_id": "q_en_04_2",
        "doc_id": "en_04_distributed_hash_table_rev_new.md",
        "query": "How do distributed hash tables achieve structured key-based routing?",
        "search_pattern": "Distributed hash tables use a more structured key-based routing",
    },
    {
        "query_id": "q_en_05_1",
        "doc_id": "en_05_b_tree_rev_new.md",
        "query": "What are the logarithmic time complexity properties of a B-tree data structure?",
        "search_pattern": "In computer science, a B-tree is a self-balancing tree data structure",
    },
    {
        "query_id": "q_en_05_2",
        "doc_id": "en_05_b_tree_rev_new.md",
        "query": "How do separation values and internal nodes divide subtrees in a B-tree?",
        "search_pattern": "The keys of each non-leaf node act as separation values",
    },
    {
        "query_id": "q_en_06_1",
        "doc_id": "en_06_log_structured_merge_tree_rev_new.md",
        "query": "Why are log-structured merge-trees attractive for high insert volume storage?",
        "search_pattern": "In computer science, the log-structured merge-tree",
    },
    {
        "query_id": "q_en_06_2",
        "doc_id": "en_06_log_structured_merge_tree_rev_new.md",
        "query": "How do LSM trees balance sequential writes against read latency using compaction?",
        "search_pattern": "Most SSTables will be merged together via compaction",
    },
    {
        "query_id": "q_en_07_1",
        "doc_id": "en_07_consensus_computer_science_rev_new.md",
        "query": "What fundamental problem does consensus address in distributed computing systems?",
        "search_pattern": "A fundamental problem in distributed computing and multi-agent systems",
    },
    {
        "query_id": "q_en_07_2",
        "doc_id": "en_07_consensus_computer_science_rev_new.md",
        "query": "What is the difference between crash failures and Byzantine failures in consensus?",
        "search_pattern": "Crash and Byzantine failures",
    },
    {
        "query_id": "q_en_08_1",
        "doc_id": "en_08_raft_algorithm_rev_new.md",
        "query": "How does Raft achieve consensus via an elected leader and heartbeats?",
        "anchor_start": "Raft achieves consensus via an elected leader.",
    },
    {
        "query_id": "q_en_08_2",
        "doc_id": "en_08_raft_algorithm_rev_new.md",
        "query": "What purpose does the Pre-Vote extension serve when a member rejoins a Raft cluster?",
        "search_pattern": "Pre-Vote: when a member rejoins the cluster",
    },
    {
        "query_id": "q_en_09_1",
        "doc_id": "en_09_consistent_hashing_rev_new.md",
        "query": "How does consistent hashing minimize key remapping when resizing node tables?",
        "anchor_start": "In computer science, consistent hashing",
    },
    {
        "query_id": "q_en_09_2",
        "doc_id": "en_09_consistent_hashing_rev_new.md",
        "query": "How does consistent hashing distribute keys across cache servers on a circle?",
        "search_pattern": "Consistent hashing was introduced by David Karger",
    },
    {
        "query_id": "q_en_10_1",
        "doc_id": "en_10_bloom_filter_rev_new.md",
        "query": "What space-efficient probabilistic guarantees are provided by a Bloom filter?",
        "anchor_start": "In computing, a Bloom filter is a space-efficient probabilistic data structure",
    },
    {
        "query_id": "q_en_11_1",
        "doc_id": "en_11_locality_sensitive_hashing_rev_new.md",
        "query": "How does locality-sensitive hashing map similar input items to identical buckets?",
        "anchor_start": "In computer science, locality-sensitive hashing (LSH) is a fuzzy hashing technique",
    },
    {
        "query_id": "q_en_12_1",
        "doc_id": "en_12_information_retrieval_rev_new.md",
        "query": "What is the core definition and objective of information retrieval systems?",
        "anchor_start": "In computing and information science, information retrieval (IR)",
    },
    {
        "query_id": "q_en_13_1",
        "doc_id": "en_13_tf_idf_rev_new.md",
        "query": "How does tf-idf measure the statistical importance of words in a document corpus?",
        "anchor_start": "In information retrieval, tf–idf",
    },
    {
        "query_id": "q_en_14_1",
        "doc_id": "en_14_okapi_bm25_rev_new.md",
        "query": "What is Okapi BM25 and how do search engines use it for document ranking?",
        "anchor_start": "In information retrieval, Okapi BM25",
    },
    {
        "query_id": "q_en_15_1",
        "doc_id": "en_15_inverted_index_rev_new.md",
        "query": "What is an inverted index and what role do postings lists play in full-text search?",
        "anchor_start": "In information science, an inverted index",
    },
    {
        "query_id": "q_en_15_2",
        "doc_id": "en_15_inverted_index_rev_new.md",
        "query": "Why do search engines use inverted indices for fast full-text querying?",
        "search_pattern": "The purpose of an inverted index is to allow fast full-text searches",
    },

    # --- Portuguese (25 queries across 15 documents) ---
    {
        "query_id": "q_pt_01_1",
        "doc_id": "pt_01_tabela_de_dispers_o_rev_new.md",
        "query": "O que é uma tabela de dispersão e como ela associa chaves de busca a valores?",
        "anchor_start": "Em ciência da computação, uma tabela de dispersão",
    },
    {
        "query_id": "q_pt_01_2",
        "doc_id": "pt_01_tabela_de_dispers_o_rev_new.md",
        "query": "Como as colisões de chaves são tratadas em uma tabela hash?",
        "search_pattern": "Colisões são inevitáveis quando o conjunto de chaves possíveis",
    },
    {
        "query_id": "q_pt_02_1",
        "doc_id": "pt_02_fun_o_hash_criptogr_fica_rev_new.md",
        "query": "Quais são as propriedades fundamentais de segurança de uma função hash criptográfica?",
        "search_pattern": "Propriedades",
    },
    {
        "query_id": "q_pt_02_2",
        "doc_id": "pt_02_fun_o_hash_criptogr_fica_rev_new.md",
        "query": "Como o efeito avalanche atua na alteração de um resumo criptográfico?",
        "search_pattern": "Note que mesmo pequenas alterações na entrada",
    },
    {
        "query_id": "q_pt_03_1",
        "doc_id": "pt_03_rvore_b_rev_new.md",
        "query": "O que é uma árvore B e como ela garante pesquisas em tempo logarítmico?",
        "anchor_start": "Em ciência da computação, uma árvore B é uma estrutura de dados",
    },
    {
        "query_id": "q_pt_03_2",
        "doc_id": "pt_03_rvore_b_rev_new.md",
        "query": "Por que as árvores B são recomendadas para bancos de dados com armazenamento em disco?",
        "search_pattern": "As árvores B são otimizadas para sistemas que leem e escrevem grandes blocos",
    },
    {
        "query_id": "q_pt_04_1",
        "doc_id": "pt_04_sistema_de_processamento_distrib_rev_new.md",
        "query": "Como funciona um sistema de processamento distribuído composto por múltiplos nós?",
        "anchor_start": "Um sistema de processamento distribuído ou paralelo é um sistema que interliga vários nós",
    },
    {
        "query_id": "q_pt_04_2",
        "doc_id": "pt_04_sistema_de_processamento_distrib_rev_new.md",
        "query": "Quais vantagens de tolerância a falhas e desempenho oferece a computação distribuída?",
        "search_pattern": "A computação distribuída permite que tarefas computacionais complexas",
    },
    {
        "query_id": "q_pt_05_1",
        "doc_id": "pt_05_processamento_de_linguagem_natur_rev_new.md",
        "query": "O que estuda o campo de Processamento de Linguagem Natural (PLN)?",
        "search_pattern": "Processamento de linguagem natural (PLN) é uma subárea da ciência da computação",
    },
    {
        "query_id": "q_pt_05_2",
        "doc_id": "pt_05_processamento_de_linguagem_natur_rev_new.md",
        "query": "Como algoritmos de aprendizagem mecânica são aplicados em PLN estatístico?",
        "search_pattern": "Os algoritmos modernos de PLN baseiam-se na aprendizagem mecânica",
    },
    {
        "query_id": "q_pt_06_1",
        "doc_id": "pt_06_aprendizado_de_m_quina_rev_new.md",
        "query": "O que estuda a área de aprendizado de máquina na ciência da computação?",
        "anchor_start": "ou também aprendizado/aprendizagem de máquina () é um subcampo da Engenharia",
    },
    {
        "query_id": "q_pt_06_2",
        "doc_id": "pt_06_aprendizado_de_m_quina_rev_new.md",
        "query": "Qual a diferença entre aprendizado supervisionado e não supervisionado?",
        "search_pattern": "Aprendizado supervisionado: São apresentadas ao computador exemplos de entradas e saídas desejadas",
    },
    {
        "query_id": "q_pt_07_1",
        "doc_id": "pt_07_intelig_ncia_artificial_rev_new.md",
        "query": "Qual a definição geral de inteligência artificial na automação de tarefas cognitivas?",
        "anchor_start": "Inteligência artificial (frequentemente abreviada por IA ou AI",
    },
    {
        "query_id": "q_pt_08_1",
        "doc_id": "pt_08_banco_de_dados_relacional_rev_new.md",
        "query": "Como o modelo relacional organiza informações em tabelas e relações?",
        "anchor_start": "Um banco de dados relacional é um banco de dados que modela os dados",
    },
    {
        "query_id": "q_pt_08_2",
        "doc_id": "pt_08_banco_de_dados_relacional_rev_new.md",
        "query": "Qual a função da chave estrangeira na implementação de restrições relacionais?",
        "search_pattern": "Por meio das chaves estrangeiras, é possível implementar restrições nos SGBDR",
    },
    {
        "query_id": "q_pt_09_1",
        "doc_id": "pt_09_compilador_rev_new.md",
        "query": "O que faz um compilador ao processar código fonte de linguagens compiladas?",
        "search_pattern": "Um compilador é um programa de computador (ou um grupo de programas)",
    },
    {
        "query_id": "q_pt_09_2",
        "doc_id": "pt_09_compilador_rev_new.md",
        "query": "Qual a atribuição do analisador léxico durante a leitura de código?",
        "search_pattern": "A análise léxica é a primeira fase do compilador",
    },
    {
        "query_id": "q_pt_10_1",
        "doc_id": "pt_10_sistema_operativo_rev_new.md",
        "query": "Como o sistema operacional gerencia memória, processamento e interface de máquina?",
        "anchor_start": "é um software que gerencia os recursos de um dispositivo, como a memória e o processamento",
    },
    {
        "query_id": "q_pt_11_1",
        "doc_id": "pt_11_mem_ria_virtual_rev_new.md",
        "query": "Como a memória física é dividida em molduras de páginas no esquema de paginação?",
        "search_pattern": "Na paginação a memória física é dividida em blocos de bytes contíguos",
    },
    {
        "query_id": "q_pt_11_2",
        "doc_id": "pt_11_mem_ria_virtual_rev_new.md",
        "query": "Qual o papel do dispositivo MMU na tradução entre endereços virtuais e físicos?",
        "search_pattern": "O endereço virtual é encaminhado para a unidade de gerenciamento de memória",
    },
    {
        "query_id": "q_pt_12_1",
        "doc_id": "pt_12_escalonamento_de_processos_rev_new.md",
        "query": "Qual é a função do escalonador de processos no gerenciamento de tempo da CPU?",
        "anchor_start": "O escalonamento de processos ou agendador de tarefas (em inglês scheduling)",
    },
    {
        "query_id": "q_pt_13_1",
        "doc_id": "pt_13_protocolo_de_controle_de_transmi_rev_new.md",
        "query": "Como o protocolo TCP fornece entrega ordenada e verificação de erros na Internet?",
        "anchor_start": "Protocolo de Controle de Transmissão (do inglês: Transmission Control Protocol",
    },
    {
        "query_id": "q_pt_14_1",
        "doc_id": "pt_14_criptografia_de_chave_p_blica_rev_new.md",
        "query": "Como se dá a divisão entre chave pública e chave privada na criptografia assimétrica?",
        "search_pattern": "O termo chave pública vem da distinção de que a chave usada para criptografia",
    },
    {
        "query_id": "q_pt_15_1",
        "doc_id": "pt_15_lei_geral_de_prote_o_de_dados_pe_rev_new.md",
        "query": "O que estabelece a Lei Geral de Proteção de Dados Pessoais (LGPD) no Brasil?",
        "anchor_start": "A Lei Geral de Proteção de Dados Pessoais (com sigla LGPD ou LGPDP)",
    },
    {
        "query_id": "q_pt_15_2",
        "doc_id": "pt_15_lei_geral_de_prote_o_de_dados_pe_rev_new.md",
        "query": "Quais são as dez bases legais previstas na LGPD para o tratamento de dados pessoais?",
        "search_pattern": "É importante destacar que a LGPD limitou – taxativamente – as possibilidades",
    },
]

def find_paragraph(text: str, spec: dict) -> tuple[str, int, int]:
    if "search_pattern" in spec:
        pattern = spec["search_pattern"]
        pos = text.find(pattern)
        if pos != -1:
            # Find the full paragraph or sentence span
            start = text.rfind("\n\n", 0, pos)
            start = 0 if start == -1 else start + 2
            end = text.find("\n\n", pos)
            end = len(text) if end == -1 else end
            para = text[start:end].strip()
            return para, start, start + len(para)
        # Try finding line
        for line in text.split("\n"):
            if pattern.lower() in line.lower() and len(line.strip()) > 30:
                pos = text.find(line.strip())
                return line.strip(), pos, pos + len(line.strip())
    elif "anchor_start" in spec:
        prefix = spec["anchor_start"]
        pos = text.find(prefix)
        if pos != -1:
            end = text.find("\n\n", pos)
            end = len(text) if end == -1 else end
            para = text[pos:end].strip()
            return para, pos, pos + len(para)
        # Try matching first 25 chars
        prefix_short = prefix[:25]
        pos = text.find(prefix_short)
        if pos != -1:
            end = text.find("\n\n", pos)
            end = len(text) if end == -1 else end
            para = text[pos:end].strip()
            return para, pos, pos + len(para)

    # Fallback to finding non-trivial paragraph
    paras = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100 and not p.strip().startswith("thumb|")]
    if paras:
        chosen = paras[0]
        pos = text.find(chosen)
        return chosen, pos, pos + len(chosen)
    return "", -1, -1

def main():
    queries_out = []
    qrels_out = {}

    missing = 0
    for idx, spec in enumerate(QUERY_SPECS):
        doc_path = CORPUS_DIR / spec["doc_id"]
        if not doc_path.exists():
            print(f"ERROR: Doc not found: {spec['doc_id']}")
            missing += 1
            continue
        text = doc_path.read_text(encoding="utf-8")
        para, start, end = find_paragraph(text, spec)
        if not para or start == -1:
            print(f"ERROR: No match for {spec['query_id']} in {spec['doc_id']}")
            missing += 1
            continue
        
        # Extract 3-5 salient keywords
        words = [w.lower() for w in re.findall(r"[a-zA-ZÀ-ÿ]{4,}", spec["query"])]
        key_terms = words[:5]

        queries_out.append({
            "query_id": spec["query_id"],
            "query": spec["query"],
            "doc_id": spec["doc_id"],
        })
        qrels_out[spec["query_id"]] = {
            "doc_id": spec["doc_id"],
            "anchor": para[:200],  # initial snippet for verification
            "full_anchor": para,
            "key_terms": key_terms,
            "start_char": start,
            "end_char": end,
        }

    print(f"Processed {len(queries_out)} queries. Missing: {missing}")
    if missing == 0:
        (DATA_DIR / "queries.json").write_text(json.dumps(queries_out, indent=2, ensure_ascii=False), encoding="utf-8")
        (DATA_DIR / "qrels.json").write_text(json.dumps(qrels_out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Successfully generated {len(queries_out)} queries and qrels in {DATA_DIR}!")

if __name__ == "__main__":
    main()
