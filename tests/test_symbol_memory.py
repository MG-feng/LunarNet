import pytest
from nooht.memory.symbol_memory import SymbolMemory, SymbolEntity, SymbolType, SymbolStatus


def test_symbol_entity_creation():
    entity = SymbolEntity(
        name="test_func",
        type=SymbolType.FUNCTION,
        source="def test_func(x): return x",
        signature="test_func(x)",
        parameters=["x"],
    )
    assert entity.name == "test_func"
    assert entity.type == SymbolType.FUNCTION
    assert len(entity.id) == 36


def test_symbol_memory_crud():
    memory = SymbolMemory()
    entity = SymbolEntity(name="func1", type=SymbolType.FUNCTION)
    eid = memory.add(entity)
    
    retrieved = memory.get(eid)
    assert retrieved is not None
    assert retrieved.name == "func1"
    
    memory.update(eid, {"name": "func2"})
    updated = memory.get(eid)
    assert updated.name == "func2"
    
    assert memory.remove(eid) is True
    assert memory.get(eid) is None


def test_symbol_memory_query():
    memory = SymbolMemory()
    
    e1 = SymbolEntity(name="login", type=SymbolType.FUNCTION, tags=["auth"])
    e2 = SymbolEntity(name="logout", type=SymbolType.FUNCTION, tags=["auth"])
    e3 = SymbolEntity(name="User", type=SymbolType.CLASS, tags=["model"])
    
    memory.add(e1)
    memory.add(e2)
    memory.add(e3)
    
    results = memory.query(type=SymbolType.FUNCTION)
    assert len(results) == 2
    
    results = memory.query(tag="auth")
    assert len(results) == 2
    
    results = memory.query(name="login")
    assert len(results) == 1
    assert results[0].name == "login"


def test_symbol_memory_dependencies():
    memory = SymbolMemory()
    
    e1 = SymbolEntity(name="parent", type=SymbolType.FUNCTION)
    e2 = SymbolEntity(name="child", type=SymbolType.FUNCTION, dependencies=[e1.id])
    
    memory.add(e1)
    memory.add(e2)
    
    deps = memory.get_dependencies(e2.id)
    assert len(deps) == 1
    assert deps[0].name == "parent"


def test_symbol_memory_stats():
    memory = SymbolMemory()
    
    for i in range(10):
        entity = SymbolEntity(
            name=f"func_{i}",
            type=SymbolType.FUNCTION if i % 2 == 0 else SymbolType.CLASS,
            tags=["test"] if i % 3 == 0 else [],
        )
        memory.add(entity)
    
    stats = memory.stats()
    assert stats["total_entities"] == 10
    assert stats["by_type"]["function"] == 5
    assert stats["by_type"]["class"] == 5
