"""
Memory Backend — 存储后端抽象层
支持：InMemory (小规模), DuckDB (大规模), 可扩展
设计原则：业务逻辑与存储实现完全解耦
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from .symbol_entity import SymbolEntity, SymbolType, SymbolStatus


class MemoryBackend(ABC):
    """记忆后端抽象接口 — 百万级 Entity 友好"""
    
    @abstractmethod
    def insert(self, entity: SymbolEntity) -> str:
        pass
    
    @abstractmethod
    def get(self, entity_id: str) -> Optional[SymbolEntity]:
        pass
    
    @abstractmethod
    def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def count(self, **filters) -> int:
        pass
    
    @abstractmethod
    def search_by_source(self, pattern: str, limit: int = 100) -> List[SymbolEntity]:
        pass
    
    @abstractmethod
    def get_by_repo(self, repo_prefix: str, limit: int = 1000) -> List[SymbolEntity]:
        pass
    
    @abstractmethod
    def get_dependencies(self, entity_id: str, limit: int = 50) -> List[SymbolEntity]:
        pass
    
    @abstractmethod
    def get_callers(self, entity_id: str, limit: int = 50) -> List[SymbolEntity]:
        pass
    
    @abstractmethod
    def update_access(self, entity_id: str) -> None:
        pass
    
    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def iter_all(self, batch_size: int = 1000) -> Iterator[List[SymbolEntity]]:
        pass
    
    @abstractmethod
    def close(self) -> None:
        pass


class InMemoryBackend(MemoryBackend):
    """
    纯内存后端 — 适用于 < 10 万 Entity
    使用 Python 字典 + 倒排索引
    """
    
    def __init__(self):
        self._entities: Dict[str, SymbolEntity] = {}
        self._name_index: Dict[str, List[str]] = {}
        self._type_index: Dict[SymbolType, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}
        self._parent_index: Dict[str, List[str]] = {}
        self._status_index: Dict[SymbolStatus, List[str]] = {}
    
    def insert(self, entity: SymbolEntity) -> str:
        if entity.id in self._entities:
            raise ValueError(f"Entity {entity.id} already exists")
        self._entities[entity.id] = entity
        self._index_entity(entity)
        return entity.id
    
    def get(self, entity_id: str) -> Optional[SymbolEntity]:
        entity = self._entities.get(entity_id)
        if entity:
            entity.touch()
        return entity
    
    def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        entity = self._entities.get(entity_id)
        if not entity:
            return False
        
        old_name = entity.name
        old_type = entity.type
        old_tags = entity.tags.copy()
        old_parent = entity.parent_id
        old_status = entity.status
        
        for key, value in updates.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        entity.updated_at = __import__('datetime').datetime.now().isoformat()
        
        if "name" in updates and updates["name"] != old_name:
            self._reindex_name(entity_id, old_name, entity.name)
        if "type" in updates and updates["type"] != old_type:
            self._reindex_type(entity_id, old_type, entity.type)
        if "tags" in updates and set(updates["tags"]) != set(old_tags):
            self._reindex_tags(entity_id, old_tags, entity.tags)
        if "parent_id" in updates and updates["parent_id"] != old_parent:
            self._reindex_parent(entity_id, old_parent, entity.parent_id)
        if "status" in updates and updates["status"] != old_status:
            self._reindex_status(entity_id, old_status, entity.status)
        
        return True
    
    def delete(self, entity_id: str) -> bool:
        entity = self._entities.pop(entity_id, None)
        if not entity:
            return False
        self._deindex_entity(entity)
        return True
    
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
        results = set(self._entities.keys())
        
        if name:
            results &= set(self._name_index.get(name, []))
        if type:
            results &= set(self._type_index.get(type, []))
        if tag:
            results &= set(self._tag_index.get(tag, []))
        if parent_id:
            results &= set(self._parent_index.get(parent_id, []))
        if status:
            results &= set(self._status_index.get(status, []))
        
        entities = [self._entities[eid] for eid in results if eid in self._entities]
        entities.sort(key=lambda e: e.access_count, reverse=True)
        return entities[offset:offset + limit]
    
    def count(self, **filters) -> int:
        results = set(self._entities.keys())
        if "name" in filters and filters["name"]:
            results &= set(self._name_index.get(filters["name"], []))
        if "type" in filters and filters["type"]:
            results &= set(self._type_index.get(filters["type"], []))
        if "tag" in filters and filters["tag"]:
            results &= set(self._tag_index.get(filters["tag"], []))
        if "parent_id" in filters and filters["parent_id"]:
            results &= set(self._parent_index.get(filters["parent_id"], []))
        if "status" in filters and filters["status"]:
            results &= set(self._status_index.get(filters["status"], []))
        return len(results)
    
    def search_by_source(self, pattern: str, limit: int = 100) -> List[SymbolEntity]:
        results = []
        for entity in self._entities.values():
            if pattern in entity.source:
                results.append(entity)
                if len(results) >= limit:
                    break
        return results
    
    def get_by_repo(self, repo_prefix: str, limit: int = 1000) -> List[SymbolEntity]:
        results = []
        for entity in self._entities.values():
            if entity.file_path.startswith(repo_prefix):
                results.append(entity)
                if len(results) >= limit:
                    break
        return results
    
    def get_dependencies(self, entity_id: str, limit: int = 50) -> List[SymbolEntity]:
        entity = self._entities.get(entity_id)
        if not entity:
            return []
        results = []
        for dep_id in entity.dependencies:
            if dep_id in self._entities:
                results.append(self._entities[dep_id])
                if len(results) >= limit:
                    break
        return results
    
    def get_callers(self, entity_id: str, limit: int = 50) -> List[SymbolEntity]:
        results = []
        for entity in self._entities.values():
            if entity_id in entity.dependencies:
                results.append(entity)
                if len(results) >= limit:
                    break
        return results
    
    def update_access(self, entity_id: str) -> None:
        entity = self._entities.get(entity_id)
        if entity:
            entity.touch()
    
    def stats(self) -> Dict[str, Any]:
        return {
            "total_entities": len(self._entities),
            "by_type": {t.value: len(ids) for t, ids in self._type_index.items()},
            "by_status": {
                SymbolStatus.ACTIVE.value: len(self._status_index.get(SymbolStatus.ACTIVE, [])),
                SymbolStatus.ARCHIVED.value: len(self._status_index.get(SymbolStatus.ARCHIVED, [])),
                SymbolStatus.DEPRECATED.value: len(self._status_index.get(SymbolStatus.DEPRECATED, [])),
            },
            "backend": "in_memory",
            "max_capacity": "~100,000 entities recommended",
        }
    
    def iter_all(self, batch_size: int = 1000) -> Iterator[List[SymbolEntity]]:
        keys = list(self._entities.keys())
        for i in range(0, len(keys), batch_size):
            batch_keys = keys[i:i + batch_size]
            yield [self._entities[k] for k in batch_keys if k in self._entities]
    
    def close(self) -> None:
        self._entities.clear()
        self._name_index.clear()
        self._type_index.clear()
        self._tag_index.clear()
        self._parent_index.clear()
        self._status_index.clear()
    
    # ─── 内部索引管理 ─────────────────────────────────────────────
    
    def _index_entity(self, entity: SymbolEntity) -> None:
        self._name_index.setdefault(entity.name, []).append(entity.id)
        self._type_index.setdefault(entity.type, []).append(entity.id)
        self._status_index.setdefault(entity.status, []).append(entity.id)
        for tag in entity.tags:
            self._tag_index.setdefault(tag, []).append(entity.id)
        if entity.parent_id:
            self._parent_index.setdefault(entity.parent_id, []).append(entity.id)
    
    def _deindex_entity(self, entity: SymbolEntity) -> None:
        if entity.name in self._name_index and entity.id in self._name_index[entity.name]:
            self._name_index[entity.name].remove(entity.id)
        if entity.type in self._type_index and entity.id in self._type_index[entity.type]:
            self._type_index[entity.type].remove(entity.id)
        if entity.status in self._status_index and entity.id in self._status_index[entity.status]:
            self._status_index[entity.status].remove(entity.id)
        for tag in entity.tags:
            if tag in self._tag_index and entity.id in self._tag_index[tag]:
                self._tag_index[tag].remove(entity.id)
        if entity.parent_id and entity.parent_id in self._parent_index:
            if entity.id in self._parent_index[entity.parent_id]:
                self._parent_index[entity.parent_id].remove(entity.id)
    
    def _reindex_name(self, eid: str, old: str, new: str) -> None:
        if old in self._name_index:
            self._name_index[old].remove(eid)
        self._name_index.setdefault(new, []).append(eid)
    
    def _reindex_type(self, eid: str, old: SymbolType, new: SymbolType) -> None:
        if old in self._type_index:
            self._type_index[old].remove(eid)
        self._type_index.setdefault(new, []).append(eid)
    
    def _reindex_status(self, eid: str, old: SymbolStatus, new: SymbolStatus) -> None:
        if old in self._status_index:
            self._status_index[old].remove(eid)
        self._status_index.setdefault(new, []).append(eid)
    
    def _reindex_tags(self, eid: str, old: List[str], new: List[str]) -> None:
        for tag in old:
            if tag in self._tag_index:
                self._tag_index[tag].remove(eid)
        for tag in new:
            self._tag_index.setdefault(tag, []).append(eid)
    
    def _reindex_parent(self, eid: str, old: Optional[str], new: Optional[str]) -> None:
        if old and old in self._parent_index:
            self._parent_index[old].remove(eid)
        if new:
            self._parent_index.setdefault(new, []).append(eid)


class DuckDBBackend(MemoryBackend):
    """
    DuckDB 后端 — 适用于 > 10 万 Entity
    使用列式存储 + SIMD 向量化扫描，内存占用极低
    线程安全：使用 Thread-Local Connection
    """
    
    def __init__(self, db_path: str = ":memory:"):
        try:
            import duckdb
        except ImportError:
            raise ImportError("DuckDB not installed. Run: pip install duckdb")
        
        self.db_path = db_path
        self._local = __import__('threading').local()
        self._init_tables()
    
    @property
    def conn(self):
        """线程局部连接 — 保证并发安全"""
        import duckdb
        if not hasattr(self._local, 'conn'):
            self._local.conn = duckdb.connect(self.db_path)
        return self._local.conn
    
    def _init_tables(self) -> None:
        """初始化表结构 — 使用原生 LIST 类型"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id VARCHAR PRIMARY KEY,
                name VARCHAR,
                type VARCHAR,
                source TEXT,
                file_path VARCHAR,
                line_start INTEGER,
                line_end INTEGER,
                signature VARCHAR,
                docstring TEXT,
                parameters JSON,
                return_type VARCHAR,
                dependencies VARCHAR[],
                callers VARCHAR[],
                parent_id VARCHAR,
                summary TEXT,
                semantic_hash VARCHAR,
                status VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                metadata JSON,
                tags VARCHAR[],
                embedding BLOB,
                tombstone BOOLEAN DEFAULT FALSE
            )
        """)
        
        # DuckDB 的 SIMD 向量化扫描本身极快，不需要传统索引
        # 仅对常用标量字段建立轻量索引，加速过滤查询
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON symbols(name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON symbols(type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON symbols(status)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_tombstone ON symbols(tombstone)")
    
    def insert(self, entity: SymbolEntity) -> str:
        import json
        self.conn.execute("""
            INSERT OR REPLACE INTO symbols (
                id, name, type, source, file_path, line_start, line_end,
                signature, docstring, parameters, return_type,
                dependencies, callers, parent_id, summary,
                semantic_hash, status, created_at, updated_at,
                access_count, last_accessed, metadata, tags, embedding,
                tombstone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity.id, entity.name, entity.type.value, entity.source,
            entity.file_path, entity.line_start, entity.line_end,
            entity.signature, entity.docstring,
            json.dumps(entity.parameters), entity.return_type,
            entity.dependencies, entity.callers,
            entity.parent_id, entity.summary,
            entity.semantic_hash, entity.status.value,
            entity.created_at, entity.updated_at,
            entity.access_count, entity.last_accessed,
            json.dumps(entity.metadata),
            entity.tags,
            json.dumps(entity.embedding) if entity.embedding else None,
            False
        ))
        return entity.id
    
    def get(self, entity_id: str) -> Optional[SymbolEntity]:
        import json
        result = self.conn.execute(
            "SELECT * FROM symbols WHERE id = ? AND tombstone = FALSE",
            (entity_id,)
        ).fetchone()
        if not result:
            return None
        return self._row_to_entity(result)
    
    def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        set_clauses = []
        params = []
        for key, value in updates.items():
            if key in ["parameters", "dependencies", "callers", "metadata", "tags", "embedding"]:
                import json
                value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            params.append(value)
        params.append(entity_id)
        result = self.conn.execute(
            f"UPDATE symbols SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND tombstone = FALSE",
            params
        )
        return result.rowcount > 0
    
    def delete(self, entity_id: str) -> bool:
        result = self.conn.execute(
            "UPDATE symbols SET tombstone = TRUE WHERE id = ?",
            (entity_id,)
        )
        return result.rowcount > 0
    
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
        import json
        conditions = ["tombstone = FALSE"]
        params = []
        
        if name:
            conditions.append("name = ?")
            params.append(name)
        if type:
            conditions.append("type = ?")
            params.append(type.value)
        if parent_id:
            conditions.append("parent_id = ?")
            params.append(parent_id)
        if status:
            conditions.append("status = ?")
            params.append(status.value)
        if tag:
            conditions.append("list_contains(tags, ?)")
            params.append(tag)
        
        sql = "SELECT * FROM symbols"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY access_count DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = self.conn.execute(sql, params).fetchall()
        return [self._row_to_entity(row) for row in results]
    
    def count(self, **filters) -> int:
        conditions = ["tombstone = FALSE"]
        params = []
        for key, value in filters.items():
            if key == "tag":
                conditions.append("list_contains(tags, ?)")
                params.append(value)
            elif key == "type":
                conditions.append("type = ?")
                params.append(value.value if isinstance(value, SymbolType) else value)
            elif key == "status":
                conditions.append("status = ?")
                params.append(value.value if isinstance(value, SymbolStatus) else value)
            else:
                conditions.append(f"{key} = ?")
                params.append(value)
        
        sql = "SELECT COUNT(*) FROM symbols"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        return self.conn.execute(sql, params).fetchone()[0]
    
    def search_by_source(self, pattern: str, limit: int = 100) -> List[SymbolEntity]:
        results = self.conn.execute(
            "SELECT * FROM symbols WHERE source LIKE ? AND tombstone = FALSE LIMIT ?",
            (f"%{pattern}%", limit)
        ).fetchall()
        return [self._row_to_entity(row) for row in results]
    
    def get_by_repo(self, repo_prefix: str, limit: int = 1000) -> List[SymbolEntity]:
        results = self.conn.execute(
            "SELECT * FROM symbols WHERE file_path LIKE ? AND tombstone = FALSE LIMIT ?",
            (f"{repo_prefix}%", limit)
        ).fetchall()
        return [self._row_to_entity(row) for row in results]
    
    def get_dependencies(self, entity_id: str, limit: int = 50) -> List[SymbolEntity]:
        results = self.conn.execute(
            "SELECT * FROM symbols WHERE list_contains(dependencies, ?) AND tombstone = FALSE LIMIT ?",
            (entity_id, limit)
        ).fetchall()
        return [self._row_to_entity(row) for row in results]
    
    def get_callers(self, entity_id: str, limit: int = 50) -> List[SymbolEntity]:
        results = self.conn.execute(
            "SELECT * FROM symbols WHERE list_contains(callers, ?) AND tombstone = FALSE LIMIT ?",
            (entity_id, limit)
        ).fetchall()
        return [self._row_to_entity(row) for row in results]
    
    def update_access(self, entity_id: str) -> None:
        self.conn.execute(
            "UPDATE symbols SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE id = ? AND tombstone = FALSE",
            (entity_id,)
        )
    
    def stats(self) -> Dict[str, Any]:
        total = self.conn.execute("SELECT COUNT(*) FROM symbols WHERE tombstone = FALSE").fetchone()[0]
        tombstone_count = self.conn.execute("SELECT COUNT(*) FROM symbols WHERE tombstone = TRUE").fetchone()[0]
        by_type = self.conn.execute("""
            SELECT type, COUNT(*) FROM symbols WHERE tombstone = FALSE GROUP BY type
        """).fetchall()
        by_status = self.conn.execute("""
            SELECT status, COUNT(*) FROM symbols WHERE tombstone = FALSE GROUP BY status
        """).fetchall()
        return {
            "total_entities": total,
            "tombstone_entities": tombstone_count,
            "by_type": {t: c for t, c in by_type},
            "by_status": {s: c for s, c in by_status},
            "backend": "duckdb",
            "db_path": self.db_path,
            "thread_safe": True,
        }
    
    def iter_all(self, batch_size: int = 1000) -> Iterator[List[SymbolEntity]]:
        offset = 0
        while True:
            rows = self.conn.execute(
                "SELECT * FROM symbols WHERE tombstone = FALSE ORDER BY id LIMIT ? OFFSET ?",
                (batch_size, offset)
            ).fetchall()
            if not rows:
                break
            yield [self._row_to_entity(row) for row in rows]
            offset += batch_size
    
    def vacuum(self) -> int:
        """物理删除所有墓碑记录"""
        result = self.conn.execute("DELETE FROM symbols WHERE tombstone = TRUE")
        return result.rowcount
    
    def close(self) -> None:
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            delattr(self._local, 'conn')
    
    def _row_to_entity(self, row) -> SymbolEntity:
        import json
        from .symbol_entity import SymbolType, SymbolStatus
        
        data = {
            "id": row[0],
            "name": row[1],
            "type": SymbolType(row[2]),
            "source": row[3],
            "file_path": row[4],
            "line_start": row[5],
            "line_end": row[6],
            "signature": row[7],
            "docstring": row[8],
            "parameters": json.loads(row[9]) if row[9] else [],
            "return_type": row[10],
            "dependencies": row[11] if row[11] else [],
            "callers": row[12] if row[12] else [],
            "parent_id": row[13],
            "summary": row[14],
            "semantic_hash": row[15],
            "status": SymbolStatus(row[16]),
            "created_at": row[17].isoformat() if row[17] else None,
            "updated_at": row[18].isoformat() if row[18] else None,
            "access_count": row[19],
            "last_accessed": row[20].isoformat() if row[20] else None,
            "metadata": json.loads(row[21]) if row[21] else {},
            "tags": row[22] if row[22] else [],
            "embedding": json.loads(row[23]) if row[23] else None,
        }
        return SymbolEntity(**data)
