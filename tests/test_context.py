import pytest
from nooht.context.manager import ContextManager, ContextItem, ContextPriority


def test_context_manager():
    manager = ContextManager(max_tokens=100)
    
    item1 = ContextItem(
        id="1",
        content="x" * 30,
        priority=ContextPriority.HIGH,
        token_count=30,
        source="test"
    )
    item2 = ContextItem(
        id="2",
        content="y" * 40,
        priority=ContextPriority.MEDIUM,
        token_count=40,
        source="test"
    )
    item3 = ContextItem(
        id="3",
        content="z" * 50,
        priority=ContextPriority.LOW,
        token_count=50,
        source="test"
    )
    
    allocated, overflow = manager.allocate_context([item1, item2, item3])
    assert allocated == [item1, item2]
    assert overflow is True


def test_context_manager_compression():
    manager = ContextManager(max_tokens=100)
    
    for i in range(10):
        item = ContextItem(
            id=str(i),
            content=f"content_{i}" * 5,
            priority=ContextPriority.MEDIUM,
            token_count=15,
            source="test"
        )
        manager.add(item)
    
    compressed = manager.compress_if_needed(0.5)
    assert len(compressed) > 0


def test_context_manager_stats():
    manager = ContextManager(max_tokens=1000)
    
    item = ContextItem(
        id="1",
        content="test content",
        priority=ContextPriority.HIGH,
        token_count=10,
        source="test"
    )
    manager.add(item)
    
    stats = manager.stats()
    assert stats["total_items"] == 1
    assert stats["total_tokens"] == 10
    assert stats["max_tokens"] == 1000
