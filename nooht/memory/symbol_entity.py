"""
Symbol Entity — 原子记忆单元
定义：所有代码符号的标准化表示
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from uuid import uuid4
from datetime import datetime


class SymbolType(Enum):
    """符号类型"""
    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    API = "api"
    MODULE = "module"
    CONSTANT = "constant"


class SymbolStatus(Enum):
    """符号生命周期状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


@dataclass
class SymbolEntity:
    """
    核心符号实体 — 框架的原子记忆单元
    设计原则：自包含、可序列化、支持扩展
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    type: SymbolType = SymbolType.FUNCTION
    source: str = ""
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    
    # 签名与文档
    signature: str = ""
    docstring: str = ""
    parameters: List[str] = field(default_factory=list)
    return_type: str = ""
    
    # 关系图谱
    dependencies: List[str] = field(default_factory=list)
    callers: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    
    # 语义信息
    summary: str = ""
    embedding: Optional[List[float]] = None
    semantic_hash: str = ""
    
    # 状态管理
    status: SymbolStatus = SymbolStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    last_accessed: Optional[str] = None
    
    # 扩展字段
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def touch(self) -> None:
        """更新访问时间戳"""
        self.access_count += 1
        self.last_accessed = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "source": self.source,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "signature": self.signature,
            "docstring": self.docstring,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "dependencies": self.dependencies,
            "callers": self.callers,
            "parent_id": self.parent_id,
            "summary": self.summary,
            "embedding": self.embedding,
            "semantic_hash": self.semantic_hash,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "metadata": self.metadata,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SymbolEntity":
        """从字典反序列化"""
        if "type" in data and isinstance(data["type"], str):
            data["type"] = SymbolType(data["type"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = SymbolStatus(data["status"])
        return cls(**data)
