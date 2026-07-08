"""
Vector Store — 向量检索独立层
支持：FAISS (CPU/GPU), 可扩展至 Milvus/Qdrant
设计原则：与 SymbolMemory 解耦，只负责向量相似度检索
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


class VectorStore(ABC):
    """向量存储抽象"""
    
    @abstractmethod
    def add(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        pass
    
    @abstractmethod
    def search(self, query: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        pass
    
    @abstractmethod
    def remove(self, ids: List[str]) -> None:
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        pass
    
    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def vacuum(self) -> int:
        """物理清理墓碑，重建索引"""
        pass


class FAISSVectorStore(VectorStore):
    """FAISS 向量存储 — CPU 优先，带 Tombstone 过滤"""
    
    def __init__(self, dimension: int, metric: str = "cosine"):
        try:
            import faiss
        except ImportError:
            raise ImportError("FAISS not installed. Run: pip install faiss-cpu")
        
        self.dimension = dimension
        self.metric = metric
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (需归一化)
        self.metadata: List[Dict[str, Any]] = []
        self.ids: List[str] = []
        self._tombstone_ids: set = set()
        self._normalize = True
        self._vectors: List[np.ndarray] = []  # 保存原始向量用于重建
    
    def add(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        if self._normalize:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / (norms + 1e-8)
        
        self.index.add(vectors.astype(np.float32))
        self.metadata.extend(metadata)
        for meta in metadata:
            if "id" in meta:
                self.ids.append(meta["id"])
        
        # 保存原始向量用于 vacuum 重建
        self._vectors.extend([v.copy() for v in vectors])
    
    def mark_tombstone(self, entity_id: str) -> None:
        """标记墓碑 — 不物理删除，只过滤"""
        self._tombstone_ids.add(entity_id)
    
    def search(self, query: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        if self._normalize:
            query = query / (np.linalg.norm(query) + 1e-8)
        
        search_k = min(top_k * 3, len(self.metadata))
        if search_k == 0:
            return []
        
        distances, indices = self.index.search(query.astype(np.float32).reshape(1, -1), search_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                meta = self.metadata[idx]
                entity_id = meta.get("id")
                if entity_id and entity_id not in self._tombstone_ids:
                    results.append((float(dist), meta))
                    if len(results) >= top_k:
                        break
        return results
    
    def remove(self, ids: List[str]) -> None:
        """标记为墓碑（软删除）"""
        for eid in ids:
            self._tombstone_ids.add(eid)
    
    def vacuum(self, raw_vectors: Optional[np.ndarray] = None) -> int:
        """
        物理清理墓碑 — 重建索引
        注意：需要传入原始向量以重建索引
        如果 raw_vectors 为 None，则使用内部保存的向量
        """
        valid_indices = []
        valid_metadata = []
        valid_vectors = []
        
        for i, meta in enumerate(self.metadata):
            entity_id = meta.get("id")
            if entity_id and entity_id not in self._tombstone_ids:
                valid_indices.append(i)
                valid_metadata.append(meta)
                if i < len(self._vectors):
                    valid_vectors.append(self._vectors[i])
        
        removed_count = len(self.metadata) - len(valid_metadata)
        
        if valid_vectors:
            import faiss
            self.index.reset()
            vectors_array = np.array(valid_vectors)
            if self._normalize:
                norms = np.linalg.norm(vectors_array, axis=1, keepdims=True)
                vectors_array = vectors_array / (norms + 1e-8)
            self.index.add(vectors_array.astype(np.float32))
            self.metadata = valid_metadata
            self._vectors = valid_vectors
            self._tombstone_ids.clear()
        elif len(valid_metadata) == 0:
            self.index.reset()
            self.metadata = []
            self._vectors = []
            self._tombstone_ids.clear()
        else:
            # 只清理元数据，不重建索引
            self.metadata = valid_metadata
            self._tombstone_ids.clear()
        
        return removed_count
    
    def save(self, path: str) -> None:
        import faiss
        import pickle
        faiss.write_index(self.index, f"{path}.faiss")
        with open(f"{path}.meta.pkl", "wb") as f:
            pickle.dump({
                "metadata": self.metadata,
                "ids": self.ids,
                "tombstone_ids": list(self._tombstone_ids),
                "vectors": self._vectors,
            }, f)
    
    def load(self, path: str) -> None:
        import faiss
        import pickle
        self.index = faiss.read_index(f"{path}.faiss")
        with open(f"{path}.meta.pkl", "rb") as f:
            data = pickle.load(f)
            self.metadata = data["metadata"]
            self.ids = data["ids"]
            self._tombstone_ids = set(data.get("tombstone_ids", []))
            self._vectors = data.get("vectors", [])
    
    def stats(self) -> Dict[str, Any]:
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "metric": self.metric,
            "tombstone_count": len(self._tombstone_ids),
            "active_count": len(self.metadata) - len(self._tombstone_ids),
            "backend": "faiss-cpu",
        }
