"""
Hierarchical Memory Compression (HMC)
分层记忆压缩 — 核心原则：Compression > Deletion
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class MemoryLevel(IntEnum):
    """记忆层级 — 从原始到归档"""
    L0_RAW = 0
    L1_SUMMARY = 1
    L2_SEMANTIC = 2
    L3_ARCHIVE = 3


@dataclass
class CompressedMemory:
    """压缩后的记忆单元"""
    id: str
    original_id: str
    level: MemoryLevel
    data: Dict[str, Any]
    compression_ratio: float
    compressed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def size_bytes(self) -> int:
        import sys
        return sys.getsizeof(self.data)


class CompressionStrategy:
    """压缩策略基类"""
    
    def compress(self, symbol: Any, target_level: MemoryLevel) -> CompressedMemory:
        raise NotImplementedError
    
    def can_compress(self, symbol: Any, target_level: MemoryLevel) -> bool:
        return True


class SymbolCompressor(CompressionStrategy):
    """符号压缩器 — 按层级压缩 SymbolEntity"""
    
    def compress(self, symbol: Any, target_level: MemoryLevel) -> CompressedMemory:
        from ..memory.symbol_entity import SymbolEntity
        
        if not isinstance(symbol, SymbolEntity):
            raise ValueError("SymbolCompressor requires SymbolEntity")
        
        data = {}
        original_size = len(symbol.source) + len(symbol.docstring)
        
        if target_level == MemoryLevel.L0_RAW:
            data = symbol.to_dict()
            ratio = 1.0
        
        elif target_level == MemoryLevel.L1_SUMMARY:
            data = {
                "name": symbol.name,
                "type": symbol.type.value,
                "signature": symbol.signature,
                "summary": symbol.summary or symbol.name,
                "file_path": symbol.file_path,
                "line_start": symbol.line_start,
                "line_end": symbol.line_end,
                "dependencies": symbol.dependencies[:10],
            }
            compressed_size = len(str(data))
            ratio = original_size / max(compressed_size, 1)
        
        elif target_level == MemoryLevel.L2_SEMANTIC:
            data = {
                "id": symbol.id,
                "name": symbol.name,
                "type": symbol.type.value,
                "embedding": symbol.embedding[:64] if symbol.embedding else None,
                "semantic_hash": symbol.semantic_hash,
                "dependencies": symbol.dependencies[:5],
                "summary": symbol.summary or symbol.name,
            }
            compressed_size = len(str(data))
            ratio = original_size / max(compressed_size, 1)
        
        elif target_level == MemoryLevel.L3_ARCHIVE:
            data = {
                "id": symbol.id,
                "name": symbol.name,
                "type": symbol.type.value,
                "semantic_hash": symbol.semantic_hash,
                "archived_at": datetime.now().isoformat(),
            }
            compressed_size = len(str(data))
            ratio = original_size / max(compressed_size, 1)
        
        else:
            raise ValueError(f"Unknown target level: {target_level}")
        
        return CompressedMemory(
            id=f"compressed_{symbol.id}_{target_level.value}",
            original_id=symbol.id,
            level=target_level,
            data=data,
            compression_ratio=ratio
        )


class HMCController:
    """
    HMC 控制器 — 管理记忆的生命周期
    Compression > Deletion 是核心原则
    """
    
    def __init__(
        self,
        compressor: Optional[CompressionStrategy] = None,
        max_raw_count: int = 10000,
        max_summary_count: int = 50000,
        max_semantic_count: int = 100000,
        archive_after_days: int = 90,
    ):
        self.compressor = compressor or SymbolCompressor()
        self.max_raw_count = max_raw_count
        self.max_summary_count = max_summary_count
        self.max_semantic_count = max_semantic_count
        self.archive_after_days = archive_after_days
        
        self.raw_memories: Dict[str, CompressedMemory] = {}
        self.summary_memories: Dict[str, CompressedMemory] = {}
        self.semantic_memories: Dict[str, CompressedMemory] = {}
        self.archive_memories: Dict[str, CompressedMemory] = {}
    
    def add_memory(self, symbol: Any, initial_level: MemoryLevel = MemoryLevel.L0_RAW) -> str:
        compressed = self.compressor.compress(symbol, initial_level)
        self._store_at_level(compressed)
        return compressed.id
    
    def _store_at_level(self, compressed: CompressedMemory) -> None:
        if compressed.level == MemoryLevel.L0_RAW:
            self.raw_memories[compressed.id] = compressed
            self._trigger_compression(MemoryLevel.L0_RAW)
        elif compressed.level == MemoryLevel.L1_SUMMARY:
            self.summary_memories[compressed.id] = compressed
            self._trigger_compression(MemoryLevel.L1_SUMMARY)
        elif compressed.level == MemoryLevel.L2_SEMANTIC:
            self.semantic_memories[compressed.id] = compressed
            self._trigger_compression(MemoryLevel.L2_SEMANTIC)
        elif compressed.level == MemoryLevel.L3_ARCHIVE:
            self.archive_memories[compressed.id] = compressed
    
    def _trigger_compression(self, level: MemoryLevel) -> None:
        if level == MemoryLevel.L0_RAW and len(self.raw_memories) > self.max_raw_count:
            items = list(self.raw_memories.items())
            items.sort(key=lambda x: x[1].compressed_at)
            to_compress = items[:int(self.max_raw_count * 0.2)]
            for cid, comp in to_compress:
                new_comp = self.compressor.compress(comp.data, MemoryLevel.L1_SUMMARY)
                self.summary_memories[new_comp.id] = new_comp
                del self.raw_memories[cid]
        
        elif level == MemoryLevel.L1_SUMMARY and len(self.summary_memories) > self.max_summary_count:
            items = list(self.summary_memories.items())
            items.sort(key=lambda x: x[1].compressed_at)
            to_compress = items[:int(self.max_summary_count * 0.2)]
            for cid, comp in to_compress:
                new_comp = self.compressor.compress(comp.data, MemoryLevel.L2_SEMANTIC)
                self.semantic_memories[new_comp.id] = new_comp
                del self.summary_memories[cid]
        
        elif level == MemoryLevel.L2_SEMANTIC and len(self.semantic_memories) > self.max_semantic_count:
            items = list(self.semantic_memories.items())
            items.sort(key=lambda x: x[1].compressed_at)
            to_compress = items[:int(self.max_semantic_count * 0.2)]
            for cid, comp in to_compress:
                new_comp = self.compressor.compress(comp.data, MemoryLevel.L3_ARCHIVE)
                self.archive_memories[new_comp.id] = new_comp
                del self.semantic_memories[cid]
    
    def get_memory(self, memory_id: str) -> Optional[CompressedMemory]:
        for store in [self.raw_memories, self.summary_memories, self.semantic_memories, self.archive_memories]:
            if memory_id in store:
                return store[memory_id]
        return None
    
    def stats(self) -> Dict[str, int]:
        return {
            "raw": len(self.raw_memories),
            "summary": len(self.summary_memories),
            "semantic": len(self.semantic_memories),
            "archive": len(self.archive_memories),
            "total": len(self.raw_memories) + len(self.summary_memories) +
                     len(self.semantic_memories) + len(self.archive_memories),
        }
    
    def force_archive_old(self, days_threshold: Optional[int] = None) -> int:
        threshold = days_threshold or self.archive_after_days
        cutoff = datetime.now() - timedelta(days=threshold)
        archived_count = 0
        
        for level, store in [
            (MemoryLevel.L0_RAW, self.raw_memories),
            (MemoryLevel.L1_SUMMARY, self.summary_memories),
            (MemoryLevel.L2_SEMANTIC, self.semantic_memories),
        ]:
            items = list(store.items())
            for cid, comp in items:
                comp_time = datetime.fromisoformat(comp.compressed_at)
                if comp_time < cutoff:
                    new_comp = self.compressor.compress(comp.data, MemoryLevel.L3_ARCHIVE)
                    self.archive_memories[new_comp.id] = new_comp
                    del store[cid]
                    archived_count += 1
        
        return archived_count
