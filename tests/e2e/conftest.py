"""Pytest fixtures and configuration for E2E opaque-box test suite."""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from tests.e2e.adapter import (
    ChunkerConfig,
    ChunkResult,
    chunk_documents_batch,
    chunker_fingerprint,
    cache_key,
    diff_chunks,
)


@pytest.fixture
def repo_root() -> Path:
    """Returns absolute path to the repository root directory."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def corpus_dir(repo_root: Path) -> Path:
    """Returns absolute path to bench/corpus/data/ if present."""
    return repo_root / "bench" / "corpus" / "data"


@pytest.fixture
def sample_en_text() -> bytes:
    """Sample technical English text with headings, sentences, and lists."""
    return (
        "# Content-Defined Chunking Engine\n\n"
        "Content-defined chunking (FastCDC) breaks data streams into variable-sized chunks. "
        "Unlike fixed-size chunking, FastCDC determines boundaries using rolling hashes.\n\n"
        "## Algorithmic Properties\n\n"
        "The primary advantage is boundary shift resistance during insertions and deletions. "
        "Dr. Smith demonstrated that deduplication efficiency exceeds 85% on source code. "
        "Furthermore, e.g. technical documentation exhibits substantial reusability.\n\n"
        "### Performance Considerations\n\n"
        "High throughput is maintained via SIMD-accelerated hashing routines.\n"
    ).encode("utf-8")


@pytest.fixture
def sample_pt_text() -> bytes:
    """Sample technical Portuguese text with legal abbreviations and accented words."""
    return (
        "# Arquitetura de Indexação RAG\n\n"
        "A segmentação semântica preserva a integridade de unidades textuais completas. "
        "O art. 5º da legislação vigente estabelece diretrizes para privacidade de dados. "
        "Conforme indicado no inc. I, o consentimento do titular deve ser inequívoco.\n\n"
        "## Requisitos de Engenharia\n\n"
        "A biblioteca garante que termos como coração, computação e eficiência "
        "permaneçam coesos dentro do mesmo bloco textual. "
        "Segundo o Prof. Silva, a ressincronização local minimiza o custo de re-embedding.\n"
    ).encode("utf-8")


@pytest.fixture
def sample_cjk_text() -> bytes:
    """Sample CJK text with Chinese and Japanese full-width punctuation."""
    return (
        "# 智能文本切分引擎\n\n"
        "基于内容的文本切分算法能够有效识别自然语言边界。FastCDC算法在海量数据检索中表现出色！"
        "全角标点符号不需要跟随空格即可作为句子切分依据。例如问号？以及叹号！均能正确识别。\n\n"
        "## 系统架构与性能\n\n"
        "结合BLAKE3哈希算法，可以实现微秒级的高速内容指纹计算……这是一项关键特性。\n"
    ).encode("utf-8")
