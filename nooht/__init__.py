"""
Nooht Framework — 模型无关的代码智能记忆引擎
版本：0.1.3-final
"""

__version__ = "0.1.3"
__author__ = "Nooht Team"

from .memory.symbol_memory import SymbolMemory, SymbolEntity, SymbolType, SymbolStatus
from .memory.backend import MemoryBackend, InMemoryBackend, DuckDBBackend
from .memory.vector_store import VectorStore, FAISSVectorStore
from .compression.hmc import HMCController, MemoryLevel, CompressedMemory
from .semantic.scm import CodeSemanticAnalyzer, SemanticCodeMemory, CodeSemantic
from .context.manager import ContextManager, ContextItem, ContextPriority
from .adapters.base import ModelAdapter, TransformersAdapter, AdapterFactory
from .retrieval.retriever import Retriever, RetrievalResult, RetrievalStrategy

__all__ = [
    # Memory
    "SymbolMemory",
    "SymbolEntity",
    "SymbolType",
    "SymbolStatus",
    "MemoryBackend",
    "InMemoryBackend",
    "DuckDBBackend",
    "VectorStore",
    "FAISSVectorStore",
    # Compression
    "HMCController",
    "MemoryLevel",
    "CompressedMemory",
    # Semantic
    "CodeSemanticAnalyzer",
    "SemanticCodeMemory",
    "CodeSemantic",
    # Context
    "ContextManager",
    "ContextItem",
    "ContextPriority",
    # Adapters
    "ModelAdapter",
    "TransformersAdapter",
    "AdapterFactory",
    # Retrieval
    "Retriever",
    "RetrievalResult",
    "RetrievalStrategy",
]
