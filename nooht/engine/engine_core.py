import asyncio
from typing import Dict, Any
from .module_registry import ModuleRegistry
from .pipeline_registry import PipelineRegistry
from .pipeline import PipelineExecutor, Pipeline
import logging

logger = logging.getLogger(__name__)

class NoohtEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.module_registry = ModuleRegistry()
        self.pipeline_registry = PipelineRegistry()
        self.pipeline_executor = PipelineExecutor(self.module_registry)
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}

    async def start(self) -> bool:
        self._running = True
        self._tasks['monitor'] = asyncio.create_task(self._monitor_loop())
        return True

    async def stop(self) -> bool:
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        await self.module_registry.shutdown_all()
        self.pipeline_registry.clear()
        return True

    def register_pipeline(self, pipeline: Pipeline) -> bool:
        return self.pipeline_registry.register(pipeline)

    async def execute_pipeline(self, pipeline_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self._running:
            raise RuntimeError("Engine is not running")
        pipeline = self.pipeline_registry.get(pipeline_name)
        if pipeline is None:
            raise ValueError(f"Pipeline not found: {pipeline_name}")
        return await self.pipeline_executor.execute(pipeline, inputs)

    async def _monitor_loop(self):
        while self._running:
            await asyncio.sleep(10)
