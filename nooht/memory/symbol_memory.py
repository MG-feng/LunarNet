"""
Symbol Memory — 核心符号存储单元 (Backend 驱动版本)
设计原则：业务逻辑与存储实现完全分离
"""

from typing import List, Dict, Any, Optional, Iterator
from .symbol_entity import SymbolEntity, SymbolType, SymbolStatus
from .backend import MemoryBackend, InMemoryBackend


class SymbolMemory:
    """
    符号记忆库 — 依赖注入 Backend
    不再持有任何字典，所有操作委托给 Backend
    """
    
    def __init__(self, backend: Optional[MemoryBackend] = None):
        self.backend = backend or InMemoryBackend()
    
    # ─── CRUD ────────────────────────────────────────────────────
    
    def add(self, entity: SymbolEntity) -> str:
        return self.backend.insert(entity)
    
    def get(self, entity_id: str) -> Optional[SymbolEntity]:
        return self.backend.get(entity_id)
    
    def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        return self.backend.update(entity_id, updates)
    
    def remove(self, entity_id: str) -> bool:
        return self.backend.delete(entity_id)
    
    def exists(self, entity_id: str) -> bool:
        return self.backend.get(entity_id) is not None
    
    # ─── 查询 ─────────────────────────────────────────────────────
    
    def query(
        self,
        name: Optional[str] = None,
        type: Optional[SymbolType] = None,
        tag: Optional[str] = None,
        parent_id: Optional[str] = None,
        status: Optional[SymbolStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SymbolEntity]:
        return self.backend.query(
            name=name,
            type=type,
            tag=tag,
            parent_id=parent_id,
            status=status,
            limit=limit,
            offset=offset,
        )
    
    def count(self, **filters) -> int:
        return self.backend.count(**filters)
    
    def search_by_source(self, pattern: str, limit: int = 100) -> List[SymbolEntity]:
        return self.backend.search_by_source(pattern, limit)
    
    def get_by_repo(self, repo_prefix: str, limit: int = 1000) -> List[SymbolEntity]:
        return self.backend.get_by_repo(repo_prefix, limit)
    
    def get_dependencies(self, entity_id: str, limit: int = 50) -> List[SymbolEntity]:
        return self.backend.get_dependencies(entity_id, limit)
    
    def get_callers(self, entity_id: str, limit: int = 50) -> List[SymbolEntity]:
        return self.backend.get_callers(entity_id, limit)
    
    def update_access(self, entity_id: str) -> None:
        self.backend.update_access(entity_id)
    
    def stats(self) -> Dict[str, Any]:
        return self.backend.stats()
    
    def iter_all(self, batch_size: int = 1000) -> Iterator[List[SymbolEntity]]:
        yield from self.backend.iter_all(batch_size)
    
    def close(self) -> None:
        """关闭后端连接"""
        self.backend.close()
