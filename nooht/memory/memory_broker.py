import asyncio
from collections import OrderedDict
from typing import Dict, Any, List, Optional
from .memory_interface import MemoryEntry, MemoryLevel, MemoryQuery
from .hmc_compressor import HMCCompressor
from ..engine.module_interface import NoohtModule
import logging

logger = logging.getLogger(__name__)

class MemoryBroker(NoohtModule):
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._l0_memory: OrderedDict = OrderedDict()
        self._l0_max_bytes = config.get("l0_max_bytes", 16 * (1024**3))
        self._current_l0_bytes = 0
        self._hmc_compressor = HMCCompressor("hmc_compressor", config)
        self._lock = None

    def _get_lock(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def initialize(self) -> bool:
        await self._hmc_compressor.initialize()
        return True

    async def execute(self, inputs: dict) -> dict:
        return inputs

    async def cleanup(self) -> bool:
        return True

    async def store(self, entry: MemoryEntry) -> str:
        async with self._get_lock():
            entry_size = entry.estimate_bytes()
            
            while self._current_l0_bytes + entry_size > self._l0_max_bytes:
                if not self._l0_memory:
                    break
                old_id, old_entry = self._l0_memory.popitem(last=False)
                self._current_l0_bytes -= old_entry.estimate_bytes()
                asyncio.create_task(self._hmc_compressor.compress_l0_to_l1([old_entry]))
            
            self._l0_memory[entry.entry_id] = entry
            self._current_l0_bytes += entry_size
            return entry.entry_id
