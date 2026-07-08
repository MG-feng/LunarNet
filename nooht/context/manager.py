"""
Context Manager — Token 预算管理与上下文调度
设计原则：
1. 永远不要溢出 Token 限制
2. 压缩优先于丢弃
3. 保留高优先级内容
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class ContextPriority(Enum):
    """上下文优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ARCHIVE = "archive"


@dataclass
class ContextItem:
    """上下文中的一项"""
    id: str
    content: str
    priority: ContextPriority
    token_count: int
    source: str  # e.g., "current", "memory", "retrieved"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """
    上下文管理器 — 管理 Token 预算
    """
    
    def __init__(self, max_tokens: int = 8192):
        self.max_tokens = max_tokens
        self.context: List[ContextItem] = []
        self._token_counter = None
    
    def set_token_counter(self, counter_fn):
        """注入 token 计数函数"""
        self._token_counter = counter_fn
    
    def allocate_context(self, items: List[ContextItem]) -> Tuple[List[ContextItem], bool]:
        """
        分配上下文 — 在 Token 预算内选择最佳组合
        返回：(分配结果，是否有溢出)
        """
        priority_order = {
            ContextPriority.CRITICAL: 0,
            ContextPriority.HIGH: 1,
            ContextPriority.MEDIUM: 2,
            ContextPriority.LOW: 3,
            ContextPriority.ARCHIVE: 4,
        }
        
        sorted_items = sorted(items, key=lambda x: priority_order[x.priority])
        
        allocated = []
        total_tokens = 0
        overflow = False
        
        for item in sorted_items:
            if total_tokens + item.token_count <= self.max_tokens:
                allocated.append(item)
                total_tokens += item.token_count
            else:
                overflow = True
                break
        
        return allocated, overflow
    
    def compress_if_needed(self, threshold_ratio: float = 0.9) -> List[ContextItem]:
        """
        当上下文使用率超过阈值时触发压缩
        返回被压缩的项
        """
        current_tokens = sum(item.token_count for item in self.context)
        usage_ratio = current_tokens / self.max_tokens
        
        if usage_ratio < threshold_ratio:
            return []
        
        priority_order = {
            ContextPriority.CRITICAL: 0,
            ContextPriority.HIGH: 1,
            ContextPriority.MEDIUM: 2,
            ContextPriority.LOW: 3,
            ContextPriority.ARCHIVE: 4,
        }
        
        items_by_priority = sorted(self.context, key=lambda x: priority_order[x.priority])
        
        compressed = []
        new_context = []
        current_tokens = 0
        
        for item in items_by_priority:
            if current_tokens + item.token_count <= self.max_tokens * threshold_ratio:
                new_context.append(item)
                current_tokens += item.token_count
            else:
                compressed.append(item)
        
        self.context = new_context
        return compressed
    
    def retrieve_memory(self, query: str, top_k: int = 3) -> List[ContextItem]:
        """从上下文中检索相关项（基于关键词匹配）"""
        query_terms = set(query.lower().split())
        results = []
        
        for item in self.context:
            content_terms = set(item.content.lower().split())
            score = len(query_terms & content_terms)
            if score > 0:
                results.append((item, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in results[:top_k]]
    
    def remove_redundancy(self) -> List[ContextItem]:
        """移除冗余项（基于内容重叠）"""
        removed = []
        seen_content = set()
        
        new_context = []
        for item in self.context:
            fingerprint = item.content[:100]
            if fingerprint not in seen_content:
                seen_content.add(fingerprint)
                new_context.append(item)
            else:
                removed.append(item)
        
        self.context = new_context
        return removed
    
    def add(self, item: ContextItem) -> None:
        """添加上下文项（自动检查溢出）"""
        if self._token_counter:
            item.token_count = self._token_counter(item.content)
        self.context.append(item)
        
        if sum(i.token_count for i in self.context) > self.max_tokens:
            self.compress_if_needed(0.95)
    
    def clear(self) -> None:
        self.context.clear()
    
    def stats(self) -> Dict[str, Any]:
        total = sum(item.token_count for item in self.context)
        return {
            "total_items": len(self.context),
            "total_tokens": total,
            "usage_ratio": total / self.max_tokens,
            "max_tokens": self.max_tokens,
            "by_priority": {
                p.value: sum(1 for i in self.context if i.priority == p)
                for p in ContextPriority
            },
            "by_source": {
                source: sum(1 for i in self.context if i.source == source)
                for source in set(i.source for i in self.context)
            },
        }
