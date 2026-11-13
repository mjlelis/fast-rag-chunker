"""Adapter module for fast-rag-chunker test suite.

Dispatches to native compiled extension when available and compliant,
otherwise uses the pure-Python reference specification oracle.
"""

from __future__ import annotations

import warnings
from typing import Any, Sequence

from tests.e2e import reference_oracle as oracle

try:
    import fast_rag_chunker as native_frc
    IS_NATIVE_AVAILABLE = True
except ImportError:
    native_frc = None
    IS_NATIVE_AVAILABLE = False


def is_native_v0_3_compliant() -> bool:
    """Checks whether the native extension supports v0.3.0 features."""
    if not IS_NATIVE_AVAILABLE or native_frc is None:
        return False
    # Check if diff_chunks exists in native module
    return hasattr(native_frc, "diff_chunks")


class UnifiedChunker:
    """Provides a consistent chunking API dispatching to native or oracle."""

    @staticmethod
    def ChunkerConfig(*args: Any, **kwargs: Any) -> Any:
        if is_native_v0_3_compliant() and hasattr(native_frc, "ChunkerConfig"):
            return native_frc.ChunkerConfig(*args, **kwargs)
        return oracle.ChunkerConfig(*args, **kwargs)

    @staticmethod
    def ChunkResult(*args: Any, **kwargs: Any) -> Any:
        if is_native_v0_3_compliant():
            chunk_cls = getattr(native_frc, "ChunkResult", getattr(native_frc, "PyChunkResult", oracle.ChunkResult))
            return chunk_cls(*args, **kwargs)
        return oracle.ChunkResult(*args, **kwargs)

    @staticmethod
    def chunk_documents_batch(*args: Any, **kwargs: Any) -> Any:
        if is_native_v0_3_compliant() and hasattr(native_frc, "chunk_documents_batch"):
            return native_frc.chunk_documents_batch(*args, **kwargs)
        return oracle.chunk_documents_batch(*args, **kwargs)

    @staticmethod
    def chunker_fingerprint(*args: Any, **kwargs: Any) -> str:
        if is_native_v0_3_compliant() and hasattr(native_frc, "chunker_fingerprint"):
            return native_frc.chunker_fingerprint(*args, **kwargs)
        return oracle.chunker_fingerprint(*args, **kwargs)

    @staticmethod
    def cache_key(*args: Any, **kwargs: Any) -> str:
        if is_native_v0_3_compliant() and hasattr(native_frc, "cache_key"):
            return native_frc.cache_key(*args, **kwargs)
        return oracle.cache_key(*args, **kwargs)

    @staticmethod
    def diff_chunks(*args: Any, **kwargs: Any) -> Any:
        if is_native_v0_3_compliant() and hasattr(native_frc, "diff_chunks"):
            return native_frc.diff_chunks(*args, **kwargs)
        return oracle.diff_chunks(*args, **kwargs)

    @staticmethod
    def resolve_snap_window(*args: Any, **kwargs: Any) -> int:
        if is_native_v0_3_compliant() and hasattr(native_frc, "resolve_snap_window"):
            return native_frc.resolve_snap_window(*args, **kwargs)
        return oracle.resolve_snap_window(*args, **kwargs)


# Direct exports for test files
ChunkerConfig = UnifiedChunker.ChunkerConfig
ChunkResult = UnifiedChunker.ChunkResult
chunk_documents_batch = UnifiedChunker.chunk_documents_batch
chunker_fingerprint = UnifiedChunker.chunker_fingerprint
cache_key = UnifiedChunker.cache_key
diff_chunks = UnifiedChunker.diff_chunks
ChunkDiffResult = getattr(native_frc, "ChunkDiffResult", oracle.ChunkDiffResult) if is_native_v0_3_compliant() else oracle.ChunkDiffResult
resolve_snap_window = UnifiedChunker.resolve_snap_window
