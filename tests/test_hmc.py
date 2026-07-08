import pytest
from nooht.compression.hmc import HMCController, MemoryLevel, SymbolCompressor
from nooht.memory.symbol_entity import SymbolEntity, SymbolType


def test_hmc_compression():
    compressor = SymbolCompressor()
    controller = HMCController(compressor, max_raw_count=5, max_summary_count=3)
    
    entity = SymbolEntity(
        name="test_func",
        type=SymbolType.FUNCTION,
        source="def test_func(x, y): return x + y",
        signature="test_func(x, y)",
    )
    
    cid = controller.add_memory(entity, MemoryLevel.L0_RAW)
    assert cid is not None
    
    stats = controller.stats()
    assert stats["raw"] == 1
    assert stats["total"] == 1


def test_hmc_compression_trigger():
    compressor = SymbolCompressor()
    controller = HMCController(compressor, max_raw_count=3)
    
    for i in range(5):
        entity = SymbolEntity(
            name=f"func_{i}",
            type=SymbolType.FUNCTION,
            source=f"def func_{i}(x): return x",
        )
        controller.add_memory(entity, MemoryLevel.L0_RAW)
    
    stats = controller.stats()
    assert stats["total"] == 5
    assert stats["raw"] <= 3
    assert stats["summary"] >= 2


def test_hmc_force_archive():
    compressor = SymbolCompressor()
    controller = HMCController(compressor, archive_after_days=1)
    
    entity = SymbolEntity(
        name="old_func",
        type=SymbolType.FUNCTION,
        source="def old(): pass",
    )
    controller.add_memory(entity, MemoryLevel.L0_RAW)
    
    import time
    time.sleep(0.1)
    
    archived = controller.force_archive_old(days_threshold=0)
    assert archived >= 1
