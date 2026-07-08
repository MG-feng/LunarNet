import pytest
from nooht.memory.backend import InMemoryBackend
from nooht.memory.symbol_memory import SymbolEntity, SymbolType


def test_in_memory_backend_crud():
    backend = InMemoryBackend()
    entity = SymbolEntity(name="test", type=SymbolType.FUNCTION)
    
    eid = backend.insert(entity)
    assert backend.get(eid) is not None
    
    backend.update(eid, {"name": "updated"})
    assert backend.get(eid).name == "updated"
    
    assert backend.delete(eid) is True
    assert backend.get(eid) is None


def test_in_memory_backend_query():
    backend = InMemoryBackend()
    e1 = SymbolEntity(name="login", type=SymbolType.FUNCTION, tags=["auth"])
    e2 = SymbolEntity(name="User", type=SymbolType.CLASS, tags=["model"])
    
    backend.insert(e1)
    backend.insert(e2)
    
    results = backend.query(type=SymbolType.FUNCTION)
    assert len(results) == 1
    assert results[0].name == "login"


def test_in_memory_backend_count():
    backend = InMemoryBackend()
    for i in range(100):
        entity = SymbolEntity(
            name=f"test_{i}",
            type=SymbolType.FUNCTION if i % 2 == 0 else SymbolType.CLASS,
            tags=["auth"] if i % 3 == 0 else [],
        )
        backend.insert(entity)
    
    total = backend.count()
    assert total == 100
    
    by_type = backend.count(type=SymbolType.FUNCTION)
    assert by_type == 50
    
    with_tag = backend.count(tag="auth")
    assert with_tag == 33  # 100/3 ≈ 33


@pytest.mark.skipif(not __import__('importlib').util.find_spec("duckdb"), reason="DuckDB not installed")
def test_duckdb_backend_basic():
    import tempfile
    import os
    from nooht.memory.backend import DuckDBBackend
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        backend = DuckDBBackend(db_path)
        entity = SymbolEntity(
            name="duck_test",
            type=SymbolType.FUNCTION,
            source="def test(): pass",
            tags=["tag1", "tag2"],
            dependencies=["dep1", "dep2"],
        )
        
        eid = backend.insert(entity)
        assert backend.get(eid) is not None
        
        results = backend.query(tag="tag1")
        assert len(results) == 1
        assert results[0].name == "duck_test"
        
        deps = backend.get_dependencies(eid)
        assert len(deps) == 2
        
        stats = backend.stats()
        assert stats["backend"] == "duckdb"
        
        backend.delete(eid)
        assert backend.get(eid) is None
        
        removed = backend.vacuum()
        assert removed >= 1
        
    finally:
        os.unlink(db_path)
